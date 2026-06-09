"""
携程酒店评论爬虫 - API 响应解析
===============================
从携程评论 API 返回的 JSON 中提取结构化评论数据。
"""

import json
import os
from config import OUTPUT_DIR, FIELD_MAP, SEARCH_CANDIDATES


def deep_find(obj, keys: list[str], depth: int = 10):
    """
    在嵌套的 dict / list 结构中递归查找第一个匹配 key 的列表值。

    Args:
        obj: 要搜索的嵌套结构（dict 或 list）
        keys: 要查找的键名列表
        depth: 最大递归深度

    Returns:
        匹配到的列表值，未找到返回 None
    """
    if depth <= 0:
        return None
    if isinstance(obj, dict):
        for k in keys:
            v = obj.get(k)
            if isinstance(v, list) and len(v) > 0:
                return v
        for v in obj.values():
            r = deep_find(v, keys, depth - 1)
            if r:
                return r
    elif isinstance(obj, list):
        for item in obj:
            r = deep_find(item, keys, depth - 1)
            if r:
                return r
    return None


def parse_reviews(data: dict, hotel_id: str) -> list[dict]:
    """
    从 API 响应 JSON 中解析评论列表。

    如果解析失败，会将原始响应写入 output/debug_{hotel_id}.json 以便调试。

    Args:
        data: API 响应的 JSON 对象
        hotel_id: 酒店 ID，用于调试文件命名

    Returns:
        解析后的评论列表，每个元素为 dict
    """
    review_list = deep_find(data, SEARCH_CANDIDATES)

    if not review_list:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_DIR / f"debug_{hotel_id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return []

    reviews = []
    for item in review_list:
        if not isinstance(item, dict):
            continue
        review = {}
        for key, cands in FIELD_MAP.items():
            review[key] = ""
            for c in cands:
                if c in item and item[c] is not None:
                    review[key] = str(item[c]).strip()
                    break
        if review.get("content"):
            reviews.append(review)
    return reviews
