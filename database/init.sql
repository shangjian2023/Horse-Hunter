-- 财务数据库初始化脚本
-- 创建核心业绩指标表
CREATE TABLE IF NOT EXISTS core_performance_indicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_abbr VARCHAR(50) COMMENT '股票简称',
    report_period VARCHAR(20) NOT NULL COMMENT '报告期',
    basic_eps DECIMAL(15,4) COMMENT '基本每股收益',
    diluted_eps DECIMAL(15,4) COMMENT '稀释每股收益',
    net_asset_ps DECIMAL(15,4) COMMENT '每股净资产',
    operating_revenue DECIMAL(15,2) COMMENT '营业总收入',
    net_profit DECIMAL(15,2) COMMENT '净利润',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stock_period (stock_code, report_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='核心业绩指标表';

-- 创建资产负债表
CREATE TABLE IF NOT EXISTS balance_sheet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_abbr VARCHAR(50) COMMENT '股票简称',
    report_period VARCHAR(20) NOT NULL COMMENT '报告期',
    report_type VARCHAR(20) COMMENT '报告类型',
    total_assets DECIMAL(15,2) COMMENT '资产总计',
    total_liabilities DECIMAL(15,2) COMMENT '负债合计',
    total_equity DECIMAL(15,2) COMMENT '所有者权益合计',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stock_period (stock_code, report_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产负债表';

-- 创建利润表
CREATE TABLE IF NOT EXISTS income_sheet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_abbr VARCHAR(50) COMMENT '股票简称',
    report_period VARCHAR(20) NOT NULL COMMENT '报告期',
    report_type VARCHAR(20) COMMENT '报告类型',
    operating_revenue DECIMAL(15,2) COMMENT '营业总收入',
    operating_cost DECIMAL(15,2) COMMENT '营业总成本',
    operating_profit DECIMAL(15,2) COMMENT '营业利润',
    total_profit DECIMAL(15,2) COMMENT '利润总额',
    net_profit DECIMAL(15,2) COMMENT '净利润',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stock_period (stock_code, report_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='利润表';

-- 创建现金流量表
CREATE TABLE IF NOT EXISTS cash_flow_sheet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_abbr VARCHAR(50) COMMENT '股票简称',
    report_period VARCHAR(20) NOT NULL COMMENT '报告期',
    report_type VARCHAR(20) COMMENT '报告类型',
    operating_cash_inflow DECIMAL(15,2) COMMENT '经营活动现金流入小计',
    operating_cash_outflow DECIMAL(15,2) COMMENT '经营活动现金流出小计',
    operating_net_cash_flow DECIMAL(15,2) COMMENT '经营活动产生的现金流量净额',
    investing_net_cash_flow DECIMAL(15,2) COMMENT '投资活动产生的现金流量净额',
    financing_net_cash_flow DECIMAL(15,2) COMMENT '筹资活动产生的现金流量净额',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stock_period (stock_code, report_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='现金流量表';
