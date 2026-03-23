import streamlit as st
import pandas as pd
import os
import sys
import tempfile
from datetime import datetime
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="财报数据处理系统",
    page_icon="📊",
    layout="wide"
)

if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None

def main():
    st.title("📊 上市公司财报数据处理系统")
    
    with st.sidebar:
        st.header("功能导航")
        page = st.radio(
            "选择功能",
            ["首页", "PDF解析", "数据预览", "数据校验", "数据导出"],
            label_visibility="collapsed"
        )
        
        st.divider()
        st.subheader("系统状态")
        if st.session_state.parsed_data:
            st.success("已加载数据")
        else:
            st.info("等待数据")
    
    if page == "首页":
        show_home_page()
    elif page == "PDF解析":
        show_parse_page()
    elif page == "数据预览":
        show_preview_page()
    elif page == "数据校验":
        show_validation_page()
    elif page == "数据导出":
        show_export_page()

def show_home_page():
    st.header("欢迎使用财报数据处理系统")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📤 PDF解析")
        st.write("上传PDF财报文件，自动提取财务数据")
        st.markdown("- 支持批量上传\n- 自动识别报告类型\n- 提取四大财务报表")
    
    with col2:
        st.subheader("📋 数据处理")
        st.write("智能清洗和校验财务数据")
        st.markdown("- 数据格式标准化\n- 多维度校验\n- 一致性检查")
    
    with col3:
        st.subheader("💾 数据导出")
        st.write("多种格式导出处理结果")
        st.markdown("- CSV格式\n- Excel格式\n- 数据库入库")
    
    st.divider()
    
    st.header("快速开始")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**步骤1: 上传PDF文件**")
        st.write("1. 点击左侧导航栏的'PDF解析'")
        st.write("2. 上传单个或多个PDF财报文件")
        st.write("3. 点击'开始解析'按钮")
    
    with col2:
        st.markdown("**步骤2: 查看和导出数据**")
        st.write("1. 在'数据预览'查看提取的数据")
        st.write("2. 在'数据校验'检查数据质量")
        st.write("3. 在'数据导出'下载处理结果")
    
    if st.session_state.parsed_data:
        st.divider()
        st.header("当前数据概览")
        
        data = st.session_state.parsed_data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("资产负债表", f"{len(data.get('balance_sheet', []))} 条")
        with col2:
            st.metric("利润表", f"{len(data.get('income_statement', []))} 条")
        with col3:
            st.metric("现金流量表", f"{len(data.get('cash_flow_statement', []))} 条")
        with col4:
            st.metric("核心指标", f"{len(data.get('key_metrics', []))} 条")

def show_parse_page():
    st.header("📤 PDF财报解析")
    
    tab1, tab2 = st.tabs(["上传文件", "选择目录"])
    
    with tab1:
        st.subheader("上传PDF文件")
        st.info("支持上传多个PDF文件，系统将自动解析并提取财务数据")
        
        uploaded_files = st.file_uploader(
            "选择PDF文件",
            type=['pdf'],
            accept_multiple_files=True,
            help="可以同时上传多个PDF财报文件"
        )
        
        if uploaded_files:
            st.write(f"已选择 {len(uploaded_files)} 个文件:")
            for file in uploaded_files:
                st.write(f"  - {file.name}")
            
            if st.button("开始解析", type="primary"):
                parse_uploaded_files(uploaded_files)
    
    with tab2:
        st.subheader("选择报告目录")
        
        default_dir = os.path.join(
            os.path.dirname(__file__), 
            "B题-示例数据", "示例数据", "附件2：财务报告"
        )
        
        if os.path.exists(default_dir):
            st.info(f"默认目录: {default_dir}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**上交所报告**")
                sse_dir = os.path.join(default_dir, "reports-上交所")
                if os.path.exists(sse_dir):
                    sse_files = [f for f in os.listdir(sse_dir) if f.endswith('.pdf')]
                    st.write(f"共 {len(sse_files)} 个文件")
            
            with col2:
                st.write("**深交所报告**")
                szse_dir = os.path.join(default_dir, "reports-深交所")
                if os.path.exists(szse_dir):
                    szse_files = [f for f in os.listdir(szse_dir) if f.endswith('.pdf')]
                    st.write(f"共 {len(szse_files)} 个文件")
            
            if st.button("解析默认目录", type="primary"):
                parse_directory(default_dir)
        else:
            st.warning("默认目录不存在，请手动输入目录路径")
            
            dir_path = st.text_input("输入PDF报告目录路径")
            if dir_path and os.path.exists(dir_path):
                if st.button("开始解析", type="primary"):
                    parse_directory(dir_path)

def parse_uploaded_files(uploaded_files):
    from parsers.pdf_parser import EnhancedPDFParser, ReportBatchParser
    from utils.data_validator import DataCleaner
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    parser = EnhancedPDFParser()
    batch_parser = ReportBatchParser()
    
    all_reports = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"正在解析: {uploaded_file.name}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            report = parser.parse_report(tmp_path)
            all_reports.append(report)
        except Exception as e:
            st.error(f"解析 {uploaded_file.name} 失败: {e}")
        
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.text("正在转换数据格式...")
    dataframes = batch_parser.parse_reports_to_dataframe(all_reports)
    
    cleaner = DataCleaner()
    cleaned_data = {}
    for table_name, df in dataframes.items():
        cleaned_data[table_name] = cleaner.clean_dataframe(df, table_name)
    
    st.session_state.parsed_data = {
        'balance_sheet': dataframes['balance_sheet'].to_dict('records'),
        'income_statement': dataframes['income_statement'].to_dict('records'),
        'cash_flow_statement': dataframes['cash_flow_statement'].to_dict('records'),
        'key_metrics': dataframes['key_metrics'].to_dict('records')
    }
    
    st.session_state.cleaned_data = {
        'balance_sheet': cleaned_data['balance_sheet'].to_dict('records'),
        'income_statement': cleaned_data['income_statement'].to_dict('records'),
        'cash_flow_statement': cleaned_data['cash_flow_statement'].to_dict('records'),
        'key_metrics': cleaned_data['key_metrics'].to_dict('records')
    }
    
    progress_bar.progress(1.0)
    status_text.empty()
    
    st.success(f"成功解析 {len(all_reports)} 份报告！")
    show_parse_summary(dataframes)

def parse_directory(directory):
    from parsers.pdf_parser import EnhancedPDFParser, ReportBatchParser
    from utils.data_validator import DataCleaner
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("正在扫描目录...")
    
    batch_parser = ReportBatchParser()
    
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    if not pdf_files:
        st.error("未找到PDF文件")
        return
    
    parser = EnhancedPDFParser()
    all_reports = []
    
    for i, pdf_path in enumerate(pdf_files):
        status_text.text(f"正在解析: {os.path.basename(pdf_path)}")
        
        try:
            report = parser.parse_report(pdf_path)
            all_reports.append(report)
        except Exception as e:
            st.warning(f"解析 {os.path.basename(pdf_path)} 失败: {e}")
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.text("正在转换数据格式...")
    dataframes = batch_parser.parse_reports_to_dataframe(all_reports)
    
    cleaner = DataCleaner()
    cleaned_data = {}
    for table_name, df in dataframes.items():
        cleaned_data[table_name] = cleaner.clean_dataframe(df, table_name)
    
    st.session_state.parsed_data = {
        'balance_sheet': dataframes['balance_sheet'].to_dict('records'),
        'income_statement': dataframes['income_statement'].to_dict('records'),
        'cash_flow_statement': dataframes['cash_flow_statement'].to_dict('records'),
        'key_metrics': dataframes['key_metrics'].to_dict('records')
    }
    
    st.session_state.cleaned_data = {
        'balance_sheet': cleaned_data['balance_sheet'].to_dict('records'),
        'income_statement': cleaned_data['income_statement'].to_dict('records'),
        'cash_flow_statement': cleaned_data['cash_flow_statement'].to_dict('records'),
        'key_metrics': cleaned_data['key_metrics'].to_dict('records')
    }
    
    progress_bar.progress(1.0)
    status_text.empty()
    
    st.success(f"成功解析 {len(all_reports)} 份报告！")
    show_parse_summary(dataframes)

def show_parse_summary(dataframes):
    st.subheader("解析结果摘要")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("资产负债表", f"{len(dataframes['balance_sheet'])} 条记录")
    with col2:
        st.metric("利润表", f"{len(dataframes['income_statement'])} 条记录")
    with col3:
        st.metric("现金流量表", f"{len(dataframes['cash_flow_statement'])} 条记录")
    with col4:
        st.metric("核心指标", f"{len(dataframes['key_metrics'])} 条记录")

def show_preview_page():
    st.header("📋 数据预览")
    
    if not st.session_state.cleaned_data:
        st.warning("请先在'PDF解析'页面上传并解析PDF文件")
        return
    
    data = st.session_state.cleaned_data
    
    table_names = {
        'balance_sheet': '资产负债表',
        'income_statement': '利润表',
        'cash_flow_statement': '现金流量表',
        'key_metrics': '核心业绩指标'
    }
    
    tabs = st.tabs(list(table_names.values()))
    
    for i, (table_key, table_name) in enumerate(table_names.items()):
        with tabs[i]:
            df = pd.DataFrame(data.get(table_key, []))
            
            if df.empty:
                st.info(f"暂无{table_name}数据")
                continue
            
            st.write(f"**共 {len(df)} 条记录，{len(df.columns)} 个字段**")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                show_count = st.selectbox(
                    "显示行数",
                    [10, 20, 50, 100, "全部"],
                    key=f"show_count_{table_key}"
                )
            
            if show_count == "全部":
                display_df = df
            else:
                display_df = df.head(int(show_count))
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            with st.expander("数据统计"):
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if len(numeric_cols) > 0:
                    st.write(df[numeric_cols].describe())
                else:
                    st.info("无数值型字段")

def show_validation_page():
    st.header("✅ 数据校验")
    
    if not st.session_state.cleaned_data:
        st.warning("请先在'PDF解析'页面上传并解析PDF文件")
        return
    
    data = st.session_state.cleaned_data
    
    if st.button("开始校验", type="primary"):
        run_validation(data)
    
    if st.session_state.validation_results:
        show_validation_results()

def run_validation(data):
    from utils.data_validator import DataValidator, DataConsistencyChecker
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    validator = DataValidator()
    consistency_checker = DataConsistencyChecker()
    
    results = {}
    table_names = {
        'balance_sheet': '资产负债表',
        'income_statement': '利润表',
        'cash_flow_statement': '现金流量表',
        'key_metrics': '核心业绩指标'
    }
    
    for i, (table_key, table_name) in enumerate(table_names.items()):
        status_text.text(f"正在校验: {table_name}")
        df = pd.DataFrame(data.get(table_key, []))
        results[table_key] = validator.validate_dataframe(df, table_key)
        progress_bar.progress((i + 1) / 4)
    
    status_text.text("正在进行一致性检查...")
    dataframes = {k: pd.DataFrame(v) for k, v in data.items()}
    inconsistencies = consistency_checker.check_cross_table_consistency(dataframes)
    results['consistency'] = inconsistencies
    
    progress_bar.progress(1.0)
    status_text.empty()
    
    st.session_state.validation_results = results
    st.success("校验完成！")

def show_validation_results():
    results = st.session_state.validation_results
    
    table_names = {
        'balance_sheet': '资产负债表',
        'income_statement': '利润表',
        'cash_flow_statement': '现金流量表',
        'key_metrics': '核心业绩指标'
    }
    
    st.subheader("校验结果")
    
    passed_count = sum(1 for k, v in results.items() if k != 'consistency' and v.get('status') == 'passed')
    total_count = len([k for k in results if k != 'consistency'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("通过校验", passed_count)
    with col2:
        st.metric("未通过", total_count - passed_count)
    with col3:
        st.metric("通过率", f"{passed_count/total_count*100:.1f}%" if total_count > 0 else "0%")
    
    for table_key, table_name in table_names.items():
        if table_key in results:
            with st.expander(f"{'✅' if results[table_key].get('status') == 'passed' else '❌'} {table_name}", 
                           expanded=results[table_key].get('status') != 'passed'):
                table_result = results[table_key]
                
                st.write(f"**状态**: {table_result.get('status', 'unknown')}")
                st.write(f"**记录数**: {table_result.get('total_rows', 0)}")
                st.write(f"**字段数**: {table_result.get('total_columns', 0)}")
                
                st.write("**详细检查结果**:")
                for validation in table_result.get('validations', []):
                    check_name = validation.get('check', 'unknown')
                    passed = validation.get('passed', True)
                    
                    if passed:
                        st.write(f"  ✅ {check_name}")
                    else:
                        st.write(f"  ❌ {check_name}")
                        for key, value in validation.items():
                            if key not in ['check', 'passed']:
                                st.write(f"      - {key}: {value}")
    
    if 'consistency' in results and results['consistency']:
        with st.expander("⚠️ 一致性问题"):
            for issue in results['consistency']:
                st.warning(f"**{issue['type']}**: {issue['message']} (严重程度: {issue['severity']})")

def show_export_page():
    st.header("💾 数据导出")
    
    if not st.session_state.cleaned_data:
        st.warning("请先在'PDF解析'页面上传并解析PDF文件")
        return
    
    data = st.session_state.cleaned_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("导出Excel文件")
        st.info("将所有表格导出为一个Excel文件，每个表格为一个工作表")
        
        if st.button("生成Excel文件", type="primary"):
            excel_buffer = BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                table_names = {
                    'balance_sheet': '资产负债表',
                    'income_statement': '利润表',
                    'cash_flow_statement': '现金流量表',
                    'key_metrics': '核心业绩指标'
                }
                
                for table_key, sheet_name in table_names.items():
                    df = pd.DataFrame(data.get(table_key, []))
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            excel_buffer.seek(0)
            
            st.download_button(
                label="下载Excel文件",
                data=excel_buffer,
                file_name=f"financial_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        st.subheader("导出CSV文件")
        st.info("选择要导出的表格，下载为CSV文件")
        
        table_names = {
            'balance_sheet': '资产负债表',
            'income_statement': '利润表',
            'cash_flow_statement': '现金流量表',
            'key_metrics': '核心业绩指标'
        }
        
        for table_key, table_name in table_names.items():
            df = pd.DataFrame(data.get(table_key, []))
            if not df.empty:
                csv_buffer = BytesIO()
                df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_buffer.seek(0)
                
                st.download_button(
                    label=f"下载{table_name}CSV",
                    data=csv_buffer,
                    file_name=f"{table_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    st.divider()
    st.subheader("导出校验报告")
    
    if st.session_state.validation_results:
        if st.button("生成校验报告"):
            report_content = generate_validation_report()
            
            st.download_button(
                label="下载校验报告",
                data=report_content,
                file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    else:
        st.info("请先在'数据校验'页面运行校验")

def generate_validation_report():
    results = st.session_state.validation_results
    
    lines = [
        "=" * 60,
        "财务报告数据校验报告",
        "=" * 60,
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "一、校验结果概览",
        "-" * 40
    ]
    
    table_names = {
        'balance_sheet': '资产负债表',
        'income_statement': '利润表',
        'cash_flow_statement': '现金流量表',
        'key_metrics': '核心业绩指标'
    }
    
    for table_key, table_name in table_names.items():
        if table_key in results:
            status = "通过" if results[table_key].get('status') == 'passed' else "未通过"
            lines.append(f"{table_name}: {status}")
    
    lines.extend([
        "",
        "二、详细校验结果",
        "-" * 40
    ])
    
    for table_key, table_name in table_names.items():
        if table_key in results:
            lines.extend([
                "",
                f"【{table_name}】",
                f"  状态: {results[table_key].get('status', 'unknown')}",
                f"  记录数: {results[table_key].get('total_rows', 0)}",
                f"  字段数: {results[table_key].get('total_columns', 0)}",
                "  检查项:"
            ])
            
            for validation in results[table_key].get('validations', []):
                check_name = validation.get('check', 'unknown')
                passed = "通过" if validation.get('passed', True) else "未通过"
                lines.append(f"    - {check_name}: {passed}")
    
    if 'consistency' in results and results['consistency']:
        lines.extend([
            "",
            "三、一致性问题",
            "-" * 40
        ])
        
        for issue in results['consistency']:
            lines.append(f"  - {issue['type']}: {issue['message']}")
    
    lines.extend([
        "",
        "=" * 60,
        "报告结束",
        "=" * 60
    ])
    
    return "\n".join(lines)

if __name__ == "__main__":
    main()
