"""
批量导入数据解析应用

用于批量解析 data/import 目录中的财报文件，支持：
1. 从示例数据目录导入
2. 从自定义目录导入
3. 查看解析结果
4. 导出为 CSV/Excel
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

from src.import_batch_processor import BatchImportProcessor
from src.etl.financial_parser import FinancialParser


# 页面配置
st.set_page_config(
    page_title="财报批量导入解析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if 'processing_result' not in st.session_state:
    st.session_state.processing_result = None
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'processing_log' not in st.session_state:
    st.session_state.processing_log = []


def main():
    st.title("📊 财报批量导入解析系统")
    st.caption("基于题目要求，批量解析财报 PDF 并输出结构化数据")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")

        # 数据源选择
        st.subheader("📂 数据源")
        source_type = st.radio(
            "选择数据来源",
            ["示例数据目录", "导入数据目录 (data/import)", "自定义目录"],
            index=1
        )

        # 输出目录
        output_dir = st.text_input(
            "输出目录",
            value="./data/import/output",
            help="解析结果保存路径"
        )

        st.divider()

        # 处理状态
        st.subheader("📈 处理状态")
        if st.session_state.processing_log:
            success_count = sum(1 for log in st.session_state.processing_log if log.get('status') == '处理成功')
            error_count = len(st.session_state.processing_log) - success_count
            st.metric("成功处理", success_count)
            st.metric("失败", error_count)
        else:
            st.info("暂无处理记录")

        st.divider()

        # 使用说明
        with st.expander("📖 使用说明"):
            st.markdown("""
            ### 快速开始

            1. **选择数据源**
               - 示例数据目录：使用 B 题示例数据
               - 导入数据目录：从 data/import 读取
               - 自定义目录：指定任意目录

            2. **放置文件**
               - PDF 文件放入：`data/import/pdf_reports/`
               - Excel 文件放入：`data/import/excel_reports/`

            3. **开始处理**
               - 点击"开始批量处理"按钮

            4. **查看结果**
               - 在处理结果标签页查看解析数据
               - 支持导出 CSV/Excel 格式

            ### 输出文件

            - `key_metrics.csv` - 核心业绩指标
            - `balance_sheet.csv` - 资产负债表
            - `income_statement.csv` - 利润表
            - `cash_flow_statement.csv` - 现金流量表
            - `processing_log.xlsx` - 处理日志
            """)

    # 主界面 - 标签页
    tabs = st.tabs(["📁 数据导入", "📊 处理结果", "📝 处理日志", "📋 题目要求"])

    with tabs[0]:
        show_import_section(source_type, output_dir)

    with tabs[1]:
        show_results_section()

    with tabs[2]:
        show_log_section()

    with tabs[3]:
        show_requirements_section()


def show_import_section(source_type: str, output_dir: str):
    """显示数据导入界面"""
    st.subheader("📁 数据导入")

    # 根据数据源类型确定输入目录
    input_dir = None

    if source_type == "示例数据目录":
        # 使用 rglob 动态查找示例数据目录
        base_path = Path(".")
        sample_dirs = list(base_path.rglob("B 题 - 示例数据"))
        if sample_dirs:
            input_dir = str(sample_dirs[0])
            st.info(f"示例数据目录：{input_dir}")
        else:
            st.error("未找到示例数据目录")
            input_dir = "./B 题 - 示例数据"

    elif source_type == "导入数据目录 (data/import)":
        input_dir = "./data/import"
        import_path = Path(input_dir)
        if import_path.exists():
            # 检查子目录
            pdf_dir = import_path / "pdf_reports"
            excel_dir = import_path / "excel_reports"

            col1, col2 = st.columns(2)
            with col1:
                if pdf_dir.exists():
                    pdf_count = len(list(pdf_dir.rglob("*.pdf")))
                    st.metric("PDF 文件", pdf_count)
                else:
                    st.warning("pdf_reports 目录不存在")

            with col2:
                if excel_dir.exists():
                    excel_count = len(list(excel_dir.rglob("*.xlsx"))) + len(list(excel_dir.rglob("*.xls")))
                    st.metric("Excel 文件", excel_count)
                else:
                    st.warning("excel_reports 目录不存在")
        else:
            st.warning("导入数据目录不存在，将自动创建")

    else:  # 自定义目录
        input_dir = st.text_input(
            "自定义目录路径",
            value="./data/import",
            help="输入包含财报文件的目录路径"
        )

    # 显示文件预览
    if input_dir:
        input_path = Path(input_dir)
        if input_path.exists():
            st.markdown("### 📄 文件预览")

            # 使用 rglob 查找文件，避免中文路径问题
            pdf_files = list(input_path.rglob("*.pdf"))
            excel_files = list(input_path.rglob("*.xlsx")) + list(input_path.rglob("*.xls"))

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**PDF 文件**: {len(pdf_files)} 个")
                for f in pdf_files[:5]:
                    st.write(f"  - {f.name}")
                if len(pdf_files) > 5:
                    st.write(f"  ... 还有 {len(pdf_files) - 5} 个")

            with col2:
                st.write(f"**Excel 文件**: {len(excel_files)} 个")
                for f in excel_files[:5]:
                    st.write(f"  - {f.name}")
                if len(excel_files) > 5:
                    st.write(f"  ... 还有 {len(excel_files) - 5} 个")

    # 处理按钮
    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        process_btn = st.button("🚀 开始批量处理", type="primary", use_container_width=True)

    if process_btn and input_dir:
        run_batch_processing(input_dir, output_dir)


def run_batch_processing(input_dir: str, output_dir: str):
    """运行批量处理"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_container = st.container()

    try:
        status_text.text("正在初始化处理器...")

        # 创建处理器
        processor = BatchImportProcessor(
            input_dir=input_dir,
            output_dir=output_dir
        )

        # 扫描目录
        status_text.text("正在扫描输入目录...")
        files = processor.scan_input_directories()
        total_files = len(files["pdf_files"]) + len(files["excel_files"])

        if total_files == 0:
            st.warning("⚠️ 未找到任何待处理文件")
            return

        status_text.text(f"找到 {total_files} 个文件，开始处理...")

        # 处理 PDF 文件
        all_dataframes = {}
        if files["pdf_files"]:
            status_text.text(f"正在处理 PDF 文件 (共{len(files['pdf_files'])} 个)...")
            pdf_results = processor.process_pdf_files(files["pdf_files"])
            all_dataframes.update(pdf_results)
            progress_bar.progress(0.5)

        # 处理 Excel 文件
        if files["excel_files"]:
            status_text.text(f"正在处理 Excel 文件 (共{len(files['excel_files'])} 个)...")
            excel_results = processor.process_excel_files(files["excel_files"])
            all_dataframes.update(excel_results)
            progress_bar.progress(0.8)

        # 保存结果
        status_text.text("正在保存处理结果...")
        saved_files = processor.save_results(all_dataframes)
        progress_bar.progress(1.0)

        # 更新会话状态
        st.session_state.processing_result = saved_files
        st.session_state.dataframes = all_dataframes
        st.session_state.processing_log = processor.processing_log

        status_text.text("处理完成!")

        # 显示结果摘要
        with result_container:
            st.success("✅ 批量处理完成!")

            col1, col2, col3 = st.columns(3)
            with col1:
                success_count = sum(1 for log in processor.processing_log if log['status'] == '处理成功')
                st.metric("成功", success_count)
            with col2:
                error_count = len(processor.processing_log) - success_count
                st.metric("失败", error_count)
            with col3:
                st.metric("输出文件", len(saved_files))

            st.markdown("### 输出文件")
            for name, path in saved_files.items():
                st.write(f"- **{name}**: `{path}`")

            # 自动切换到结果标签页
            st.info("💡 请切换到'处理结果'标签页查看详细数据")

    except Exception as e:
        status_text.text("")
        st.error(f"❌ 处理出错：{e}")
        import traceback
        st.code(traceback.format_exc())


def show_results_section():
    """显示处理结果"""
    st.subheader("📊 处理结果")

    if not st.session_state.dataframes:
        st.info("暂无处理结果，请先在'数据导入'标签页执行批量处理")
        return

    # 显示可用的数据集
    dataframes = st.session_state.dataframes
    dataset_names = list(dataframes.keys())

    if not dataset_names:
        st.warning("暂无数据")
        return

    # 数据集选择
    selected_dataset = st.selectbox(
        "选择数据集",
        dataset_names,
        format_func=lambda x: get_dataset_display_name(x)
    )

    if selected_dataset in dataframes:
        df = dataframes[selected_dataset]

        if df is not None and not df.empty:
            # 显示统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("记录数", len(df))
            with col2:
                st.metric("字段数", len(df.columns))
            with col3:
                st.metric("内存使用", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

            # 显示数据预览
            st.markdown("### 数据预览")
            st.dataframe(df, use_container_width=True, height=400)

            # 导出选项
            st.markdown("### 📥 导出")
            col1, col2 = st.columns(2)

            with col1:
                csv_data = df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 下载 CSV",
                    data=csv_data,
                    file_name=f"{selected_dataset}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col2:
                excel_buffer = pd.ExcelWriter("temp_export.xlsx", engine="openpyxl")
                df.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                with open("temp_export.xlsx", "rb") as f:
                    st.download_button(
                        label="📥 下载 Excel",
                        data=f.read(),
                        file_name=f"{selected_dataset}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                Path("temp_export.xlsx").unlink()
        else:
            st.warning("该数据集为空")


def get_dataset_display_name(name: str) -> str:
    """获取数据集的显示名称"""
    names = {
        "key_metrics": "核心业绩指标",
        "balance_sheet": "资产负债表",
        "income_statement": "利润表",
        "cash_flow_statement": "现金流量表",
        "excel_imports": "Excel 导入数据",
        "processing_log": "处理日志"
    }
    return names.get(name, name)


def show_log_section():
    """显示处理日志"""
    st.subheader("📝 处理日志")

    if not st.session_state.processing_log:
        st.info("暂无处理日志")
        return

    # 转换为 DataFrame 显示
    df_log = pd.DataFrame(st.session_state.processing_log)

    # 状态筛选
    status_filter = st.multiselect(
        "筛选状态",
        options=df_log["status"].unique().tolist(),
        default=df_log["status"].unique().tolist()
    )

    if status_filter:
        df_filtered = df_log[df_log["status"].isin(status_filter)]
    else:
        df_filtered = df_log

    st.dataframe(df_filtered, use_container_width=True)

    # 导出日志
    if len(df_log) > 0:
        excel_buffer = pd.ExcelWriter("processing_log_export.xlsx", engine="openpyxl")
        df_log.to_excel(excel_buffer, index=False)
        excel_buffer.close()
        with open("processing_log_export.xlsx", "rb") as f:
            st.download_button(
                label="📥 导出日志",
                data=f.read(),
                file_name="processing_log.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        Path("processing_log_export.xlsx").unlink()


def show_requirements_section():
    """显示题目要求"""
    st.subheader("📋 题目要求（基于 B 题）")

    st.markdown("""
    ### 任务要求

    #### 1. 财报数据解析（任务一）

    解析上市公司财报 PDF 文件，提取结构化数据：

    **数据表结构：**

    1. **核心业绩指标表** (core_performance_indicators)
       - 股票代码、股票简称、报告期
       - 基本每股收益、稀释每股收益、每股净资产
       - 营业总收入、净利润

    2. **资产负债表** (balance_sheet)
       - 资产：货币资金、应收账款、存货、流动资产合计、固定资产、总资产等
       - 负债：短期借款、应付账款、流动负债合计、长期借款、总负债等
       - 所有者权益：股本、资本公积、盈余公积、未分配利润、所有者权益合计

    3. **利润表** (income_statement)
       - 营业总收入、营业总成本、营业成本、销售费用、管理费用、财务费用、研发费用
       - 营业利润、利润总额、净利润

    4. **现金流量表** (cash_flow_statement)
       - 经营活动现金流：流入小计、流出小计、净额
       - 投资活动现金流：流入小计、流出小计、净额
       - 筹资活动现金流：流入小计、流出小计、净额

    #### 2. 智能问数（任务二）

    支持自然语言查询财报数据：
    - 单公司查询："贵州茅台 2024 年的净利润是多少？"
    - 排名查询："查询所有公司的营业收入排名"
    - 对比查询："对比招商银行和浦发银行的总资产"

    #### 3. RAG 增强与归因分析（任务三）

    整合行业报告、企业信息等非结构化文档：
    - 支持上传 PDF 研报
    - 基于 RAG 的智能问答
    - 输出答案包含参考来源

    ### 输出格式

    #### 任务二输出 (task2_output.xlsx)

    | 问题编号 | 问题 | SQL | 图表路径 | 时间戳 |
    |----------|------|-----|----------|--------|
    | B002_01  | ...  | ... | ./result/B002_01_01.jpg | 2026-03-24T10:00:00 |

    #### 任务三输出 (task3_output.xlsx)

    | 问题编号 | 问题 | SQL | 图表路径 | 答案 | references |
    |----------|------|-----|----------|------|------------|
    | B003_01  | ...  | ... | ... | ... | [{source, content, similarity}] |

    ### 支持的财报格式

    **上交所格式：**
    - 格式：`股票代码_报告日期_随机标识.pdf`
    - 示例：`600080_20230428_FQ2V.pdf`

    **深交所格式：**
    - 格式：`公司简称：年份 + 报告类型.pdf`
    - 示例：`华润三九：2023 年年度报告.pdf`
    """)


if __name__ == "__main__":
    main()
