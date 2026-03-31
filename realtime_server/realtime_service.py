import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

import websockets
from websockets.server import WebSocketServerProtocol

# 导入前面实现的模块
from location_service import LocationOptimizer, LocationData
from distance_calculator import DistanceCalculator, GeoPoint
from state_manager import StateManager, OnlineStatus, LocationSyncStatus, ChatConnectionStatus
from data_sync import DataSynchronizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    nickname: str
    schedule: List[dict] = field(default_factory=list)
    location: Optional[LocationData] = None


@dataclass
class MatchResult:
    """匹配结果"""
    user_id: str
    nickname: str
    distance: float
    schedule_similarity: float
    match_score: float


@dataclass
class ChatMessage:
    """聊天消息"""
    msg_id: str
    from_user: str
    to_user: str
    content: str
    timestamp: float
    read: bool = False
    
    def to_dict(self):
        return {
            'msg_id': self.msg_id,
            'from_user': self.from_user,
            'to_user': self.to_user,
            'content': self.content,
            'timestamp': self.timestamp,
            'read': self.read
        }


class RealtimeService:
    """
    实时通信与定位服务（完整版）
    整合所有模块提供统一服务
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        
        # 初始化各模块
        self.location_optimizer = LocationOptimizer()
        self.distance_calculator = DistanceCalculator()
        self.state_manager = StateManager()
        self.data_sync = DataSynchronizer()
        
        # WebSocket连接管理
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        
        # 用户档案（简化版，实际应从后端加载）
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # 聊天记录
        self.chat_history: Dict[str, List[ChatMessage]] = {}  # session_key -> messages
        
        # 匹配关系
        self.match_relations: Dict[str, Set[str]] = {}  # user_id -> {matched_user_ids}
        
        # 运行状态
        self.running = False
    
    async def start(self):
        """启动服务"""
        self.running = True
        
        # 启动数据同步服务
        await self.data_sync.start()
        
        # 启动WebSocket服务器
        logger.info(f"实时服务启动于 ws://{self.host}:{self.port}")
        
        # 启动定时任务
        asyncio.create_task(self._periodic_tasks())
        
        # 启动WebSocket服务
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        ):
            await asyncio.Future()
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """处理WebSocket连接"""
        addr = websocket.remote_address
        logger.info(f"新连接: {addr}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._route_message(websocket, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON")
                except Exception as e:
                    logger.error(f"处理错误: {e}")
                    await self._send_error(websocket, str(e))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._cleanup(websocket)
    
    async def _route_message(self, ws: WebSocketServerProtocol, data: dict):
        """路由消息"""
        msg_type = data.get('type')
        payload = data.get('data', {})
        
        # 认证
        if msg_type == 'auth':
            await self._handle_auth(ws, payload)
            return
        
        # 获取用户ID
        user_id = self._get_user_id(ws)
        if not user_id:
            await self._send_error(ws, "请先认证")
            return
        
        # 更新活跃时间
        self.state_manager.get_state(user_id).update_active()
        
        # 路由到处理器
        handlers = {
            'location_update': self._handle_location_update,
            'scan_nearby': self._handle_scan_nearby,
            'find_matches': self._handle_find_matches,
            'send_message': self._handle_send_message,
            'get_history': self._handle_get_history,
            'ping': self._handle_ping,
            'toggle_match': self._handle_toggle_match,
            'start_chat': self._handle_start_chat,
            'end_chat': self._handle_end_chat,
        }
        
        handler = handlers.get(msg_type)
        if handler:
            await handler(user_id, payload, ws)
        else:
            await self._send_error(ws, f"未知消息类型: {msg_type}")
    
    # ========== 消息处理器 ==========
    
    async def _handle_auth(self, ws: WebSocketServerProtocol, data: dict):
        """用户认证"""
        user_id = data.get('user_id')
        nickname = data.get('nickname', 'Unknown')
        schedule = data.get('schedule', [])
        match_switch = data.get('match_switch', True)
        
        if not user_id:
            await self._send_error(ws, "user_id不能为空")
            return
        
        # 保存连接
        self.connections[user_id] = ws
        
        # 创建用户档案
        self.user_profiles[user_id] = UserProfile(
            user_id=user_id,
            nickname=nickname,
            schedule=schedule
        )
        
        # 更新状态
        self.state_manager.set_online(user_id, str(id(ws)))
        self.state_manager.set_match_enabled(user_id, match_switch)
        
        # 发送成功响应
        await ws.send(json.dumps({
            'type': 'auth_success',
            'data': {
                'user_id': user_id,
                'server_time': time.time()
            }
        }))
        
        logger.info(f"用户 {user_id} ({nickname}) 已连接")
    
    async def _handle_location_update(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """处理位置更新（核心功能1）"""
        lat = data.get('latitude')
        lon = data.get('longitude')
        accuracy = data.get('accuracy', 10.0)
        
        if lat is None or lon is None:
            await self._send_error(ws, "经纬度不能为空")
            return
        
        # 创建原始位置数据
        raw_location = LocationData(
            user_id=user_id,
            latitude=lat,
            longitude=lon,
            accuracy=accuracy,
            timestamp=time.time()
        )
        
        # 优化位置（GPS平滑、异常过滤）
        optimized = self.location_optimizer.optimize(user_id, raw_location)
        
        if not optimized:
            await self._send_error(ws, "位置数据无效")
            return
        
        # 更新用户档案
        self.user_profiles[user_id].location = optimized
        
        # 更新状态
        self.state_manager.set_location_synced(user_id, {
            'lat': optimized.latitude,
            'lon': optimized.longitude,
            'accuracy': optimized.accuracy
        })
        
        # 同步给后端和NLP模块
        await self.data_sync.sync_location(user_id, {
            'latitude': optimized.latitude,
            'longitude': optimized.longitude,
            'accuracy': optimized.accuracy,
            'timestamp': optimized.timestamp
        })
        
        # 响应客户端
        await ws.send(json.dumps({
            'type': 'location_updated',
            'data': {
                'latitude': optimized.latitude,
                'longitude': optimized.longitude,
                'accuracy': optimized.accuracy
            }
        }))
        
        logger.debug(f"用户 {user_id} 位置更新: ({optimized.latitude:.6f}, {optimized.longitude:.6f})")
    
    async def _handle_scan_nearby(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """处理200米路人扫描（核心功能2）"""
        # 检查权限
        state = self.state_manager.get_state(user_id)
        if not state.match_enabled:
            await ws.send(json.dumps({
                'type': 'permission_denied',
                'data': {'message': '匹配开关已关闭'}
            }))
            return
        
        # 获取当前用户位置
        user_profile = self.user_profiles.get(user_id)
        if not user_profile or not user_profile.location:
            await self._send_error(ws, "位置信息不可用，请先更新位置")
            return
        
        # 构建中心点
        center = GeoPoint(
            user_id=user_id,
            latitude=user_profile.location.latitude,
            longitude=user_profile.location.longitude
        )
        
        # 构建所有其他用户点
        other_points = []
        for uid, profile in self.user_profiles.items():
            if uid != user_id and profile.location:
                other_points.append(GeoPoint(
                    user_id=uid,
                    latitude=profile.location.latitude,
                    longitude=profile.location.longitude,
                    allow_match=self.state_manager.get_state(uid).match_enabled
                ))
        
        # 执行200米范围扫描
        nearby = self.distance_calculator.find_nearby_users(center, other_points)
        
        # 构建结果
        results = []
        for point, distance in nearby:
            profile = self.user_profiles.get(point.user_id)
            results.append({
                'user_id': point.user_id,
                'nickname': profile.nickname if profile else 'Unknown',
                'distance': round(distance, 1),
                'status': self.state_manager.get_state(point.user_id).online_status.value
            })
        
        await ws.send(json.dumps({
            'type': 'scan_results',
            'data': {
                'count': len(results),
                'users': results,
                'radius': 200,
                'timestamp': time.time()
            }
        }))
        
        logger.info(f"用户 {user_id} 扫描完成，发现 {len(results)} 个附近用户")
    
    async def _handle_find_matches(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """处理行程匹配（核心功能3）"""
        # 检查权限
        state = self.state_manager.get_state(user_id)
        if not state.match_enabled:
            await ws.send(json.dumps({
                'type': 'permission_denied',
                'data': {'message': '匹配开关已关闭'}
            }))
            return
        
        # 设置匹配中状态
        self.state_manager.set_matching(user_id)
        
        # 获取当前用户
        user_profile = self.user_profiles.get(user_id)
        if not user_profile or not user_profile.location:
            await self._send_error(ws, "位置信息不可用")
            return
        
        # 200米范围筛选
        center = GeoPoint(
            user_id=user_id,
            latitude=user_profile.location.latitude,
            longitude=user_profile.location.longitude
        )
        
        candidates = []
        for uid, profile in self.user_profiles.items():
            if uid != user_id and profile.location:
                candidates.append(GeoPoint(
                    user_id=uid,
                    latitude=profile.location.latitude,
                    longitude=profile.location.longitude,
                    allow_match=self.state_manager.get_state(uid).match_enabled
                ))
        
        nearby = self.distance_calculator.find_nearby_users(center, candidates)
        
        # 行程相似度计算（简化版，实际应调用NLP模块）
        matches = []
        for point, distance in nearby:
            similarity = self._calculate_schedule_similarity(
                user_profile.schedule,
                self.user_profiles[point.user_id].schedule
            )
            
            if similarity >= 0.6:  # 60%相似度阈值
                match = MatchResult(
                    user_id=point.user_id,
                    nickname=self.user_profiles[point.user_id].nickname,
                    distance=distance,
                    schedule_similarity=similarity,
                    match_score=(1 - distance/200) * 0.5 + similarity * 0.5
                )
                matches.append(match)
                
                # 记录匹配关系
                if user_id not in self.match_relations:
                    self.match_relations[user_id] = set()
                self.match_relations[user_id].add(point.user_id)
        
        # 按匹配度排序
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # 发送结果给请求者
        await ws.send(json.dumps({
            'type': 'match_results',
            'data': {
                'count': len(matches),
                'matches': [
                    {
                        'user_id': m.user_id,
                        'nickname': m.nickname,
                        'distance': m.distance,
                        'similarity': round(m.schedule_similarity, 2),
                        'score': round(m.match_score * 100, 1)
                    }
                    for m in matches
                ]
            }
        }))
        
        # 实时推送匹配提醒给匹配到的用户（弹窗提示）
        for match in matches:
            await self._send_to_user(match.user_id, {
                'type': 'match_notification',
                'data': {
                    'from_user': user_id,
                    'nickname': user_profile.nickname,
                    'distance': match.distance,
                    'message': f"发现行程相似的附近用户：{user_profile.nickname}，距离{match.distance:.1f}米"
                }
            })
        
        # 同步匹配结果给后端
        await self.data_sync.sync_match_result(user_id, [
            {
                'user_id': m.user_id,
                'distance': m.distance,
                'similarity': m.schedule_similarity
            }
            for m in matches
        ])
        
        logger.info(f"用户 {user_id} 匹配完成，找到 {len(matches)} 个匹配")
    
    async def _handle_send_message(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """处理聊天消息（核心功能4）"""
        to_user = data.get('to_user')
        content = data.get('content', '').strip()
        
        if not to_user or not content:
            await self._send_error(ws, "接收者ID和消息内容不能为空")
            return
        
        # 检查是否已匹配
        if not self._can_chat(user_id, to_user):
            await self._send_error(ws, "只能与已匹配的用户聊天")
            return
        
        # 创建消息
        msg = ChatMessage(
            msg_id=f"{int(time.time()*1000)}_{user_id}",
            from_user=user_id,
            to_user=to_user,
            content=content,
            timestamp=time.time()
        )
        
        # 保存历史
        session_key = self._get_session_key(user_id, to_user)
        if session_key not in self.chat_history:
            self.chat_history[session_key] = []
        self.chat_history[session_key].append(msg)
        
        # 限制历史长度
        if len(self.chat_history[session_key]) > 100:
            self.chat_history[session_key].pop(0)
        
        # 实时转发
        success = await self._send_to_user(to_user, {
            'type': 'chat_message',
            'data': msg.to_dict()
        })
        
        if success:
            msg.read = True
            await ws.send(json.dumps({
                'type': 'message_sent',
                'data': {'msg_id': msg.msg_id, 'timestamp': msg.timestamp}
            }))
        else:
            # 用户离线，保存未读
            self.state_manager.add_unread(to_user)
            await ws.send(json.dumps({
                'type': 'message_cached',
                'data': {'msg_id': msg.msg_id, 'reason': 'user_offline'}
            }))
    
    async def _handle_get_history(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """获取聊天历史"""
        target_user = data.get('target_user')
        if not target_user:
            return
        
        session_key = self._get_session_key(user_id, target_user)
        history = self.chat_history.get(session_key, [])
        
        await ws.send(json.dumps({
            'type': 'chat_history',
            'data': {
                'target_user': target_user,
                'messages': [m.to_dict() for m in history[-50:]]  # 最近50条
            }
        }))
    
    async def _handle_ping(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """心跳"""
        await ws.send(json.dumps({
            'type': 'pong',
            'data': {'timestamp': time.time()}
        }))
    
    async def _handle_toggle_match(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """切换匹配开关"""
        enable = data.get('enable', True)
        self.state_manager.set_match_enabled(user_id, enable)
        
        await ws.send(json.dumps({
            'type': 'match_switch_updated',
            'data': {'enabled': enable}
        }))
    
    async def _handle_start_chat(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """开始聊天"""
        partner_id = data.get('partner_id')
        if not partner_id or not self._can_chat(user_id, partner_id):
            await self._send_error(ws, "无法与该用户聊天")
            return
        
        self.state_manager.set_chatting(user_id, partner_id)
        await ws.send(json.dumps({
            'type': 'chat_started',
            'data': {'partner_id': partner_id}
        }))
    
    async def _handle_end_chat(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """结束聊天"""
        self.state_manager.end_chat(user_id)
        await ws.send(json.dumps({
            'type': 'chat_ended',
            'data': {}
        }))
    
    # ========== 辅助方法 ==========
    
    def _get_user_id(self, ws: WebSocketServerProtocol) -> Optional[str]:
        """通过WebSocket获取用户ID"""
        for uid, conn in self.connections.items():
            if conn == ws:
                return uid
        return None
    
    def _can_chat(self, user1: str, user2: str) -> bool:
        """检查两个用户是否可以聊天"""
        if user1 in self.match_relations:
            return user2 in self.match_relations[user1]
        return False
    
    def _get_session_key(self, user1: str, user2: str) -> str:
        """生成会话key"""
        return f"{min(user1, user2)}_{max(user1, user2)}"
    
    async def _send_to_user(self, user_id: str, message: dict) -> bool:
        """发送消息给指定用户"""
        if user_id not in self.connections:
            return False
        
        try:
            await self.connections[user_id].send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"发送消息给 {user_id} 失败: {e}")
            return False
    
    async def _send_error(self, ws: WebSocketServerProtocol, message: str):
        """发送错误"""
        try:
            await ws.send(json.dumps({
                'type': 'error',
                'data': {'message': message}
            }))
        except:
            pass
    
    async def _cleanup(self, ws: WebSocketServerProtocol):
        """清理连接"""
        user_id = self._get_user_id(ws)
        if user_id:
            self.state_manager.set_offline(user_id)
            if user_id in self.connections:
                del self.connections[user_id]
            logger.info(f"用户 {user_id} 断开连接")
    
    def _calculate_schedule_similarity(self, schedule1: List[dict], schedule2: List[dict]) -> float:
        """计算行程相似度（简化版，实际应调用NLP模块）"""
        if not schedule1 or not schedule2:
            return 0.0
        
        # 简单计算：检查是否有相同类型和时间的行程
        score = 0.0
        for s1 in schedule1:
            for s2 in schedule2:
                # 时间重叠检查（简化）
                if s1.get('type') == s2.get('type'):
                    score += 0.5
                if s1.get('location') == s2.get('location'):
                    score += 0.5
        
        return min(score / max(len(schedule1), len(schedule2)), 1.0)
    
    async def _periodic_tasks(self):
        """定时任务"""
        while self.running:
            await asyncio.sleep(30)
            
            # 清理不活跃用户
            cleaned = self.state_manager.cleanup_inactive(300)
            if cleaned > 0:
                logger.info(f"清理了 {cleaned} 个不活跃用户")
            
            # 输出统计
            stats = self.state_manager.get_all_status_summary()
            logger.info(f"系统状态: {stats}")


# ========== 启动入口 ==========
async def main():
    service = RealtimeService(host="0.0.0.0", port=8765)
    await service.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务已停止")