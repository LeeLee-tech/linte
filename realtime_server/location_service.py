import math
import time
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
# 引入统一的距离计算器，收敛重复逻辑
from distance_calculator import DistanceCalculator, GeoPoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LocationData:
    """位置数据结构"""
    user_id: str
    latitude: float      # 纬度 -90 ~ 90
    longitude: float     # 经度 -180 ~ 180
    accuracy: float      # 精度（米）
    altitude: Optional[float] = None  # 海拔（米）
    heading: Optional[float] = None   # 方向
    speed: Optional[float] = None    # 速度（米/秒）
    timestamp: float = 0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()
    
    def is_valid(self) -> bool:
        """验证坐标有效性"""
        return (-90 <= self.latitude <= 90 and 
                -180 <= self.longitude <= 180 and
                self.accuracy > 0)
    
    def to_geo_point(self, allow_match: bool = True) -> GeoPoint:
        """转换为统一的GeoPoint，对接距离计算器"""
        return GeoPoint(
            user_id=self.user_id,
            latitude=self.latitude,
            longitude=self.longitude,
            allow_match=allow_match
        )

class LocationOptimizer:
    """
    定位优化器
    功能：精度验证、异常值过滤、平滑处理、加权平均
    """
    
    def __init__(self):
        self.location_history: Dict[str, List[LocationData]] = {}
        self.max_history = 5  # 保留最近5个位置点用于平滑
        self.max_speed = 50   # 最大合理速度 50m/s (180km/h)
        # 引入统一的距离计算器
        self.distance_calculator = DistanceCalculator()
        
    def optimize(self, user_id: str, raw_location: LocationData) -> Optional[LocationData]:
        """
        优化原始定位数据
        返回：优化后的位置，或None（如果数据无效）
        """
        # 1. 基础验证
        if not raw_location.is_valid():
            logger.warning(f"用户 {user_id} 坐标无效: ({raw_location.latitude}, {raw_location.longitude})")
            return None
        
        # 2. 精度检查（低精度警告但接受）
        if raw_location.accuracy > 100:
            logger.warning(f"用户 {user_id} 定位精度较低: {raw_location.accuracy}米")
        
        # 3. 异常值检测（GPS漂移）
        if user_id in self.location_history and self.location_history[user_id]:
            last_valid = self.location_history[user_id][-1]
            # 复用统一的距离计算逻辑
            distance = self.distance_calculator.haversine(
                last_valid.latitude, last_valid.longitude,
                raw_location.latitude, raw_location.longitude
            )
            time_diff = raw_location.timestamp - last_valid.timestamp
            
            if time_diff > 0:
                speed = distance / time_diff
                # 如果速度异常（如GPS跳变），进行平滑处理
                if speed > self.max_speed:
                    logger.warning(f"用户 {user_id} 位置突变 {distance:.1f}米，进行平滑处理")
                    return self._smooth_location(user_id, raw_location)
        
        # 4. 保存历史
        if user_id not in self.location_history:
            self.location_history[user_id] = []
        self.location_history[user_id].append(raw_location)
        if len(self.location_history[user_id]) > self.max_history:
            self.location_history[user_id].pop(0)
        
        return raw_location
    
    def _smooth_location(self, user_id: str, new_loc: LocationData) -> LocationData:
        """
        位置平滑处理：加权平均
        权重：历史位置0.7，新位置0.3
        """
        if not self.location_history.get(user_id):
            return new_loc
        
        last_loc = self.location_history[user_id][-1]
        
        # 加权平均
        smoothed_lat = last_loc.latitude * 0.7 + new_loc.latitude * 0.3
        smoothed_lon = last_loc.longitude * 0.7 + new_loc.longitude * 0.3
        
        # 精度取较差值
        smoothed_accuracy = max(last_loc.accuracy, new_loc.accuracy)
        
        return LocationData(
            user_id=user_id,
            latitude=smoothed_lat,
            longitude=smoothed_lon,
            accuracy=smoothed_accuracy,
            timestamp=new_loc.timestamp
        )
    
    def get_location(self, user_id: str) -> Optional[LocationData]:
        """获取用户最新位置"""
        if user_id in self.location_history and self.location_history[user_id]:
            return self.location_history[user_id][-1]
        return None
    
    def get_average_location(self, user_id: str) -> Optional[LocationData]:
        """获取用户平均位置（用于提高稳定性）"""
        if user_id not in self.location_history or len(self.location_history[user_id]) < 3:
            return self.get_location(user_id)
        
        history = self.location_history[user_id]
        avg_lat = sum(loc.latitude for loc in history) / len(history)
        avg_lon = sum(loc.longitude for loc in history) / len(history)
        avg_accuracy = sum(loc.accuracy for loc in history) / len(history)
        
        return LocationData(
            user_id=user_id,
            latitude=avg_lat,
            longitude=avg_lon,
            accuracy=avg_accuracy,
            timestamp=time.time()
        )
    
    def remove_user(self, user_id: str):
        """清理用户数据"""
        if user_id in self.location_history:
            del self.location_history[user_id]

# ========== 测试代码 ==========
if __name__ == "__main__":
    optimizer = LocationOptimizer()
    
    # 模拟位置更新
    test_locations = [
        LocationData("user_001", 39.9042, 116.4074, 10),   # 正常
        LocationData("user_001", 39.9043, 116.4075, 15),   # 正常移动
        LocationData("user_001", 39.9100, 116.4200, 20),   # 异常跳变（模拟GPS漂移）
        LocationData("user_001", 39.9044, 116.4076, 12),   # 恢复正常
    ]
    
    for loc in test_locations:
        result = optimizer.optimize(loc.user_id, loc)
        if result:
            print(f"优化后位置: ({result.latitude:.6f}, {result.longitude:.6f}), "
                  f"精度: {result.accuracy}米")