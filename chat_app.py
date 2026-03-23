"""
智能问数助手 - Streamlit 前端
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from models.chat_agent import ChatAgent
from models.multimodal import MultimodalProcessor

st.set_page_config(
    page_title="智能问数助手",
    page_icon="🤖",
    layout="wide"
)

# 初始化会话状态
if 'chat_agent' not in st.session_state:
    st.session_state.chat_agent = ChatAgent()
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_image' not in st.session_state:
    st.session_state.current_image = None


def main():
    st.title("🤖 上市公司财报智能问数助手")

    # 侧边栏
    with st.sidebar:
        st.header("功能设置")

        # 会话管理
        st.subheader("会话管理")
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

        # 图片上传
        st.subheader("多模态输入")
        uploaded_image = st.file_uploader(
            "上传图表/财报图片（可选）",
            type=['png', 'jpg', 'jpeg', 'webp'],
            help="上传财务图表或财报截图，助手将自动分析"
        )

        if uploaded_image:
            st.session_state.current_image = uploaded_image
            st.image(uploaded_image, caption="已上传的图片", use_container_width=True)
        else:
            st.session_state.current_image = None

        st.divider()

        # 使用指南
        with st.expander("📖 使用指南"):
            st.markdown("""
            ### 支持的问题类型

            **1. 数据查询**
            - "贵州茅台 2024 年的净利润是多少？"
            - "查询中国平安的资产负债率"

            **2. 对比分析**
            - "对比招商银行和浦发银行的营业收入"
            - "2024 年净利润排名前十的公司"

            **3. 趋势分析**
            - "贵州茅台近 5 年营业收入变化趋势"
            - "分析某公司的利润增长情况"

            **4. 多轮对话**
            - 可以先问"查询贵州茅台的净利润"
            - 再问"那营业收入呢？"（会理解上下文）

            ### 多模态功能
            上传财务图表截图，助手可以：
            - 识别图表类型和数据
            - 回答基于图表的问题
            """)

    # 主界面
    # 显示聊天历史
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
                    if msg.get('image'):
                        st.image(msg['image'], width=200)
            else:
                with st.chat_message("assistant"):
                    st.write(msg['content'])

                    # 显示 SQL（如果有）
                    if msg.get('sql'):
                        with st.expander("查看生成的 SQL"):
                            st.code(msg['sql'], language='sql')

                    # 显示数据（如果有）
                    if msg.get('data'):
                        df = pd.DataFrame(msg['data'])
                        with st.expander("查看查询结果"):
                            st.dataframe(df, use_container_width=True)

                    # 显示图表（如果有）
                    if msg.get('image_path'):
                        if os.path.exists(msg['image_path']):
                            st.image(msg['image_path'], caption=f"自动生成的{msg.get('chart_type', '图表')}",
                                   use_container_width=True)

                    # 显示建议（如果有）
                    if msg.get('suggestions'):
                        st.write("**您可以继续问：**")
                        for suggestion in msg['suggestions']:
                            st.write(f"- {suggestion}")

    # 输入区域
    st.divider()

    # 输入框
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.chat_input(
            "输入您的问题，例如：'贵州茅台 2024 年的净利润是多少？'",
            key="chat_input"
        )
    with col2:
        quick_questions = [
            "贵州茅台净利润",
            "营收排名前十",
            "资产负债率对比"
        ]
        selected = st.selectbox("快捷问题", ["", *quick_questions])

    # 处理用户输入
    if user_input or selected:
        question = user_input or selected

        # 添加用户消息到历史
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question,
            'image': None  # 可以添加图片引用
        })

        # 处理图片
        image_path = None
        if st.session_state.current_image:
            # 保存图片
            image_data = st.session_state.current_image.getvalue()
            image_dir = "result/uploaded_images"
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            with open(image_path, 'wb') as f:
                f.write(image_data)

        # 调用 ChatAgent 处理
        with st.spinner("正在分析..."):
            chat_agent = st.session_state.chat_agent
            response = chat_agent.chat(question, st.session_state.session_id, image_path)

        # 添加助手回复到历史
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response.get('answer', '抱歉，我无法回答这个问题'),
            'sql': response.get('sql'),
            'data': response.get('data'),
            'image_path': response.get('image'),
            'chart_type': response.get('chart_type'),
            'suggestions': response.get('suggestions', [])
        })

        # 清空图片
        if image_path:
            st.session_state.current_image = None
            if os.path.exists(image_path):
                os.remove(image_path)

        st.rerun()

    # 页脚
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"会话 ID: `{st.session_state.session_id[:20]}...`")
    with col2:
        st.write(f"对话轮数：{len(st.session_state.chat_history)}")
    with col3:
        st.write("💡 支持多轮对话和上下文理解")


if __name__ == "__main__":
    main()
