"""
智能问数助手 - 整合 RAG 知识库版本
美化版 - 支持多模型选择和 API Key 配置
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from models.chat_agent import ChatAgent
from models.rag.retriever import Retriever
from models.rag.knowledge_base import KnowledgeBase

# 页面配置 - 只在直接运行时或首次导入时设置
if 'page_config_set' not in st.session_state:
    try:
        st.set_page_config(
            page_title="上市公司财报智能问数助手",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.session_state.page_config_set = True
    except:
        pass  # 已经设置过，跳过

# 自定义 CSS 样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1f77b4, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }

    /* 副标题样式 */
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }

    /* 聊天消息样式优化 */
    .stChatMessage {
        border-radius: 12px;
        margin: 8px 0;
    }

    /* 侧边栏样式 */
    .sidebar-content {
        padding: 1rem;
    }

    /* 卡片式布局 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }

    /* 隐藏顶部装饰 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 输入框样式优化 */
    .stChatInput > div {
        border-radius: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 预设模型列表
PRESET_MODELS = {
    "阿里云 - 通义千问": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long-context"]
    },
    "百度 - 文心一言": {
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1",
        "models": ["ernie-4.0", "ernie-3.5", "ernie-speed"]
    },
    "智谱 AI - GLM": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4", "glm-3-turbo", "glm-4v"]
    },
    "月之暗面 - Kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
    },
    "深度求索 - DeepSeek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder"]
    },
    "零一万物 - Yi": {
        "base_url": "https://api.lingyiwanwu.com/v1",
        "models": ["yi-large", "yi-medium", "yi-spark"]
    },
    "自定义 API": {
        "base_url": "",
        "models": []
    }
}

# 初始化会话状态
if 'chat_agent' not in st.session_state:
    st.session_state.chat_agent = ChatAgent()
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'use_rag' not in st.session_state:
    st.session_state.use_rag = True
if 'consecutive_errors' not in st.session_state:
    st.session_state.consecutive_errors = 0
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'api_config' not in st.session_state:
    st.session_state.api_config = {
        'api_key': '',
        'base_url': '',
        'model': 'qwen-plus',
        'provider': '阿里云 - 通义千问'
    }
if 'api_configured' not in st.session_state:
    st.session_state.api_configured = False


def update_chat_agent_api_config():
    """更新 ChatAgent 的 API 配置"""
    if st.session_state.api_config.get('api_key') and st.session_state.api_config.get('base_url'):
        st.session_state.chat_agent.update_api_config(st.session_state.api_config)
        return True
    return False


def save_api_config():
    """保存 API 配置到.env 文件"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    config = st.session_state.api_config

    env_content = f"""# ===========================================
# 环境变量配置文件
# ===========================================

# 数据库配置
MYSQL_ROOT_PASSWORD=root123
MYSQL_DATABASE=financial_report
MYSQL_USER=fin_user
MYSQL_PASSWORD=fin_pass123
MYSQL_PORT=3306

# 应用配置
APP_PORT=8501
STREAMLIT_PORT=8502

# LLM API 配置
LLM_API_KEY={config['api_key']}
LLM_BASE_URL={config['base_url']}
LLM_MODEL={config['model']}

# 可选配置
DEBUG=true
TZ=Asia/Shanghai
"""

    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        return True
    except Exception as e:
        st.error(f"保存配置失败：{e}")
        return False


def init_rag():
    """初始化 RAG 检索器"""
    try:
        st.session_state.retriever = Retriever()
        return True
    except Exception as e:
        st.error(f"RAG 初始化失败：{e}")
        return False


def render_api_config_section():
    """渲染 API 配置区域"""
    with st.sidebar:
        with st.expander("🔑 API 配置", expanded=not st.session_state.api_configured):
            # 提供商选择
            provider = st.selectbox(
                "模型提供商",
                options=list(PRESET_MODELS.keys()),
                index=0,
                key="provider_select"
            )

            # 更新可用模型列表
            available_models = PRESET_MODELS[provider]["models"]
            default_base_url = PRESET_MODELS[provider]["base_url"]

            # 模型选择
            if available_models:
                model = st.selectbox(
                    "选择模型",
                    options=available_models,
                    index=0,
                    key="model_select"
                )
            else:
                model = st.text_input("模型名称", key="model_input", value="")

            # Base URL
            base_url = st.text_input(
                "API Base URL",
                value=default_base_url if default_base_url else "",
                key="base_url_input",
                help="API 服务的基础 URL"
            )

            # API Key
            api_key = st.text_input(
                "API Key",
                type="password",
                key="api_key_input",
                help="您的 API 密钥",
                placeholder="请输入 API Key"
            )

            # 测试连接按钮
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("💾 保存配置", use_container_width=True, key="save_config_btn"):
                    st.session_state.api_config = {
                        'api_key': api_key,
                        'base_url': base_url,
                        'model': model,
                        'provider': provider
                    }
                    if save_api_config():
                        st.session_state.api_configured = True
                        # 更新 ChatAgent 的 API 配置
                        update_chat_agent_api_config()
                        st.success("配置已保存!")
                        st.rerun()

            with col2:
                if st.button("🧪 测试", use_container_width=True, key="test_config_btn"):
                    if api_key and base_url:
                        # 临时更新配置并测试
                        test_config = {
                            'api_key': api_key,
                            'base_url': base_url,
                            'model': model,
                            'provider': provider
                        }
                        from models.text_to_sql import TextToSQL
                        test_sql = TextToSQL(api_config=test_config)
                        result = test_sql._call_llm("你是一个测试助手。", "请回复'测试成功'以确认 API 正常工作。")
                        if 'ERROR' in result:
                            st.error(f"测试失败：{result}")
                        else:
                            st.success(f"测试成功：{result[:50]}...")
                    else:
                        st.warning("请先填写 API Key 和 Base URL")


def main():
    # 渲染 API 配置
    render_api_config_section()

    # 主界面标题
    st.markdown('<p class="main-title">📊 上市公司财报智能问数助手</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">基于大模型的财报数据智能查询分析系统 | 支持自然语言查询、多轮对话、RAG 知识库增强</p>', unsafe_allow_html=True)

    # 状态指示器
    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        if st.session_state.api_configured:
            st.success("✅ API 已配置")
        else:
            st.warning("⚠️ 请先配置 API")
    with status_col2:
        if st.session_state.retriever:
            stats = st.session_state.retriever.kb.get_stats()
            st.success(f"📚 知识库：{stats['total_chunks']} 片段")
        else:
            st.info("📚 知识库未初始化")
    with status_col3:
        mode = "RAG 增强" if st.session_state.use_rag else "标准模式"
        st.info(f"🔧 {mode}")

    st.divider()

    # 侧边栏 - 功能设置
    with st.sidebar:
        st.divider()

        # RAG 开关
        st.subheader("📚 知识库增强")
        st.session_state.use_rag = st.toggle(
            "启用 RAG 知识库",
            value=st.session_state.use_rag,
            help="启用后将结合行业报告、企业信息等知识库内容回答问题"
        )

        if st.session_state.use_rag:
            if st.session_state.retriever is None:
                if st.button("📚 初始化知识库", use_container_width=True):
                    with st.spinner("正在加载知识库..."):
                        if init_rag():
                            st.success("知识库初始化成功!")
                            st.rerun()
                        else:
                            st.error("知识库初始化失败")

        st.divider()

        # 会话管理
        st.subheader("💬 会话管理")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ 新建会话", use_container_width=True):
                st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("🗑️ 清空历史", use_container_width=True):
                st.session_state.chat_agent.clear_session(st.session_state.session_id)
                st.session_state.chat_history = []
                st.rerun()

        st.divider()

        # 使用指南
        with st.expander("📖 使用指南"):
            st.markdown("""
            #### 🔍 支持的问题类型

            **1. 财报数据查询**
            - 贵州茅台 2024 年的净利润是多少？
            - 查询中国平安的资产负债率

            **2. 对比分析**
            - 对比招商银行和浦发银行的营业收入
            - 2024 年净利润排名前十的公司

            **3. 趋势分析**
            - 贵州茅台近 5 年营业收入变化趋势
            - 分析某公司的利润增长情况

            **4. 行业知识 (RAG)**
            - 医药行业的政策环境如何？
            - 新能源行业的发展趋势

            #### 💬 多轮对话
            支持上下文理解，可以追问：
            - 查询贵州茅台的净利润
            - 那营业收入呢？
            - 对比一下五粮液
            """)

        # 页脚信息
        st.divider()
        st.markdown("""
        <div style="text-align: center; color: #999; font-size: 0.9rem;">
            Powered by Streamlit & LLM
        </div>
        """, unsafe_allow_html=True)

    # 聊天历史区域
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.markdown(f"**{msg['content']}**")
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg['content'])

                    # 显示 SQL
                    if msg.get('sql'):
                        with st.expander("📝 查看生成的 SQL"):
                            st.code(msg['sql'], language='sql')

                    # 显示数据
                    if msg.get('data'):
                        df = pd.DataFrame(msg['data'])
                        with st.expander("📊 查看查询结果"):
                            st.dataframe(df, use_container_width=True)

                    # 显示图表
                    if msg.get('image_path'):
                        if os.path.exists(msg['image_path']):
                            st.image(
                                msg['image_path'],
                                caption=f"📈 {msg.get('chart_type', '图表')}",
                                use_container_width=True
                            )

                    # 显示引用来源
                    if msg.get('references'):
                        with st.expander("📚 参考来源"):
                            for j, ref in enumerate(msg['references'], 1):
                                st.markdown(f"**来源 {j}**: `{ref.get('source', '未知')}`")
                                st.markdown(f"> {ref['content'][:200]}...")

                    # 显示建议
                    if msg.get('suggestions'):
                        st.markdown("**💡 您可以继续问：**")
                        cols = st.columns(len(msg['suggestions']))
                        for idx, suggestion in enumerate(msg['suggestions']):
                            with cols[idx]:
                                st.markdown(f"- {suggestion}")

    # 错误处理区域
    if st.session_state.consecutive_errors >= 3:
        st.error("⚠️ 连续 3 次请求失败，已自动停止")
        st.warning(f"错误信息：{st.session_state.last_error}")
        with st.expander("🔧 解决方法"):
            st.markdown("""
            1. 检查侧边栏 API Key 是否正确
            2. 确认 Base URL 配置
            3. 检查网络连接
            """)
        if st.button("🔄 重置错误计数并重试"):
            st.session_state.consecutive_errors = 0
            st.session_state.last_error = None
            st.rerun()
        return

    # 输入区域
    st.divider()

    # 快捷问题
    quick_questions = [
        "💰 贵州茅台净利润",
        "📈 营收排名前十",
        "🏥 医药行业政策",
        "⚡ 新能源发展趋势",
        "🏦 银行资产负债率对比"
    ]

    st.markdown("##### ⚡ 快捷提问")
    quick_cols = st.columns(5)
    selected_quick = None
    for idx, qq in enumerate(quick_questions):
        with quick_cols[idx]:
            if st.button(qq, key=f"quick_{idx}", use_container_width=True):
                selected_quick = qq.split(" ", 1)[1] if " " in qq else qq

    # 输入框
    user_input = st.chat_input(
        "输入您的问题，按 Enter 发送...",
        key="chat_input"
    )

    # 处理输入
    question = user_input or selected_quick

    if question:
        # 检查 API 配置
        if not st.session_state.api_configured:
            st.warning("⚠️ 请先在侧边栏配置 API Key")
            return

        # 确保 ChatAgent 使用最新的 API 配置
        update_chat_agent_api_config()

        # 添加用户消息
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question
        })

        # 处理查询
        with st.spinner("🔄 正在分析..."):
            if st.session_state.use_rag and is_knowledge_question(question):
                if st.session_state.retriever:
                    result = st.session_state.retriever.retrieve_and_answer(question)
                    response = {
                        'answer': result['answer'],
                        'references': result.get('references', []),
                        'sql': None,
                        'data': None,
                        'image': None
                    }
                    st.session_state.consecutive_errors = 0
                else:
                    response = {
                        'answer': 'RAG 知识库未初始化，请先在侧边栏点击"📚 初始化知识库"',
                        'references': [],
                        'suggestions': ['点击"初始化知识库"加载文档']
                    }
            else:
                chat_agent = st.session_state.chat_agent
                response = chat_agent.chat(question, st.session_state.session_id)

                # 检查错误
                answer = response.get('answer', '')
                if 'API 调用失败' in answer or '查询失败' in answer:
                    st.session_state.consecutive_errors += 1
                    st.session_state.last_error = answer
                else:
                    st.session_state.consecutive_errors = 0

        # 添加助手回复
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response.get('answer', '抱歉，我无法回答这个问题'),
            'sql': response.get('sql'),
            'data': response.get('data'),
            'image_path': response.get('image'),
            'chart_type': response.get('chart_type'),
            'references': response.get('references'),
            'suggestions': response.get('suggestions', [])
        })

        st.rerun()

    # 页脚
    st.divider()
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    with footer_col1:
        st.caption(f"会话 ID: `{st.session_state.session_id[:20]}...`")
    with footer_col2:
        st.caption(f"对话轮数：{len(st.session_state.chat_history)}")
    with footer_col3:
        current_model = st.session_state.api_config.get('model', '未配置')
        st.caption(f"当前模型：{current_model}")


def is_knowledge_question(question: str) -> bool:
    """判断是否是知识库相关问题"""
    knowledge_keywords = ['行业', '政策', '趋势', '竞争', '市场', '发展', '企业', '优势', '环境', '背景', '报告']
    return any(keyword in question for keyword in knowledge_keywords)


if __name__ == "__main__":
    main()
