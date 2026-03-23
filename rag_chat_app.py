"""
智能问数助手 - 整合 RAG 知识库版本
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from models.chat_agent import ChatAgent
from models.rag.retriever import Retriever
from models.rag.knowledge_base import KnowledgeBase

st.set_page_config(
    page_title="智能问数助手 (RAG 增强版)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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


def init_rag():
    """初始化 RAG 检索器"""
    try:
        st.session_state.retriever = Retriever()
        return True
    except Exception as e:
        st.error(f"RAG 初始化失败：{e}")
        return False


def main():
    st.title("🤖 上市公司财报智能问数助手")
    st.caption("支持自然语言查询、多轮对话、RAG 知识库增强")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 功能设置")

        # RAG 开关
        st.subheader("知识库增强")
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
                        else:
                            st.error("知识库初始化失败")

            # 显示知识库统计
            if st.session_state.retriever:
                stats = st.session_state.retriever.kb.get_stats()
                st.info(f"知识库：{stats['total_chunks']} 个片段")

        st.divider()

        # 会话管理
        st.subheader("💬 会话管理")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("新建会话", use_container_width=True):
                st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("清空历史", use_container_width=True):
                st.session_state.chat_agent.clear_session(st.session_state.session_id)
                st.session_state.chat_history = []
                st.rerun()

        st.divider()

        # 使用指南
        with st.expander("📖 使用指南"):
            st.markdown("""
            ### 支持的问题类型

            **1. 财报数据查询**
            - "贵州茅台 2024 年的净利润是多少？"
            - "查询中国平安的资产负债率"

            **2. 对比分析**
            - "对比招商银行和浦发银行的营业收入"
            - "2024 年净利润排名前十的公司"

            **3. 趋势分析**
            - "贵州茅台近 5 年营业收入变化趋势"
            - "分析某公司的利润增长情况"

            **4. 行业知识 (RAG)**
            - "医药行业的政策环境如何？"
            - "新能源行业的发展趋势"
            - "某企业的竞争优势分析"

            ### 多轮对话
            支持上下文理解，可以追问：
            - "查询贵州茅台的净利润"
            - "那营业收入呢？"
            - "对比一下五粮液"
            """)

    # 主界面 - 聊天历史
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(msg['content'])

                    # 显示 SQL（如果有）
                    if msg.get('sql'):
                        with st.expander("📝 查看生成的 SQL"):
                            st.code(msg['sql'], language='sql')

                    # 显示数据（如果有）
                    if msg.get('data'):
                        df = pd.DataFrame(msg['data'])
                        with st.expander("📊 查看查询结果"):
                            st.dataframe(df, use_container_width=True)

                    # 显示图表（如果有）
                    if msg.get('image_path'):
                        if os.path.exists(msg['image_path']):
                            st.image(msg['image_path'], caption=f"自动生成的{msg.get('chart_type', '图表')}",
                                   use_container_width=True)

                    # 显示 RAG 引用来源
                    if msg.get('references'):
                        with st.expander("📚 参考来源"):
                            for j, ref in enumerate(msg['references'], 1):
                                st.write(f"**来源 {j}**: {ref.get('source', '未知')}")
                                st.write(ref['content'][:200] + "...")

                    # 显示建议（如果有）
                    if msg.get('suggestions'):
                        st.write("**💡 您可以继续问：**")
                        for suggestion in msg['suggestions']:
                            st.write(f"- {suggestion}")

    # 输入区域
    st.divider()

    # 输入框和模式选择
    col1, col2, col3 = st.columns([1, 5, 1])

    with col1:
        query_mode = st.selectbox(
            "查询模式",
            ["自动", "仅 SQL", "仅 RAG"],
            help="自动：根据问题类型选择; 仅 SQL: 查询结构化数据; 仅 RAG: 查询知识库"
        )

    with col2:
        user_input = st.chat_input(
            "输入您的问题...",
            key="chat_input"
        )

    with col3:
        quick_questions = [
            "贵州茅台净利润",
            "营收排名前十",
            "医药行业政策"
        ]
        selected = st.selectbox("快捷问题", ["", *quick_questions], label_visibility="collapsed")

    # 处理用户输入
    if user_input or selected:
        question = user_input or selected

        # 添加用户消息到历史
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question
        })

        # 根据模式选择处理方式
        with st.spinner("正在分析..."):
            if query_mode == "仅 RAG" or (query_mode == "自动" and is_knowledge_question(question)):
                # 使用 RAG 检索
                if st.session_state.retriever:
                    result = st.session_state.retriever.retrieve_and_answer(question)
                    response = {
                        'answer': result['answer'],
                        'references': result.get('references', []),
                        'sql': None,
                        'data': None,
                        'image': None
                    }
                else:
                    response = {
                        'answer': 'RAG 知识库未初始化，请先在侧边栏点击"初始化知识库"',
                        'references': [],
                        'suggestions': ['点击"初始化知识库"加载文档']
                    }
            else:
                # 使用 ChatAgent 查询结构化数据
                chat_agent = st.session_state.chat_agent
                response = chat_agent.chat(question, st.session_state.session_id)

        # 添加助手回复到历史
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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"会话 ID: `{st.session_state.session_id[:20]}...`")
    with col2:
        st.write(f"对话轮数：{len(st.session_state.chat_history)}")
    with col3:
        mode = "RAG 增强" if st.session_state.use_rag else "标准模式"
        st.write(f"当前模式：{mode}")


def is_knowledge_question(question: str) -> bool:
    """判断是否是知识库相关问题"""
    knowledge_keywords = ['行业', '政策', '趋势', '竞争', '市场', '发展', '企业', '优势', '环境', '背景']
    return any(keyword in question for keyword in knowledge_keywords)


if __name__ == "__main__":
    main()
