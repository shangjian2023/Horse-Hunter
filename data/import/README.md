# 导入数据目录

## 目录结构

```
data/import/
├── pdf_reports/          # PDF 财报文件
│   ├── sse/             # 上交所财报（可选子目录）
│   └── szse/            # 深交所财报（可选子目录）
├── excel_reports/        # Excel 格式财报
├── processed/           # 已处理标记文件
└── output/              # 解析输出目录
```

## 使用方法

### 1. 放置文件
将需要导入的财报文件放入对应目录：
- PDF 文件 → `data/import/pdf_reports/`
- Excel 文件 → `data/import/excel_reports/`

### 2. 运行解析
```bash
# 方式 1：使用 Streamlit 应用
streamlit run apps/file_processor_app.py

# 方式 2：使用命令行
python src/import_batch_processor.py --input-dir data/import --output-dir data/import/output
```

### 3. 查看结果
解析后的数据将保存到 `data/import/output/` 目录：
- `key_metrics.csv` - 核心业绩指标
- `balance_sheet.csv` - 资产负债表
- `income_statement.csv` - 利润表
- `cash_flow_statement.csv` - 现金流量表
- `processing_log.xlsx` - 处理日志

## 支持的文件格式

### PDF 财报
- 上交所格式：`股票代码_报告日期_随机标识.pdf`
  - 示例：`600080_20230428_FQ2V.pdf`
- 深交所格式：`公司简称：年份 + 报告类型.pdf`
  - 示例：`华润三九：2023 年年度报告.pdf`

### Excel 财报
- `.xlsx` 格式
- `.xls` 格式

## 输出字段说明

### 核心业绩指标表 (key_metrics.csv)
| 字段 | 说明 |
|------|------|
| stock_code | 股票代码 |
| company_name | 公司名称 |
| exchange | 交易所 (SSE/SZSE) |
| report_date | 报告日期 |
| report_type | 报告类型 (annual/Q1/Q3/semi-annual) |
| total_assets | 资产总计 |
| total_liabilities | 负债合计 |
| operating_revenue | 营业总收入 |
| net_profit | 净利润 |

### 资产负债表 (balance_sheet.csv)
| 字段 | 说明 |
|------|------|
| stock_code | 股票代码 |
| report_date | 报告日期 |
| monetary_funds | 货币资金 |
| accounts_receivable | 应收账款 |
| inventory | 存货 |
| total_current_assets | 流动资产合计 |
| fixed_assets | 固定资产 |
| total_non_current_assets | 非流动资产合计 |
| total_assets | 资产总计 |
| short_term_borrowings | 短期借款 |
| accounts_payable | 应付账款 |
| total_current_liabilities | 流动负债合计 |
| long_term_borrowings | 长期借款 |
| total_liabilities | 负债合计 |
| share_capital | 股本 |
| undistributed_profit | 未分配利润 |
| total_equity | 所有者权益合计 |

### 利润表 (income_statement.csv)
| 字段 | 说明 |
|------|------|
| stock_code | 股票代码 |
| report_date | 报告日期 |
| operating_revenue | 营业总收入 |
| operating_cost | 营业总成本 |
| operating_profit | 营业利润 |
| total_profit | 利润总额 |
| net_profit | 净利润 |

### 现金流量表 (cash_flow_statement.csv)
| 字段 | 说明 |
|------|------|
| stock_code | 股票代码 |
| report_date | 报告日期 |
| operating_cash_inflow | 经营活动现金流入小计 |
| operating_cash_outflow | 经营活动现金流出小计 |
| operating_net_cash_flow | 经营活动产生的现金流量净额 |
| investing_net_cash_flow | 投资活动产生的现金流量净额 |
| financing_net_cash_flow | 筹资活动产生的现金流量净额 |
