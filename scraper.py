"""
携程酒店评论爬虫 - 核心爬虫类
=============================
负责浏览器控制、页面交互、API 拦截和分页抓取。
"""

import asyncio
import json

from playwright.async_api import async_playwright

from config import (
    BROWSER_VIEWPORT,
    BROWSER_USER_AGENT,
    API_KEYWORDS,
    REVIEW_TAB_SELECTORS,
    REQUEST_DELAY,
    MAX_PAGES,
)
from review_parser import parse_reviews
from exporter import export_to_excel


class CtripReviewScraper:
    """携程酒店评论爬虫"""

    def __init__(self, hotel_url: str, hotel_id: str):
        self.hotel_url = hotel_url
        self.hotel_id = hotel_id
        self.all_reviews: list[dict] = []
        self.api_url: str | None = None
        self._intercept_done = asyncio.Event()
        self._captured_reviews: list[dict] = []
        self._new_data_ready = asyncio.Event()

    # ========================================================
    # 主流程
    # ========================================================
    async def run(self):
        """启动爬虫主流程"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport=BROWSER_VIEWPORT,
                user_agent=BROWSER_USER_AGENT,
            )
            page = await context.new_page()

            print("\n" + "=" * 60)
            print("  携程酒店评论爬虫")
            print("=" * 60)

            # Step 1: 打开页面，等用户登录
            print(f"\n📌 打开酒店页面...")
            await page.goto(self.hotel_url, wait_until="networkidle", timeout=60000)
            print("📌 请在浏览器中扫码登录携程账号")
            input("\n👉 登录完成后按 Enter 继续...\n")

            # Step 2: 设置 API 拦截
            self._setup_interception(page)

            # Step 3: 等待用户手动点击「点评」
            print("📌 请在浏览器中手动点击「点评」标签进入评论页面")
            input("👉 点击完成后按 Enter 继续...\n")

            # Step 4: 等待评论数据加载
            print("⏳ 等待评论数据加载...")
            await self._wait_for_data(page)

            if not self.api_url:
                print("❌ 未能捕获评论 API，请确保已进入评论页面")
                await browser.close()
                return

            print(f"✅ 已捕获评论 API")

            # Step 5: 分页抓取
            await self._fetch_all_pages(page)

            # Step 6: 导出
            export_to_excel(self.all_reviews, self.hotel_id)

            await browser.close()
            print("\n🎉 全部完成!")

    # ========================================================
    # API 拦截
    # ========================================================
    def _setup_interception(self, page):
        """设置网络响应拦截，捕获评论 API 数据"""
        async def on_response(response):
            url = response.url
            if any(kw in url for kw in API_KEYWORDS):
                if not self.api_url:
                    self.api_url = url.split("?")[0]
                    print(f"   📡 拦截到 API: {self.api_url[:80]}...")
                    self._intercept_done.set()

                try:
                    body = await response.body()
                    data = json.loads(body)
                    reviews = parse_reviews(data, self.hotel_id)
                    if reviews:
                        self._captured_reviews.extend(reviews)
                        self._new_data_ready.set()
                except Exception:
                    pass

        page.on("response", on_response)

    # ========================================================
    # 等待数据
    # ========================================================
    async def _wait_for_data(self, page):
        """等待评论 API 被拦截到"""
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight*0.5)")
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight*0.7)")
        await asyncio.sleep(1)
        try:
            await asyncio.wait_for(self._intercept_done.wait(), timeout=20)
        except asyncio.TimeoutError:
            print("   ⚠️ 超时，尝试其他方式...")
            # 尝试点"更多"
            for s in ['text=查看更多', 'text=加载更多', 'a:has-text("更多")']:
                try:
                    el = await page.query_selector(s)
                    if el:
                        await el.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass

    # ========================================================
    # 分页抓取
    # ========================================================
    async def _fetch_all_pages(self, page):
        """逐页抓取所有评论"""
        seen_ids: set[str] = set()
        self._new_data_ready.clear()

        # 第一页
        new_reviews = self._drain_captured(seen_ids)
        total_pages = await self._detect_total_pages(page)
        if total_pages:
            print(f"\n📊 检测到共 {total_pages} 页评论")
        print(f"  第1页: {len(new_reviews)}条, 累计{len(self.all_reviews)}条\n")

        if not new_reviews:
            print("⚠️ 首页无评论数据")
            return

        # 翻页循环
        for page_num in range(2, MAX_PAGES + 1):
            await asyncio.sleep(REQUEST_DELAY)
            self._captured_reviews.clear()
            self._new_data_ready.clear()

            # 尝试自动点击
            ok = await self._try_click_next(page, page_num)

            if not ok:
                # 手动模式
                hint = f"第{page_num}页"
                if total_pages:
                    hint += f"/{total_pages}"
                print(f"  🔧 请手动点击 {hint} 的页码，然后按 Enter (q=退出)")
                choice = input("    > ").strip().lower()
                if choice == 'q':
                    break

            # 等数据
            try:
                await asyncio.wait_for(self._new_data_ready.wait(), timeout=30)
            except asyncio.TimeoutError:
                print(f"  ⚠️ 第{page_num}页超时")
                continue

            new_reviews = self._drain_captured(seen_ids)
            pct = ""
            if total_pages:
                pct = f" ({min(100, int(page_num / total_pages * 100))}%)"
            print(f"  第{page_num}页{pct}: +{len(new_reviews)}, 共{len(self.all_reviews)}条")

            if len(new_reviews) < 2:
                print("  已到最后一页。")
                break

        print(f"\n✅ 共抓取 {len(self.all_reviews)} 条评论")

    async def _try_click_next(self, page, target_page: int) -> bool:
        """尝试自动点击下一页，多次重试"""
        for attempt in range(5):
            if await self._click_page_number(page, target_page):
                return True
            wait = 2 + attempt * 1.5
            await asyncio.sleep(wait)
        return False

    async def _click_page_number(self, page, target_page: int) -> bool:
        """
        在页面底部找到目标页码并点击。
        核心思路：扫描页面下半部分所有元素，找到内容刚好是 target_page 数字的，
        排除掉明显是"当前页"的元素（无href、加粗、有active类），点击剩下的。
        """
        result = await page.evaluate("""
            (targetPage) => {
                // 收集页面底部包含目标数字的元素
                const candidates = [];
                const all = document.querySelectorAll('*');

                for (const el of all) {
                    const rect = el.getBoundingClientRect();
                    // 只看页面底部50%区域
                    if (rect.top < window.innerHeight * 0.45) continue;
                    if (rect.width < 10 || rect.height < 10) continue;

                    const text = (el.textContent || '').trim();
                    // 必须是精确匹配（如 "3" 而不是 "3楼"）
                    if (text !== String(targetPage)) continue;

                    const tag = el.tagName;
                    const cls = (el.className || '').toString();
                    const href = el.href || el.getAttribute('href') || '';
                    const hasHref = href && href !== '#' && !href.startsWith('javascript:void');

                    // 判断是否可能是"当前页"：无链接、加粗、有active类
                    const style = window.getComputedStyle(el);
                    const isBold = parseInt(style.fontWeight) >= 600;
                    const hasActiveCls = /\\b(active|current|selected|cur|on)\\b/i.test(cls);
                    const isLikelyCurrent = (!hasHref && el.tagName !== 'A') || isBold || hasActiveCls;

                    // 检查父元素
                    const pCls = (el.parentElement && el.parentElement.className) || '';
                    const pHasActiveCls = /\\b(active|current|selected|cur|on)\\b/i.test(pCls);

                    candidates.push({
                        tag, cls, hasHref, isBold, hasActiveCls,
                        isLikelyCurrent: isLikelyCurrent || pHasActiveCls,
                        y: rect.top,
                        hasOnClick: el.onclick !== null,
                    });
                }

                if (candidates.length === 0) {
                    return {ok: false, reason: 'no-candidates', total: 0};
                }

                // 排除当前页候选
                const clickable = candidates.filter(c => !c.isLikelyCurrent);

                // 如果全部被排除了，放宽条件
                const targets = clickable.length > 0 ? clickable : candidates;

                // 现在去页面上找到对应元素并点击
                for (const el of all) {
                    const rect = el.getBoundingClientRect();
                    if (rect.top < window.innerHeight * 0.45) continue;
                    if (rect.width < 10 || rect.height < 10) continue;
                    const text = (el.textContent || '').trim();
                    if (text !== String(targetPage)) continue;

                    const cls = (el.className || '').toString();
                    const href = el.href || el.getAttribute('href') || '';
                    const hasHref = href && href !== '#';
                    const style = window.getComputedStyle(el);
                    const isBold = parseInt(style.fontWeight) >= 600;
                    const isLikelyCurrent = (!hasHref && el.tagName !== 'A') || isBold ||
                        /\\b(active|current|selected|cur|on)\\b/i.test(cls);

                    if (isLikelyCurrent && clickable.length > 0) continue;

                    // === 点击！ ===
                    el.scrollIntoView({block: 'center', behavior: 'instant'});

                    // 尝试各种方式触发点击
                    el.click();
                    el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
                    el.dispatchEvent(new PointerEvent('click', {bubbles: true, cancelable: true, view: window}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));

                    // 也点击父元素
                    const p = el.parentElement;
                    if (p && p.tagName !== 'BODY') {
                        p.click();
                        p.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
                    }

                    return {
                        ok: true,
                        tag: el.tagName,
                        cls: cls.substring(0, 50),
                        candidatesFound: candidates.length,
                        clickableFound: clickable.length,
                    };
                }

                return {ok: false, reason: 'element-lost', candidatesFound: candidates.length};
            }
        """, target_page)

        if result.get("ok"):
            await asyncio.sleep(3)
            return True
        else:
            print(f"    [自动点击诊断] {result}")
            return False

    async def _detect_total_pages(self, page) -> int | None:
        """从页面内容检测总页数"""
        try:
            total = await page.evaluate("""
                () => {
                    const m = document.body.innerText.match(/共\\s*(\\d+)\\s*页/);
                    if (m) return parseInt(m[1]);
                    // 找分页区最大页码
                    let max = 0;
                    document.querySelectorAll('*').forEach(el => {
                        const r = el.getBoundingClientRect();
                        if (r.top < window.innerHeight*0.4) return;
                        const n = parseInt((el.textContent||'').trim());
                        if (n>max && n<1000) max=n;
                    });
                    return max>0 ? max : null;
                }
            """)
            return total if total else None
        except Exception:
            return None

    # ========================================================
    # 辅助
    # ========================================================
    async def _force_click(self, page, element):
        """强制点击：click + 多种事件 = 最大兼容性"""
        await element.scroll_into_view_if_needed()
        await element.evaluate("""
            el => {
                el.click();
                el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                el.dispatchEvent(new PointerEvent('click', {bubbles:true, cancelable:true, view:window}));
                const p = el.parentElement;
                if (p && p.tagName !== 'BODY') {
                    p.click();
                    p.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                }
            }
        """)

    def _drain_captured(self, seen_ids: set) -> list[dict]:
        """取出捕获的评论数据，去重后返回新增的"""
        new_list = []
        for r in self._captured_reviews:
            rid = r.get("reviewId") or r.get("commentId") or r.get("id", "")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                self.all_reviews.append(r)
                new_list.append(r)
        self._captured_reviews.clear()
        return new_list
