"""
NL2SQL - 自然语言转 SQL 转换器

实现自然语言到 MySQL 查询语句的自动转换，支持：
- Schema 信息注入
- Few-shot 示例学习
- SQL 语法验证
- 澄清机制
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SQLResult:
    """SQL 查询结果"""
    sql: str
    is_valid: bool
    error_message: Optional[str] = None
    data: Optional[List[Dict]] = None
    columns: Optional[List[str]] = None


class NL2SQLConverter:
    """自然语言转 SQL 转换器"""

    # 数据库 Schema 定义（根据附件 3）
    SCHEMA = {
        'financial_reports': {
            'description': '核心业绩指标表',
            'columns': {
                'stock_code': '股票代码',
                'company_name': '公司简称',
                'exchange': '交易所',
                'report_date': '报告期',
                'report_type': '报告类型',
                'total_assets': '资产总计',
                'total_liabilities': '负债合计',
                'total_equity': '所有者权益合计',
                'operating_revenue': '营业总收入',
                'net_profit': '净利润',
                'total_profit': '利润总额',
                'operating_profit': '营业利润',
            }
        },
        'balance_sheet': {
            'description': '资产负债表',
            'columns': {
                'stock_code': '股票代码',
                'company_name': '公司简称',
                'report_date': '报告期',
                'item_name': '项目名称',
                'ending_balance': '期末余额',
                'beginning_balance': '期初余额',
            }
        },
        'income_statement': {
            'description': '利润表',
            'columns': {
                'stock_code': '股票代码',
                'company_name': '公司简称',
                'report_date': '报告期',
                'item_name': '项目名称',
                'current_amount': '本期金额',
                'previous_amount': '上期金额',
            }
        },
        'cash_flow_statement': {
            'description': '现金流量表',
            'columns': {
                'stock_code': '股票代码',
                'company_name': '公司简称',
                'report_date': '报告期',
                'item_name': '项目名称',
                'current_amount': '本期金额',
                'previous_amount': '上期金额',
            }
        }
    }

    # Few-shot 示例
    FEW_SHOT_EXAMPLES = [
        {
            'question': '贵州茅台 2024 年的净利润是多少？',
            'sql': "SELECT net_profit FROM financial_reports WHERE company_name = '贵州茅台' AND report_date = '2024'"
        },
        {
            'question': '查询所有公司的营业收入排名',
            'sql': "SELECT company_name, operating_revenue FROM financial_reports ORDER BY operating_revenue DESC"
        },
        {
            'question': '对比招商银行和浦发银行的总资产',
            'sql': "SELECT company_name, total_assets FROM financial_reports WHERE company_name IN ('招商银行', '浦发银行') ORDER BY total_assets DESC"
        },
        {
            'question': '贵州茅台近 5 年的净利润变化趋势',
            'sql': "SELECT report_date, net_profit FROM financial_reports WHERE company_name = '贵州茅台' ORDER BY report_date DESC LIMIT 5"
        },
        {
            'question': '2024 年净利润排名前十的公司',
            'sql': "SELECT company_name, net_profit FROM financial_reports WHERE report_date = '2024' ORDER BY net_profit DESC LIMIT 10"
        }
    ]

    def __init__(self, llm_client=None):
        """
        初始化转换器

        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        self.conversation_history = []

    def build_prompt(self, question: str, context: Optional[Dict] = None) -> str:
        """
        构建 SQL 生成提示词

        Args:
            question: 用户问题
            context: 上下文信息

        Returns:
            提示词字符串
        """
        # Schema 信息
        schema_info = self._format_schema()

        # Few-shot 示例
        examples = self._format_examples()

        # 澄清信息（如果有）
        clarification = ""
        if context and context.get('clarified_fields'):
            clarification = f"\n已确认信息：{context['clarified_fields']}\n"

        prompt = f"""你是一个 SQL 生成助手，请根据以下数据库 Schema 将用户问题转换为 MySQL 查询语句。

## 数据库 Schema

{schema_info}

## 示例

{examples}
{clarification}
## 当前问题

用户问题：{question}

请生成 SQL 查询语句（只返回 SQL，不要解释）：
"""
        return prompt

    def _format_schema(self) -> str:
        """格式化 Schema 信息"""
        lines = []
        for table_name, table_info in self.SCHEMA.items():
            lines.append(f"\n表名：{table_name}")
            lines.append(f"说明：{table_info['description']}")
            lines.append("字段:")
            for col_name, col_desc in table_info['columns'].items():
                lines.append(f"  - {col_name}: {col_desc}")
        return "\n".join(lines)

    def _format_examples(self) -> str:
        """格式化 Few-shot 示例"""
        lines = []
        for i, example in enumerate(self.FEW_SHOT_EXAMPLES, 1):
            lines.append(f"{i}. 问题：{example['question']}")
            lines.append(f"   SQL: {example['sql']}")
        return "\n".join(lines)

    def convert(self, question: str, context: Optional[Dict] = None) -> SQLResult:
        """
        将自然语言转换为 SQL

        Args:
            question: 用户问题
            context: 上下文信息

        Returns:
            SQL 查询结果
        """
        # 构建提示词
        prompt = self.build_prompt(question, context)

        # 调用 LLM 生成 SQL
        if self.llm_client:
            sql = self.llm_client.generate(prompt)
        else:
            # 简单规则匹配（fallback）
            sql = self._rule_based_convert(question)

        # 验证 SQL
        is_valid, error_message = self.validate_sql(sql)

        return SQLResult(
            sql=sql,
            is_valid=is_valid,
            error_message=error_message
        )

    def _rule_based_convert(self, question: str) -> str:
        """基于规则的 SQL 转换（fallback）"""

        # 检测关键词
        if '排名' in question or 'top' in question.lower():
            return self._generate_ranking_sql(question)
        elif '对比' in question or '比较' in question:
            return self._generate_comparison_sql(question)
        elif '趋势' in question or '变化' in question:
            return self._generate_trend_sql(question)
        else:
            return self._generate_simple_query_sql(question)

    def _generate_ranking_sql(self, question: str) -> str:
        """生成排名查询 SQL"""
        metric = self._extract_metric_from_question(question)

        if '前十' in question or 'top10' in question.lower():
            limit = 10
        elif '前五' in question:
            limit = 5
        else:
            limit = 10

        return f"SELECT company_name, {metric} FROM financial_reports ORDER BY {metric} DESC LIMIT {limit}"

    def _generate_comparison_sql(self, question: str) -> str:
        """生成对比查询 SQL"""
        metric = self._extract_metric_from_question(question)

        # 提取公司名（简化实现）
        companies = re.findall(r'([\u4e00-\u9fa5]{2,}(?:公司 | 股份 | 银行))', question)
        if companies:
            company_list = "', '".join(companies)
            return f"SELECT company_name, {metric} FROM financial_reports WHERE company_name IN ('{company_list}') ORDER BY {metric} DESC"

        return f"SELECT company_name, {metric} FROM financial_reports ORDER BY {metric} DESC"

    def _generate_trend_sql(self, question: str) -> str:
        """生成趋势查询 SQL"""
        metric = self._extract_metric_from_question(question)

        # 提取公司名
        companies = re.findall(r'([\u4e00-\u9fa5]{2,}(?:公司 | 股份 | 银行))', question)
        company = companies[0] if companies else '未知公司'

        # 提取年份
        years = re.findall(r'(\d{4})', question)
        if years:
            years_str = "', '".join(years)
            year_condition = f"report_date IN ('{years_str}')"
        else:
            year_condition = "report_date >= YEAR(CURDATE()) - 5"

        return f"SELECT report_date, {metric} FROM financial_reports WHERE company_name = '{company}' AND {year_condition} ORDER BY report_date"

    def _generate_simple_query_sql(self, question: str) -> str:
        """生成简单查询 SQL"""
        metric = self._extract_metric_from_question(question)

        # 提取公司名
        companies = re.findall(r'([\u4e00-\u9fa5]{2,}(?:公司 | 股份 | 银行))', question)
        if companies:
            company = companies[0]
            return f"SELECT {metric} FROM financial_reports WHERE company_name = '{company}'"

        return f"SELECT {metric} FROM financial_reports LIMIT 10"

    def _extract_metric_from_question(self, question: str) -> str:
        """从问题中提取指标名"""
        metric_map = {
            '净利润': 'net_profit',
            '利润': 'net_profit',
            '营业收入': 'operating_revenue',
            '收入': 'operating_revenue',
            '营收': 'operating_revenue',
            '总资产': 'total_assets',
            '资产': 'total_assets',
            '负债': 'total_liabilities',
            '所有者权益': 'total_equity',
            '权益': 'total_equity',
            '营业利润': 'operating_profit',
            '利润总额': 'total_profit',
        }

        for kw, col_name in metric_map.items():
            if kw in question:
                return col_name

        return 'net_profit'  # 默认

    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        验证 SQL 语法

        Args:
            sql: SQL 语句

        Returns:
            (是否有效，错误信息)
        """
        # 基本检查
        if not sql or not sql.strip():
            return False, "SQL 为空"

        sql = sql.strip()

        # 检查是否以 SELECT 开头
        if not sql.upper().startswith('SELECT'):
            return False, "SQL 必须以 SELECT 开头"

        # 检查危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
        for kw in dangerous_keywords:
            if kw in sql.upper():
                return False, f"不允许执行{kw}操作"

        # 检查表名是否在白名单中
        table_names = self.SCHEMA.keys()
        for table in table_names:
            if table in sql:
                break
        else:
            # 可能是子查询或别名，放宽检查
            pass

        return True, None

    def add_to_history(self, question: str, sql: str, result: Dict) -> None:
        """添加到对话历史"""
        self.conversation_history.append({
            'question': question,
            'sql': sql,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })

        # 限制历史记录长度
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    def get_context(self) -> Dict:
        """获取当前上下文"""
        if not self.conversation_history:
            return {}

        # 返回最近一次查询的上下文
        last = self.conversation_history[-1]
        return {
            'last_question': last['question'],
            'last_sql': last['sql'],
            'last_company': self._extract_company(last['question']),
            'last_year': self._extract_year(last['question']),
        }

    def _extract_company(self, question: str) -> Optional[str]:
        """提取公司名"""
        companies = re.findall(r'([\u4e00-\u9fa5]{2,}(?:公司 | 股份 | 银行))', question)
        return companies[0] if companies else None

    def _extract_year(self, question: str) -> Optional[str]:
        """提取年份"""
        matches = re.findall(r'(\d{4}) 年', question)
        if matches:
            return matches[0]

        matches = re.findall(r'(\d{4})', question)
        if matches:
            return matches[0]

        return None


class ClarificationManager:
    """澄清管理器 - 处理关键信息缺失时的主动澄清"""

    def __init__(self):
        self.pending_fields = {}
        self.clarified_values = {}

    def check_and_request_clarification(
        self,
        question: str,
        required_fields: List[str] = ['company', 'year']
    ) -> Tuple[bool, Optional[str]]:
        """
        检查是否需要澄清并生成澄清请求

        Args:
            question: 用户问题
            required_fields: 必需字段列表

        Returns:
            (是否需要澄清，澄清请求消息)
        """
        missing = []

        for field in required_fields:
            if field not in self.clarified_values:
                if not self._extract_from_question(question, field):
                    missing.append(field)

        if missing:
            return True, self._generate_clarification_message(missing)

        return False, None

    def _extract_from_question(self, question: str, field: str) -> Optional[str]:
        """从问题中提取字段值"""
        if field == 'company':
            companies = re.findall(r'([\u4e00-\u9fa5]{2,}(?:公司 | 股份 | 银行))', question)
            return companies[0] if companies else None

        elif field == 'year':
            matches = re.findall(r'(\d{4}) 年', question)
            if matches:
                return matches[0]
            matches = re.findall(r'(\d{4})', question)
            return matches[0] if matches else None

        elif field == 'metric':
            metrics = ['净利润', '营业收入', '总资产', '负债']
            for m in metrics:
                if m in question:
                    return m
            return None

        return None

    def _generate_clarification_message(self, missing: List[str]) -> str:
        """生成澄清消息"""
        messages = {
            'company': '请问您想查询哪家公司？请提供公司全称或股票代码。',
            'year': '请问您想查询哪一年的数据？',
            'metric': '请问您想查询什么指标？',
        }

        return ' '.join(messages.get(m, f'请提供{m}信息') for m in missing)

    def save_clarified_value(self, field: str, value: str) -> None:
        """保存澄清后的值"""
        self.clarified_values[field] = value

    def clear(self) -> None:
        """清除所有澄清值"""
        self.clarified_values = {}
