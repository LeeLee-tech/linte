# filepath: d:\MatchModule\server\match.py
import os
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Optional


class MatcherEngine:
    """
    日程匹配引擎
    用法:
        1. 初始化: engine = MatcherEngine(model_path="...")
        2. 调用: result = engine.match(my_profile, candidates)
    """

    def __init__(self, model_path: str, high_thresh: float = 0.77, low_thresh: float = 0.65):
        """
        初始化引擎并预加载模型 (只加载一次)
        :param model_path: 模型文件夹路径
        :param high_thresh: 高匹配度阈值
        :param low_thresh: 低匹配度阈值
        """
        self.model_path = model_path
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.model = None

        # 启动时立即加载模型
        self._load_model()

    def _load_model(self):
        """内部方法：加载模型"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"[ERROR] 模型文件未找到: {self.model_path}")

        print(f"正在加载匹配模型...（路径: {self.model_path}）")
        try:
            # device='cpu' 可改为 'cuda' 如果有显卡
            self.model = SentenceTransformer(self.model_path, device='cpu')
            print("模型加载成功，引擎就绪。")
        except Exception as e:
            print(f"[ERROR] 模型加载失败: {e}")
            raise e

    def _parse_time(self, time_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """解析 'HH:MM-HH:MM'"""
        try:
            today = datetime.now().date()
            if '-' not in time_str:
                return None, None
            s_str, e_str = time_str.split('-', 1)
            start = datetime.combine(today, datetime.strptime(s_str.strip(), "%H:%M").time())
            end = datetime.combine(today, datetime.strptime(e_str.strip(), "%H:%M").time())
            if end < start:
                end += timedelta(days=1)
            return start, end
        except:
            return None, None

    def _check_overlap(self, s1, e1, s2, e2) -> bool:
        """检查时间交集"""
        if not all([s1, e1, s2, e2]):
            return False
        return s1 < e2 and e1 > s2

    def match(self, my_profile: Tuple[str, str, str], candidates: List[Tuple[str, str, str]]) -> List[
        Tuple[str, str, str]]:
        """
        【核心调用接口】
        输入:
            my_profile: (id, time_range, content)
            candidates: [(id, time_range, content), ...]
        返回:
            [(id, time_range, content), ...]  # 筛选并排序后的列表
        """
        if not self.model:
            raise RuntimeError("模型未加载，无法执行匹配。")

        if not candidates:
            return []

        # 1. 提取文本
        my_text = my_profile[2]
        candidate_texts = [c[2] for c in candidates]
        all_texts = [my_text] + candidate_texts

        # 2. 批量计算向量 (高性能关键)
        embeddings = self.model.encode(all_texts, normalize_embeddings=True, show_progress_bar=False)
        my_vec = embeddings[0].reshape(1, -1)

        # 3. 解析我的时间
        my_start, my_end = self._parse_time(my_profile[1])

        scored_high = []
        scored_fallback = []

        # 4. 遍历计算分数和时间
        for i, (c_id, time_str, text) in enumerate(candidates):
            # 计算语义相似度
            score = float(cosine_similarity(my_vec, embeddings[i + 1].reshape(1, -1))[0][0])

            # 检查时间
            c_start, c_end = self._parse_time(time_str)
            is_time_ok = self._check_overlap(my_start, my_end, c_start, c_end)

            if is_time_ok:
                item = {'data': (c_id, time_str, text), 'score': score}
                if score > self.high_thresh:
                    scored_high.append(item)
                elif self.low_thresh <= score <= self.high_thresh:
                    scored_fallback.append(item)

        # 5. 决策与排序
        final_result = []

        if scored_high:
            # 策略A: 有高分，全部返回，按分数降序
            scored_high.sort(key=lambda x: x['score'], reverse=True)
            final_result = [item['data'] for item in scored_high]
        elif scored_fallback:
            # 策略B: 无高分，取前2个中等分，按分数降序
            scored_fallback.sort(key=lambda x: x['score'], reverse=True)
            top_2 = scored_fallback[:2]
            final_result = [item['data'] for item in top_2]

        return final_result
