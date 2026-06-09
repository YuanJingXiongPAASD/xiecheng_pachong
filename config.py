"""
携程酒店评论爬虫 - 配置文件
===========================
修改此文件中的参数来适配不同的酒店和爬取需求。
"""

from pathlib import Path

# ============================================================
# 酒店信息
# ============================================================
HOTEL_URL = "https://hotels.ctrip.com/hotels/391750.html?cityid=1"
HOTEL_ID = "391750"

# ============================================================
# 输出设置
# ============================================================
OUTPUT_DIR = Path(__file__).parent / "output"

# ============================================================
# 爬取参数
# ============================================================
MAX_PAGES = 200              # 最大翻页数（安全上限）
REQUEST_DELAY = 2.0          # 每次翻页的请求间隔（秒）

# ============================================================
# 浏览器设置
# ============================================================
BROWSER_VIEWPORT = {"width": 1280, "height": 900}
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ============================================================
# API 拦截关键词
# 用于识别携程评论 API 的请求 URL
# ============================================================
API_KEYWORDS = [
    "getCommentCollapseList",
    "getCommentList",
    "getHotelCommentList",
    "commentList",
    "getComment",
    "getReviewList",
    "json/getComment",
]

# ============================================================
# 「点评」标签选择器（按优先级排列）
# ============================================================
REVIEW_TAB_SELECTORS = [
    'a:has-text("点评")',
    'span:has-text("点评")',
    'li:has-text("点评")',
    'div:has-text("点评")',
    'text=点评',
    'a:has-text("用户点评")',
    'text=用户点评',
    'a:has-text("住客点评")',
    'text=住客点评',
    'a:has-text("全部点评")',
    'text=全部点评',
    'text=评论',
]

# ============================================================
# 评论字段映射
# 目标字段 -> API 响应中可能的 key 名（按优先级排列）
# ============================================================
FIELD_MAP = {
    "reviewId":     ["reviewId", "commentId", "id", "ReviewID", "CommentID"],
    "content":      ["content", "commentContent", "commentDetail", "reviewContent", "comment", "text", "detail"],
    "score":        ["score", "rating", "overallRating", "commentScore", "point"],
    "userName":     ["userName", "nickName", "nickname", "author", "userNickName"],
    "checkInDate":  ["checkInDate", "travelDate", "checkinDate", "liveDate", "stayDate", "checkIn"],
    "roomType":     ["roomType", "roomName", "roomTypeName", "room"],
    "postDate":     ["postDate", "createTime", "commentTime", "publishDate", "time", "created", "commentDate"],
    "travelType":   ["travelType", "tripType", "travelPurpose", "travelTypeName", "tripPurpose"],
    "usefulCount":  ["usefulCount", "likeCount", "praiseCount", "helpfulCount"],
    "replyContent": ["replyContent", "merchantReply", "hotelReply", "reply"],
}

# ============================================================
# API 响应中评论列表的候选键名
# ============================================================
SEARCH_CANDIDATES = [
    "commentList", "commentCollapseList", "reviewList",
    "comments", "reviews", "data", "list", "items",
]

# ============================================================
# Excel 导出设置
# ============================================================
EXCEL_HEADERS = [
    "序号", "评论ID", "用户昵称", "评分", "入住日期",
    "房型", "出行类型", "评论内容", "酒店回复", "有用数", "发布日期",
]
EXCEL_COLUMN_WIDTHS = [6, 22, 14, 6, 12, 14, 10, 55, 40, 8, 18]
