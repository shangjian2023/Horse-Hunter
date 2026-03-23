import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "B题-示例数据" / "示例数据"
REPORTS_DIR = DATA_DIR / "附件2：财务报告"
SSE_REPORTS_DIR = REPORTS_DIR / "reports-上交所"
SZSE_REPORTS_DIR = REPORTS_DIR / "reports-深交所"

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "financial_reports",
    "user": "postgres",
    "password": "postgres"
}

DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

REPORT_TYPE_MAPPING = {
    "一季度报告": "Q1",
    "半年度报告": "HY",
    "三季度报告": "Q3",
    "年度报告": "FY",
    "年度报告摘要": "FY",
    "半年度报告摘要": "HY"
}

FIELD_MAPPINGS = {
    "balance_sheet": {
        "货币资金": "monetary_funds",
        "应收票据": "notes_receivable",
        "应收账款": "accounts_receivable",
        "应收款项融资": "receivables_financing",
        "预付款项": "prepayments",
        "其他应收款": "other_receivables",
        "存货": "inventory",
        "其他流动资产": "other_current_assets",
        "流动资产合计": "total_current_assets",
        "长期股权投资": "long_term_equity_investment",
        "固定资产": "fixed_assets",
        "在建工程": "construction_in_progress",
        "使用权资产": "right_of_use_assets",
        "无形资产": "intangible_assets",
        "商誉": "goodwill",
        "长期待摊费用": "long_term_deferred_expenses",
        "递延所得税资产": "deferred_tax_assets",
        "其他非流动资产": "other_non_current_assets",
        "非流动资产合计": "total_non_current_assets",
        "资产总计": "total_assets",
        "短期借款": "short_term_borrowings",
        "应付票据": "notes_payable",
        "应付账款": "accounts_payable",
        "预收款项": "advance_receipts",
        "合同负债": "contract_liabilities",
        "应付职工薪酬": "employee_benefits_payable",
        "应交税费": "taxes_payable",
        "其他应付款": "other_payables",
        "一年内到期的非流动负债": "non_current_liabilities_due_within_one_year",
        "其他流动负债": "other_current_liabilities",
        "流动负债合计": "total_current_liabilities",
        "长期借款": "long_term_borrowings",
        "租赁负债": "lease_liabilities",
        "递延所得税负债": "deferred_tax_liabilities",
        "其他非流动负债": "other_non_current_liabilities",
        "非流动负债合计": "total_non_current_liabilities",
        "负债合计": "total_liabilities",
        "股本": "share_capital",
        "资本公积": "capital_reserve",
        "盈余公积": "surplus_reserve",
        "未分配利润": "undistributed_profit",
        "归属于母公司所有者权益合计": "total_equity_attributable_to_parent",
        "少数股东权益": "minority_interest",
        "所有者权益合计": "total_equity",
        "负债和所有者权益总计": "total_liabilities_and_equity"
    },
    "income_statement": {
        "营业总收入": "total_operating_revenue",
        "营业收入": "operating_revenue",
        "营业总成本": "total_operating_expenses",
        "营业成本": "operating_expense_cost_of_sales",
        "税金及附加": "operating_expense_taxes_and_surcharges",
        "销售费用": "operating_expense_selling_expenses",
        "管理费用": "operating_expense_administrative_expenses",
        "财务费用": "operating_expense_financial_expenses",
        "研发费用": "operating_expense_rnd_expenses",
        "其他收益": "other_income",
        "投资收益": "investment_income",
        "资产减值损失": "asset_impairment_loss",
        "信用减值损失": "credit_impairment_loss",
        "营业利润": "operating_profit",
        "利润总额": "total_profit",
        "净利润": "net_profit"
    },
    "cash_flow_statement": {
        "销售商品、提供劳务收到的现金": "cash_received_from_sales",
        "收到的税费返还": "tax_refunds_received",
        "收到其他与经营活动有关的现金": "other_cash_received_from_operating",
        "经营活动现金流入小计": "operating_cash_inflows",
        "购买商品、接受劳务支付的现金": "cash_paid_for_goods",
        "支付给职工以及为职工支付的现金": "cash_paid_to_employees",
        "支付的各项税费": "taxes_paid",
        "支付其他与经营活动有关的现金": "other_cash_paid_for_operating",
        "经营活动现金流出小计": "operating_cash_outflows",
        "经营活动产生的现金流量净额": "operating_cf_net_amount",
        "收回投资收到的现金": "cash_received_from_investment_disposal",
        "取得投资收益收到的现金": "investment_income_received",
        "处置固定资产、无形资产和其他长期资产收回的现金净额": "cash_received_from_asset_disposal",
        "收到其他与投资活动有关的现金": "other_cash_received_from_investing",
        "投资活动现金流入小计": "investing_cash_inflows",
        "购建固定资产、无形资产和其他长期资产支付的现金": "cash_paid_for_assets",
        "投资支付的现金": "cash_paid_for_investment",
        "支付其他与投资活动有关的现金": "other_cash_paid_for_investing",
        "投资活动现金流出小计": "investing_cash_outflows",
        "投资活动产生的现金流量净额": "investing_cf_net_amount",
        "吸收投资收到的现金": "cash_received_from_capital_injection",
        "取得借款收到的现金": "cash_received_from_borrowings",
        "收到其他与筹资活动有关的现金": "other_cash_received_from_financing",
        "筹资活动现金流入小计": "financing_cash_inflows",
        "偿还债务支付的现金": "cash_paid_for_debt_repayment",
        "分配股利、利润或偿付利息支付的现金": "cash_paid_for_dividends",
        "支付其他与筹资活动有关的现金": "other_cash_paid_for_financing",
        "筹资活动现金流出小计": "financing_cash_outflows",
        "筹资活动产生的现金流量净额": "financing_cf_net_amount",
        "现金及现金等价物净增加额": "net_increase_in_cash"
    },
    "key_metrics": {
        "基本每股收益": "basic_eps",
        "稀释每股收益": "diluted_eps",
        "归属于上市公司股东的净利润": "net_profit_attributable_to_parent",
        "归属于上市公司股东的扣除非经常性损益的净利润": "net_profit_deducted_non_recurring",
        "经营活动产生的现金流量净额": "operating_cash_flow",
        "营业收入": "operating_revenue",
        "归属于上市公司股东的净资产": "net_assets_attributable_to_parent",
        "总资产": "total_assets"
    }
}
