"""
文件处理应用 - 用于导入和处理财报数据
支持 PDF/Excel/Word 多种格式，现场演示使用
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入解析器模块
from src.etl.financial_parser import FinancialParser, ReportBatchParser


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

    # 动态查找数据目录 - 避免中文路径编码问题
    default_dirs = []

    # 使用 rglob 查找包含 PDF 的目录
    base_path = Path(".")

    # 查找 reports-上交所 和 reports-深交所 目录
    for dir_pattern in ["**/reports-上交所", "**/reports-深交所", "**/data/input"]:
        for found_dir in base_path.glob(dir_pattern):
            if found_dir.is_dir():
                default_dirs.append(str(found_dir))

    # 如果没有找到，使用硬编码路径作为 fallback
    if not default_dirs:
        default_dirs = [
            "B 题 - 示例数据/示例数据/附件 2：财务报告/reports-上交所",
            "B 题 - 示例数据/示例数据/附件 2：财务报告/reports-深交所",
            "data/input",
        ]

    if not default_dirs:
        st.warning("未找到默认数据目录，请手动输入路径")
        default_dirs = [""]

    selected_dir = st.selectbox(
        "选择预设目录",
        default_dirs,
        index=0 if default_dirs[0] else -1
    )

    custom_dir = st.text_input("或输入自定义目录路径")

    target_dir = Path(custom_dir) if custom_dir else Path(selected_dir)

    if st.button("📁 扫描目录"):
        if target_dir.exists():
            scan_directory(str(target_dir))
        else:
            st.error(f"目录不存在：{target_dir}")


def process_file(uploaded_file):
    """处理上传文件"""
    file_name = uploaded_file.name
    file_ext = file_name.split('.')[-1].lower()

    with st.spinner(f"正在处理 {file_name}..."):
        try:
            # 创建临时文件
            temp_dir = Path("./data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / file_name

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # 根据格式选择解析器
            if file_ext == 'pdf':
                parser = FinancialParser()
                result = parser.parse_pdf(str(temp_path))

                # 提取核心指标
                if 'error' not in result:
                    key_metrics = parser.extract_key_metrics(result)
                    result = {'data': [key_metrics] if key_metrics else [], 'source': file_name}
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
            if temp_path.exists():
                temp_path.unlink()

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
                    Path('output.xlsx').unlink()
            else:
                st.warning("暂无数据")


def scan_directory(directory):
    """扫描目录并显示文件列表"""
    st.write(f"扫描目录：**{directory}**")

    dir_path = Path(directory)
    pdf_files = list(dir_path.rglob("*.pdf"))  # 递归查找所有 PDF 文件

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
            process_batch([str(f) for f in pdf_files])
    else:
        st.warning("未找到 PDF 文件")


def process_batch(files):
    """批量处理文件"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_text = st.empty()

    success_count = 0
    error_count = 0
    total_records = 0

    # 初始化解析器
    parser = FinancialParser()

    for i, file_path in enumerate(files):
        status_text.text(f"正在处理 ({i+1}/{len(files)}): {Path(file_path).name}")

        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                error_count += 1
                continue

            # 使用 parse_pdf 方法解析文件
            result = parser.parse_pdf(file_path)

            # 检查是否有错误
            if 'error' in result:
                error_count += 1
                continue

            # 提取核心指标
            key_metrics = parser.extract_key_metrics(result)

            # 转换为字典格式保存
            data_records = [key_metrics] if key_metrics else []
            result = {
                'data': data_records,
                'source': Path(file_path).name,
                'stock_code': key_metrics.get('stock_code'),
                'report_type': key_metrics.get('report_type')
            }

            if result and result['data']:
                # 保存到 session_state
                st.session_state.processed_data[Path(file_path).name] = result

                # 记录导入历史
                st.session_state.import_history.append({
                    'file': Path(file_path).name,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'records': len(result['data'])
                })

                success_count += 1
                total_records += len(result['data'])
            else:
                error_count += 1

        except Exception as e:
            error_count += 1

        progress_bar.progress((i + 1) / len(files))

    status_text.text("批量处理完成!")

    # 显示详细结果
    result_text.markdown(f"**共处理 {len(files)} 个文件，成功 {success_count} 个，失败 {error_count} 个，总计 {total_records} 条记录**")

    col1, col2 = st.columns(2)
    with col1:
        st.success(f"成功：{success_count}")
    with col2:
        st.error(f"失败：{error_count}")

    # 显示处理结果按钮
    if success_count > 0:
        if st.button("📊 查看处理结果"):
            display_processed_data()


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
