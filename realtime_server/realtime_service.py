import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import aiohttp
import websockets
from websockets.server import WebSocketServerProtocol
# 引入统一的状态管理器，收敛状态逻辑
from state_manager import StateManager, OnlineStatus, LocationSyncStatus
# 引入数据同步器
from data_sync import DataSynchronizer
# 引入距离计算器
from distance_calculator import DistanceCalculator, GeoPoint

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== 配置 ==========
class Config:
    """服务配置 - 从.env文件读取，无需修改代码"""
    WS_HOST = "0.0.0.0"
    WS_PORT = 8765
    BACKEND_URL = "http://localhost:8000"
    NLP_URL = "http://localhost:8001"
    PING_INTERVAL = 20
    PING_TIMEOUT = 10
    SCAN_RADIUS = 200  
    MATCH_NOTIFY_LIMIT = 5  # 每分钟最多推送5条匹配提醒
    CHAT_HISTORY_RETENTION = 86400  # 聊天记录保留24小时

# 加载.env配置
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    Config.WS_PORT = int(os.getenv("WS_PORT", Config.WS_PORT))
    Config.BACKEND_URL = os.getenv("BACKEND_URL", Config.BACKEND_URL)
    Config.NLP_URL = os.getenv("NLP_URL", Config.NLP_URL)
    Config.SCAN_RADIUS = int(os.getenv("SCAN_RADIUS", Config.SCAN_RADIUS))
    Config.MATCH_NOTIFY_LIMIT = int(os.getenv("MATCH_NOTIFY_LIMIT", Config.MATCH_NOTIFY_LIMIT))
    Config.CHAT_HISTORY_RETENTION = int(os.getenv("CHAT_HISTORY_RETENTION", Config.CHAT_HISTORY_RETENTION))
except Exception as e:
    logger.warning(f"加载.env配置失败，使用默认配置: {e}")

@dataclass
class UserConnection:
    """用户连接信息"""
    user_id: str
    websocket: WebSocketServerProtocol
    nickname: str = ""
    last_ping: float = field(default_factory=time.time)
    match_enabled: bool = True
    match_notify_count: int = 0
    last_notify_reset: float = field(default_factory=time.time)
    blocked_users: Set[str] = field(default_factory=set)

@dataclass
class ChatMessage:
    """聊天消息结构"""
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
    """实时通信核心服务"""
    def __init__(self):
        self.host = Config.WS_HOST
        self.port = Config.WS_PORT
        self.backend_url = Config.BACKEND_URL
        self.nlp_url = Config.NLP_URL
        
        self.connections: Dict[str, UserConnection] = {}
        self.user_sockets: Dict[WebSocketServerProtocol, str] = {}
        self.chat_history: Dict[str, List[ChatMessage]] = {}
        self.match_relations: Dict[str, Set[str]] = {}
        
        # 统一依赖注入
        self.state_manager = StateManager()
        self.distance_calculator = DistanceCalculator(scan_radius=Config.SCAN_RADIUS)
        self.data_syncer = DataSynchronizer(backend_url=self.backend_url, nlp_url=self.nlp_url)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.running = False

    async def start(self):
        """启动服务"""
        self.running = True
        self.http_session = aiohttp.ClientSession()
        await self.data_syncer.start()
        logger.info(f"实时服务启动于 ws://{self.host}:{self.port}")
        logger.info(f"后端API地址: {self.backend_url}")
        logger.info(f"默认扫描半径: {self.distance_calculator.SCAN_RADIUS}米")

        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=Config.PING_INTERVAL,
            ping_timeout=Config.PING_TIMEOUT
        ):
            asyncio.create_task(self._periodic_tasks())
            await asyncio.Future()

    async def stop(self):
        """停止服务"""
        self.running = False
        if self.http_session:
            await self.http_session.close()
        await self.data_syncer.stop()

    # ========== WebSocket核心消息处理 ==========
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """处理新连接"""
        addr = websocket.remote_address
        logger.info(f"新连接: {addr}")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._route_message(websocket, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "消息格式错误：需要JSON")
                except Exception as e:
                    logger.error(f"处理错误: {e}")
                    await self._send_error(websocket, str(e))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._cleanup(websocket)

    async def _route_message(self, ws: WebSocketServerProtocol, data: dict):
        """消息路由分发"""
        msg_type = data.get('type')
        payload = data.get('data', {})
        
        if msg_type == 'auth':
            await self._handle_auth(ws, payload)
            return
        
        user_id = self.user_sockets.get(ws)
        if not user_id:
            await self._send_error(ws, "请先发送认证消息")
            return
        
        if user_id in self.connections:
            self.connections[user_id].last_ping = time.time()
            self.state_manager.get_state(user_id).update_active()

        # 消息处理器映射
        handlers = {
            'ping': self._handle_ping,
            'send_message': self._handle_send_message,
            'get_history': self._handle_get_history,
            'start_chat': self._handle_start_chat,
            'end_chat': self._handle_end_chat,
            'update_status': self._handle_status_update,
            'notify_match': self._handle_match_notification,
            'trigger_scan': self._handle_trigger_scan,
            'block_user': self._handle_block_user,
            'upload_location': self._handle_upload_location,
        }
        handler = handlers.get(msg_type)
        if handler:
            await handler(user_id, payload, ws)
        else:
            await self._send_error(ws, f"未知消息类型: {msg_type}")

    # ========== 1. 认证与权限（对接后端登录体系） ==========
    async def _handle_auth(self, ws: WebSocketServerProtocol, data: dict):
        """用户认证，完全复用后端权限体系"""
        user_id = data.get('user_id')
        token = data.get('token')
        nickname = data.get('nickname', 'Unknown')
        match_switch = data.get('match_switch', True)

        if not user_id or not token:
            await self._send_error(ws, "user_id和token不能为空")
            return

        # 对接后端校验token有效性
        try:
            async with self.http_session.post(
                f"{self.backend_url}/api/auth/verify",
                json={"user_id": user_id, "token": token},
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status != 200:
                    await self._send_error(ws, "登录态无效，请重新登录")
                    return
                auth_result = await response.json()
                match_switch = auth_result.get('match_enabled', match_switch)
        except Exception as e:
            logger.error(f"后端权限校验失败: {e}")
            await self._send_error(ws, "权限校验失败，请检查网络")
            return

        # 处理多端登录
        if user_id in self.connections:
            old_conn = self.connections[user_id]
            try:
                await old_conn.websocket.close(1000, "新设备登录")
            except:
                pass
            logger.info(f"用户 {user_id} 重新登录，断开旧连接")

        # 创建新连接
        conn = UserConnection(
            user_id=user_id,
            websocket=ws,
            nickname=nickname,
            match_enabled=match_switch
        )
        self.connections[user_id] = conn
        self.user_sockets[ws] = user_id

        # 更新状态管理器
        self.state_manager.set_online(user_id, connection_id=str(id(ws)))
        self.state_manager.set_match_enabled(user_id, match_switch)

        logger.info(f"用户 {user_id} ({nickname}) 已连接，匹配开关: {match_switch}")
        await ws.send(json.dumps({
            'type': 'auth_success',
            'data': {
                'user_id': user_id,
                'server_time': time.time(),
                'online_users': len(self.connections),
                'match_enabled': match_switch
            }
        }))

        await self._broadcast_to_matches(user_id, {
            'type': 'user_online',
            'data': {'user_id': user_id, 'nickname': nickname}
        })

    # ========== 2. 定位上传与同步（分工文档核心要求） ==========
    async def _handle_upload_location(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """处理前端定位上传，优化后同步给后端和NLP"""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy', 100)

        if latitude is None or longitude is None:
            await self._send_error(ws, "经纬度不能为空")
            return

        self.state_manager.set_location_syncing(user_id)

        # 定位优化处理
        from location_service import LocationData, LocationOptimizer
        loc_optimizer = LocationOptimizer()
        raw_loc = LocationData(user_id=user_id, latitude=latitude, longitude=longitude, accuracy=accuracy)
        optimized_loc = loc_optimizer.optimize(user_id, raw_loc)

        if not optimized_loc:
            self.state_manager.set_location_error(user_id, "定位数据无效")
            await self._send_error(ws, "定位数据无效")
            return

        # 更新定位状态
        self.state_manager.set_location_synced(user_id, {
            'latitude': optimized_loc.latitude,
            'longitude': optimized_loc.longitude,
            'accuracy': optimized_loc.accuracy
        })

        # 异步同步给后端和NLP
        await self.data_syncer.sync_location(
            user_id=user_id,
            location={
                'latitude': optimized_loc.latitude,
                'longitude': optimized_loc.longitude,
                'accuracy': optimized_loc.accuracy,
                'timestamp': optimized_loc.timestamp
            },
            priority=False
        )

        await ws.send(json.dumps({
            'type': 'location_uploaded',
            'data': {
                'latitude': optimized_loc.latitude,
                'longitude': optimized_loc.longitude,
                'accuracy': optimized_loc.accuracy,
                'status': 'synced'
            }
        }))
        logger.info(f"用户 {user_id} 定位数据已同步")

    # ========== 3. 实时扫描全链路（分工文档核心要求） ==========
    async def _handle_trigger_scan(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """处理前端扫描请求，完成范围筛选→NLP匹配→结果推送全流程"""
        custom_radius = data.get('radius', Config.SCAN_RADIUS)

        # 权限校验
        conn = self.connections.get(user_id)
        if not conn or not conn.match_enabled:
            await self._send_error(ws, "请先开启匹配开关，才能使用扫描功能")
            return

        user_state = self.state_manager.get_state(user_id)
        if user_state.location_status != LocationSyncStatus.SYNCED:
            await self._send_error(ws, "定位未同步，请先开启定位权限")
            return

        self.state_manager.set_matching(user_id)
        user_loc = user_state.last_location
        center_point = GeoPoint(
            user_id=user_id,
            latitude=user_loc['latitude'],
            longitude=user_loc['longitude'],
            allow_match=conn.match_enabled
        )

        # 从后端获取开启匹配的用户列表
        try:
            async with self.http_session.get(
                f"{self.backend_url}/api/user/matchable_list",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status != 200:
                    await self._send_error(ws, "获取用户列表失败")
                    self.state_manager.set_online(user_id, str(id(ws)))
                    return
                user_list = await response.json()
        except Exception as e:
            logger.error(f"获取匹配用户列表失败: {e}")
            await self._send_error(ws, "获取用户列表失败，请检查网络")
            self.state_manager.set_online(user_id, str(id(ws)))
            return

        # 筛选范围内用户
        all_points = []
        for user in user_list:
            if user['user_id'] == user_id:
                continue
            all_points.append(GeoPoint(
                user_id=user['user_id'],
                latitude=user['latitude'],
                longitude=user['longitude'],
                allow_match=user['match_enabled']
            ))
        nearby_users = self.distance_calculator.find_nearby_users(
            center_user=center_point,
            all_users=all_points,
            custom_radius=custom_radius
        )

        # 调用NLP模块做行程匹配
        nearby_user_ids = [user.user_id for user, distance in nearby_users]
        try:
            async with self.http_session.post(
                f"{self.nlp_url}/api/match/nearby",
                json={'user_id': user_id, 'nearby_user_ids': nearby_user_ids, 'radius': custom_radius},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                match_result = await response.json() if response.status == 200 else {'matches': []}
        except Exception as e:
            logger.error(f"NLP匹配调用失败: {e}")
            match_result = {'matches': []}

        # 合并结果推送给前端
        scan_result = []
        for user, distance in nearby_users:
            match_info = next((m for m in match_result['matches'] if m['user_id'] == user.user_id), None)
            scan_result.append({
                'user_id': user.user_id,
                'nickname': self.connections.get(user.user_id, UserConnection(user.user_id, None)).nickname,
                'distance': round(distance, 2),
                'match_score': match_info.get('score', 0) if match_info else 0,
                'trip_summary': match_info.get('trip_summary', '') if match_info else ''
            })

        await ws.send(json.dumps({
            'type': 'scan_result',
            'data': {'radius': custom_radius, 'count': len(scan_result), 'nearby_users': scan_result}
        }))
        self.state_manager.set_online(user_id, str(id(ws)))
        await self.data_syncer.sync_match_result(user_id, scan_result)
        logger.info(f"用户 {user_id} 扫描完成，发现{len(scan_result)}个附近用户")

    # ========== 4. 聊天消息处理（优化拉黑、合规审核） ==========
    async def _handle_send_message(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """发送聊天消息，新增拉黑拦截、合规审核"""
        to_user = data.get('to_user')
        content = data.get('content', '').strip()

        if not to_user or not content:
            await self._send_error(ws, "接收者ID和消息内容不能为空")
            return

        # 拉黑拦截
        to_conn = self.connections.get(to_user)
        if to_conn and user_id in to_conn.blocked_users:
            await self._send_error(ws, "消息发送失败，对方已拒收您的消息")
            return

        # 匹配关系校验
        if not self._can_chat(user_id, to_user):
            await self._send_error(ws, "只能与已匹配的用户聊天")
            return

        # 内容合规审核（对接后端）
        try:
            async with self.http_session.post(
                f"{self.backend_url}/api/content/audit",
                json={"content": content, "from_user": user_id, "to_user": to_user},
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                audit_result = await response.json()
                if not audit_result.get('pass', True):
                    await self._send_error(ws, "消息包含违规内容，无法发送")
                    return
        except Exception as e:
            logger.warning(f"内容审核调用失败，放行消息: {e}")

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
        if len(self.chat_history[session_key]) > 100:
            self.chat_history[session_key].pop(0)

        # 实时转发
        success = await self._send_to_user(to_user, {
            'type': 'chat_message',
            'data': {**msg.to_dict(), 'from_nickname': self.connections[user_id].nickname}
        })

        # 发送回执
        if success:
            msg.read = True
            await ws.send(json.dumps({
                'type': 'message_sent',
                'data': {'msg_id': msg.msg_id, 'timestamp': msg.timestamp, 'delivered': True}
            }))
            logger.info(f"消息已送达: {user_id} -> {to_user}")
        else:
            await ws.send(json.dumps({
                'type': 'message_sent',
                'data': {'msg_id': msg.msg_id, 'timestamp': msg.timestamp, 'delivered': False, 'reason': 'offline'}
            }))
            logger.info(f"消息已缓存（对方离线）: {user_id} -> {to_user}")

    # ========== 辅助方法与其他处理器 ==========
    async def _handle_block_user(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """拉黑用户"""
        blocked_user_id = data.get('blocked_user_id')
        if not blocked_user_id:
            await self._send_error(ws, "被拉黑用户ID不能为空")
            return

        conn = self.connections.get(user_id)
        if not conn:
            return

        conn.blocked_users.add(blocked_user_id)
        if user_id in self.match_relations:
            self.match_relations[user_id].discard(blocked_user_id)
        if blocked_user_id in self.match_relations:
            self.match_relations[blocked_user_id].discard(user_id)

        await ws.send(json.dumps({
            'type': 'user_blocked',
            'data': {'blocked_user_id': blocked_user_id}
        }))
        logger.info(f"用户 {user_id} 拉黑了 {blocked_user_id}")

    async def _handle_match_notification(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        """匹配成功通知，新增防骚扰限流"""
        matched_user_id = data.get('matched_user_id')
        matched_nickname = data.get('matched_nickname', 'Unknown')
        distance = data.get('distance', 0)

        if not matched_user_id:
            return

        conn = self.connections.get(user_id)
        if not conn or not conn.match_enabled:
            return

        # 限流控制
        current_time = time.time()
        if current_time - conn.last_notify_reset > 60:
            conn.match_notify_count = 0
            conn.last_notify_reset = current_time
        if conn.match_notify_count >= Config.MATCH_NOTIFY_LIMIT:
            logger.warning(f"用户 {user_id} 匹配提醒超限，拒绝推送")
            return
        conn.match_notify_count += 1

        # 建立匹配关系
        if user_id not in self.match_relations:
            self.match_relations[user_id] = set()
        self.match_relations[user_id].add(matched_user_id)
        if matched_user_id not in self.match_relations:
            self.match_relations[matched_user_id] = set()
        self.match_relations[matched_user_id].add(user_id)

        logger.info(f"建立匹配关系: {user_id} <-> {matched_user_id}")
        await ws.send(json.dumps({
            'type': 'match_ready',
            'data': {'matched_user_id': matched_user_id, 'matched_nickname': matched_nickname, 'distance': distance, 'can_chat': True}
        }))
        await self._send_to_user(matched_user_id, {
            'type': 'match_notification',
            'data': {'from_user': user_id, 'nickname': conn.nickname, 'distance': distance, 'message': f"发现行程相似的附近用户：{conn.nickname}，距离{distance:.1f}米"}
        })

    async def _handle_ping(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        await ws.send(json.dumps({'type': 'pong', 'data': {'timestamp': time.time(), 'user_id': user_id}}))

    async def _handle_get_history(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        target_user = data.get('target_user')
        if not target_user:
            return
        session_key = self._get_session_key(user_id, target_user)
        history = self.chat_history.get(session_key, [])
        await ws.send(json.dumps({
            'type': 'chat_history',
            'data': {'target_user': target_user, 'messages': [m.to_dict() for m in history[-50:]]}
        }))

    async def _handle_start_chat(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        partner_id = data.get('partner_id')
        if not partner_id or not self._can_chat(user_id, partner_id):
            await self._send_error(ws, "无法与该用户聊天（未匹配）")
            return
        self.state_manager.set_chatting(user_id, partner_id)
        await ws.send(json.dumps({'type': 'chat_started', 'data': {'partner_id': partner_id}}))
        await self._send_to_user(partner_id, {
            'type': 'chat_invitation',
            'data': {'from_user': user_id, 'nickname': self.connections[user_id].nickname}
        })

    async def _handle_end_chat(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        self.state_manager.end_chat(user_id)
        await ws.send(json.dumps({'type': 'chat_ended', 'data': {}}))

    async def _handle_status_update(self, user_id: str, data: dict, ws: WebSocketServerProtocol):
        status = data.get('status')
        if status in ['online', 'matching', 'chatting', 'offline']:
            if status == 'online':
                self.state_manager.set_online(user_id, str(id(ws)))
            elif status == 'matching':
                self.state_manager.set_matching(user_id)
            elif status == 'chatting':
                self.state_manager.set_chatting(user_id, self.state_manager.get_state(user_id).current_chat_partner)
            elif status == 'offline':
                self.state_manager.set_offline(user_id)
            logger.info(f"用户 {user_id} 状态更新: {status}")

    def _can_chat(self, user1: str, user2: str) -> bool:
        return user1 in self.match_relations and user2 in self.match_relations[user1]

    def _get_session_key(self, user1: str, user2: str) -> str:
        return f"{min(user1, user2)}_{max(user1, user2)}"

    async def _send_to_user(self, user_id: str, message: dict) -> bool:
        if user_id not in self.connections:
            return False
        try:
            await self.connections[user_id].websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"发送消息给 {user_id} 失败: {e}")
            return False

    async def _broadcast_to_matches(self, user_id: str, message: dict):
        if user_id not in self.match_relations:
            return
        for matched_id in self.match_relations[user_id]:
            if matched_id in self.connections:
                await self._send_to_user(matched_id, message)

    async def _send_error(self, ws: WebSocketServerProtocol, message: str):
        try:
            await ws.send(json.dumps({'type': 'error', 'data': {'message': message}}))
        except:
            pass

    async def _cleanup(self, ws: WebSocketServerProtocol):
        """连接清理"""
        user_id = self.user_sockets.get(ws)
        if user_id and user_id in self.connections:
            await self._broadcast_to_matches(user_id, {'type': 'user_offline', 'data': {'user_id': user_id}})
            self.state_manager.set_offline(user_id)
            del self.connections[user_id]
            logger.info(f"用户 {user_id} 断开连接")
        if ws in self.user_sockets:
            del self.user_sockets[ws]

    async def _periodic_tasks(self):
        """定时任务：清理超时连接、过期数据"""
        while self.running:
            await asyncio.sleep(30)
            current_time = time.time()
            # 清理超时连接
            timeout_users = [uid for uid, conn in self.connections.items() if current_time - conn.last_ping > 60]
            for user_id in timeout_users:
                logger.info(f"用户 {user_id} 心跳超时")
                if user_id in self.connections:
                    try:
                        await self.connections[user_id].websocket.close(1000, "心跳超时")
                    except:
                        pass
            # 清理过期聊天记录
            expire_time = current_time - Config.CHAT_HISTORY_RETENTION
            for session_key, history in list(self.chat_history.items()):
                self.chat_history[session_key] = [msg for msg in history if msg.timestamp > expire_time]
                if not self.chat_history[session_key]:
                    del self.chat_history[session_key]
            logger.info(f"在线用户: {len(self.connections)}, 匹配关系: {len(self.match_relations)}, 活跃会话: {len(self.chat_history)}")

# ========== 启动入口 ==========
async def main():
    service = RealtimeService()
    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()
        logger.info("服务已停止")

if __name__ == "__main__":
    # 安装依赖: pip install websockets aiohttp python-dotenv
    asyncio.run(main())