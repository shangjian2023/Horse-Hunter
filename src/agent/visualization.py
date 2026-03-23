"""
Visualization - 自动化可视化引擎

根据查询结果自动选择图表类型并生成：
- 折线图：趋势分析
- 柱状图：对比分析、排名
- 饼图：构成分析

图表按【问题编号_顺序编号】.jpg 格式保存至 result/ 文件夹
"""

import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


# 配置中文字体支持
def setup_chinese_font():
    """设置中文字体"""
    # Windows 系统字体
    font_paths = [
        'C:/Windows/Fonts/simhei.ttf',  # 黑体
        'C:/Windows/Fonts/simsun.ttc',  # 宋体
        'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_prop = fm.FontProperties(fname=font_path)
                plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
                plt.rcParams['axes.unicode_minus'] = False
                return font_prop
            except Exception:
                continue

    # 如果找不到，尝试使用默认字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    return None


@dataclass
class ChartConfig:
    """图表配置"""
    chart_type: str  # line, bar, pie
    title: str
    x_label: str = ""
    y_label: str = ""
    save_path: str = ""
    figsize: Tuple[int, int] = (10, 6)


class VisualizationEngine:
    """可视化引擎"""

    def __init__(self, output_dir: str = './result'):
        """
        初始化可视化引擎

        Args:
            output_dir: 图表保存目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置字体
        self.chinese_font = setup_chinese_font()

        # 图表计数器（用于生成问题编号）
        self.chart_counter = 0
        self.current_question_id = ""

    def set_question_id(self, question_id: str) -> None:
        """
        设置当前问题 ID

        Args:
            question_id: 问题编号（如 B002）
        """
        self.current_question_id = question_id
        self.chart_counter = 0

    def auto_select_chart_type(self, data: pd.DataFrame, question: str) -> str:
        """
        自动选择图表类型

        Args:
            data: 数据 DataFrame
            question: 用户问题

        Returns:
            图表类型
        """
        # 根据问题关键词判断
        if any(kw in question for kw in ['趋势', '变化', '走势', '增长']):
            return 'line'
        elif any(kw in question for kw in ['排名', '对比', '比较', 'top']):
            return 'bar'
        elif any(kw in question for kw in ['占比', '构成', '比例']):
            return 'pie'

        # 根据数据结构判断
        if len(data) == 0:
            return 'bar'

        # 默认柱状图
        return 'bar'

    def create_chart(
        self,
        data: pd.DataFrame,
        question: str,
        chart_type: Optional[str] = None,
        question_id: Optional[str] = None
    ) -> str:
        """
        创建图表

        Args:
            data: 数据 DataFrame
            question: 用户问题
            chart_type: 图表类型（可选，自动判断）
            question_id: 问题编号（可选）

        Returns:
            保存的文件路径
        """
        if data.empty:
            return self._create_empty_chart(question)

        # 自动选择图表类型
        if chart_type is None:
            chart_type = self.auto_select_chart_type(data, question)

        # 生成文件编号
        if question_id:
            self.current_question_id = question_id
        self.chart_counter += 1

        # 生成文件名：【问题编号_顺序编号】.jpg
        filename = f"{self.current_question_id}_{self.chart_counter:02d}.jpg"
        save_path = self.output_dir / filename

        # 创建图表
        try:
            if chart_type == 'line':
                self._create_line_chart(data, question, save_path)
            elif chart_type == 'bar':
                self._create_bar_chart(data, question, save_path)
            elif chart_type == 'pie':
                self._create_pie_chart(data, question, save_path)
            else:
                self._create_bar_chart(data, question, save_path)

            return str(save_path)
        except Exception as e:
            # 创建失败时返回空图表
            return self._create_error_chart(question, str(e))

    def _create_line_chart(
        self,
        data: pd.DataFrame,
        question: str,
        save_path: Path
    ) -> None:
        """创建折线图"""
        fig, ax = plt.subplots(figsize=(12, 6))

        # 尝试识别 X 轴和 Y 轴
        x_col = None
        y_cols = []

        for col in data.columns:
            col_str = str(col).lower()
            if 'date' in col_str or 'year' in col_str or '期' in str(col) or '年' in str(col):
                x_col = col
            elif col_str not in ['company', '公司', 'name', '名称']:
                y_cols.append(col)

        if x_col is None and len(data.columns) > 1:
            x_col = data.columns[0]
            y_cols = data.columns[1:].tolist()
        elif x_col is None:
            x_col = data.columns[0]
            y_cols = [data.columns[0]]

        # 绘制折线
        for y_col in y_cols:
            ax.plot(data[x_col], data[y_col], marker='o', label=y_col)

        # 设置标题和标签
        ax.set_title(question, fontsize=14, fontproperties=self.chinese_font)
        ax.set_xlabel(x_col, fontproperties=self.chinese_font)
        ax.set_ylabel('数值', fontproperties=self.chinese_font)

        # 旋转 X 轴标签
        plt.xticks(rotation=45)

        # 显示图例
        ax.legend(prop=self.chinese_font or {'family': 'sans-serif'})

        # 网格
        ax.grid(True, alpha=0.3)

        # 自动调整布局
        plt.tight_layout()

        # 保存
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _create_bar_chart(
        self,
        data: pd.DataFrame,
        question: str,
        save_path: Path
    ) -> None:
        """创建柱状图"""
        fig, ax = plt.subplots(figsize=(12, 6))

        # 识别类别列和数值列
        category_col = None
        value_col = None

        for col in data.columns:
            col_str = str(col).lower()
            if 'company' in col_str or '公司' in str(col) or 'name' in col_str or '名称' in str(col):
                category_col = col
            elif col_str not in ['date', 'year', '期', '年']:
                value_col = col

        if category_col is None:
            category_col = data.columns[0]
        if value_col is None and len(data.columns) > 1:
            value_col = data.columns[1]
        elif value_col is None:
            value_col = data.columns[0]

        # 绘制柱状图
        x = range(len(data))
        heights = data[value_col].values

        bars = ax.bar(x, heights, color='steelblue', alpha=0.8)

        # 设置 X 轴标签
        ax.set_xticks(x)
        ax.set_xticklabels(data[category_col].values, rotation=45, fontproperties=self.chinese_font)

        # 设置标题和标签
        ax.set_title(question, fontsize=14, fontproperties=self.chinese_font)
        ax.set_ylabel('数值', fontproperties=self.chinese_font)

        # 在柱子上方添加数值标签
        for i, (bar, height) in enumerate(zip(bars, heights)):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                fontsize=9
            )

        # 网格
        ax.grid(True, alpha=0.3, axis='y')

        # 自动调整布局
        plt.tight_layout()

        # 保存
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _create_pie_chart(
        self,
        data: pd.DataFrame,
        question: str,
        save_path: Path
    ) -> None:
        """创建饼图"""
        fig, ax = plt.subplots(figsize=(10, 8))

        # 识别类别列和数值列
        category_col = None
        value_col = None

        for col in data.columns:
            col_str = str(col).lower()
            if 'company' in col_str or '公司' in str(col) or 'name' in str(col):
                category_col = col
            elif col_str not in ['date', 'year', '期', '年']:
                value_col = col

        if category_col is None:
            category_col = data.columns[0]
        if value_col is None and len(data.columns) > 1:
            value_col = data.columns[1]
        elif value_col is None:
            value_col = data.columns[0]

        # 绘制饼图
        labels = data[category_col].values
        sizes = data[value_col].values

        # 过滤掉 0 或负值
        valid_indices = [i for i, s in enumerate(sizes) if s > 0]
        labels = [labels[i] for i in valid_indices]
        sizes = [sizes[i] for i in valid_indices]

        if not sizes:
            ax.text(0.5, 0.5, '无有效数据', ha='center', va='center',
                   fontproperties=self.chinese_font, fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            # 创建爆炸效果（突出最大值）
            explode = [0.05 if s == max(sizes) else 0 for s in sizes]

            ax.pie(
                sizes,
                labels=labels,
                explode=explode,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontproperties': self.chinese_font}
            )
            ax.set_title(question, fontsize=14, fontproperties=self.chinese_font)

        # 保存
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _create_empty_chart(self, question: str) -> str:
        """创建空数据图表"""
        self.chart_counter += 1
        filename = f"{self.current_question_id}_{self.chart_counter:02d}.jpg"
        save_path = self.output_dir / filename

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
               fontproperties=self.chinese_font, fontsize=16)
        ax.set_title(question, fontsize=14, fontproperties=self.chinese_font)
        ax.axis('off')

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return str(save_path)

    def _create_error_chart(self, question: str, error: str) -> str:
        """创建错误图表"""
        self.chart_counter += 1
        filename = f"{self.current_question_id}_{self.chart_counter:02d}.jpg"
        save_path = self.output_dir / filename

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'图表生成失败\n{error}', ha='center', va='center',
               fontproperties=self.chinese_font, fontsize=12)
        ax.set_title(question, fontsize=14, fontproperties=self.chinese_font)
        ax.axis('off')

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return str(save_path)


class ChartAutoSelector:
    """图表自动选择器"""

    @staticmethod
    def select(data: pd.DataFrame, question: str) -> str:
        """
        根据数据和问题自动选择图表类型

        Args:
            data: 数据
            question: 问题

        Returns:
            图表类型
        """
        # 检查数据是否为空
        if data.empty or len(data) == 0:
            return 'empty'

        # 检查问题关键词
        question_lower = question.lower()

        # 趋势类问题 -> 折线图
        trend_keywords = ['趋势', '变化', '走势', '增长', '同比', '环比', '近年']
        if any(kw in question_lower for kw in trend_keywords):
            return 'line'

        # 排名/对比类问题 -> 柱状图
        ranking_keywords = ['排名', '对比', '比较', 'top', '前十', '前五', '孰高']
        if any(kw in question_lower for kw in ranking_keywords):
            return 'bar'

        # 构成/占比类问题 -> 饼图
        pie_keywords = ['占比', '构成', '比例', '结构', '份额']
        if any(kw in question_lower for kw in pie_keywords):
            return 'pie'

        # 根据数据结构判断
        num_rows, num_cols = data.shape

        if num_cols == 2:
            # 两列数据可能是时间序列 -> 折线图
            first_col = str(data.columns[0]).lower()
            if 'year' in first_col or 'date' in first_col or '年' in first_col:
                return 'line'
            return 'bar'

        if num_rows <= 5:
            # 数据量少 -> 柱状图或饼图
            return 'bar'

        # 默认柱状图
        return 'bar'
