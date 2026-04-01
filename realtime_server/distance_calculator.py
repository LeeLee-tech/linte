import math
from typing import List, Tuple, Dict
from dataclasses import dataclass

@dataclass
class GeoPoint:
    """地理坐标点"""
    user_id: str
    latitude: float
    longitude: float
    allow_match: bool = True  # 是否允许被匹配

class DistanceCalculator:
    """
    距离计算器
    核心功能：Haversine公式精确计算范围内用户，支持可配置扫描半径
    """
    EARTH_RADIUS = 6371000  # 地球半径（米）
    DEFAULT_SCAN_RADIUS = 200       # 默认扫描半径（米），兼容分工文档
    MIN_SCAN_RADIUS = 50            # 最小扫描半径，兼容需求文档
    MAX_SCAN_RADIUS = 200           # 最大扫描半径，不可突破

    def __init__(self, scan_radius: float = None):
        # 初始化扫描半径，限制在50-200米之间
        self.SCAN_RADIUS = max(
            self.MIN_SCAN_RADIUS,
            min(scan_radius or self.DEFAULT_SCAN_RADIUS, self.MAX_SCAN_RADIUS)
        )

    def calculate_distance(self, point1: GeoPoint, point2: GeoPoint) -> float:
        """
        计算两点间距离（米）
        使用Haversine公式，考虑地球曲率
        """
        return self.haversine(
            point1.latitude, point1.longitude,
            point2.latitude, point2.longitude
        )

    def haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Haversine公式实现
        输入：两点的经纬度（度）
        输出：距离（米）
        """
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine公式
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = self.EARTH_RADIUS * c
        return distance

    def is_within_range(self, center: GeoPoint, target: GeoPoint, radius: float = None) -> Tuple[bool, float]:
        """
        判断目标点是否在范围内
        返回：(是否在范围内, 距离)
        """
        if radius is None:
            radius = self.SCAN_RADIUS
        # 限制最大半径
        radius = min(radius, self.MAX_SCAN_RADIUS)
        distance = self.calculate_distance(center, target)
        return (distance <= radius, distance)

    def find_nearby_users(self, center_user: GeoPoint, all_users: List[GeoPoint], custom_radius: float = None) -> List[Tuple[GeoPoint, float]]:
        """
        查找范围内的所有用户
        返回：[(用户, 距离), ...] 按距离升序排列
        """
        nearby = []
        scan_radius = custom_radius if custom_radius else self.SCAN_RADIUS
        for user in all_users:
            # 跳过自己
            if user.user_id == center_user.user_id:
                continue
            # 检查是否允许被匹配
            if not user.allow_match:
                continue
            is_near, distance = self.is_within_range(center_user, user, scan_radius)
            if is_near:
                nearby.append((user, distance))
        # 按距离排序（最近的在前）
        nearby.sort(key=lambda x: x[1])
        return nearby

    def filter_by_distance(self, center: GeoPoint, candidates: List[GeoPoint], max_distance: float = 200) -> List[Tuple[GeoPoint, float]]:
        """
        按距离筛选候选用户
        可自定义最大距离（但不超过200米）
        """
        max_distance = min(max_distance, self.MAX_SCAN_RADIUS)
        results = []
        for candidate in candidates:
            if candidate.user_id == center.user_id:
                continue
            distance = self.calculate_distance(center, candidate)
            if distance <= max_distance:
                results.append((candidate, distance))
        results.sort(key=lambda x: x[1])
        return results

    def get_bounding_box(self, lat: float, lon: float, radius: float = 200) -> Dict[str, float]:
        """
        获取指定半径的边界框（用于数据库预筛选优化）
        返回：{'min_lat', 'max_lat', 'min_lon', 'max_lon'}
        """
        radius = min(radius, self.MAX_SCAN_RADIUS)
        # 1度纬度约111km
        lat_delta = radius / 111000
        # 1度经度在不同纬度不同
        lon_delta = radius / (111000 * math.cos(math.radians(lat)))

        return {
            'min_lat': lat - lat_delta,
            'max_lat': lat + lat_delta,
            'min_lon': lon - lon_delta,
            'max_lon': lon + lon_delta
        }

# ========== 测试代码 ==========
if __name__ == "__main__":
    calculator_200m = DistanceCalculator(scan_radius=200)

    # 测试数据：模拟5个用户位置（以天安门为中心）
    center = GeoPoint("user_center", 39.9042, 116.4074)
    test_users = [
        GeoPoint("user_001", 39.9043, 116.4075),   # 约15米
        GeoPoint("user_002", 39.9050, 116.4080),   # 约120米
        GeoPoint("user_003", 39.9060, 116.4090),   # 约280米（超出200米）
        GeoPoint("user_004", 39.9042, 116.4074, allow_match=False),  # 同位置但不允许匹配
        GeoPoint("user_005", 39.90425, 116.40745), # 约7米
    ]

 

    print("\n=== 200米范围扫描测试===")
    nearby_200m = calculator_200m.find_nearby_users(center, test_users)
    print(f"中心用户: {center.user_id} ({center.latitude}, {center.longitude})")
    print(f"扫描半径: {calculator_200m.SCAN_RADIUS}米")
    print(f"发现附近用户: {len(nearby_200m)}个\n")
    for user, distance in nearby_200m:
        print(f"用户: {user.user_id}, 距离: {distance:.2f}米")

    # 测试边界框计算
    bbox = calculator_200m.get_bounding_box(center.latitude, center.longitude)
    print(f"\n边界框: {bbox}")