"""
文件处理应用 - 用于导入和处理财报数据
支持 PDF/Excel/Word 多种格式，现场演示使用
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

# 导入解析器模块
from parsers.pdf_parser import EnhancedPDFParser, ReportBatchParser
from utils.data_validator import DataCleaner, DataValidator


st.set_page_config(
    page_title="财报数据处理工具",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = {}
if 'import_history' not in st.session_state:
    st.session_state.import_history = []


def main():
    st.title("📁 财报数据处理工具")
    st.caption("支持 PDF/Excel/Word 多种格式，自动识别财报类型并提取数据")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 处理设置")

        # 数据目录选择
        st.subheader("📂 数据源")
        source_type = st.radio(
            "选择数据源类型",
            ["单文件上传", "批量导入目录"],
            index=0
        )

        # 输出目录
        output_dir = st.text_input(
            "输出目录",
            value="./data/processed",
            help="处理后的数据保存路径"
        )

        st.divider()

        # 导入统计
        st.subheader("📊 导入统计")
        if st.session_state.import_history:
            total_files = len(st.session_state.import_history)
            st.metric("已导入文件数", total_files)

            last_import = st.session_state.import_history[-1]
            st.info(f"最近导入：{last_import['time']}")

        st.divider()

        # 使用指南
        with st.expander("📖 使用指南"):
            st.markdown("""
            ### 快速开始

            1. **单文件上传**: 直接拖拽 PDF/Excel 文件
            2. **批量导入**: 选择包含多个财报的目录
            3. **查看结果**: 在处理结果中查看提取的数据
            4. **导出数据**: 导出为 CSV/Excel 格式

            ### 支持的格式
            - PDF: 财报 PDF 文件
            - Excel: .xlsx, .xls
            - Word: .doc, .docx (表格)

            ### 输出说明
            处理后的数据将保存到指定目录，包括:
            - 原始数据 CSV
            - 清洗后数据 CSV
            - 验证报告
            """)

    # 主界面
    if source_type == "单文件上传":
        handle_single_file()
    else:
        handle_batch_import()

    # 显示处理历史
    st.divider()
    show_import_history()


def handle_single_file():
    """处理单文件上传"""
    st.subheader("📄 单文件上传")

    uploaded_file = st.file_uploader(
        "上传财报文件",
        type=['pdf', 'xlsx', 'xls', 'doc', 'docx'],
        help="支持 PDF/Excel/Word 格式"
    )

    if uploaded_file:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.info(f"当前文件：**{uploaded_file.name}** ({format_size(uploaded_file.size)})")

        with col2:
            if st.button("🚀 开始处理", use_container_width=True):
                process_file(uploaded_file)

        # 显示处理结果
        if st.session_state.processed_data:
            display_processed_data()


def handle_batch_import():
    """处理批量导入"""
    st.subheader("📂 批量导入")

    # 默认数据目录
    default_dirs = [
        "B 题 - 示例数据/示例数据/附件 2：财务报告/reports-上交所",
        "B 题 - 示例数据/示例数据/附件 2：财务报告/reports-深交所",
        "data/input",
    ]

    selected_dir = st.selectbox(
        "选择预设目录",
        default_dirs,
        index=0
    )

    custom_dir = st.text_input("或输入自定义目录路径")

    target_dir = custom_dir if custom_dir else selected_dir

    if st.button("📁 扫描目录"):
        if os.path.exists(target_dir):
            scan_directory(target_dir)
        else:
            st.error(f"目录不存在：{target_dir}")


def process_file(uploaded_file):
    """处理上传文件"""
    file_name = uploaded_file.name
    file_ext = file_name.split('.')[-1].lower()

    with st.spinner(f"正在处理 {file_name}..."):
        try:
            # 创建临时文件
            temp_path = f"./data/temp/{file_name}"
            os.makedirs("./data/temp", exist_ok=True)

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # 根据格式选择解析器
            if file_ext == 'pdf':
                parser = EnhancedPDFParser()
                result = parser.parse_pdf(temp_path)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(temp_path)
                result = {'data': df.to_dict('records'), 'source': file_name}
            elif file_ext in ['doc', 'docx']:
                # TODO: Word 解析
                result = {'data': [], 'source': file_name, 'warning': 'Word 解析功能开发中'}
            else:
                result = {'error': f'不支持的格式：{file_ext}'}

            # 保存处理结果
            if result and 'error' not in result:
                st.session_state.processed_data[file_name] = result

                # 记录导入历史
                st.session_state.import_history.append({
                    'file': file_name,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'records': len(result.get('data', []))
                })

                st.success(f"✅ 处理成功！共提取 {len(result.get('data', []))} 条记录")
            else:
                st.error(f"❌ 处理失败：{result.get('error', '未知错误')}")

            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

        except Exception as e:
            st.error(f"处理出错：{e}")


def display_processed_data():
    """显示处理结果"""
    st.subheader("📊 处理结果")

    for file_name, data in st.session_state.processed_data.items():
        with st.expander(f"📄 {file_name}", expanded=True):
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])

                # 显示统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("记录数", len(df))
                with col2:
                    st.metric("字段数", len(df.columns))
                with col3:
                    st.metric("数据来源", data.get('source', '未知'))

                # 显示数据预览
                st.dataframe(df.head(10), use_container_width=True)

                # 导出选项
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "📥 导出 CSV",
                        csv,
                        f"{file_name}_processed.csv",
                        use_container_width=True
                    )
                with col2:
                    excel_buffer = pd.ExcelWriter('output.xlsx', engine='openpyxl')
                    df.to_excel(excel_buffer, index=False)
                    excel_buffer.close()
                    with open('output.xlsx', 'rb') as f:
                        st.download_button(
                            "📥 导出 Excel",
                            f.read(),
                            f"{file_name}_processed.xlsx",
                            use_container_width=True
                        )
                    os.remove('output.xlsx')
            else:
                st.warning("暂无数据")


def scan_directory(directory):
    """扫描目录并显示文件列表"""
    st.write(f"扫描目录：**{directory}**")

    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.pdf'):
                pdf_files.append(os.path.join(root, f))

    if pdf_files:
        st.success(f"找到 {len(pdf_files)} 个 PDF 文件")

        # 显示文件列表
        st.write("文件列表:")
        for f in pdf_files[:20]:  # 只显示前 20 个
            st.write(f"- {f}")

        if len(pdf_files) > 20:
            st.write(f"... 还有 {len(pdf_files) - 20} 个文件")

        # 批量处理按钮
        if st.button(f"🚀 批量处理所有 {len(pdf_files)} 个文件"):
            process_batch(pdf_files)
    else:
        st.warning("未找到 PDF 文件")


def process_batch(files):
    """批量处理文件"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    success_count = 0
    error_count = 0

    for i, file_path in enumerate(files):
        status_text.text(f"正在处理 ({i+1}/{len(files)}): {os.path.basename(file_path)}")

        try:
            # 简化处理逻辑
            parser = EnhancedPDFParser()
            result = parser.parse_pdf(file_path)

            if result and 'error' not in result:
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1

        progress_bar.progress((i + 1) / len(files))

    status_text.text("批量处理完成!")

    col1, col2 = st.columns(2)
    with col1:
        st.success(f"成功：{success_count}")
    with col2:
        st.error(f"失败：{error_count}")


def show_import_history():
    """显示导入历史"""
    st.subheader("📜 导入历史")

    if st.session_state.import_history:
        history_df = pd.DataFrame(st.session_state.import_history)
        st.dataframe(history_df, use_container_width=True)

        # 清空历史按钮
        if st.button("🗑️ 清空历史"):
            st.session_state.import_history = []
            st.rerun()
    else:
        st.info("暂无导入记录")


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"


if __name__ == "__main__":
    main()
