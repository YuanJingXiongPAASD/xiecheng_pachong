"""
携程酒店评论爬虫 - 入口
=======================
使用方法：
    conda activate 260608pachong
    python main.py

流程：
    1. 弹出浏览器 → 打开酒店页面
    2. 扫码登录携程
    3. 手动点击「点评」标签进入评论页面
    4. 程序自动逐页抓取评论（翻页失败自动切换手动模式）
    5. 导出 Excel 到 output/ 目录
"""

import asyncio

from scraper import CtripReviewScraper
from config import HOTEL_URL, HOTEL_ID


async def main():
    scraper = CtripReviewScraper(hotel_url=HOTEL_URL, hotel_id=HOTEL_ID)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
