"""
使用 Playwright 测试 Streamlit 应用
"""
import asyncio
from playwright.async_api import async_playwright


async def test_streamlit_app():
    """测试 Streamlit 应用是否能正常加载和交互"""

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # 访问应用
        print("正在访问 http://localhost:8501...")
        await page.goto("http://localhost:8501", wait_until="networkidle")

        # 等待页面加载
        await asyncio.sleep(3)

        # 截图
        await page.screenshot(path="test_result_1_page_load.png")
        print("✓ 页面加载成功，已截图：test_result_1_page_load.png")

        # 检查是否包含 API 配置区域
        api_config_expander = page.locator('text="API 配置"')
        if await api_config_expander.count() > 0:
            print("✓ API 配置区域存在")
        else:
            print("✗ API 配置区域不存在")

        # 检查是否包含主标题
        title = page.locator('text="智能问数助手"')
        if await title.count() > 0:
            print("✓ 主标题存在")
        else:
            print("✗ 主标题不存在")

        # 检查侧边栏是否存在
        sidebar = page.locator('section[data-testid="stSidebar"]')
        if await sidebar.count() > 0:
            print("✓ 侧边栏存在")
            await sidebar.screenshot(path="test_result_2_sidebar.png")
            print("  侧边栏截图：test_result_2_sidebar.png")
        else:
            print("✗ 侧边栏不存在")

        # 检查输入框是否存在
        chat_input = page.locator('textarea[aria-label="输入您的问题，按 Enter 发送..."]')
        if await chat_input.count() > 0:
            print("✓ 输入框存在")
        else:
            print("✗ 输入框不存在")

        # 检查快捷问题按钮
        quick_buttons = page.locator('text="贵州茅台净利润"')
        if await quick_buttons.count() > 0:
            print("✓ 快捷问题按钮存在")
        else:
            print("✗ 快捷问题按钮不存在")

        # 尝试输入测试问题
        print("\n尝试输入测试问题...")
        await page.fill('textarea[aria-label="输入您的问题，按 Enter 发送..."]', "测试")
        await asyncio.sleep(1)

        # 截图
        await page.screenshot(path="test_result_3_input.png")
        print("✓ 输入测试完成，已截图：test_result_3_input.png")

        # 关闭浏览器
        await browser.close()
        print("\n✓ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_streamlit_app())
