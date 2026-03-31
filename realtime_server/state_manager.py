
import time
import logging
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OnlineStatus(Enum):
    """用户在线状态"""
    OFFLINE = "offline"         # 离线
    ONLINE = "online"           # 在线
    MATCHING = "matching"       # 正在匹配
    CHATTING = "chatting"       # 正在聊天
    AWAY = "away"               # 离开（长时间无操作）


class LocationSyncStatus(Enum):
    """定位同步状态"""
    NO_SIGNAL = "no_signal"     # 无信号
    SYNCING = "syncing"         # 同步中
    SYNCED = "synced"           # 已同步
    ERROR = "error"             # 同步错误


class ChatConnectionStatus(Enum):
    """聊天连接状态"""
    DISCONNECTED = "disconnected"   # 未连接
    CONNECTING = "connecting"       # 连接中
    CONNECTED = "connected"         # 已连接
    RECONNECTING = "reconnecting"   # 重连中


@dataclass
class UserState:
    """用户完整状态"""
    user_id: str
    
    # 在线状态
    online_status: OnlineStatus = OnlineStatus.OFFLINE
    last_active: float = field(default_factory=time.time)
    connection_id: Optional[str] = None  # WebSocket连接ID
    
    # 定位状态
    location_status: LocationSyncStatus = LocationSyncStatus.NO_SIGNAL
    last_location: Optional[Dict] = None
    location_update_time: float = 0
    
    # 聊天状态
    chat_status: ChatConnectionStatus = ChatConnectionStatus.DISCONNECTED
    current_chat_partner: Optional[str] = None  # 当前聊天对象
    unread_messages: int = 0
    
    # 匹配设置
    match_enabled: bool = True
    last_match_time: float = 0
    
    def update_active(self):
        """更新活跃时间"""
        self.last_active = time.time()
        if self.online_status == OnlineStatus.AWAY:
            self.online_status = OnlineStatus.ONLINE
    
    def is_active(self, timeout: int = 60) -> bool:
        """检查是否活跃"""
        return (time.time() - self.last_active) < timeout
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'online_status': self.online_status.value,
            'location_status': self.location_status.value,
            'chat_status': self.chat_status.value,
            'current_chat_partner': self.current_chat_partner,
            'unread_messages': self.unread_messages,
            'match_enabled': self.match_enabled,
            'is_active': self.is_active()
        }


class StateManager:
    """
    状态管理器
    统一管理所有用户的在线、定位、聊天状态
    """
    
    def __init__(self):
        self.states: Dict[str, UserState] = {}  # user_id -> UserState
        
        # 状态变更监听器
        self.listeners: Dict[str, List[callable]] = {
            'online': [],
            'location': [],
            'chat': [],
            'match': []
        }
    
    def get_state(self, user_id: str) -> UserState:
        """获取用户状态（不存在则创建）"""
        if user_id not in self.states:
            self.states[user_id] = UserState(user_id=user_id)
        return self.states[user_id]
    
    def remove_user(self, user_id: str):
        """移除用户"""
        if user_id in self.states:
            del self.states[user_id]
            logger.info(f"用户 {user_id} 状态已移除")
    
    # ========== 在线状态管理 ==========
    
    def set_online(self, user_id: str, connection_id: str):
        """设置用户在线"""
        state = self.get_state(user_id)
        old_status = state.online_status
        
        state.online_status = OnlineStatus.ONLINE
        state.connection_id = connection_id
        state.update_active()
        
        if old_status != OnlineStatus.ONLINE:
            self._notify('online', user_id, {
                'from': old_status.value,
                'to': 'online',
                'connection_id': connection_id
            })
            logger.info(f"用户 {user_id} 上线")
    
    def set_offline(self, user_id: str):
        """设置用户离线"""
        if user_id not in self.states:
            return
        
        state = self.states[user_id]
        old_status = state.online_status
        
        state.online_status = OnlineStatus.OFFLINE
        state.connection_id = None
        state.chat_status = ChatConnectionStatus.DISCONNECTED
        state.current_chat_partner = None
        
        self._notify('online', user_id, {
            'from': old_status.value,
            'to': 'offline'
        })
        logger.info(f"用户 {user_id} 离线")
    
    def set_away(self, user_id: str):
        """设置用户离开状态"""
        state = self.get_state(user_id)
        if state.online_status == OnlineStatus.ONLINE:
            state.online_status = OnlineStatus.AWAY
            self._notify('online', user_id, {
                'from': 'online',
                'to': 'away'
            })
    
    def set_matching(self, user_id: str):
        """设置用户正在匹配"""
        state = self.get_state(user_id)
        state.online_status = OnlineStatus.MATCHING
        state.last_match_time = time.time()
        state.update_active()
        self._notify('match', user_id, {'status': 'matching'})
    
    def set_chatting(self, user_id: str, partner_id: str):
        """设置用户正在聊天"""
        state = self.get_state(user_id)
        state.online_status = OnlineStatus.CHATTING
        state.chat_status = ChatConnectionStatus.CONNECTED
        state.current_chat_partner = partner_id
        state.update_active()
        self._notify('chat', user_id, {
            'status': 'chatting',
            'partner': partner_id
        })
    
    # ========== 定位状态管理 ==========
    
    def set_location_syncing(self, user_id: str):
        """设置定位同步中"""
        state = self.get_state(user_id)
        state.location_status = LocationSyncStatus.SYNCING
        self._notify('location', user_id, {'status': 'syncing'})
    
    def set_location_synced(self, user_id: str, location: Dict):
        """设置定位已同步"""
        state = self.get_state(user_id)
        state.location_status = LocationSyncStatus.SYNCED
        state.last_location = location
        state.location_update_time = time.time()
        state.update_active()
        self._notify('location', user_id, {
            'status': 'synced',
            'location': location
        })
    
    def set_location_error(self, user_id: str, error: str):
        """设置定位错误"""
        state = self.get_state(user_id)
        state.location_status = LocationSyncStatus.ERROR
        self._notify('location', user_id, {
            'status': 'error',
            'error': error
        })
    
    # ========== 聊天状态管理 ==========
    
    def set_chat_connecting(self, user_id: str):
        """设置聊天连接中"""
        state = self.get_state(user_id)
        state.chat_status = ChatConnectionStatus.CONNECTING
        self._notify('chat', user_id, {'status': 'connecting'})
    
    def set_chat_connected(self, user_id: str):
        """设置聊天已连接"""
        state = self.get_state(user_id)
        state.chat_status = ChatConnectionStatus.CONNECTED
        self._notify('chat', user_id, {'status': 'connected'})
    
    def set_chat_reconnecting(self, user_id: str):
        """设置聊天重连中"""
        state = self.get_state(user_id)
        state.chat_status = ChatConnectionStatus.RECONNECTING
        self._notify('chat', user_id, {'status': 'reconnecting'})
    
    def end_chat(self, user_id: str):
        """结束聊天"""
        state = self.get_state(user_id)
        state.chat_status = ChatConnectionStatus.CONNECTED
        state.current_chat_partner = None
        state.online_status = OnlineStatus.ONLINE
        self._notify('chat', user_id, {'status': 'ended'})
    
    def add_unread(self, user_id: str, count: int = 1):
        """增加未读消息数"""
        state = self.get_state(user_id)
        state.unread_messages += count
    
    def clear_unread(self, user_id: str):
        """清空未读消息"""
        state = self.get_state(user_id)
        state.unread_messages = 0
    
    # ========== 匹配设置 ==========
    
    def set_match_enabled(self, user_id: str, enabled: bool):
        """设置匹配开关"""
        state = self.get_state(user_id)
        state.match_enabled = enabled
        self._notify('match', user_id, {'enabled': enabled})
    
    # ========== 查询方法 ==========
    
    def get_online_users(self) -> List[str]:
        """获取所有在线用户"""
        return [
            uid for uid, state in self.states.items()
            if state.online_status != OnlineStatus.OFFLINE
        ]
    
    def get_active_users(self, timeout: int = 60) -> List[str]:
        """获取活跃用户（指定时间内有操作）"""
        return [
            uid for uid, state in self.states.items()
            if state.is_active(timeout)
        ]
    
    def get_matching_enabled_users(self) -> List[str]:
        """获取开启匹配的用户"""
        return [
            uid for uid, state in self.states.items()
            if state.match_enabled and state.online_status != OnlineStatus.OFFLINE
        ]
    
    def get_chatting_users(self) -> Dict[str, str]:
        """获取正在聊天的用户对"""
        chatting = {}
        for uid, state in self.states.items():
            if state.online_status == OnlineStatus.CHATTING and state.current_chat_partner:
                chatting[uid] = state.current_chat_partner
        return chatting
    
    def get_user_summary(self, user_id: str) -> Optional[Dict]:
        """获取用户状态摘要"""
        if user_id not in self.states:
            return None
        return self.states[user_id].to_dict()
    
    def get_all_status_summary(self) -> Dict:
        """获取所有状态统计"""
        total = len(self.states)
        online = sum(1 for s in self.states.values() if s.online_status != OnlineStatus.OFFLINE)
        matching = sum(1 for s in self.states.values() if s.online_status == OnlineStatus.MATCHING)
        chatting = sum(1 for s in self.states.values() if s.online_status == OnlineStatus.CHATTING)
        location_synced = sum(1 for s in self.states.values() if s.location_status == LocationSyncStatus.SYNCED)
        
        return {
            'total_users': total,
            'online': online,
            'matching': matching,
            'chatting': chatting,
            'location_synced': location_synced,
            'timestamp': time.time()
        }
    
    # ========== 监听器 ==========
    
    def add_listener(self, event_type: str, callback: callable):
        """添加状态变更监听器"""
        if event_type in self.listeners:
            self.listeners[event_type].append(callback)
    
    def _notify(self, event_type: str, user_id: str, data: dict):
        """通知监听器"""
        for callback in self.listeners.get(event_type, []):
            try:
                callback(user_id, data)
            except Exception as e:
                logger.error(f"监听器错误: {e}")
    
    def cleanup_inactive(self, timeout: int = 300):
        """清理长时间不活跃的用户"""
        current_time = time.time()
        to_remove = []
        
        for user_id, state in self.states.items():
            if (current_time - state.last_active > timeout and 
                state.online_status == OnlineStatus.OFFLINE):
                to_remove.append(user_id)
        
        for user_id in to_remove:
            self.remove_user(user_id)
        
        return len(to_remove)


# ========== 测试代码 ==========
if __name__ == "__main__":
    manager = StateManager()
    
    # 模拟状态变化
    print("=== 状态管理测试 ===\n")
    
    # 用户上线
    manager.set_online("user_001", "conn_001")
    manager.set_location_synced("user_001", {"lat": 39.9, "lon": 116.4})
    print(f"用户001状态: {manager.get_user_summary('user_001')}")
    
    # 用户开始匹配
    manager.set_matching("user_001")
    print(f"匹配状态: {manager.get_user_summary('user_001')['online_status']}")
    
    # 用户开始聊天
    manager.set_chatting("user_001", "user_002")
    print(f"聊天状态: {manager.get_user_summary('user_001')}")
    
    # 统计信息
    print(f"\n系统统计: {manager.get_all_status_summary()}")
    
    # 用户下线
    manager.set_offline("user_001")
    print(f"\n下线后状态: {manager.get_user_summary('user_001')}")