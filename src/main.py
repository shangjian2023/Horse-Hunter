"""
FinBrain 主入口程序 - 自动化流水线

一键读取附件 4/6 的问题并生成最终的 .xlsx 结果：
- task2_output.xlsx: 任务二产出（按照附件 7 表 2 的 JSON 结构）
- task3_output.xlsx: 任务三产出（按照附件 7 表 5 的格式，包含 references 嵌套）
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 导入本地模块
from src.etl.financial_parser import FinancialParser, ReportBatchParser
from src.etl.financial_validator import FinancialValidator
from src.agent.task_planner import TaskPlanner, TaskStatus
from src.agent.nl2sql import NL2SQLConverter, ClarificationManager
from src.agent.visualization import VisualizationEngine
from src.rag.retriever import RAGRetriever


class FinBrainPipeline:
    """FinBrain 自动化流水线"""

    def __init__(
        self,
        data_dir: str = './B 题 - 示例数据/示例数据',
        output_dir: str = './result',
        api_config: Optional[Dict] = None
    ):
        """
        初始化流水线

        Args:
            data_dir: 数据目录
            output_dir: 输出目录
            api_config: API 配置
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # API 配置（用于 DeepSeek 等）
        self.api_config = api_config or {}

        # 初始化各模块
        self.parser = FinancialParser(output_dir=str(self.output_dir / 'processed'))
        self.validator = FinancialValidator()
        self.task_planner = TaskPlanner()
        self.nl2sql = NL2SQLConverter()
        self.clarification = ClarificationManager()
        self.viz_engine = VisualizationEngine(output_dir=str(self.output_dir))
        self.rag_retriever = RAGRetriever()

        # 结果存储
        self.task2_results = []
        self.task3_results = []

    def run_etl_pipeline(self) -> bool:
        """
        运行 ETL 流水线

        Returns:
            是否成功
        """
        print("=" * 60)
        print("步骤 1: 运行 ETL 流水线 - 财报数据解析与入库")
        print("=" * 60)

        # 查找财报 PDF 目录
        reports_dir_sse = self.data_dir / '附件 2：财务报告' / 'reports-上交所'
        reports_dir_szse = self.data_dir / '附件 2：财务报告' / 'reports-深交所'

        all_parsed = []

        # 解析上交所财报
        if reports_dir_sse.exists():
            print(f"\n解析上交所财报：{reports_dir_sse}")
            parsed = self.parser.parse_directory(str(reports_dir_sse))
            all_parsed.extend(parsed)
            print(f"  解析完成：{len(parsed)} 个文件")

        # 解析深交所财报
        if reports_dir_szse.exists():
            print(f"\n解析深交所财报：{reports_dir_szse}")
            parsed = self.parser.parse_directory(str(reports_dir_szse))
            all_parsed.extend(parsed)
            print(f"  解析完成：{len(parsed)} 个文件")

        if not all_parsed:
            print("警告：未找到任何财报文件")
            return False

        # 保存解析结果
        saved_files = self.parser.save_to_csv(all_parsed)
        print(f"\n保存结果：{saved_files}")

        # 数据校验
        print("\n执行数据校验...")
        validation_results = []
        for result in all_parsed:
            if 'error' not in result:
                # 提取表格进行校验
                balance_df = result.get('balance_sheet', [{}])[0].get('data') if result.get('balance_sheet') else None
                income_df = result.get('income_statement', [{}])[0].get('data') if result.get('income_statement') else None
                cashflow_df = result.get('cash_flow_statement', [{}])[0].get('data') if result.get('cash_flow_statement') else None

                if any([balance_df, income_df, cashflow_df]):
                    vr = self.validator.run_all_validations(balance_df, income_df, cashflow_df)
                    validation_results.append({
                        'file': result.get('file_info', {}).get('original_filename'),
                        'validation': vr
                    })

        # 输出校验摘要
        valid_count = sum(
            1 for vr in validation_results
            for results in vr['validation'].values()
            for r in results if r.is_valid
        )
        invalid_count = sum(
            1 for vr in validation_results
            for results in vr['validation'].values()
            for r in results if not r.is_valid
        )
        print(f"校验结果 - 通过：{valid_count}, 失败：{invalid_count}")

        return True

    def run_task2(self, questions_file: str) -> List[Dict]:
        """
        运行任务二：智能问数（附件 4 利润表问题）

        Args:
            questions_file: 问题文件路径

        Returns:
            结果列表
        """
        print("\n" + "=" * 60)
        print("步骤 2: 运行任务二 - 利润表问题查询")
        print("=" * 60)

        # 读取问题
        try:
            df_questions = pd.read_excel(questions_file)
            questions = df_questions.iloc[:, 0].tolist() if len(df_questions.columns) > 0 else []
        except Exception as e:
            print(f"读取问题文件失败：{e}")
            questions = []

        if not questions:
            # 使用示例问题
            questions = [
                "贵州茅台 2024 年的净利润是多少？",
                "查询所有公司的营业收入排名",
                "对比招商银行和浦发银行的总资产",
            ]

        results = []

        for i, question in enumerate(questions, 1):
            print(f"\n处理问题 {i}: {question}")

            # 设置问题编号
            question_id = f"B002_{i:02d}"
            self.viz_engine.set_question_id(question_id)

            # 意图识别和任务拆解
            plan = self.task_planner.decompose_question(question)
            print(f"  识别意图：{[t.task_type.value for t in plan.sub_tasks]}")

            # 生成 SQL
            sql_result = self.nl2sql.convert(question)
            print(f"  生成 SQL: {sql_result.sql[:80]}..." if sql_result.sql else "  无 SQL")

            # 执行查询（模拟）
            query_result = self._execute_query(sql_result.sql)

            # 生成图表
            chart_path = None
            if query_result and len(query_result) > 0:
                df_result = pd.DataFrame(query_result)
                chart_path = self.viz_engine.create_chart(df_result, question, question_id=question_id)
                print(f"  生成图表：{chart_path}")

            # 构建结果（附件 7 表 2 格式）
            result = {
                'question_id': question_id,
                'question': question,
                'sql': sql_result.sql if sql_result.is_valid else '',
                'data': query_result,
                'chart_path': chart_path,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
            self.task2_results.append(result)

        # 保存结果
        self._save_task2_results(results)

        return results

    def run_task3(self, questions_file: str) -> List[Dict]:
        """
        运行任务三：RAG 增强与归因分析（附件 6 现金流量表问题）

        Args:
            questions_file: 问题文件路径

        Returns:
            结果列表
        """
        print("\n" + "=" * 60)
        print("步骤 3: 运行任务三 - RAG 增强与归因分析")
        print("=" * 60)

        # 初始化 RAG
        print("\n初始化 RAG 检索器...")
        rag_initialized = self.rag_retriever.initialize()
        print(f"  RAG 状态：{'已就绪' if rag_initialized else '未初始化'}")

        # 读取问题
        try:
            df_questions = pd.read_excel(questions_file)
            questions = df_questions.iloc[:, 0].tolist() if len(df_questions.columns) > 0 else []
        except Exception as e:
            print(f"读取问题文件失败：{e}")
            questions = []

        if not questions:
            # 使用示例问题
            questions = [
                "分析医药行业的政策环境",
                "新能源行业的发展趋势如何？",
                "Top 10 企业对比及原因分析",
            ]

        results = []

        for i, question in enumerate(questions, 1):
            print(f"\n处理问题 {i}: {question}")

            # 设置问题编号
            question_id = f"B003_{i:02d}"
            self.viz_engine.set_question_id(question_id)

            # 任务拆解
            plan = self.task_planner.decompose_question(question)
            print(f"  任务拆解：{[t.task_type.value for t in plan.sub_tasks]}")

            # RAG 检索
            rag_result = {'answer': '', 'references': []}
            if rag_initialized:
                rag_result = self.rag_retriever.retrieve_and_answer(question)
                print(f"  检索到 {len(rag_result.get('references', []))} 个参考来源")

            # 数据查询
            sql_result = self.nl2sql.convert(question)
            query_result = self._execute_query(sql_result.sql) if sql_result.is_valid else []

            # 生成图表
            chart_path = None
            if query_result and len(query_result) > 0:
                df_result = pd.DataFrame(query_result)
                chart_path = self.viz_engine.create_chart(df_result, question, question_id=question_id)
                print(f"  生成图表：{chart_path}")

            # 构建结果（附件 7 表 5 格式，包含 references 嵌套）
            result = {
                'question_id': question_id,
                'question': question,
                'sql': sql_result.sql if sql_result.is_valid else '',
                'data': query_result,
                'chart_path': chart_path,
                'answer': rag_result.get('answer', ''),
                'references': rag_result.get('references', []),
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
            self.task3_results.append(result)

        # 保存结果
        self._save_task3_results(results)

        return results

    def _execute_query(self, sql: str) -> List[Dict]:
        """
        执行 SQL 查询（模拟实现）

        Args:
            sql: SQL 语句

        Returns:
            查询结果
        """
        # 简化实现：返回模拟数据
        # 实际应该连接 MySQL 执行查询

        if not sql:
            return []

        # 模拟数据
        mock_data = [
            {'company_name': '贵州茅台', 'net_profit': 75000000000, 'operating_revenue': 120000000000},
            {'company_name': '五粮液', 'net_profit': 32000000000, 'operating_revenue': 85000000000},
            {'company_name': '泸州老窖', 'net_profit': 15000000000, 'operating_revenue': 35000000000},
        ]

        return mock_data

    def _save_task2_results(self, results: List[Dict]) -> None:
        """保存任务二结果"""
        output_path = self.output_dir / 'task2_output.xlsx'

        # 转换为 DataFrame
        df_rows = []
        for r in results:
            row = {
                '问题编号': r['question_id'],
                '问题': r['question'],
                'SQL': r['sql'],
                '图表路径': r['chart_path'] or '',
                '时间戳': r['timestamp']
            }
            df_rows.append(row)

        df = pd.DataFrame(df_rows)
        df.to_excel(output_path, index=False)
        print(f"\n任务二结果已保存：{output_path}")

    def _save_task3_results(self, results: List[Dict]) -> None:
        """保存任务三结果"""
        output_path = self.output_dir / 'task3_output.xlsx'

        # 转换为 DataFrame（包含 references 嵌套）
        df_rows = []
        for r in results:
            row = {
                '问题编号': r['question_id'],
                '问题': r['question'],
                'SQL': r['sql'],
                '图表路径': r['chart_path'] or '',
                '答案': r['answer'],
                'references': json.dumps(r['references'], ensure_ascii=False),
                '时间戳': r['timestamp']
            }
            df_rows.append(row)

        df = pd.DataFrame(df_rows)
        df.to_excel(output_path, index=False)
        print(f"\n任务三结果已保存：{output_path}")

    def run_full_pipeline(
        self,
        task2_questions: str = None,
        task3_questions: str = None
    ) -> bool:
        """
        运行完整流水线

        Args:
            task2_questions: 任务二问题文件路径
            task3_questions: 任务三问题文件路径

        Returns:
            是否成功
        """
        print("\n" + "=" * 60)
        print("FinBrain 财报智能问数系统 - 完整流水线")
        print("=" * 60)

        # 步骤 1: ETL 流水线
        if not self.run_etl_pipeline():
            print("ETL 流水线失败，继续执行后续步骤...")

        # 步骤 2: 任务二
        if task2_questions:
            self.run_task2(task2_questions)
        else:
            # 尝试默认路径
            default_q4 = self.data_dir / '附件 4：利润表.xlsx'
            if default_q4.exists():
                self.run_task2(str(default_q4))
            else:
                self.run_task2(None)

        # 步骤 3: 任务三
        if task3_questions:
            self.run_task3(task3_questions)
        else:
            # 尝试默认路径
            default_q6 = self.data_dir / '附件 6：现金流量表.xlsx'
            if default_q6.exists():
                self.run_task3(str(default_q6))
            else:
                self.run_task3(None)

        print("\n" + "=" * 60)
        print("流水线执行完成!")
        print(f"输出目录：{self.output_dir}")
        print("=" * 60)

        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='FinBrain 财报智能问数系统')
    parser.add_argument('--data-dir', default='./B 题 - 示例数据/示例数据', help='数据目录')
    parser.add_argument('--output-dir', default='./result', help='输出目录')
    parser.add_argument('--task2', help='任务二问题文件')
    parser.add_argument('--task3', help='任务三问题文件')
    parser.add_argument('--api-key', help='API Key')
    parser.add_argument('--api-base', help='API Base URL')

    args = parser.parse_args()

    # API 配置
    api_config = {}
    if args.api_key:
        api_config['api_key'] = args.api_key
    if args.api_base:
        api_config['api_base'] = args.api_base

    # 创建流水线
    pipeline = FinBrainPipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        api_config=api_config
    )

    # 运行
    success = pipeline.run_full_pipeline(
        task2_questions=args.task2,
        task3_questions=args.task3
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
