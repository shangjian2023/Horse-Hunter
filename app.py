"""
主应用入口 - 提供应用选择界面
"""

import streamlit as st
import subprocess
import sys
import os

st.set_page_config(
    page_title="财报智能问数系统",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1f77b4, #2ecc71, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
    }

    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }

    .app-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }

    .app-card:hover {
        transform: scale(1.02);
    }

    .app-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    .app-name {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .app-desc {
        color: #666;
        font-size: 0.9rem;
    }

    .feature-list {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # 标题
    st.markdown('<p class="main-title">📊 上市公司财报智能问数系统</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">泰迪杯 B 题 - 数据处理与智能分析平台</p>', unsafe_allow_html=True)

    st.divider()

    # 应用选择
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="app-card">
            <div class="app-icon">📁</div>
            <div class="app-name">文件处理工具</div>
            <div class="app-desc">导入和处理财报数据</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
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

        if st.button("📁 打开文件处理工具", use_container_width=True, key="btn_file"):
            launch_app("apps/file_processor_app.py")

    with col2:
        st.markdown("""
        <div class="app-card">
            <div class="app-icon">🤖</div>
            <div class="app-name">智能问数助手</div>
            <div class="app-desc">自然语言查询和分析</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
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

        if st.button("🤖 打开智能问数助手", use_container_width=True, key="btn_chat"):
            launch_app("rag_chat_app.py")

    st.divider()

    # 快捷工具
    st.markdown("### 🛠️ 快捷工具")

    tool_col1, tool_col2, tool_col3 = st.columns(3)

    with tool_col1:
        st.markdown("""
        #### 命令行工具
        用于快速处理和查询数据
        ```bash
        python -m cli process -i ./data/
        python -m cli demo
        ```
        """)

    with tool_col2:
        st.markdown("""
        #### RAG 知识库
        初始化和管理知识库
        ```bash
        python rag_init.py --init
        ```
        """)

    with tool_col3:
        st.markdown("""
        #### 数据处理
        批量处理示例数据
        ```bash
        python main.py --input ./reports/
        ```
        """)

    # 系统状态
    st.divider()
    st.markdown("### 📊 系统状态")

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)

    with status_col1:
        # 检查数据库
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
        # 检查 API 配置
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_AUTH_TOKEN', '')
        if api_key and api_key != 'your-api-key-here':
            st.success("✅ API 配置")
        else:
            st.warning("⚠️ API 配置")

    with status_col3:
        # 检查知识库
        kb_path = "./data/knowledge_base"
        if os.path.exists(kb_path) and os.listdir(kb_path):
            st.success("✅ 知识库")
        else:
            st.info("ℹ️ 知识库")

    with status_col4:
        # Docker 状态
        st.success("✅ 运行中")


def launch_app(app_file):
    """启动子应用"""
    if not os.path.exists(app_file):
        st.error(f"应用文件不存在：{app_file}")
        return

    # 使用 subprocess 启动
    python = sys.executable
    subprocess.run([python, "-m", "streamlit", "run", app_file, "--server.port", "8501"])


if __name__ == "__main__":
    main()
