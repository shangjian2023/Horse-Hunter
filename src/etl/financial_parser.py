"""
FinancialParser - 多交易所财报 PDF 解析器

支持上交所和深交所不同命名规则的财报 PDF 解析：
- 上交所规则：股票代码_报告日期_随机标识.pdf
- 深交所规则：A 股简称：年份 + 报告周期 + 报告类型.pdf
"""

import os
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 第三方库
import pdfplumber


class FinancialParser:
    """财报 PDF 解析器 - 支持多交易所规则"""

    # 上交所命名规则：股票代码_报告日期_随机标识.pdf
    SH_PATTERN = re.compile(r'^(\d{6})_(\d{8})_([A-Z0-9]+)\.pdf$')

    # 深交所命名规则：A 股简称：年份 + 报告周期 + 报告类型.pdf
    SZ_PATTERN = re.compile(r'^(.+?)：(\d{4}) 年 (.*?)(?:\.pdf)$')

    # 报告类型映射
    REPORT_TYPE_MAP = {
        '年度报告': 'annual',
        '半年度报告': 'semi-annual',
        '第一季度报告': 'Q1',
        '第三季度报告': 'Q3',
        '摘要': 'summary'
    }

    def __init__(self, output_dir: str = './data/processed'):
        """
        初始化解析器

        Args:
            output_dir: 处理后数据输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 解析结果存储
        self.parsed_data = {
            'financial_reports': [],      # 核心业绩指标
            'balance_sheet': [],          # 资产负债表
            'income_statement': [],       # 利润表
            'cash_flow_statement': [],    # 现金流量表
        }

    def parse_filename(self, filename: str) -> Dict:
        """
        解析文件名，识别交易所和报告类型

        Args:
            filename: PDF 文件名

        Returns:
            包含交易所、股票代码、报告类型等信息的字典
        """
        result = {
            'original_filename': filename,
            'exchange': 'unknown',
            'stock_code': None,
            'report_date': None,
            'report_type': None,
            'company_name': None
        }

        # 尝试上交所规则
        sh_match = self.SH_PATTERN.match(filename)
        if sh_match:
            result['exchange'] = 'SSE'  # 上海证券交易所
            result['stock_code'] = sh_match.group(1)
            result['report_date'] = sh_match.group(2)
            result['report_type'] = 'unknown'
            return result

        # 尝试深交所规则
        sz_match = self.SZ_PATTERN.match(filename)
        if sz_match:
            result['exchange'] = 'SZSE'  # 深圳证券交易所
            result['company_name'] = sz_match.group(1)
            year = sz_match.group(2)
            report_desc = sz_match.group(3)

            # 解析报告类型
            for cn_name, en_code in self.REPORT_TYPE_MAP.items():
                if cn_name in report_desc:
                    result['report_type'] = en_code
                    break

            result['report_date'] = year
            return result

        return result

    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        解析单个 PDF 文件

        Args:
            pdf_path: PDF 文件路径

        Returns:
            解析结果字典
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {'error': f'文件不存在：{pdf_path}'}

        # 解析文件名
        file_info = self.parse_filename(pdf_path.name)

        result = {
            'file_info': file_info,
            'tables': [],
            'text': '',
            'metrics': {}
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 提取所有页面文本
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        result['text'] += text + '\n'

                    # 提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            result['tables'].append(table)

            # 从提取的数据中识别财务报表
            self._identify_financial_statements(result)

        except Exception as e:
            result['error'] = f'PDF 解析失败：{str(e)}'

        return result

    def _identify_financial_statements(self, result: Dict) -> None:
        """
        识别并分类财务报表（资产负债表、利润表、现金流量表）

        Args:
            result: 包含提取表格的结果字典
        """
        # 关键词匹配
        balance_keywords = ['资产', '负债', '所有者权益', '资产负债表']
        income_keywords = ['利润表', '营业收入', '营业成本', '净利润', '综合收益']
        cashflow_keywords = ['现金流量', '经营活动', '投资活动', '筹资活动']

        for i, table in enumerate(result['tables']):
            # 将表格转换为 DataFrame 便于分析
            df = pd.DataFrame(table)
            table_text = df.to_string()

            # 识别报表类型
            if any(kw in table_text for kw in balance_keywords):
                result.setdefault('balance_sheet', []).append({
                    'table_index': i,
                    'data': df,
                    'type': 'balance_sheet'
                })
            elif any(kw in table_text for kw in income_keywords):
                result.setdefault('income_statement', []).append({
                    'table_index': i,
                    'data': df,
                    'type': 'income_statement'
                })
            elif any(kw in table_text for kw in cashflow_keywords):
                result.setdefault('cash_flow_statement', []).append({
                    'table_index': i,
                    'data': df,
                    'type': 'cash_flow'
                })

    def parse_directory(self, directory: str, pattern: str = '*.pdf') -> List[Dict]:
        """
        批量解析目录中的所有 PDF 文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            所有解析结果的列表
        """
        directory = Path(directory)
        if not directory.exists():
            return [{'error': f'目录不存在：{directory}'}]

        results = []
        pdf_files = list(directory.glob(pattern))

        # 递归查找子目录
        for subdirectory in directory.glob('**/*.pdf'):
            if subdirectory not in pdf_files:
                pdf_files.append(subdirectory)

        for pdf_file in pdf_files:
            print(f'正在解析：{pdf_file.name}')
            result = self.parse_pdf(pdf_file)
            result['file_path'] = str(pdf_file)
            results.append(result)

        return results

    def extract_key_metrics(self, parsed_result: Dict) -> Dict:
        """
        从解析结果中提取核心业绩指标

        Args:
            parsed_result: PDF 解析结果

        Returns:
            核心业绩指标字典
        """
        metrics = {
            'stock_code': parsed_result.get('file_info', {}).get('stock_code'),
            'company_name': parsed_result.get('file_info', {}).get('company_name'),
            'exchange': parsed_result.get('file_info', {}).get('exchange'),
            'report_date': parsed_result.get('file_info', {}).get('report_date'),
            'report_type': parsed_result.get('file_info', {}).get('report_type'),
        }

        # 从文本中提取关键数值
        text = parsed_result.get('text', '')

        # 常见财务指标正则
        metric_patterns = {
            'total_assets': r'资产总计 [：:\s]*([\d,\.]+)',
            'total_liabilities': r'负债合计 [：:\s]*([\d,\.]+)',
            'total_equity': r'所有者权益 (?:合计|总计) [：:\s]*([\d,\.]+)',
            'operating_revenue': r'营业总收入 [：:\s]*([\d,\.]+)',
            'net_profit': r'净利润 [：:\s]*([\d,\.]+)',
            'total_profit': r'利润总额 [：:\s]*([\d,\.]+)',
            'operating_profit': r'营业利润 [：:\s]*([\d,\.]+)',
        }

        for metric_name, pattern in metric_patterns.items():
            match = re.search(pattern, text)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    metrics[metric_name] = float(value_str)
                except ValueError:
                    metrics[metric_name] = None

        return metrics

    def save_to_csv(self, parsed_results: List[Dict]) -> Dict[str, str]:
        """
        将解析结果保存为 CSV 文件

        Args:
            parsed_results: 解析结果列表

        Returns:
            保存的文件路径字典
        """
        saved_files = {}

        # 按报表类型分类
        all_balance = []
        all_income = []
        all_cashflow = []
        all_metrics = []

        for result in parsed_results:
            if 'error' in result:
                continue

            # 提取指标
            metrics = self.extract_key_metrics(result)
            all_metrics.append(metrics)

            # 收集报表
            for statement_type in ['balance_sheet', 'income_statement', 'cash_flow_statement']:
                for stmt in result.get(statement_type, []):
                    df = stmt.get('data')
                    if df is not None:
                        if statement_type == 'balance_sheet':
                            all_balance.append(df)
                        elif statement_type == 'income_statement':
                            all_income.append(df)
                        else:
                            all_cashflow.append(df)

        # 保存为 CSV
        if all_metrics:
            metrics_df = pd.DataFrame(all_metrics)
            metrics_path = self.output_dir / 'key_metrics.csv'
            metrics_df.to_csv(metrics_path, index=False, encoding='utf-8-sig')
            saved_files['key_metrics'] = str(metrics_path)

        return saved_files


class ReportBatchParser(FinancialParser):
    """批量解析器 - 继承自 FinancialParser"""

    def __init__(self, output_dir: str = './data/processed'):
        super().__init__(output_dir)
        self.results = []

    def parse_directory(self, directory: str) -> List[Dict]:
        """解析整个目录"""
        self.results = super().parse_directory(directory)
        return self.results

    def parse_reports_to_dataframe(self, reports: List[Dict]) -> Dict[str, pd.DataFrame]:
        """
        将解析结果转换为标准化的 DataFrame

        Args:
            reports: 解析结果列表

        Returns:
            包含各类型报表 DataFrame 的字典
        """
        dataframes = {}

        # 核心指标
        metrics_data = []
        for report in reports:
            if 'error' not in report:
                metrics = self.extract_key_metrics(report)
                metrics_data.append(metrics)

        if metrics_data:
            dataframes['key_metrics'] = pd.DataFrame(metrics_data)

        return dataframes
