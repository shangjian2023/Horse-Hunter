"""
批量导入数据解析器

用于批量解析 data/import 目录中的财报文件，并输出结构化的数据。
支持 PDF 和 Excel 格式，自动识别财报类型并提取数据。
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.etl.financial_parser import FinancialParser
from src.etl.financial_validator import FinancialValidator


class BatchImportProcessor:
    """批量导入数据处理器"""

    def __init__(
        self,
        input_dir: str = "./data/import",
        output_dir: str = "./data/import/output"
    ):
        """
        初始化处理器

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 子目录
        self.pdf_dir = self.input_dir / "pdf_reports"
        self.excel_dir = self.input_dir / "excel_reports"
        self.processed_dir = self.input_dir / "processed"

        # 初始化解析器和验证器
        self.parser = FinancialParser(output_dir=str(self.output_dir))
        self.validator = FinancialValidator()

        # 处理日志
        self.processing_log = []

    def scan_input_directories(self) -> Dict[str, List[Path]]:
        """
        扫描输入目录，查找待处理的文件

        Returns:
            包含各类文件路径的字典
        """
        result = {
            "pdf_files": [],
            "excel_files": []
        }

        # 扫描 PDF 文件
        if self.pdf_dir.exists():
            # 使用 rglob 递归查找，避免中文路径问题
            pdf_files = list(self.pdf_dir.rglob("*.pdf"))
            result["pdf_files"] = [f for f in pdf_files if f.is_file()]
            print(f"找到 {len(result['pdf_files'])} 个 PDF 文件")

        # 扫描 Excel 文件
        if self.excel_dir.exists():
            excel_files = list(self.excel_dir.rglob("*.xlsx"))
            excel_files += list(self.excel_dir.rglob("*.xls"))
            result["excel_files"] = [f for f in excel_files if f.is_file()]
            print(f"找到 {len(result['excel_files'])} 个 Excel 文件")

        return result

    def process_pdf_files(self, pdf_files: List[Path]) -> Dict[str, pd.DataFrame]:
        """
        批量处理 PDF 文件

        Args:
            pdf_files: PDF 文件路径列表

        Returns:
            包含各类报表 DataFrame 的字典
        """
        all_results = []
        dataframes = {
            "key_metrics": [],
            "balance_sheet": [],
            "income_statement": [],
            "cash_flow_statement": []
        }

        for i, pdf_path in enumerate(pdf_files):
            print(f"\n[{i+1}/{len(pdf_files)}] 处理：{pdf_path.name}")

            try:
                # 解析 PDF
                result = self.parser.parse_pdf(str(pdf_path))

                if "error" in result:
                    self._log_processing(pdf_path.name, "PDF 解析失败", result.get("error"))
                    continue

                # 提取核心指标
                metrics = self.parser.extract_key_metrics(result)

                # 记录解析结果
                file_info = result.get("file_info", {})
                record = {
                    "file_name": pdf_path.name,
                    "stock_code": file_info.get("stock_code", ""),
                    "company_name": file_info.get("company_name", ""),
                    "exchange": file_info.get("exchange", ""),
                    "report_date": file_info.get("report_date", ""),
                    "report_type": file_info.get("report_type", ""),
                    "process_time": datetime.now().isoformat(),
                    "status": "success"
                }

                # 添加指标数据
                if metrics:
                    record.update(metrics)
                    dataframes["key_metrics"].append(metrics)

                # 提取表格数据
                for stmt_type in ["balance_sheet", "income_statement", "cash_flow_statement"]:
                    for stmt in result.get(stmt_type, []):
                        df = stmt.get("data")
                        if df is not None and not df.empty:
                            # 转换表格为结构化数据
                            stmt_data = self._convert_table_to_dict(df, stmt_type)
                            if stmt_data:
                                stmt_data["stock_code"] = file_info.get("stock_code", "")
                                stmt_data["report_date"] = file_info.get("report_date", "")
                                dataframes[stmt_type].append(stmt_data)

                self._log_processing(pdf_path.name, "处理成功", "")
                all_results.append(result)

            except Exception as e:
                error_msg = str(e)
                print(f"  处理失败：{error_msg}")
                self._log_processing(pdf_path.name, "异常", error_msg)

        # 转换为 DataFrame
        result_dfs = {}
        for key, records in dataframes.items():
            if records:
                result_dfs[key] = pd.DataFrame(records)
            else:
                result_dfs[key] = pd.DataFrame()

        return result_dfs

    def _convert_table_to_dict(self, df: pd.DataFrame, stmt_type: str) -> Dict:
        """
        将提取的表格转换为结构化字典

        Args:
            df: 表格 DataFrame
            stmt_type: 报表类型

        Returns:
            结构化数据字典
        """
        result = {}

        # 简化处理：将表格第一列作为字段名，第二列作为值
        if len(df.columns) >= 2:
            for _, row in df.iterrows():
                field_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                value = row.iloc[1] if pd.notna(row.iloc[1]) else None

                if field_name and value is not None:
                    # 尝试转换为数值
                    try:
                        if isinstance(value, str):
                            value = float(value.replace(",", "").strip())
                    except (ValueError, AttributeError):
                        pass

                    # 字段名映射（简化版）
                    field_map = self._get_field_mapping(stmt_type)
                    for cn_name, en_name in field_map.items():
                        if cn_name in field_name:
                            result[en_name] = value
                            break

        return result

    def _get_field_mapping(self, stmt_type: str) -> Dict[str, str]:
        """获取字段映射表"""
        mappings = {
            "balance_sheet": {
                "货币资金": "monetary_funds",
                "应收账款": "accounts_receivable",
                "存货": "inventory",
                "流动资产合计": "total_current_assets",
                "固定资产": "fixed_assets",
                "非流动资产合计": "total_non_current_assets",
                "资产总计": "total_assets",
                "短期借款": "short_term_borrowings",
                "应付账款": "accounts_payable",
                "流动负债合计": "total_current_liabilities",
                "长期借款": "long_term_borrowings",
                "负债合计": "total_liabilities",
                "股本": "share_capital",
                "未分配利润": "undistributed_profit",
                "所有者权益合计": "total_equity",
            },
            "income_statement": {
                "营业总收入": "operating_revenue",
                "营业成本": "operating_cost",
                "营业利润": "operating_profit",
                "利润总额": "total_profit",
                "净利润": "net_profit",
            },
            "cash_flow_statement": {
                "经营活动现金流入小计": "operating_cash_inflow",
                "经营活动现金流出小计": "operating_cash_outflow",
                "经营活动产生的现金流量净额": "operating_net_cash_flow",
                "投资活动产生的现金流量净额": "investing_net_cash_flow",
                "筹资活动产生的现金流量净额": "financing_net_cash_flow",
            }
        }
        return mappings.get(stmt_type, {})

    def process_excel_files(self, excel_files: List[Path]) -> Dict[str, pd.DataFrame]:
        """
        批量处理 Excel 文件

        Args:
            excel_files: Excel 文件路径列表

        Returns:
            包含各类报表 DataFrame 的字典
        """
        dataframes = {}
        all_data = []

        for i, excel_path in enumerate(excel_files):
            print(f"\n[{i+1}/{len(excel_files)}] 处理：{excel_path.name}")

            try:
                # 读取 Excel
                df = pd.read_excel(excel_path)

                record = {
                    "file_name": excel_path.name,
                    "process_time": datetime.now().isoformat(),
                    "status": "success",
                    "rows": len(df)
                }
                all_data.append(df)
                self._log_processing(excel_path.name, "处理成功", "")

            except Exception as e:
                error_msg = str(e)
                print(f"  处理失败：{error_msg}")
                self._log_processing(excel_path.name, "异常", error_msg)

        if all_data:
            dataframes["excel_imports"] = pd.concat(all_data, ignore_index=True)
        else:
            dataframes["excel_imports"] = pd.DataFrame()

        return dataframes

    def save_results(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """
        保存处理结果

        Args:
            dataframes: 包含各类报表的 DataFrame 字典

        Returns:
            保存的文件路径字典
        """
        saved_files = {}

        # 保存各类报表
        for name, df in dataframes.items():
            if df is not None and not df.empty:
                output_path = self.output_dir / f"{name}.csv"
                df.to_csv(output_path, index=False, encoding="utf-8-sig")
                saved_files[name] = str(output_path)
                print(f"已保存：{output_path} ({len(df)} 条记录)")

        # 保存处理日志
        if self.processing_log:
            log_path = self.output_dir / "processing_log.xlsx"
            df_log = pd.DataFrame(self.processing_log)
            df_log.to_excel(log_path, index=False)
            saved_files["processing_log"] = str(log_path)
            print(f"已保存：{log_path}")

        return saved_files

    def _log_processing(self, file_name: str, status: str, message: str):
        """记录处理日志"""
        self.processing_log.append({
            "file_name": file_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def run(self) -> Dict[str, str]:
        """
        运行完整的批量处理流程

        Returns:
            保存的文件路径字典
        """
        print("=" * 60)
        print("批量导入数据处理器")
        print("=" * 60)
        print(f"\n输入目录：{self.input_dir.absolute()}")
        print(f"输出目录：{self.output_dir.absolute()}")

        # 扫描输入目录
        print("\n扫描输入目录...")
        files = self.scan_input_directories()

        total_pdf = len(files["pdf_files"])
        total_excel = len(files["excel_files"])
        print(f"\n共找到 {total_pdf} 个 PDF 文件，{total_excel} 个 Excel 文件")

        if total_pdf == 0 and total_excel == 0:
            print("警告：未找到任何待处理文件")
            return {}

        all_dataframes = {}

        # 处理 PDF 文件
        if files["pdf_files"]:
            print("\n" + "=" * 60)
            print("处理 PDF 文件...")
            pdf_results = self.process_pdf_files(files["pdf_files"])
            all_dataframes.update(pdf_results)

        # 处理 Excel 文件
        if files["excel_files"]:
            print("\n" + "=" * 60)
            print("处理 Excel 文件...")
            excel_results = self.process_excel_files(files["excel_files"])
            all_dataframes.update(excel_results)

        # 保存结果
        print("\n" + "=" * 60)
        print("保存处理结果...")
        saved_files = self.save_results(all_dataframes)

        # 输出统计
        print("\n" + "=" * 60)
        print("处理完成!")
        print(f"成功处理：{sum(1 for log in self.processing_log if log['status'] == '处理成功')}")
        print(f"失败：{sum(1 for log in self.processing_log if log['status'] != '处理成功')}")
        print(f"输出文件：{len(saved_files)}")

        return saved_files


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="批量导入数据处理器")
    parser.add_argument(
        "--input-dir",
        default="./data/import",
        help="输入目录"
    )
    parser.add_argument(
        "--output-dir",
        default="./data/import/output",
        help="输出目录"
    )

    args = parser.parse_args()

    processor = BatchImportProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )

    processor.run()


if __name__ == "__main__":
    main()
