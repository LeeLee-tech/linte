import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


class LexicalMatcher:
    name = "lexical-fallback"

    def __init__(self, high_thresh: float = 0.77, low_thresh: float = 0.45, fallback_top_n: int = 2):
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.fallback_top_n = fallback_top_n

    def match(self, my_profile: Tuple[str, str, str], candidates: List[Tuple[str, str, str]]):
        my_start, my_end = self._parse_time(my_profile[1])
        if not my_start or not my_end:
            return []

        scored_high = []
        scored_fallback = []
        for c_id, time_str, text in candidates:
            c_start, c_end = self._parse_time(time_str)
            if not self._check_overlap(my_start, my_end, c_start, c_end):
                continue

            score = self._score(my_profile[2], text)
            item = (c_id, time_str, text, round(score, 4), "high" if score >= self.high_thresh else "medium")
            if score >= self.high_thresh:
                scored_high.append(item)
            elif score >= self.low_thresh:
                scored_fallback.append(item)

        scored_high.sort(key=lambda item: item[3], reverse=True)
        scored_fallback.sort(key=lambda item: item[3], reverse=True)

        if scored_high:
            return scored_high
        return scored_fallback[: self.fallback_top_n]

    def _parse_time(self, time_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        try:
            today = datetime.now().date()
            if "-" not in time_str:
                return None, None
            start_text, end_text = time_str.split("-", 1)
            start = datetime.combine(today, datetime.strptime(start_text.strip(), "%H:%M").time())
            end = datetime.combine(today, datetime.strptime(end_text.strip(), "%H:%M").time())
            if end < start:
                end += timedelta(days=1)
            return start, end
        except Exception:
            return None, None

    def _check_overlap(self, s1, e1, s2, e2) -> bool:
        if not all([s1, e1, s2, e2]):
            return False
        return s1 < e2 and e1 > s2

    def _score(self, left: str, right: str) -> float:
        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)
        if not left_tokens or not right_tokens:
            return 0.0
        left_set = set(left_tokens)
        right_set = set(right_tokens)
        intersection = len(left_set & right_set)
        union = len(left_set | right_set)
        jaccard = intersection / union if union else 0.0
        char_score = self._char_overlap(left, right)
        return 0.7 * jaccard + 0.3 * char_score

    def _tokenize(self, text: str) -> List[str]:
        text = (text or "").strip().lower()
        ascii_parts = []
        current = []
        for ch in text:
            if ch.isascii() and ch.isalnum():
                current.append(ch)
            else:
                if current:
                    ascii_parts.append("".join(current))
                    current.clear()
                if not ch.isspace() and not ch.isascii():
                    ascii_parts.append(ch)
        if current:
            ascii_parts.append("".join(current))
        return ascii_parts

    def _char_overlap(self, left: str, right: str) -> float:
        if not left or not right:
            return 0.0
        left_count = {}
        right_count = {}
        for ch in left:
            left_count[ch] = left_count.get(ch, 0) + 1
        for ch in right:
            right_count[ch] = right_count.get(ch, 0) + 1

        common = 0
        for ch, count in left_count.items():
            common += min(count, right_count.get(ch, 0))
        return (2 * common) / (len(left) + len(right))


def build_matcher():
    model_path = os.getenv("MATCHER_MODEL_PATH", "").strip()
    if not model_path:
        default_path = r"D:\models\bge-large-zh-v1.5"
        if os.path.exists(default_path):
            model_path = default_path

    use_transformer = os.getenv("MATCHER_USE_TRANSFORMER", "")
    if use_transformer == "0":
        return LexicalMatcher()
    if use_transformer == "1" and not model_path:
        return LexicalMatcher()

    if not model_path or not os.path.exists(model_path):
        return LexicalMatcher()

    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        return LexicalMatcher()

    class TransformerMatcher(LexicalMatcher):
        name = "sentence-transformer"

        def __init__(self):
            super().__init__()
            self.model = SentenceTransformer(model_path, device="cpu")

        def match(self, my_profile: Tuple[str, str, str], candidates: List[Tuple[str, str, str]]):
            if not candidates:
                return []

            my_start, my_end = self._parse_time(my_profile[1])
            if not my_start or not my_end:
                return []

            all_texts = [my_profile[2]] + [item[2] for item in candidates]
            embeddings = self.model.encode(all_texts, normalize_embeddings=True, show_progress_bar=False)
            my_vec = embeddings[0].reshape(1, -1)

            scored_high = []
            scored_fallback = []
            for index, (c_id, time_str, text) in enumerate(candidates):
                c_start, c_end = self._parse_time(time_str)
                if not self._check_overlap(my_start, my_end, c_start, c_end):
                    continue

                score = float(cosine_similarity(my_vec, embeddings[index + 1].reshape(1, -1))[0][0])
                item = (c_id, time_str, text, round(score, 4), "high" if score >= self.high_thresh else "medium")
                if score >= self.high_thresh:
                    scored_high.append(item)
                elif score >= self.low_thresh:
                    scored_fallback.append(item)

            scored_high.sort(key=lambda item: item[3], reverse=True)
            scored_fallback.sort(key=lambda item: item[3], reverse=True)
            if scored_high:
                return scored_high
            return scored_fallback[: self.fallback_top_n]

    return TransformerMatcher()
