import pdfplumber
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
from config.settings import FIELD_MAPPINGS, REPORT_TYPE_MAPPING

@dataclass
class FinancialReport:
    file_path: str
    stock_code: str = ""
    stock_abbr: str = ""
    report_type: str = ""
    report_year: int = 0
    report_period: str = ""
    balance_sheet: Dict = field(default_factory=dict)
    income_statement: Dict = field(default_factory=dict)
    cash_flow_statement: Dict = field(default_factory=dict)
    key_metrics: Dict = field(default_factory=dict)
    raw_tables: List = field(default_factory=list)

class EnhancedPDFParser:
    def __init__(self):
        self.field_mappings = FIELD_MAPPINGS
        self._build_reverse_mappings()
    
    def _build_reverse_mappings(self):
        self.reverse_mappings = {}
        for table_type, mappings in self.field_mappings.items():
            self.reverse_mappings[table_type] = {v: k for k, v in mappings.items()}
    
    def parse_report(self, file_path: str) -> FinancialReport:
        report = FinancialReport(file_path=file_path)
        
        with pdfplumber.open(file_path) as pdf:
            all_text = ""
            all_tables = []
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
                
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
            
            report.raw_tables = all_tables
            
            self._extract_metadata(report, all_text, pdf)
            
            self._extract_all_tables(report, all_text, all_tables)
            
            self._extract_key_metrics_from_text(report, all_text)
        
        return report
    
    def _extract_metadata(self, report: FinancialReport, text: str, pdf):
        file_name = os.path.basename(report.file_path)
        
        if "_" in file_name and file_name.endswith(".pdf"):
            parts = file_name.replace(".pdf", "").split("_")
            if len(parts) >= 3:
                report.stock_code = parts[0]
                date_str = parts[1]
                if len(date_str) == 8:
                    report.report_year = int(date_str[:4])
        else:
            code_match = re.search(r'(\d{6})', file_name)
            if code_match:
                report.stock_code = code_match.group(1)
            
            if "华润三九" in file_name:
                report.stock_code = "000999"
                report.stock_abbr = "华润三九"
        
        if not report.stock_abbr:
            name_patterns = [
                r'华润三九',
                r'金花股份',
                r'金花企业',
            ]
            for pattern in name_patterns:
                if pattern in text[:3000]:
                    report.stock_abbr = pattern
                    break
        
        if not report.stock_abbr:
            name_match = re.search(r'^[^\n]+?(?:股份有限公司|有限公司|集团)', text, re.MULTILINE)
            if name_match:
                report.stock_abbr = name_match.group(0).strip()[:20]
        
        for cn_type, en_type in REPORT_TYPE_MAPPING.items():
            if cn_type in file_name:
                report.report_type = en_type
                break
        
        if not report.report_type:
            for cn_type, en_type in REPORT_TYPE_MAPPING.items():
                if cn_type in text[:3000]:
                    report.report_type = en_type
                    break
        
        year_match = re.search(r'20\d{2}年', text[:3000])
        if year_match:
            report.report_year = int(year_match.group(0).replace("年", ""))
        
        if report.report_type:
            report.report_period = report.report_type
    
    def _extract_all_tables(self, report: FinancialReport, text: str, tables: List):
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            table_type = self._identify_table_type(table, text)
            
            if table_type == "balance_sheet":
                self._process_balance_sheet_table(report, table)
            elif table_type == "income_statement":
                self._process_income_statement_table(report, table)
            elif table_type == "cash_flow_statement":
                self._process_cash_flow_table(report, table)
            elif table_type == "key_metrics":
                self._process_key_metrics_table(report, table)
    
    def _identify_table_type(self, table: List, text: str) -> str:
        table_str = str(table)
        
        balance_keywords = ["资产负债表", "资产总计", "负债合计", "所有者权益合计", "货币资金", "应收账款", "存货"]
        income_keywords = ["利润表", "营业总收入", "营业总成本", "营业利润", "利润总额", "净利润"]
        cash_flow_keywords = ["现金流量表", "经营活动产生的现金流量", "投资活动产生的现金流量", "筹资活动产生的现金流量"]
        metrics_keywords = ["主要会计数据", "财务指标", "每股收益", "净资产收益率"]
        
        balance_score = sum(1 for kw in balance_keywords if kw in table_str)
        income_score = sum(1 for kw in income_keywords if kw in table_str)
        cash_flow_score = sum(1 for kw in cash_flow_keywords if kw in table_str)
        metrics_score = sum(1 for kw in metrics_keywords if kw in table_str)
        
        max_score = max(balance_score, income_score, cash_flow_score, metrics_score)
        
        if max_score == 0:
            return "unknown"
        
        if balance_score == max_score:
            return "balance_sheet"
        elif income_score == max_score:
            return "income_statement"
        elif cash_flow_score == max_score:
            return "cash_flow_statement"
        elif metrics_score == max_score:
            return "key_metrics"
        
        return "unknown"
    
    def _process_balance_sheet_table(self, report: FinancialReport, table: List):
        for row in table:
            if not row or len(row) < 2:
                continue
            
            item_name = self._clean_cell(row[0]) if row[0] else ""
            if not item_name or len(item_name) < 2:
                continue
            
            for cn_name, en_name in self.field_mappings["balance_sheet"].items():
                if cn_name in item_name:
                    value = self._extract_value_from_row(row)
                    if value is not None:
                        report.balance_sheet[en_name] = value
                    break
    
    def _process_income_statement_table(self, report: FinancialReport, table: List):
        for row in table:
            if not row or len(row) < 2:
                continue
            
            item_name = self._clean_cell(row[0]) if row[0] else ""
            if not item_name or len(item_name) < 2:
                continue
            
            for cn_name, en_name in self.field_mappings["income_statement"].items():
                if cn_name in item_name and en_name not in report.income_statement:
                    value = self._extract_value_from_row(row)
                    if value is not None:
                        report.income_statement[en_name] = value
                    break
    
    def _process_cash_flow_table(self, report: FinancialReport, table: List):
        for row in table:
            if not row or len(row) < 2:
                continue
            
            item_name = self._clean_cell(row[0]) if row[0] else ""
            if not item_name or len(item_name) < 2:
                continue
            
            for cn_name, en_name in self.field_mappings["cash_flow_statement"].items():
                if cn_name in item_name and en_name not in report.cash_flow_statement:
                    value = self._extract_value_from_row(row)
                    if value is not None:
                        report.cash_flow_statement[en_name] = value
                    break
    
    def _process_key_metrics_table(self, report: FinancialReport, table: List):
        for row in table:
            if not row or len(row) < 2:
                continue
            
            item_name = self._clean_cell(row[0]) if row[0] else ""
            if not item_name or len(item_name) < 2:
                continue
            
            for cn_name, en_name in self.field_mappings["key_metrics"].items():
                if cn_name in item_name and en_name not in report.key_metrics:
                    value = self._extract_value_from_row(row)
                    if value is not None:
                        report.key_metrics[en_name] = value
                    break
    
    def _extract_key_metrics_from_text(self, report: FinancialReport, text: str):
        patterns = {
            "basic_eps": [
                r'基本每股收益[^\d\-\.]*([\d\.\-]+)',
                r'基本每股收益[（(]元/股[)）][^\d\-\.]*([\d\.\-]+)',
            ],
            "diluted_eps": [
                r'稀释每股收益[^\d\-\.]*([\d\.\-]+)',
                r'稀释每股收益[（(]元/股[)）][^\d\-\.]*([\d\.\-]+)',
            ],
            "net_profit_attributable_to_parent": [
                r'归属于上市公司股东的净利润[^\d\-\.]*([\d,\.]+)',
            ],
            "operating_cash_flow": [
                r'经营活动产生的现金流量净额[^\d\-\.]*([\d,\.]+)',
            ],
        }
        
        for en_name, pattern_list in patterns.items():
            if en_name in report.key_metrics:
                continue
            
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    value = self._parse_number(match.group(1))
                    if value is not None:
                        report.key_metrics[en_name] = value
                        break
    
    def _clean_cell(self, cell) -> str:
        if cell is None:
            return ""
        return str(cell).strip().replace("\n", "").replace(" ", "")
    
    def _extract_value_from_row(self, row: List) -> Optional[float]:
        for i, cell in enumerate(row[1:], 1):
            if cell is not None:
                value = self._parse_number(str(cell))
                if value is not None:
                    return value
        return None
    
    def _parse_number(self, value_str: str) -> Optional[float]:
        if not value_str:
            return None
        
        cleaned = value_str.strip().replace(",", "").replace(" ", "").replace("\n", "")
        
        if cleaned in ["-", "—", "N/A", "不适用", "", "无"]:
            return None
        
        try:
            if "(" in cleaned or "（" in cleaned:
                cleaned = cleaned.replace("(", "-").replace("（", "-").replace(")", "").replace("）", "")
            
            return float(cleaned)
        except ValueError:
            return None

class ReportBatchParser:
    def __init__(self):
        self.parser = EnhancedPDFParser()
    
    def parse_directory(self, directory: str) -> List[FinancialReport]:
        reports = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    try:
                        report = self.parser.parse_report(file_path)
                        reports.append(report)
                        print(f"Parsed: {file}")
                    except Exception as e:
                        print(f"Error parsing {file}: {e}")
        
        return reports
    
    def parse_reports_to_dataframe(self, reports: List[FinancialReport]) -> Dict[str, pd.DataFrame]:
        balance_sheet_data = []
        income_statement_data = []
        cash_flow_data = []
        key_metrics_data = []
        
        for report in reports:
            bs_record = {
                "stock_code": report.stock_code,
                "stock_abbr": report.stock_abbr,
                "report_period": report.report_period,
                "report_year": report.report_year,
                **report.balance_sheet
            }
            balance_sheet_data.append(bs_record)
            
            is_record = {
                "stock_code": report.stock_code,
                "stock_abbr": report.stock_abbr,
                "report_period": report.report_period,
                "report_year": report.report_year,
                **report.income_statement
            }
            income_statement_data.append(is_record)
            
            cf_record = {
                "stock_code": report.stock_code,
                "stock_abbr": report.stock_abbr,
                "report_period": report.report_period,
                "report_year": report.report_year,
                **report.cash_flow_statement
            }
            cash_flow_data.append(cf_record)
            
            km_record = {
                "stock_code": report.stock_code,
                "stock_abbr": report.stock_abbr,
                "report_period": report.report_period,
                "report_year": report.report_year,
                **report.key_metrics
            }
            key_metrics_data.append(km_record)
        
        return {
            "balance_sheet": pd.DataFrame(balance_sheet_data),
            "income_statement": pd.DataFrame(income_statement_data),
            "cash_flow_statement": pd.DataFrame(cash_flow_data),
            "key_metrics": pd.DataFrame(key_metrics_data)
        }

if __name__ == "__main__":
    parser = EnhancedPDFParser()
    test_file = r"c:\Users\共产主义接班人\OneDrive\Desktop\泰迪杯\B题-示例数据\示例数据\附件2：财务报告\reports-深交所\华润三九：2023年一季度报告.pdf"
    report = parser.parse_report(test_file)
    
    print(f"Stock Code: {report.stock_code}")
    print(f"Stock Name: {report.stock_abbr}")
    print(f"Report Type: {report.report_type}")
    print(f"Report Year: {report.report_year}")
    print(f"\nBalance Sheet Items: {len(report.balance_sheet)}")
    print(f"Income Statement Items: {len(report.income_statement)}")
    print(f"Cash Flow Items: {len(report.cash_flow_statement)}")
    print(f"Key Metrics: {report.key_metrics}")
