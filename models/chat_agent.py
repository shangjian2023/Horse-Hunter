"""
Chat Agent - 智能问数助手主模块
整合 Text-to-SQL、对话管理、可视化等功能
"""

from typing import Dict, Any, List, Optional
from models.text_to_sql import TextToSQL
from models.conversation_manager import ConversationManager
from models.visualization import VisualizationEngine


class ChatAgent:
    """智能问数助手"""

    def __init__(self):
        self.text_to_sql = TextToSQL()
        self.conversation_manager = ConversationManager()
        self.visualization = VisualizationEngine()
        self.sessions: Dict[str, Dict] = {}

    def chat(self, question: str, session_id: str = 'default',
             image: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户查询

        Args:
            question: 用户问题
            session_id: 会话 ID
            image: 可选的图片（多模态输入）

        Returns:
            包含回答、SQL、数据、图表的字典
        """
        # 获取或创建会话
        session = self.conversation_manager.get_session(session_id)
        if not session:
            session = self.conversation_manager.create_session(session_id)

        # 添加用户消息
        self.conversation_manager.add_message(
            session_id, 'user', question,
            metadata={'has_image': image is not None}
        )

        # 如果有图片，先处理图片
        if image:
            image_analysis = self._analyze_image(image, question)
            question = f"{image_analysis}\n{question}"

        # 验证问题
        validation = self.text_to_sql.validate_question(question)
        if not validation['valid']:
            response = {
                'answer': self._generate_clarification(validation),
                'suggestions': validation['suggestions'],
                'sql': None,
                'data': None,
                'image': None
            }
        else:
            # 生成并执行 SQL
            context = self.conversation_manager.get_context(session_id)
            sql_result = self.text_to_sql.generate_sql(question, context)

            if sql_result['success']:
                # 生成可视化
                viz_result = None
                if sql_result['data']:
                    viz_result = self.visualization.auto_visualize(
                        sql_result['data'], question
                    )

                # 生成自然语言回答
                answer = self._generate_answer(question, sql_result)

                response = {
                    'answer': answer,
                    'sql': sql_result['sql'],
                    'data': sql_result['data'],
                    'image': viz_result['image_path'] if viz_result and viz_result.get('success') else None,
                    'chart_type': viz_result.get('chart_type') if viz_result else None
                }

                # 保存 SQL 到上下文
                self.conversation_manager.update_context(
                    session_id, {'last_sql': sql_result['sql']}
                )
            else:
                response = {
                    'answer': f"抱歉，查询失败：{sql_result['error']}",
                    'sql': sql_result.get('sql'),
                    'data': None,
                    'image': None,
                    'suggestions': ['请尝试换一种问法', '检查是否提供了足够的信息']
                }

        # 添加助手回复到对话历史
        self.conversation_manager.add_message(
            session_id, 'assistant', response['answer'],
            metadata={'sql': response.get('sql'), 'has_image': response.get('image') is not None}
        )

        return response

    def _analyze_image(self, image_path: str, question: str) -> str:
        """分析图片内容"""
        # TODO: 实现多模态图片分析
        return "[图片已接收]"

    def _generate_clarification(self, validation: Dict) -> str:
        """生成澄清追问"""
        parts = ["为了更准确地回答您的问题，我需要了解："]

        if validation['missing_info'].get('company'):
            parts.append("- 您想查询哪家公司？（例如：贵州茅台、中国平安）")

        if validation['missing_info'].get('metric'):
            parts.append("- 您想查询什么财务指标？（例如：净利润、营业收入、总资产）")

        if validation['missing_info'].get('period'):
            parts.append("- 您想查询哪个时期？（例如：2024 年、2024 年一季度）")

        return '\n'.join(parts)

    def _generate_answer(self, question: str, sql_result: Dict) -> str:
        """根据查询结果生成自然语言回答"""
        data = sql_result['data']

        if not data:
            return "未找到相关数据。"

        if len(data) == 1:
            # 单条数据，直接展示
            row = data[0]
            parts = [f"查询结果："]
            for key, value in row.items():
                parts.append(f"  - {key}: {value}")
            return '\n'.join(parts)
        else:
            # 多条数据，生成摘要
            summary = [f"共找到 {len(data)} 条记录。"]

            # 尝试识别关键指标
            df_columns = list(data[0].keys())
            metric_col = None
            for col in ['net_profit', 'operating_revenue', 'total_profit', '净利润', '营业收入']:
                if col in df_columns:
                    metric_col = col
                    break

            if metric_col:
                values = [row.get(metric_col, 0) for row in data]
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                if numeric_values:
                    summary.append(f"{metric_col} 范围：{min(numeric_values):.2f} ~ {max(numeric_values):.2f}")
                    summary.append(f"平均值：{sum(numeric_values)/len(numeric_values):.2f}")

            return '\n'.join(summary)

    def get_session_history(self, session_id: str) -> List[Dict]:
        """获取会话历史"""
        return self.conversation_manager.export_session(session_id).get('messages', [])

    def clear_session(self, session_id: str) -> None:
        """清空会话"""
        self.conversation_manager.clear_session(session_id)

    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        return self.conversation_manager.list_sessions()
