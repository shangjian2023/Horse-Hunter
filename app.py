"""
主应用入口 - 使用 Streamlit 多页面应用结构
"""

import streamlit as st

st.set_page_config(
    page_title="财报智能问数系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 侧边栏导航
st.sidebar.title("📊 财报智能问数系统")
st.sidebar.markdown("---")

# 获取当前页面状态
if "page" not in st.session_state:
    st.session_state.page = "home"

def set_page(page_name):
    st.session_state.page = page_name

# 侧边栏菜单
menu = {
    "home": "🏠 首页",
    "file_processor": "📁 文件处理工具",
    "chat": "🤖 智能问数助手"
}

for page_key, page_name in menu.items():
    if st.sidebar.button(page_name, key=f"nav_{page_key}", use_container_width=True):
        set_page(page_key)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 快捷工具")
st.sidebar.info("""
**命令行工具:**
```bash
python -m cli process -i ./data/
python -m cli demo
```

**RAG 知识库:**
```bash
python rag_init.py --init
```

**数据处理:**
```bash
python src/main.py
```
""")

# 主页面
if st.session_state.page == "home":
    st.markdown("## 📊 上市公司财报智能问数系统")
    st.markdown("泰迪杯 B 题 - 数据处理与智能分析平台")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📁 文件处理工具
        导入和处理财报数据

        **功能特点:**
        - 支持 PDF/Excel/Word 多种格式
        - 自动识别财报类型
        - 批量处理能力
        - 数据清洗和验证
        - 导出标准化数据

        **适用场景:**
        - 比赛现场导入新数据
        - 批量处理财报文件
        - 数据格式转换
        """)
        if st.button("打开文件处理工具", key="btn_file", use_container_width=True):
            set_page("file_processor")

    with col2:
        st.markdown("""
        ### 🤖 智能问数助手
        自然语言查询和分析

        **功能特点:**
        - 自然语言查询
        - 多轮对话支持
        - 自动可视化
        - RAG 知识库增强
        - 支持多种国产大模型

        **适用场景:**
        - 数据查询和分析
        - 财报对比
        - 趋势分析
        - 行业研究
        """)
        if st.button("打开智能问数助手", key="btn_chat", use_container_width=True):
            set_page("chat")

    st.divider()
    st.markdown("### 📊 系统状态")

    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            if db.connect():
                st.success("✅ 数据库")
                db.disconnect()
            else:
                st.warning("⚠️ 数据库")
        except:
            st.error("❌ 数据库")

    with status_col2:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('LLM_API_KEY', '')
        if api_key and api_key != 'your-api-key-here':
            st.success("✅ API 配置")
        else:
            st.warning("⚠️ API 配置")

    with status_col3:
        kb_path = "./data/knowledge_base"
        if os.path.exists(kb_path) and os.listdir(kb_path):
            st.success("✅ 知识库")
        else:
            st.info("ℹ️ 知识库")

elif st.session_state.page == "file_processor":
    # 导入并运行文件处理工具
    try:
        from apps.file_processor_app import main as file_main
        file_main()
    except Exception as e:
        st.error(f"加载文件处理工具失败：{e}")
        if st.button("返回首页"):
            set_page("home")

elif st.session_state.page == "chat":
    # 导入并运行智能问数助手
    try:
        from rag_chat_app import main as chat_main
        chat_main()
    except Exception as e:
        st.error(f"加载智能问数助手失败：{e}")
        if st.button("返回首页"):
            set_page("home")
