"""
FinBrain 系统测试脚本

使用 DeepSeek API Key 进行测试：sk-76f4b259f25147879777441ce24a0644
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.api.llm_client import LLMClient, APIConfig
from src.etl.financial_parser import FinancialParser
from src.etl.financial_validator import FinancialValidator
from src.agent.task_planner import TaskPlanner
from src.agent.nl2sql import NL2SQLConverter
from src.agent.visualization import VisualizationEngine


def test_llm_client():
    """测试 LLM 客户端"""
    print("\n" + "=" * 60)
    print("测试 1: LLM 客户端 (DeepSeek)")
    print("=" * 60)

    # 使用提供的 DeepSeek API Key
    api_key = "sk-76f4b259f25147879777441ce24a0644"

    client = LLMClient(
        APIConfig(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat"
        )
    )

    # 测试连接
    print("\n测试 API 连接...")
    result = client.test_connection()
    print(f"连接状态：{'OK [SUCCESS]' if result else 'FAIL'}")

    # 测试 SQL 生成
    print("\n测试 SQL 生成...")
    prompt = """你是一个 SQL 生成助手。请根据以下问题生成 MySQL 查询语句：

问题：贵州茅台 2024 年的净利润是多少？

只返回 SQL 语句，不要解释："""

    sql = client.generate(prompt)
    print(f"生成的 SQL: {sql}")

    return client


def test_financial_parser():
    """测试财报解析器"""
    print("\n" + "=" * 60)
    print("测试 2: 财报 PDF 解析器")
    print("=" * 60)

    parser = FinancialParser()

    # 测试文件名解析
    print("\n测试文件名解析...")

    test_files = [
        "600080_20230428_FQ2V.pdf",  # 上交所格式
        "贵州茅台：2023 年年度报告.pdf",  # 深交所格式
        "五粮液：2024 年第一季度报告.pdf",
    ]

    for filename in test_files:
        result = parser.parse_filename(filename)
        print(f"\n  文件名：{filename}")
        print(f"    交易所：{result['exchange']}")
        print(f"    股票代码：{result['stock_code']}")
        print(f"    公司名：{result['company_name']}")
        print(f"    报告日期：{result['report_date']}")
        print(f"    报告类型：{result['report_type']}")

    return parser


def test_task_planner():
    """测试任务规划器"""
    print("\n" + "=" * 60)
    print("测试 3: 任务规划器")
    print("=" * 60)

    planner = TaskPlanner()

    test_questions = [
        "贵州茅台 2024 年的净利润是多少？",
        "对比招商银行和浦发银行的总资产",
        "查询所有公司的营业收入排名前十",
        "贵州茅台近 5 年的净利润变化趋势",
        "Top 10 企业对比及原因分析",
    ]

    for question in test_questions:
        print(f"\n问题：{question}")
        intents = planner.analyze_intent(question)
        print(f"  识别意图：{[i.value for i in intents]}")

        missing = planner.check_missing_info(question)
        if missing:
            print(f"  缺失信息：{missing}")

        plan = planner.decompose_question(question)
        print(f"  任务拆解:")
        for task in plan.sub_tasks:
            print(f"    - [{task.task_type.value}] {task.description}")

    return planner


def test_nl2sql():
    """测试 NL2SQL 转换器"""
    print("\n" + "=" * 60)
    print("测试 4: NL2SQL 转换器")
    print("=" * 60)

    converter = NL2SQLConverter()

    test_questions = [
        "贵州茅台 2024 年的净利润是多少？",
        "查询所有公司的营业收入排名",
        "对比招商银行和浦发银行的总资产",
        "2024 年净利润排名前十的公司",
    ]

    for question in test_questions:
        print(f"\n问题：{question}")
        result = converter.convert(question)
        print(f"  SQL: {result.sql}")
        print(f"  有效性：{'VALID' if result.is_valid else 'INVALID'}")
        if result.error_message:
            print(f"  错误：{result.error_message}")

    return converter


def test_visualization():
    """测试可视化引擎"""
    print("\n" + "=" * 60)
    print("测试 5: 可视化引擎")
    print("=" * 60)

    import pandas as pd

    viz = VisualizationEngine(output_dir='./result/test')

    # 测试数据
    test_data = pd.DataFrame({
        'company_name': ['贵州茅台', '五粮液', '泸州老窖', '洋河股份', '山西汾酒'],
        'net_profit': [750, 320, 150, 130, 100],
        'operating_revenue': [1200, 850, 350, 380, 310],
    })

    test_questions = [
        "查询所有公司的净利润排名",
        "对比各公司的营业收入",
    ]

    for i, question in enumerate(test_questions):
        print(f"\n问题：{question}")
        chart_path = viz.create_chart(
            test_data,
            question,
            question_id=f"TEST_{i+1:02d}"
        )
        print(f"  生成图表：{chart_path}")

    return viz


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("FinBrain 系统测试套件")
    print("=" * 60)

    results = {
        'LLM 客户端': False,
        '财报解析器': False,
        '任务规划器': False,
        'NL2SQL': False,
        '可视化': False,
    }

    try:
        test_llm_client()
        results['LLM 客户端'] = True
    except Exception as e:
        print(f"LLM 客户端测试失败：{e}")

    try:
        test_financial_parser()
        results['财报解析器'] = True
    except Exception as e:
        print(f"财报解析器测试失败：{e}")

    try:
        test_task_planner()
        results['任务规划器'] = True
    except Exception as e:
        print(f"任务规划器测试失败：{e}")

    try:
        test_nl2sql()
        results['NL2SQL'] = True
    except Exception as e:
        print(f"NL2SQL 测试失败：{e}")

    try:
        test_visualization()
        results['可视化'] = True
    except Exception as e:
        print(f"可视化测试失败：{e}")

    # 输出测试报告
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)

    for module, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {module}: {status}")

    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\n总计：{total_passed}/{total_tests} 通过")

    return results


if __name__ == '__main__':
    run_all_tests()
