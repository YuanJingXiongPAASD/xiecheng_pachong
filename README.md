# 携程酒店评论爬虫

爬取[携程酒店](https://hotels.ctrip.com)页面下的所有用户评论，导出为 Excel 文件。
2026.6.9实测可以使用
如果存在问题，请E-mail联系paasd163@163.com
注意！！   在5 -> 6页切换的时候，需要手动翻页

## 功能

- 自动拦截携程评论 API，高效抓取数据
- 智能翻页：自动点击页码，失败时切换为手动模式
- 去重机制：基于评论 ID 自动去重
- Excel 导出：含评论明细和统计（平均评分、最高/最低分）两个工作表
- 调试支持：解析失败时自动保存原始 API 响应到 `output/` 目录

## 环境要求

- Python 3.9+
- Conda 环境（推荐）：`you_env_name`

## 安装

```bash
# 1. 激活 conda 环境
conda activate you_env_name

# 2. 安装依赖
pip install playwright openpyxl

# 3. 安装 Chromium 浏览器（首次使用）
playwright install chromium
```

## 项目结构

```
pacong-code/
├── config.py          # 配置文件（酒店、爬虫、导出参数）
├── scraper.py         # 核心爬虫类 CtripReviewScraper
├── review_parser.py   # API 响应解析（JSON → 结构化数据）
├── exporter.py        # Excel 导出
├── main.py            # 程序入口
├── ctrip_scraper.py   # 向后兼容入口
└── output/            # 导出目录（自动创建）
```

## 配置

修改 `config.py` 中的参数来适配不同酒店或调整爬取行为：

```python
# 酒店信息 — 换成你要爬的酒店
HOTEL_URL = "https://hotels.ctrip.com/hotels/391750.html?cityid=1"
HOTEL_ID = "391750"

# 爬取参数
MAX_PAGES = 200              # 最大翻页数
REQUEST_DELAY = 2.0          # 请求间隔（秒）

# Excel 导出
EXCEL_HEADERS = [...]        # 列名
EXCEL_COLUMN_WIDTHS = [...]  # 列宽
```

更多配置项（API 关键词、选择器、字段映射等）详见 `config.py` 中的注释。

## 使用方法

```bash
# 推荐方式
python main.py

# 向后兼容（效果相同）
python ctrip_scraper.py
```

### 运行流程

1. **弹出浏览器** → 自动打开酒店页面
2. **扫码登录** → 在浏览器中完成携程登录，然后按 Enter
3. **手动点击点评** → 在浏览器中点击「点评」标签进入评论页，然后按 Enter
4. **自动抓取** → 程序逐页抓取评论，翻页失败时提示手动操作
5. **导出 Excel** → 结果保存到 `output/酒店评论_{id}_{时间}.xlsx`

### 手动模式

当自动翻页失败时，程序会提示：
```
🔧 请手动点击 第5页/50页 的页码，然后按 Enter (q=退出)
```
手动点击页码后按 Enter 继续，或输入 `q` 退出。

## 编程调用

```python
import asyncio
from scraper import CtripReviewScraper

async def main():
    scraper = CtripReviewScraper(
        hotel_url="https://hotels.ctrip.com/hotels/XXXXX.html",
        hotel_id="XXXXX",
    )
    await scraper.run()

asyncio.run(main())
```

也可单独使用解析和导出模块：

```python
from review_parser import parse_reviews
from exporter import export_to_excel

# 解析 API 响应
reviews = parse_reviews(api_response_json, hotel_id="391750")

# 导出 Excel
path = export_to_excel(reviews, hotel_id="391750")
```

## License

MIT
