import asyncio
import json
import time
import logging
from typing import Dict, Set, Optional,List
from dataclasses import dataclass, field
from enum import Enum

import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserStatus(Enum):
    """用户在线状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    MATCHING = "matching"
    CHATTING = "chatting"


@dataclass
class Connection:
    """连接信息"""
    user_id: str
    websocket: WebSocketServerProtocol
    status: UserStatus = UserStatus.ONLINE
    last_ping: float = field(default_factory=time.time)


class WebSocketService:
    """
    WebSocket服务
    功能：长连接管理、消息路由、心跳检测、断连重连
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        
        # 连接管理
        self.connections: Dict[str, Connection] = {}  # user_id -> Connection
        self.user_sockets: Dict[WebSocketServerProtocol, str] = {}  # ws -> user_id
        
        # 消息处理器注册
        self.handlers: Dict[str, callable] = {}
        
        # 统计
        self.message_count = 0
        self.start_time = time.time()
    
    def register_handler(self, msg_type: str, handler: callable):
        """注册消息处理器"""
        self.handlers[msg_type] = handler
        logger.info(f"注册处理器: {msg_type}")
    
    async def start(self):
        """启动WebSocket服务器"""
        logger.info(f"WebSocket服务器启动于 ws://{self.host}:{self.port}")
        
        async with websockets.serve(
            self._handle_connection, 
            self.host, 
            self.port,
            ping_interval=20,      # 每20秒发送ping
            ping_timeout=10        # 10秒内未收到pong则断开
        ):
            # 启动定时任务
            asyncio.create_task(self._heartbeat_check())
            asyncio.create_task(self._statistics())
            
            # 永久运行
            await asyncio.Future()
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """处理新连接"""
        client_addr = websocket.remote_address
        logger.info(f"新连接: {client_addr}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._route_message(websocket, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "消息格式错误：需要JSON")
                except Exception as e:
                    logger.error(f"消息处理错误: {e}")
                    await self._send_error(websocket, f"处理错误: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"连接关闭: {client_addr}, 代码: {e.code}")
        finally:
            await self._cleanup_connection(websocket)
    
    async def _route_message(self, websocket: WebSocketServerProtocol, data: dict):
        """路由消息到对应处理器"""
        msg_type = data.get('type')
        payload = data.get('data', {})
        
        self.message_count += 1
        
        # 认证消息特殊处理
        if msg_type == 'auth':
            await self._handle_auth(websocket, payload)
            return
        
        # 其他消息需要已认证
        user_id = self.user_sockets.get(websocket)
        if not user_id:
            await self._send_error(websocket, "请先发送认证消息")
            return
        
        # 更新心跳时间
        if user_id in self.connections:
            self.connections[user_id].last_ping = time.time()
        
        # 心跳消息
        if msg_type == 'ping':
            await self._handle_ping(websocket, user_id)
            return
        
        # 查找处理器
        handler = self.handlers.get(msg_type)
        if handler:
            try:
                result = await handler(user_id, payload, websocket)
                if result:  # 如果处理器返回消息，发送给客户端
                    await websocket.send(json.dumps(result))
            except Exception as e:
                logger.error(f"处理器错误: {e}")
                await self._send_error(websocket, f"处理失败: {str(e)}")
        else:
            await self._send_error(websocket, f"未知消息类型: {msg_type}")
    
    async def _handle_auth(self, websocket: WebSocketServerProtocol, data: dict):
        """处理认证"""
        user_id = data.get('user_id')
        if not user_id:
            await self._send_error(websocket, "user_id不能为空")
            return
        
        # 如果用户已存在，断开旧连接
        if user_id in self.connections:
            old_conn = self.connections[user_id]
            try:
                await old_conn.websocket.close(1000, "新设备登录")
            except:
                pass
            logger.info(f"用户 {user_id} 重新登录，断开旧连接")
        
        # 创建新连接
        conn = Connection(
            user_id=user_id,
            websocket=websocket,
            status=UserStatus.ONLINE
        )
        
        self.connections[user_id] = conn
        self.user_sockets[websocket] = user_id
        
        logger.info(f"用户 {user_id} 认证成功")
        
        # 发送认证成功响应
        await websocket.send(json.dumps({
            'type': 'auth_success',
            'data': {
                'user_id': user_id,
                'server_time': time.time(),
                'connection_id': id(websocket)
            }
        }))
    
    async def _handle_ping(self, websocket: WebSocketServerProtocol, user_id: str):
        """处理心跳"""
        await websocket.send(json.dumps({
            'type': 'pong',
            'data': {
                'timestamp': time.time(),
                'user_id': user_id
            }
        }))
    
    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """
        发送消息给指定用户
        返回：是否发送成功
        """
        if user_id not in self.connections:
            return False
        
        conn = self.connections[user_id]
        try:
            await conn.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"发送消息给 {user_id} 失败: {e}")
            return False
    
    async def broadcast(self, message: dict, exclude: Set[str] = None):
        """广播消息给所有在线用户"""
        exclude = exclude or set()
        tasks = []
        
        for user_id, conn in self.connections.items():
            if user_id not in exclude:
                tasks.append(self.send_to_user(user_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _cleanup_connection(self, websocket: WebSocketServerProtocol):
        """清理断开的连接"""
        user_id = self.user_sockets.get(websocket)
        
        if user_id and user_id in self.connections:
            # 检查是否是当前连接（防止误删新连接）
            if self.connections[user_id].websocket == websocket:
                del self.connections[user_id]
                logger.info(f"用户 {user_id} 连接已清理")
        
        if websocket in self.user_sockets:
            del self.user_sockets[websocket]
    
    async def _heartbeat_check(self):
        """心跳检测：清理超时连接"""
        while True:
            await asyncio.sleep(30)  # 每30秒检查一次
            
            current_time = time.time()
            timeout_users = []
            
            for user_id, conn in list(self.connections.items()):
                if current_time - conn.last_ping > 60:  # 60秒无响应
                    timeout_users.append(user_id)
            
            for user_id in timeout_users:
                logger.info(f"用户 {user_id} 心跳超时，断开连接")
                conn = self.connections[user_id]
                try:
                    await conn.websocket.close(1000, "心跳超时")
                except:
                    pass
    
    async def _statistics(self):
        """统计信息"""
        while True:
            await asyncio.sleep(300)  # 每5分钟输出统计
            uptime = time.time() - self.start_time
            logger.info(f"运行统计 - 在线用户: {len(self.connections)}, "
                       f"总消息: {self.message_count}, 运行时间: {uptime/60:.1f}分钟")
    
    async def _send_error(self, websocket: WebSocketServerProtocol, message: str):
        """发送错误消息"""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'data': {'message': message}
            }))
        except:
            pass
    
    def get_online_users(self) -> List[str]:
        """获取在线用户列表"""
        return list(self.connections.keys())


# ========== 测试代码 ==========
async def test_handler(user_id: str, payload: dict, websocket):
    """测试处理器"""
    return {
        'type': 'echo',
        'data': {
            'user_id': user_id,
            'received': payload
        }
    }

async def main():
    """启动测试服务器"""
    service = WebSocketService(host="0.0.0.0", port=8765)
    
    # 注册测试处理器
    service.register_handler('echo', test_handler)
    service.register_handler('broadcast', 
        lambda uid, payload, ws: service.broadcast({
            'type': 'broadcast',
            'data': {'from': uid, 'message': payload.get('message', '')}
        }))
    
    await service.start()

if __name__ == "__main__":
    # 安装依赖: pip install websockets
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")