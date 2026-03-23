import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import DATA_DIR
from parsers.pdf_parser import EnhancedPDFParser, ReportBatchParser
from utils.data_validator import DataCleaner, DataValidator, DataConsistencyChecker

def test_single_report():
    print("=" * 60)
    print("测试单个PDF报告解析")
    print("=" * 60)
    
    test_file = os.path.join(
        str(DATA_DIR), 
        "附件2：财务报告", 
        "reports-深交所", 
        "华润三九：2023年一季度报告.pdf"
    )
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return
    
    parser = EnhancedPDFParser()
    report = parser.parse_report(test_file)
    
    print(f"\n报告基本信息:")
    print(f"  股票代码: {report.stock_code}")
    print(f"  股票简称: {report.stock_abbr}")
    print(f"  报告类型: {report.report_type}")
    print(f"  报告年份: {report.report_year}")
    print(f"  报告期: {report.report_period}")
    
    print(f"\n资产负债表提取字段数: {len(report.balance_sheet)}")
    if report.balance_sheet:
        print("  提取的字段:")
        for key, value in list(report.balance_sheet.items())[:5]:
            print(f"    {key}: {value}")
        if len(report.balance_sheet) > 5:
            print(f"    ... 共 {len(report.balance_sheet)} 个字段")
    
    print(f"\n利润表提取字段数: {len(report.income_statement)}")
    if report.income_statement:
        print("  提取的字段:")
        for key, value in list(report.income_statement.items())[:5]:
            print(f"    {key}: {value}")
    
    print(f"\n现金流量表提取字段数: {len(report.cash_flow_statement)}")
    if report.cash_flow_statement:
        print("  提取的字段:")
        for key, value in list(report.cash_flow_statement.items())[:5]:
            print(f"    {key}: {value}")
    
    print(f"\n核心指标提取字段数: {len(report.key_metrics)}")
    if report.key_metrics:
        print("  提取的字段:")
        for key, value in report.key_metrics.items():
            print(f"    {key}: {value}")
    
    return report

def test_batch_parse():
    print("\n" + "=" * 60)
    print("测试批量PDF报告解析")
    print("=" * 60)
    
    reports_dir = os.path.join(str(DATA_DIR), "附件2：财务报告")
    
    if not os.path.exists(reports_dir):
        print(f"报告目录不存在: {reports_dir}")
        return None
    
    batch_parser = ReportBatchParser()
    reports = batch_parser.parse_directory(reports_dir)
    
    print(f"\n成功解析报告数: {len(reports)}")
    
    if reports:
        print("\n报告列表:")
        for i, report in enumerate(reports[:10]):
            print(f"  {i+1}. {report.stock_code} - {report.stock_abbr} - {report.report_year}年{report.report_type}")
        if len(reports) > 10:
            print(f"  ... 共 {len(reports)} 份报告")
    
    dataframes = batch_parser.parse_reports_to_dataframe(reports)
    
    print("\n转换后的DataFrame:")
    for table_name, df in dataframes.items():
        print(f"  {table_name}: {len(df)} 行, {len(df.columns)} 列")
    
    return reports, dataframes

def test_data_cleaning():
    print("\n" + "=" * 60)
    print("测试数据清洗")
    print("=" * 60)
    
    test_df = pd.DataFrame({
        "stock_code": ["000999", "000999", "600080"],
        "stock_abbr": ["华润三九", "华润三九", "金花股份"],
        "report_year": [2023, 2023, 2023],
        "report_period": ["Q1", "Q1", "Q1"],
        "total_assets": ["1,000,000.00", "1,000,000.00", "500,000.00"],
        "total_liabilities": ["300,000.00", "300,000.00", "150,000.00"],
        "net_profit": ["(50,000.00)", "-50,000.00", "10,000.00"],
        "ratio": ["—", "N/A", "0.5"]
    })
    
    print("\n原始数据:")
    print(test_df)
    
    cleaner = DataCleaner()
    cleaned_df = cleaner.clean_dataframe(test_df, "balance_sheet")
    
    print("\n清洗后数据:")
    print(cleaned_df)
    print(f"\n数据类型:")
    print(cleaned_df.dtypes)
    
    return cleaned_df

def test_data_validation():
    print("\n" + "=" * 60)
    print("测试数据验证")
    print("=" * 60)
    
    test_df = pd.DataFrame({
        "stock_code": ["000999", "000999", "600080"],
        "stock_abbr": ["华润三九", "华润三九", "金花股份"],
        "report_year": [2023, 2023, 2023],
        "report_period": ["Q1", "Q1", "Q1"],
        "total_assets": [1000000.0, 1000000.0, 500000.0],
        "total_liabilities": [300000.0, 300000.0, 150000.0],
        "total_equity": [700000.0, 700000.0, 350000.0]
    })
    
    validator = DataValidator()
    results = validator.validate_dataframe(test_df, "balance_sheet")
    
    print(f"\n验证状态: {results['status']}")
    print(f"总行数: {results['total_rows']}")
    print(f"总列数: {results['total_columns']}")
    
    print("\n各项验证结果:")
    for validation in results['validations']:
        status = "✓ 通过" if validation.get('passed', True) else "✗ 失败"
        print(f"  {status} - {validation['check']}")
        if not validation.get('passed', True):
            print(f"    详情: {validation}")
    
    summary = validator.get_validation_summary()
    print(f"\n验证汇总:")
    print(f"  总表数: {summary['total_tables']}")
    print(f"  通过: {summary['passed']}")
    print(f"  失败: {summary['failed']}")
    
    return results

def test_full_pipeline():
    print("\n" + "=" * 60)
    print("测试完整流水线（不使用数据库）")
    print("=" * 60)
    
    reports_dir = os.path.join(str(DATA_DIR), "附件2：财务报告")
    output_dir = os.path.join(str(DATA_DIR), "processed_data")
    
    batch_parser = ReportBatchParser()
    cleaner = DataCleaner()
    validator = DataValidator()
    consistency_checker = DataConsistencyChecker()
    
    print("\n[步骤1] 解析PDF报告...")
    reports = batch_parser.parse_directory(reports_dir)
    print(f"成功解析 {len(reports)} 份报告")
    
    if not reports:
        print("未找到报告，退出")
        return
    
    print("\n[步骤2] 转换为DataFrame...")
    dataframes = batch_parser.parse_reports_to_dataframe(reports)
    for table_name, df in dataframes.items():
        print(f"  {table_name}: {len(df)} 条记录")
    
    print("\n[步骤3] 清洗数据...")
    cleaned_dataframes = {}
    for table_name, df in dataframes.items():
        cleaned_df = cleaner.clean_dataframe(df, table_name)
        cleaned_dataframes[table_name] = cleaned_df
        print(f"  {table_name}: 清洗完成")
    
    print("\n[步骤4] 验证数据...")
    for table_name, df in cleaned_dataframes.items():
        results = validator.validate_dataframe(df, table_name)
        status = "✓" if results["status"] == "passed" else "✗"
        print(f"  {status} {table_name}: {results['status']}")
    
    print("\n[步骤5] 一致性检查...")
    inconsistencies = consistency_checker.check_cross_table_consistency(cleaned_dataframes)
    if inconsistencies:
        for issue in inconsistencies:
            print(f"  - {issue['type']}: {issue['message']}")
    else:
        print("  未发现一致性问题")
    
    print("\n[步骤6] 导出数据...")
    os.makedirs(output_dir, exist_ok=True)
    
    csv_dir = os.path.join(output_dir, "csv")
    os.makedirs(csv_dir, exist_ok=True)
    
    for table_name, df in cleaned_dataframes.items():
        csv_file = os.path.join(csv_dir, f"{table_name}.csv")
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"  导出 {table_name} 到 CSV")
    
    excel_file = os.path.join(output_dir, "financial_reports.xlsx")
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        sheet_names = {
            'balance_sheet': '资产负债表',
            'income_statement': '利润表',
            'cash_flow_statement': '现金流量表',
            'key_metrics': '核心业绩指标'
        }
        for table_name, df in cleaned_dataframes.items():
            sheet_name = sheet_names.get(table_name, table_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"  导出所有表到 Excel: {excel_file}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return cleaned_dataframes

if __name__ == "__main__":
    test_single_report()
    test_data_cleaning()
    test_data_validation()
    test_full_pipeline()
