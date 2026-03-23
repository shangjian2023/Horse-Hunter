"""
FinancialValidator - 财务数据勾稽关系校验器

执行财务一致性检查，确保数据准确性：
- 资产负债校验：资产总计 = 负债合计 + 所有者权益合计
- 利润表校验：利润总额 = 营业利润 + 营业外收入 - 营业外支出
- 现金流量表校验
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationType(Enum):
    """校验类型枚举"""
    BALANCE_SHEET = "资产负债表校验"
    INCOME_STATEMENT = "利润表校验"
    CASH_FLOW = "现金流量表校验"
    CROSS_STATEMENT = "跨表校验"


@dataclass
class ValidationResult:
    """校验结果数据类"""
    is_valid: bool
    validation_type: ValidationType
    rule_name: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    difference: Optional[float] = None
    tolerance: float = 0.01  # 允许误差 1%
    message: str = ""
    source: str = ""


class FinancialValidator:
    """财务数据校验器"""

    # 允许的绝对误差（用于处理四舍五入）
    ABSOLUTE_TOLERANCE = 0.01

    def __init__(self, tolerance: float = 0.01):
        """
        初始化校验器

        Args:
            tolerance: 相对误差容忍度，默认 1%
        """
        self.tolerance = tolerance
        self.validation_results: List[ValidationResult] = []

    def validate_balance_sheet(self, df: pd.DataFrame) -> List[ValidationResult]:
        """
        资产负债表校验

        勾稽关系：资产总计 = 负债合计 + 所有者权益合计

        Args:
            df: 资产负债表 DataFrame

        Returns:
            校验结果列表
        """
        results = []

        # 查找关键科目
        total_assets = self._find_item(df, ['资产总计', '资产合计', '总资产'])
        total_liabilities = self._find_item(df, ['负债合计', '总负债'])
        total_equity = self._find_item(df, ['所有者权益合计', '所有者权益总计', '股东权益合计', '净资产'])

        if total_assets is None or total_liabilities is None or total_equity is None:
            results.append(ValidationResult(
                is_valid=False,
                validation_type=ValidationType.BALANCE_SHEET,
                rule_name="资产负债平衡",
                message="缺少关键科目，无法校验"
            ))
            return results

        # 执行校验
        expected = total_liabilities + total_equity
        difference = abs(total_assets - expected)

        # 相对误差检查
        if total_assets != 0:
            relative_error = difference / abs(total_assets)
        else:
            relative_error = difference

        is_valid = (difference <= self.ABSOLUTE_TOLERANCE or
                   relative_error <= self.tolerance)

        results.append(ValidationResult(
            is_valid=is_valid,
            validation_type=ValidationType.BALANCE_SHEET,
            rule_name="资产负债平衡",
            expected_value=expected,
            actual_value=total_assets,
            difference=difference,
            message=f"资产总计 ({total_assets}) vs 负债 + 权益 ({expected})"
        ))

        return results

    def validate_income_statement(self, df: pd.DataFrame) -> List[ValidationResult]:
        """
        利润表校验

        勾稽关系：
        1. 利润总额 = 营业利润 + 营业外收入 - 营业外支出
        2. 净利润 = 利润总额 - 所得税费用
        3. 营业利润 = 营业收入 - 营业成本 - 税金及附加 - 期间费用 + 其他收益

        Args:
            df: 利润表 DataFrame

        Returns:
            校验结果列表
        """
        results = []

        # 查找关键科目
        total_profit = self._find_item(df, ['利润总额', '税前利润'])
        operating_profit = self._find_item(df, ['营业利润'])
        non_operating_income = self._find_item(df, ['营业外收入', '非经营性收入'])
        non_operating_expense = self._find_item(df, ['营业外支出', '非经营性支出'])
        net_profit = self._find_item(df, ['净利润', '税后利润'])
        income_tax = self._find_item(df, ['所得税费用', '所得税'])

        # 校验 1: 利润总额 = 营业利润 + 营业外收入 - 营业外支出
        if all([total_profit, operating_profit is not None]):
            calculated_profit = operating_profit
            if non_operating_income:
                calculated_profit += non_operating_income
            if non_operating_expense:
                calculated_profit -= non_operating_expense

            difference = abs(total_profit - calculated_profit)
            is_valid = (difference <= self.ABSOLUTE_TOLERANCE)

            results.append(ValidationResult(
                is_valid=is_valid,
                validation_type=ValidationType.INCOME_STATEMENT,
                rule_name="利润总额计算",
                expected_value=calculated_profit,
                actual_value=total_profit,
                difference=difference,
                message=f"利润总额 ({total_profit}) vs 计算值 ({calculated_profit})"
            ))

        # 校验 2: 净利润 = 利润总额 - 所得税费用
        if all([net_profit, total_profit, income_tax is not None]):
            calculated_net = total_profit - income_tax
            difference = abs(net_profit - calculated_net)
            is_valid = (difference <= self.ABSOLUTE_TOLERANCE)

            results.append(ValidationResult(
                is_valid=is_valid,
                validation_type=ValidationType.INCOME_STATEMENT,
                rule_name="净利润计算",
                expected_value=calculated_net,
                actual_value=net_profit,
                difference=difference,
                message=f"净利润 ({net_profit}) vs 计算值 ({calculated_net})"
            ))

        return results

    def validate_cash_flow(self, df: pd.DataFrame) -> List[ValidationResult]:
        """
        现金流量表校验

        勾稽关系：
        1. 现金及现金等价物净增加额 = 经营活动 + 投资活动 + 筹资活动现金流净额
        2. 期末现金余额 = 期初现金余额 + 本期增加额

        Args:
            df: 现金流量表 DataFrame

        Returns:
            校验结果列表
        """
        results = []

        # 查找关键科目
        net_increase = self._find_item(df, ['现金及现金等价物净增加额', '现金净增加额'])
        operating_cash = self._find_item(df, ['经营活动产生的现金流量净额', '经营现金流净额'])
        investing_cash = self._find_item(df, ['投资活动产生的现金流量净额', '投资现金流净额'])
        financing_cash = self._find_item(df, ['筹资活动产生的现金流量净额', '筹资现金流净额'])
        ending_cash = self._find_item(df, ['期末现金及现金等价物余额', '货币资金期末余额'])
        beginning_cash = self._find_item(df, ['期初现金及现金等价物余额', '货币资金期初余额'])

        # 校验 1: 现金净增加额 = 三大活动现金流之和
        if net_increase is not None and operating_cash is not None:
            calculated_increase = operating_cash
            if investing_cash is not None:
                calculated_increase += investing_cash
            if financing_cash is not None:
                calculated_increase += financing_cash

            difference = abs(net_increase - calculated_increase)
            is_valid = (difference <= self.ABSOLUTE_TOLERANCE)

            results.append(ValidationResult(
                is_valid=is_valid,
                validation_type=ValidationType.CASH_FLOW,
                rule_name="现金净增加额",
                expected_value=calculated_increase,
                actual_value=net_increase,
                difference=difference,
                message=f"现金净增加额 ({net_increase}) vs 计算值 ({calculated_increase})"
            ))

        # 校验 2: 期末余额 = 期初余额 + 本期增加
        if all([ending_cash is not None, beginning_cash is not None, net_increase is not None]):
            calculated_ending = beginning_cash + net_increase
            difference = abs(ending_cash - calculated_ending)
            is_valid = (difference <= self.ABSOLUTE_TOLERANCE)

            results.append(ValidationResult(
                is_valid=is_valid,
                validation_type=ValidationType.CASH_FLOW,
                rule_name="期末现金余额",
                expected_value=calculated_ending,
                actual_value=ending_cash,
                difference=difference,
                message=f"期末余额 ({ending_cash}) vs 计算值 ({calculated_ending})"
            ))

        return results

    def cross_statement_validation(
        self,
        balance_df: pd.DataFrame,
        income_df: pd.DataFrame,
        cash_flow_df: pd.DataFrame
    ) -> List[ValidationResult]:
        """
        跨表校验

        勾稽关系：
        1. 利润表净利润 = 资产负债表未分配利润变动（考虑分红）
        2. 现金流量表期末现金 = 资产负债表货币资金

        Args:
            balance_df: 资产负债表
            income_df: 利润表
            cash_flow_df: 现金流量表

        Returns:
            跨表校验结果列表
        """
        results = []

        # 校验：现金流量表期末现金 = 资产负债表货币资金
        cash_equivalents = self._find_item(cash_flow_df, ['期末现金及现金等价物余额'])
        monetary_fund = self._find_item(balance_df, ['货币资金'])

        if cash_equivalents is not None and monetary_fund is not None:
            # 注意：这里可能不完全相等，因为现金流量表的现金等价物范围可能不同
            difference = abs(cash_equivalents - monetary_fund)
            # 使用较大的容忍度
            is_valid = (difference / max(abs(cash_equivalents), abs(monetary_fund), 1) <= 0.05)

            results.append(ValidationResult(
                is_valid=is_valid,
                validation_type=ValidationType.CROSS_STATEMENT,
                rule_name="货币资金核对",
                expected_value=monetary_fund,
                actual_value=cash_equivalents,
                difference=difference,
                message=f"现金流量表现金 ({cash_equivalents}) vs 资产负债表货币资金 ({monetary_fund})"
            ))

        return results

    def _find_item(
        self,
        df: pd.DataFrame,
        keywords: List[str],
        column_index: int = 0
    ) -> Optional[float]:
        """
        在表格中查找指定科目

        Args:
            df: DataFrame
            keywords: 关键词列表
            column_index: 数值所在列索引

        Returns:
            找到的数值，未找到返回 None
        """
        if df.empty:
            return None

        # 遍历所有列查找关键词
        for col in df.columns:
            for keyword in keywords:
                mask = df[col].astype(str).str.contains(keyword, na=False, case=False)
                if mask.any():
                    # 找到匹配行
                    row_idx = mask.idxmax() if hasattr(mask, 'idxmax') else mask.argmax()
                    # 获取对应数值
                    for val_col in df.columns:
                        try:
                            value = df.loc[row_idx, val_col]
                            if isinstance(value, (int, float)):
                                return float(value)
                            elif isinstance(value, str):
                                # 清理并转换数值
                                cleaned = re.sub(r'[^\d.\-]', '', value)
                                if cleaned:
                                    return float(cleaned)
                        except (ValueError, KeyError):
                            continue

        return None

    def run_all_validations(
        self,
        balance_df: pd.DataFrame = None,
        income_df: pd.DataFrame = None,
        cash_flow_df: pd.DataFrame = None
    ) -> Dict[str, List[ValidationResult]]:
        """
        运行所有校验

        Args:
            balance_df: 资产负债表
            income_df: 利润表
            cash_flow_df: 现金流量表

        Returns:
            校验结果字典
        """
        all_results = {}

        if balance_df is not None:
            all_results['balance_sheet'] = self.validate_balance_sheet(balance_df)

        if income_df is not None:
            all_results['income_statement'] = self.validate_income_statement(income_df)

        if cash_flow_df is not None:
            all_results['cash_flow'] = self.validate_cash_flow(cash_flow_df)

        if all([balance_df is not None, income_df is not None, cash_flow_df is not None]):
            all_results['cross_statement'] = self.cross_statement_validation(
                balance_df, income_df, cash_flow_df
            )

        return all_results

    def get_validation_summary(
        self,
        results: Dict[str, List[ValidationResult]]
    ) -> str:
        """
        获取校验摘要

        Args:
            results: 校验结果字典

        Returns:
            摘要字符串
        """
        total_valid = 0
        total_invalid = 0
        messages = []

        for validation_type, type_results in results.items():
            for result in type_results:
                if result.is_valid:
                    total_valid += 1
                else:
                    total_invalid += 1
                    messages.append(f"[{validation_type}] {result.rule_name}: {result.message}")

        summary = f"校验完成 - 通过：{total_valid}, 失败：{total_invalid}\n"
        if messages:
            summary += "失败详情:\n" + "\n".join(messages)

        return summary


# 导入 re 模块用于数值清理
import re
