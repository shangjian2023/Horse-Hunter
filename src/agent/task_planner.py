"""
TaskPlanner - 多意图任务规划器

负责将复杂问题拆解为可执行的子任务序列，支持：
- 复杂问题拆解（如"Top 10 企业对比及原因分析"）
- 多意图自主规划
- 任务依赖管理
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TaskType(Enum):
    """任务类型"""
    DATA_QUERY = "数据查询"
    COMPARISON = "对比分析"
    TREND_ANALYSIS = "趋势分析"
    RANKING = "排名分析"
    CAUSE_ANALYSIS = "归因分析"
    RAG_RETRIEVAL = "知识库检索"
    VISUALIZATION = "可视化生成"
    REPORT_GENERATION = "报告生成"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "待执行"
    RUNNING = "执行中"
    COMPLETED = "已完成"
    FAILED = "失败"
    SKIPPED = "已跳过"


@dataclass
class SubTask:
    """子任务数据类"""
    task_id: str
    task_type: TaskType
    description: str
    sql_query: Optional[str] = None
    parameters: Dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    rag_sources: List[str] = field(default_factory=list)


@dataclass
class TaskPlan:
    """任务计划数据类"""
    plan_id: str
    original_question: str
    sub_tasks: List[SubTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    execution_order: List[str] = field(default_factory=list)


class TaskPlanner:
    """多意图任务规划器"""

    # 意图识别关键词
    INTENT_KEYWORDS = {
        TaskType.DATA_QUERY: ['查询', '查找', '获取', '显示', '查看', '是多少', '有多少'],
        TaskType.COMPARISON: ['对比', '比较', '差异', '哪个更高', '孰高孰低'],
        TaskType.TREND_ANALYSIS: ['趋势', '变化', '走势', '同比增长', '环比', '近年'],
        TaskType.RANKING: ['排名', 'top', '前十', '前五', '最高', '最大', '第一'],
        TaskType.CAUSE_ANALYSIS: ['原因', '为何', '为什么', '分析', '解读', '说明'],
        TaskType.RAG_RETRIEVAL: ['行业', '政策', '背景', '环境', '发展趋势', '研报'],
    }

    # 澄清触发条件
    CLARIFICATION_TRIGGERS = {
        'year': ['年', '年度', '年份'],
        'quarter': ['季度', 'q1', 'q2', 'q3', 'q4', '一季报', '中报', '三季报', '年报'],
        'company': ['公司', '企业', '股票', '股份'],
        'metric': ['利润', '收入', '资产', '负债', '现金流']
    }

    def __init__(self, llm_client=None):
        """
        初始化规划器

        Args:
            llm_client: LLM 客户端，用于复杂意图理解
        """
        self.llm_client = llm_client
        self.plans: Dict[str, TaskPlan] = {}

    def analyze_intent(self, question: str) -> List[TaskType]:
        """
        分析问题意图

        Args:
            question: 用户问题

        Returns:
            识别出的意图类型列表
        """
        detected_intents = []

        for task_type, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in question.lower() for kw in keywords):
                detected_intents.append(task_type)

        # 如果没有检测到明确意图，默认为数据查询
        if not detected_intents:
            detected_intents.append(TaskType.DATA_QUERY)

        return detected_intents

    def check_missing_info(self, question: str) -> List[str]:
        """
        检查缺失的关键信息

        Args:
            question: 用户问题

        Returns:
            缺失信息字段列表
        """
        missing = []

        # 检查年份
        if not re.search(r'\d{4}年|\d{4}', question):
            missing.append('year')

        # 检查公司
        company_patterns = [
            r'\d{6}',  # 股票代码
            r' [A 股].*?(?:公司 | 股份 | 集团)',  # 公司名
        ]
        if not any(re.search(p, question) for p in company_patterns):
            missing.append('company')

        # 检查指标
        metric_keywords = ['利润', '收入', '资产', '负债', '权益', '现金流', '营收', '净利润']
        if not any(kw in question for kw in metric_keywords):
            missing.append('metric')

        return missing

    def generate_clarification_question(self, missing: List[str]) -> str:
        """
        生成澄清问题

        Args:
            missing: 缺失字段列表

        Returns:
            澄清问题字符串
        """
        clarifications = {
            'year': '请问您想查询哪一年的数据？',
            'company': '请问您想查询哪家公司的数据？可以提供股票代码或公司全称。',
            'metric': '请问您想查询什么指标？如净利润、营业收入等。',
            'quarter': '请问您想查询哪个季度的数据？',
        }

        questions = [clarifications.get(m, f'请提供{m}信息') for m in missing]
        return ' '.join(questions)

    def decompose_question(self, question: str) -> TaskPlan:
        """
        拆解复杂问题为子任务

        Args:
            question: 用户问题

        Returns:
            任务计划
        """
        intents = self.analyze_intent(question)
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        plan = TaskPlan(
            plan_id=plan_id,
            original_question=question,
        )

        # 根据意图类型拆解
        if TaskType.RANKING in intents:
            # 排名类问题拆解
            plan.sub_tasks = self._decompose_ranking(question)
        elif TaskType.COMPARISON in intents:
            # 对比类问题拆解
            plan.sub_tasks = self._decompose_comparison(question)
        elif TaskType.CAUSE_ANALYSIS in intents:
            # 归因分析拆解
            plan.sub_tasks = self._decompose_cause_analysis(question)
        elif TaskType.TREND_ANALYSIS in intents:
            # 趋势分析拆解
            plan.sub_tasks = self._decompose_trend(question)
        else:
            # 简单查询
            plan.sub_tasks = self._decompose_simple_query(question)

        # 添加 RAG 检索任务（如果是行业/政策相关问题）
        if TaskType.RAG_RETRIEVAL in intents:
            rag_task = SubTask(
                task_id=f"{plan_id}_rag",
                task_type=TaskType.RAG_RETRIEVAL,
                description=f"检索与'{question}'相关的行业研报",
            )
            plan.sub_tasks.insert(0, rag_task)

        # 生成执行顺序
        plan.execution_order = [t.task_id for t in plan.sub_tasks]

        # 确定整体状态
        plan.status = TaskStatus.PENDING

        # 保存计划
        self.plans[plan_id] = plan

        return plan

    def _decompose_ranking(self, question: str) -> List[SubTask]:
        """拆解排名类问题"""
        task_id = f"rank_{datetime.now().strftime('%H%M%S')}"

        # 识别排名指标
        metric = self._extract_metric(question)
        # 识别排名数量
        top_n = self._extract_top_n(question)

        return [
            SubTask(
                task_id=f"{task_id}_query",
                task_type=TaskType.DATA_QUERY,
                description=f"查询所有公司的{metric}数据",
                parameters={'metric': metric, 'top_n': top_n}
            ),
            SubTask(
                task_id=f"{task_id}_rank",
                task_type=TaskType.RANKING,
                description=f"按{metric}进行排名，取前{top_n}名",
                parameters={'metric': metric, 'top_n': top_n},
                dependencies=[f"{task_id}_query"]
            ),
            SubTask(
                task_id=f"{task_id}_viz",
                task_type=TaskType.VISUALIZATION,
                description=f"生成{metric}排名柱状图",
                parameters={'chart_type': 'bar', 'metric': metric},
                dependencies=[f"{task_id}_rank"]
            )
        ]

    def _decompose_comparison(self, question: str) -> List[SubTask]:
        """拆解对比类问题"""
        task_id = f"comp_{datetime.now().strftime('%H%M%S')}"

        # 识别对比对象和指标
        companies = self._extract_companies(question)
        metric = self._extract_metric(question)

        return [
            SubTask(
                task_id=f"{task_id}_query",
                task_type=TaskType.DATA_QUERY,
                description=f"查询{','.join(companies)}的{metric}数据",
                parameters={'companies': companies, 'metric': metric}
            ),
            SubTask(
                task_id=f"{task_id}_compare",
                task_type=TaskType.COMPARISON,
                description=f"对比分析{','.join(companies)}的{metric}",
                parameters={'companies': companies, 'metric': metric},
                dependencies=[f"{task_id}_query"]
            ),
            SubTask(
                task_id=f"{task_id}_viz",
                task_type=TaskType.VISUALIZATION,
                description=f"生成对比柱状图",
                parameters={'chart_type': 'bar', 'metric': metric},
                dependencies=[f"{task_id}_compare"]
            )
        ]

    def _decompose_cause_analysis(self, question: str) -> List[SubTask]:
        """拆解归因分析问题"""
        task_id = f"cause_{datetime.now().strftime('%H%M%S')}"

        return [
            SubTask(
                task_id=f"{task_id}_data",
                task_type=TaskType.DATA_QUERY,
                description="查询相关财务数据",
            ),
            SubTask(
                task_id=f"{task_id}_rag",
                task_type=TaskType.RAG_RETRIEVAL,
                description="检索相关研报和行业分析",
                rag_sources=['./data/knowledge_base']
            ),
            SubTask(
                task_id=f"{task_id}_analyze",
                task_type=TaskType.CAUSE_ANALYSIS,
                description="综合数据和研报进行归因分析",
                dependencies=[f"{task_id}_data", f"{task_id}_rag"]
            )
        ]

    def _decompose_trend(self, question: str) -> List[SubTask]:
        """拆解趋势分析问题"""
        task_id = f"trend_{datetime.now().strftime('%H%M%S')}"

        company = self._extract_company(question)
        metric = self._extract_metric(question)
        years = self._extract_years(question)

        return [
            SubTask(
                task_id=f"{task_id}_query",
                task_type=TaskType.DATA_QUERY,
                description=f"查询{company}{years}年的{metric}数据",
                parameters={'company': company, 'metric': metric, 'years': years}
            ),
            SubTask(
                task_id=f"{task_id}_calc",
                task_type=TaskType.TREND_ANALYSIS,
                description="计算同比增长率和环比增长率",
                dependencies=[f"{task_id}_query"]
            ),
            SubTask(
                task_id=f"{task_id}_viz",
                task_type=TaskType.VISUALIZATION,
                description="生成趋势折线图",
                parameters={'chart_type': 'line', 'metric': metric},
                dependencies=[f"{task_id}_calc"]
            )
        ]

    def _decompose_simple_query(self, question: str) -> List[SubTask]:
        """拆解简单查询问题"""
        task_id = f"query_{datetime.now().strftime('%H%M%S')}"

        return [
            SubTask(
                task_id=f"{task_id}_sql",
                task_type=TaskType.DATA_QUERY,
                description=f"生成 SQL 查询：{question}",
            )
        ]

    def _extract_metric(self, question: str) -> str:
        """提取指标名称"""
        metric_keywords = [
            '净利润', '营业收入', '总资产', '负债', '所有者权益',
            '营业利润', '毛利率', '资产负债率', '现金流'
        ]
        for kw in metric_keywords:
            if kw in question:
                return kw
        return '财务指标'

    def _extract_top_n(self, question: str) -> int:
        """提取排名数量"""
        patterns = {
            r'前 (?:十|10)': 10,
            r'前 (?:五|5)': 5,
            r'前 (?:三|3)': 3,
            r'第 (?:一|1)': 1,
        }
        for pattern, n in patterns.items():
            if re.search(pattern, question):
                return n
        return 10  # 默认前 10

    def _extract_companies(self, question: str) -> List[str]:
        """提取公司名称列表"""
        # 简化实现，实际应该用 NER
        company_patterns = [
            r'([A 股].*?(?:公司 | 股份 | 集团))',
            r'([\u4e00-\u9fa5]{2,} 股份)',
            r'([\u4e00-\u9fa5]{2,} 公司)',
        ]
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, question)
            companies.extend(matches)
        return list(set(companies)) if companies else ['未知公司']

    def _extract_company(self, question: str) -> str:
        """提取单个公司名称"""
        companies = self._extract_companies(question)
        return companies[0] if companies else '未知公司'

    def _extract_years(self, question: str) -> List[int]:
        """提取年份列表"""
        matches = re.findall(r'(\d{4}) 年', question)
        if not matches:
            matches = re.findall(r'(\d{4})', question)

        if matches:
            return [int(y) for y in matches]

        # 默认近 5 年
        current_year = datetime.now().year
        return list(range(current_year - 5, current_year + 1))

    def get_plan_status(self, plan_id: str) -> Optional[TaskPlan]:
        """获取计划状态"""
        return self.plans.get(plan_id)

    def update_task_status(
        self,
        plan_id: str,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> None:
        """更新任务状态"""
        plan = self.plans.get(plan_id)
        if not plan:
            return

        for task in plan.sub_tasks:
            if task.task_id == task_id:
                task.status = status
                task.result = result
                task.error_message = error_message
                break

        # 检查所有任务是否完成
        all_completed = all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
            for t in plan.sub_tasks
        )
        any_failed = any(
            t.status == TaskStatus.FAILED for t in plan.sub_tasks
        )

        if all_completed:
            plan.status = TaskStatus.COMPLETED
        elif any_failed:
            plan.status = TaskStatus.FAILED

    def export_plan(self, plan_id: str) -> Dict:
        """导出计划为字典"""
        plan = self.plans.get(plan_id)
        if not plan:
            return {}

        return {
            'plan_id': plan.plan_id,
            'original_question': plan.original_question,
            'status': plan.status.value,
            'created_at': plan.created_at.isoformat(),
            'sub_tasks': [
                {
                    'task_id': t.task_id,
                    'task_type': t.task_type.value,
                    'description': t.description,
                    'status': t.status.value,
                    'result': t.result,
                    'error_message': t.error_message,
                    'dependencies': t.dependencies,
                }
                for t in plan.sub_tasks
            ]
        }
