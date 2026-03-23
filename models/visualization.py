"""
可视化引擎 - 自动生成图表
"""

import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Optional, Any
import io
import base64


class VisualizationEngine:
    """可视化图表引擎"""

    def __init__(self, output_dir: str = 'result'):
        self.output_dir = output_dir
        self.style_cache = {}

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def auto_visualize(self, data: List[Dict], question: str,
                       chart_type: Optional[str] = None) -> Dict[str, Any]:
        """
        自动可视化数据

        Args:
            data: 查询结果数据
            question: 用户问题
            chart_type: 指定的图表类型

        Returns:
            包含图表信息和图片路径的字典
        """
        if not data:
            return {'success': False, 'error': '没有数据可可视化'}

        df = pd.DataFrame(data)

        # 自动判断图表类型
        if chart_type is None:
            chart_type = self._infer_chart_type(df, question)

        # 生成图表
        try:
            fig = self._create_chart(df, chart_type)
            image_path = self._save_figure(fig, question)
            plt.close(fig)

            return {
                'success': True,
                'chart_type': chart_type,
                'image_path': image_path,
                'data_summary': self._summarize_data(df)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _infer_chart_type(self, df: pd.DataFrame, question: str) -> str:
        """根据数据和问题推断图表类型"""
        num_cols = df.select_dtypes(include=['number']).columns
        has_time = any('period' in col.lower() or 'date' in col.lower() or '年' in col for col in df.columns)

        # 关键词匹配
        if '趋势' in question or '变化' in question or has_time:
            return 'line'
        elif '对比' in question or '排名' in question or 'top' in question.lower():
            return 'bar'
        elif '占比' in question or '比例' in question or '分布' in question:
            if len(df) <= 10:
                return 'pie'
            else:
                return 'bar'
        elif '关系' in question or '相关' in question:
            if len(num_cols) >= 2:
                return 'scatter'
            else:
                return 'bar'
        elif len(num_cols) >= 2:
            return 'bar'
        else:
            return 'bar'

    def _create_chart(self, df: pd.DataFrame, chart_type: str) -> plt.Figure:
        """创建图表"""
        num_cols = df.select_dtypes(include=['number']).columns

        if len(df) > 50:
            df = df.head(50)

        if chart_type == 'line':
            return self._create_line_chart(df, num_cols)
        elif chart_type == 'bar':
            return self._create_bar_chart(df, num_cols)
        elif chart_type == 'pie':
            return self._create_pie_chart(df, num_cols)
        elif chart_type == 'scatter':
            return self._create_scatter_chart(df, num_cols)
        else:
            return self._create_bar_chart(df, num_cols)

    def _create_line_chart(self, df: pd.DataFrame, num_cols: pd.Index) -> plt.Figure:
        """创建折线图"""
        fig, ax = plt.subplots(figsize=(10, 6))

        x_col = df.columns[0]  # 假设第一列是 x 轴
        for col in num_cols[:3]:  # 最多显示 3 条线
            ax.plot(df[x_col], df[col], marker='o', label=col)

        ax.set_xlabel(x_col)
        ax.set_ylabel('数值')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

    def _create_bar_chart(self, df: pd.DataFrame, num_cols: pd.Index) -> plt.Figure:
        """创建柱状图"""
        fig, ax = plt.subplots(figsize=(12, 6))

        x_col = df.columns[0]
        x_values = df[x_col].astype(str)

        if len(num_cols) == 1:
            bars = ax.bar(range(len(df)), df[num_cols[0]])
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(x_values, rotation=45, ha='right')
            ax.set_ylabel(num_cols[0])
        else:
            x = range(len(df))
            width = 0.8 / len(num_cols[:4])
            for i, col in enumerate(num_cols[:4]):
                offset = (i - len(num_cols[:4])/2 + 0.5) * width
                ax.bar([j + offset for j in x], df[col], width, label=col)
            ax.set_xticks(x)
            ax.set_xticklabels(x_values, rotation=45, ha='right')
            ax.legend()

        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()

        return fig

    def _create_pie_chart(self, df: pd.DataFrame, num_cols: pd.Index) -> plt.Figure:
        """创建饼图"""
        fig, ax = plt.subplots(figsize=(8, 8))

        x_col = df.columns[0]
        y_col = num_cols[0] if len(num_cols) > 0 else df.columns[1]

        # 只显示前 10 个
        if len(df) > 10:
            df = df.head(10)

        wedges, texts, autotexts = ax.pie(
            df[y_col],
            labels=df[x_col],
            autopct='%1.1f%%',
            startangle=90
        )

        ax.axis('equal')
        plt.tight_layout()

        return fig

    def _create_scatter_chart(self, df: pd.DataFrame, num_cols: pd.Index) -> plt.Figure:
        """创建散点图"""
        fig, ax = plt.subplots(figsize=(8, 6))

        if len(num_cols) >= 2:
            ax.scatter(df[num_cols[0]], df[num_cols[1]])
            ax.set_xlabel(num_cols[0])
            ax.set_ylabel(num_cols[1])
            ax.grid(True, alpha=0.3)
        else:
            ax.scatter(range(len(df)), df[num_cols[0]])

        plt.tight_layout()
        return fig

    def _save_figure(self, fig: plt.Figure, question: str) -> str:
        """保存图表"""
        import os
        import re
        from datetime import datetime

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 从问题中提取关键词作为文件名
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', question)[:20]
        filename = f"chart_{safe_name}_{timestamp}.png"

        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)

        fig.savefig(filepath, dpi=150, bbox_inches='tight')

        return filepath

    def _summarize_data(self, df: pd.DataFrame) -> str:
        """生成数据摘要"""
        lines = [f"共 {len(df)} 条记录，{len(df.columns)} 个字段"]

        num_cols = df.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            for col in num_cols[:3]:
                lines.append(f"  {col}: 平均值={df[col].mean():.2f}, 最大值={df[col].max()}, 最小值={df[col].min()}")

        return '\n'.join(lines)

    def encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{image_data}"
