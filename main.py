import os
import sys
import argparse
from datetime import datetime
import pandas as pd

from config.settings import (
    SSE_REPORTS_DIR, SZSE_REPORTS_DIR, DATA_DIR,
    DATABASE_CONFIG
)
from parsers.pdf_parser import EnhancedPDFParser, ReportBatchParser
from utils.data_validator import DataCleaner, DataValidator, DataConsistencyChecker
from database.db_manager import DatabaseManager, DataLoader, DataExporter

class FinancialReportPipeline:
    def __init__(self, use_database: bool = True):
        self.parser = EnhancedPDFParser()
        self.batch_parser = ReportBatchParser()
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.consistency_checker = DataConsistencyChecker()
        
        self.use_database = use_database
        self.db_manager = None
        self.data_loader = None
        self.data_exporter = None
        
        if use_database:
            self._init_database()
    
    def _init_database(self):
        self.db_manager = DatabaseManager()
        self.db_manager.create_database()
        
        if self.db_manager.connect():
            self.db_manager.create_tables()
            self.data_loader = DataLoader(self.db_manager)
            self.data_exporter = DataExporter(self.db_manager)
    
    def run(self, reports_dir: str = None, output_dir: str = None):
        print("=" * 60)
        print("Financial Report Processing Pipeline")
        print("=" * 60)
        
        if reports_dir is None:
            reports_dir = str(DATA_DIR / "附件2：财务报告")
        
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(reports_dir), "processed_data")
        
        print(f"\n[Step 1] Parsing PDF reports from: {reports_dir}")
        reports = self.batch_parser.parse_directory(reports_dir)
        print(f"Parsed {len(reports)} reports")
        
        if not reports:
            print("No reports found. Exiting.")
            return
        
        print("\n[Step 2] Converting to DataFrames")
        dataframes = self.batch_parser.parse_reports_to_dataframe(reports)
        
        for table_name, df in dataframes.items():
            print(f"  {table_name}: {len(df)} records")
        
        print("\n[Step 3] Cleaning data")
        cleaned_dataframes = {}
        for table_name, df in dataframes.items():
            cleaned_df = self.cleaner.clean_dataframe(df, table_name)
            cleaned_dataframes[table_name] = cleaned_df
            print(f"  Cleaned {table_name}: {len(cleaned_df)} records")
        
        print("\n[Step 4] Validating data")
        for table_name, df in cleaned_dataframes.items():
            results = self.validator.validate_dataframe(df, table_name)
            status = "✓" if results["status"] == "passed" else "✗"
            print(f"  {status} {table_name}: {results['status']}")
            if results["status"] == "failed":
                for validation in results["validations"]:
                    if not validation.get("passed", True):
                        print(f"    - {validation}")
        
        print("\n[Step 5] Checking cross-table consistency")
        inconsistencies = self.consistency_checker.check_cross_table_consistency(cleaned_dataframes)
        if inconsistencies:
            print(f"  Found {len(inconsistencies)} consistency issues:")
            for issue in inconsistencies:
                print(f"    - {issue['type']}: {issue['message']}")
        else:
            print("  No consistency issues found")
        
        if self.use_database and self.db_manager:
            print("\n[Step 6] Loading data to database")
            load_results = self.data_loader.load_all_tables(cleaned_dataframes)
            for table_name, count in load_results.items():
                print(f"  {table_name}: {count} records loaded")
        
        print("\n[Step 7] Exporting data")
        os.makedirs(output_dir, exist_ok=True)
        
        csv_dir = os.path.join(output_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
        for table_name, df in cleaned_dataframes.items():
            csv_file = os.path.join(csv_dir, f"{table_name}.csv")
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  Exported {table_name} to CSV")
        
        excel_file = os.path.join(output_dir, "financial_reports.xlsx")
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            for table_name, df in cleaned_dataframes.items():
                sheet_name = {
                    'balance_sheet': '资产负债表',
                    'income_statement': '利润表',
                    'cash_flow_statement': '现金流量表',
                    'key_metrics': '核心业绩指标'
                }.get(table_name, table_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"  Exported all tables to Excel: {excel_file}")
        
        print("\n[Step 8] Generating validation report")
        validation_report = self._generate_validation_report(cleaned_dataframes)
        report_file = os.path.join(output_dir, "validation_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(validation_report)
        print(f"  Validation report saved to: {report_file}")
        
        print("\n" + "=" * 60)
        print("Pipeline completed successfully!")
        print("=" * 60)
        
        return cleaned_dataframes
    
    def _generate_validation_report(self, dataframes: dict) -> str:
        report_lines = [
            "财务报告数据验证报告",
            "=" * 50,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "一、数据概览",
            "-" * 30
        ]
        
        for table_name, df in dataframes.items():
            report_lines.extend([
                f"\n{table_name}:",
                f"  记录数: {len(df)}",
                f"  字段数: {len(df.columns)}",
                f"  字段列表: {', '.join(df.columns.tolist())}"
            ])
        
        report_lines.extend([
            "",
            "二、验证结果",
            "-" * 30
        ])
        
        summary = self.validator.get_validation_summary()
        report_lines.extend([
            f"\n总表数: {summary['total_tables']}",
            f"通过: {summary['passed']}",
            f"失败: {summary['failed']}"
        ])
        
        for table_name, results in summary['details'].items():
            report_lines.append(f"\n{table_name}:")
            for validation in results.get('validations', []):
                status = "通过" if validation.get('passed', True) else "失败"
                report_lines.append(f"  - {validation['check']}: {status}")
        
        report_lines.extend([
            "",
            "三、一致性检查",
            "-" * 30
        ])
        
        inconsistencies = self.consistency_checker.inconsistencies
        if inconsistencies:
            for issue in inconsistencies:
                report_lines.append(f"  - {issue['type']}: {issue['message']} (严重程度: {issue['severity']})")
        else:
            report_lines.append("  未发现一致性问题")
        
        return "\n".join(report_lines)
    
    def close(self):
        if self.db_manager:
            self.db_manager.disconnect()

def main():
    parser = argparse.ArgumentParser(description='财务报告数据处理流水线')
    parser.add_argument('--input', '-i', type=str, help='输入报告目录路径')
    parser.add_argument('--output', '-o', type=str, help='输出数据目录路径')
    parser.add_argument('--no-db', action='store_true', help='不使用数据库存储')
    
    args = parser.parse_args()
    
    pipeline = FinancialReportPipeline(use_database=not args.no_db)
    
    try:
        pipeline.run(reports_dir=args.input, output_dir=args.output)
    finally:
        pipeline.close()

if __name__ == "__main__":
    main()
