"""
Text-to-SQL 模块
将自然语言查询转换为 SQL 语句并执行
"""

import re
import json
from typing import Optional, Dict, Any, List
from database.db_manager import DatabaseManager


class TextToSQL:
    """Text-to-SQL 转换器"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 api_config: Optional[Dict] = None):
        self.db_manager = db_manager or DatabaseManager()
        self.schema_info = self._get_schema_info()
        self.api_config = api_config
        self.api_base_url = None
        self.api_key = None
        self.model = None
        self._load_api_config()

    def _load_api_config(self):
        """加载 API 配置 - 优先使用传入的配置，否则从环境变量加载"""
        import os
        from dotenv import load_dotenv

        # 如果传入了 api_config，优先使用
        if self.api_config:
            self.api_base_url = self.api_config.get('base_url', '')
            self.api_key = self.api_config.get('api_key', '')
            self.model = self.api_config.get('model', 'qwen-plus')
        else:
            # 从环境变量加载
            load_dotenv()
            self.api_base_url = os.getenv('LLM_BASE_URL', '')
            self.api_key = os.getenv('LLM_API_KEY', '')
            self.model = os.getenv('LLM_MODEL', 'qwen-plus')

    def update_api_config(self, api_config: Dict):
        """动态更新 API 配置"""
        self.api_config = api_config
        self.api_base_url = api_config.get('base_url', '')
        self.api_key = api_config.get('api_key', '')
        self.model = api_config.get('model', 'qwen-plus')

    def _get_schema_info(self) -> str:
        """获取数据库表结构信息"""
        return """
数据库表结构：

1. core_performance_indicators (核心业绩指标表)
   - stock_code: 股票代码
   - stock_abbr: 股票简称
   - report_period: 报告期
   - basic_eps: 基本每股收益
   - diluted_eps: 稀释每股收益
   - net_asset_ps: 每股净资产
   - operating_revenue: 营业总收入
   - net_profit: 净利润

2. balance_sheet (资产负债表)
   - stock_code: 股票代码
   - stock_abbr: 股票简称
   - report_period: 报告期
   - total_assets: 资产总计
   - total_liabilities: 负债合计
   - total_equity: 所有者权益合计

3. income_sheet (利润表)
   - stock_code: 股票代码
   - stock_abbr: 股票简称
   - report_period: 报告期
   - operating_revenue: 营业总收入
   - operating_cost: 营业总成本
   - operating_profit: 营业利润
   - total_profit: 利润总额
   - net_profit: 净利润

4. cash_flow_sheet (现金流量表)
   - stock_code: 股票代码
   - stock_abbr: 股票简称
   - report_period: 报告期
   - operating_net_cash_flow: 经营活动现金流量净额
   - investing_net_cash_flow: 投资活动现金流量净额
   - financing_net_cash_flow: 筹资活动现金流量净额
"""

    def generate_sql(self, question: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        根据自然语言问题生成 SQL

        Args:
            question: 用户的自然语言问题
            context: 对话上下文历史

        Returns:
            包含 SQL 和执行结果的字典
        """
        # 构建 prompt
        system_prompt = f"""你是一个专业的 SQL 生成助手。根据数据库表结构，将用户的自然语言问题转换为 SQL 查询语句。

{self.schema_info}

要求：
1. 只输出 SQL 语句，不要有其他解释
2. 使用 MySQL 语法
3. 字段名使用反引号包裹
4. 字符串值使用单引号
5. 如果问题无法转换为 SQL，返回：ERROR: 无法理解问题

示例：
用户：查询贵州茅台 2024 年的净利润
SQL: SELECT net_profit FROM income_sheet WHERE stock_abbr = '贵州茅台' AND report_period = '2024FY';

用户：所有公司 2024 年营业收入排名
SQL: SELECT stock_abbr, operating_revenue FROM income_sheet WHERE report_period = '2024FY' ORDER BY operating_revenue DESC;
"""

        user_prompt = f"请将以下问题转换为 SQL 查询：\n{question}"

        if context:
            user_prompt += f"\n\n对话历史：\n{json.dumps(context, ensure_ascii=False)}"

        # 调用 LLM 生成 SQL
        sql = self._call_llm(system_prompt, user_prompt)

        result = {
            'question': question,
            'sql': sql,
            'success': False,
            'data': None,
            'error': None
        }

        if sql.startswith('ERROR:'):
            result['error'] = sql.replace('ERROR:', '').strip()
            return result

        # 执行 SQL 查询
        try:
            data = self._execute_sql(sql)
            result['success'] = True
            result['data'] = data
        except Exception as e:
            result['error'] = str(e)
            result['sql'] = sql  # 保留生成的 SQL 便于调试

        return result

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM API"""
        import requests

        if not self.api_key:
            # 没有 API key 时返回示例 SQL
            return "SELECT * FROM income_sheet LIMIT 10;"

        # 构建请求头
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # 构建 API URL - 智能拼接，避免重复路径
        def build_api_url(base_url: str) -> str:
            """构建完整的 API URL"""
            if not base_url:
                return ''
            base = base_url.rstrip('/')
            # 如果 base_url 已经包含 /chat/completions，直接返回
            if base.endswith('/chat/completions'):
                return base
            # 否则拼接 /chat/completions
            return f"{base}/chat/completions"

        api_url = build_api_url(self.api_base_url)

        if not api_url:
            return "ERROR: 未配置有效的 API Base URL"

        payload = {
            'model': self.model or 'qwen-plus',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.1,
            'max_tokens': 500
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            if 'choices' in result:
                return result['choices'][0]['message']['content'].strip()
            elif 'content' in result:
                # 某些 API 返回格式
                return result['content'][0].get('text', '').strip()
            else:
                return f"ERROR: 未知的 API 响应格式 - {result}"

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json().get('error', {}).get('message', str(e))
            except:
                error_detail = str(e)
            return f"ERROR: HTTP {response.status_code} - {error_detail}"
        except requests.exceptions.ConnectionError as e:
            return f"ERROR: 网络连接失败 - {str(e)}"
        except requests.exceptions.Timeout as e:
            return f"ERROR: 请求超时 - {str(e)}"
        except Exception as e:
            error_msg = str(e)
            # 检查是否是 API 调用错误，避免重复调用
            if 'API 调用失败' in error_msg or '404' in error_msg or '401' in error_msg:
                return f"ERROR: API 服务不可用 - {error_msg}"
            return f"ERROR: API 调用失败 - {str(e)}"

    def _execute_sql(self, sql: str) -> List[Dict]:
        """执行 SQL 查询"""
        if not self.db_manager or not self.db_manager.is_connected():
            # 如果没有数据库连接，返回模拟数据
            return [{'提示': '数据库未连接，返回模拟数据'}]

        return self.db_manager.execute_query(sql)

    def explain_sql(self, sql: str) -> str:
        """解释 SQL 语句的含义"""
        prompt = f"""请解释以下 SQL 查询语句的作用：

```sql
{sql}
```

请用简洁的中文解释这个查询要获取什么数据。"""

        return self._call_llm("你是一个 SQL 解释助手。", prompt)

    def validate_question(self, question: str) -> Dict[str, Any]:
        """
        验证问题是否可以转换为 SQL

        Returns:
            包含验证结果的字典
        """
        # 检查是否包含关键信息
        has_company = any(keyword in question for keyword in ['公司', '股票', '股份', '集团'])
        has_metric = any(keyword in question for keyword in ['利润', '收入', '资产', '负债', '现金流', '收益'])
        has_period = any(keyword in question for keyword in ['年', '季度', '期', '202', '203'])

        return {
            'valid': has_company or has_metric,
            'missing_info': {
                'company': not has_company,
                'metric': not has_metric,
                'period': not has_period
            },
            'suggestions': self._generate_suggestions(question)
        }

    def _generate_suggestions(self, question: str) -> List[str]:
        """生成追问建议"""
        suggestions = []

        if '公司' not in question and '股票' not in question:
            suggestions.append("您想查询哪家公司的数据？")

        if '年' not in question and '季度' not in question:
            suggestions.append("您想查询哪个时期的数据？")

        if '利润' not in question and '收入' not in question and '资产' not in question:
            suggestions.append("您想查询什么财务指标？")

        return suggestions
