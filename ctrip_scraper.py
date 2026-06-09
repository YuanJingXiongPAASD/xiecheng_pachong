"""
携程酒店评论爬虫 — 向后兼容模块
===============================
此文件保留以确保向后兼容。

推荐使用新入口：
    python main.py

或直接导入：
    from main import main
    from scraper import CtripReviewScraper
"""

# 向后兼容：重新导出所有公共接口
from config import (
    HOTEL_URL,
    HOTEL_ID,
    OUTPUT_DIR,
    MAX_PAGES,
    REQUEST_DELAY,
)
from scraper import CtripReviewScraper
from review_parser import parse_reviews, deep_find
from exporter import export_to_excel
from main import main

# 保持原有的 __main__ 行为
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
