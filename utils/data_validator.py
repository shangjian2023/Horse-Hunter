import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import re

class DataCleaner:
    def __init__(self):
        self.unit_converters = {
            "元": 1,
            "万元": 10000,
            "千元": 1000,
            "百万元": 1000000,
            "亿元": 100000000
        }
    
    def clean_dataframe(self, df: pd.DataFrame, table_type: str) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        df = self._clean_column_names(df)
        
        df = self._clean_numeric_columns(df)
        
        df = self._standardize_units(df)
        
        df = self._fill_missing_values(df)
        
        df = self._remove_duplicates(df)
        
        return df
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        return df
    
    def _clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_patterns = [
            (r'[,\s]', ''),
            (r'\(([^)]+)\)', r'-\1'),
            (r'（([^）]+)）', r'-\1'),
            (r'^-$', 'NaN'),
            (r'^—$', 'NaN'),
            (r'^N/A$', 'NaN'),
            (r'^不适用$', 'NaN'),
        ]
        
        for col in df.columns:
            if col not in ['stock_code', 'stock_abbr', 'report_period']:
                if df[col].dtype == object:
                    for pattern, replacement in numeric_patterns:
                        df[col] = df[col].astype(str).str.replace(pattern, replacement, regex=True)
                    
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
        
        return df
    
    def _standardize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        return df
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col not in ['report_year', 'serial_number']:
                df[col] = df[col].fillna(0)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        subset = ['stock_code', 'report_year', 'report_period']
        existing_cols = [col for col in subset if col in df.columns]
        
        if existing_cols:
            df = df.drop_duplicates(subset=existing_cols, keep='last')
        
        return df

class DataValidator:
    def __init__(self):
        self.validation_results = {}
    
    def validate_dataframe(self, df: pd.DataFrame, table_type: str) -> Dict:
        if df.empty:
            return {"status": "error", "message": "DataFrame is empty"}
        
        results = {
            "table_type": table_type,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "validations": []
        }
        
        results["validations"].append(
            self._check_required_fields(df, table_type)
        )
        
        results["validations"].append(
            self._check_data_types(df)
        )
        
        results["validations"].append(
            self._check_value_ranges(df, table_type)
        )
        
        results["validations"].append(
            self._check_balance_sheet_balance(df, table_type)
        )
        
        results["validations"].append(
            self._check_duplicates(df)
        )
        
        passed = all(v.get("passed", True) for v in results["validations"])
        results["status"] = "passed" if passed else "failed"
        
        self.validation_results[table_type] = results
        return results
    
    def _check_required_fields(self, df: pd.DataFrame, table_type: str) -> Dict:
        required_fields = {
            "balance_sheet": ["stock_code", "report_year", "report_period"],
            "income_statement": ["stock_code", "report_year", "report_period"],
            "cash_flow_statement": ["stock_code", "report_year", "report_period"],
            "key_metrics": ["stock_code", "report_year", "report_period"]
        }
        
        required = required_fields.get(table_type, [])
        missing = [f for f in required if f not in df.columns]
        
        null_counts = {}
        for field in required:
            if field in df.columns:
                null_count = df[field].isnull().sum()
                if null_count > 0:
                    null_counts[field] = null_count
        
        return {
            "check": "required_fields",
            "passed": len(missing) == 0 and len(null_counts) == 0,
            "missing_fields": missing,
            "null_counts": null_counts
        }
    
    def _check_data_types(self, df: pd.DataFrame) -> Dict:
        type_issues = []
        
        for col in df.columns:
            if col in ['stock_code', 'stock_abbr', 'report_period']:
                continue
            
            if df[col].dtype not in [np.float64, np.int64, float, int]:
                type_issues.append(f"{col}: {df[col].dtype}")
        
        return {
            "check": "data_types",
            "passed": len(type_issues) == 0,
            "issues": type_issues
        }
    
    def _check_value_ranges(self, df: pd.DataFrame, table_type: str) -> Dict:
        issues = []
        
        if 'report_year' in df.columns:
            invalid_years = df[(df['report_year'] < 2000) | (df['report_year'] > 2030)]
            if len(invalid_years) > 0:
                issues.append(f"Invalid report_year values: {len(invalid_years)} rows")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ['report_year', 'serial_number']:
                continue
            
            if df[col].abs().max() > 1e15:
                issues.append(f"Column {col} has extremely large values")
        
        return {
            "check": "value_ranges",
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def _check_balance_sheet_balance(self, df: pd.DataFrame, table_type: str) -> Dict:
        if table_type != "balance_sheet":
            return {"check": "balance_sheet_balance", "passed": True, "skipped": True}
        
        issues = []
        
        if all(col in df.columns for col in ['total_assets', 'total_liabilities', 'total_equity']):
            calculated_total = df['total_liabilities'] + df['total_equity']
            diff = abs(df['total_assets'] - calculated_total)
            tolerance = df['total_assets'].abs() * 0.01
            
            unbalanced = diff > tolerance
            if unbalanced.any():
                issues.append(f"Balance sheet not balanced in {unbalanced.sum()} rows")
        
        return {
            "check": "balance_sheet_balance",
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def _check_duplicates(self, df: pd.DataFrame) -> Dict:
        subset = ['stock_code', 'report_year', 'report_period']
        existing_cols = [col for col in subset if col in df.columns]
        
        if not existing_cols:
            return {"check": "duplicates", "passed": True, "skipped": True}
        
        duplicates = df.duplicated(subset=existing_cols, keep=False)
        duplicate_count = duplicates.sum()
        
        return {
            "check": "duplicates",
            "passed": duplicate_count == 0,
            "duplicate_count": duplicate_count
        }
    
    def validate_with_great_expectations(self, df: pd.DataFrame, table_type: str) -> Dict:
        try:
            issues = []
            
            if 'stock_code' not in df.columns:
                issues.append("Missing stock_code column")
            if 'report_year' not in df.columns:
                issues.append("Missing report_year column")
            
            if 'stock_code' in df.columns:
                null_count = df['stock_code'].isnull().sum()
                if null_count > 0:
                    issues.append(f"stock_code has {null_count} null values")
            
            if 'report_year' in df.columns:
                null_count = df['report_year'].isnull().sum()
                if null_count > 0:
                    issues.append(f"report_year has {null_count} null values")
                
                invalid_years = df[(df['report_year'] < 2000) | (df['report_year'] > 2030)]
                if len(invalid_years) > 0:
                    issues.append(f"report_year has {len(invalid_years)} invalid values")
            
            return {
                "check": "great_expectations",
                "passed": len(issues) == 0,
                "issues": issues
            }
        except Exception as e:
            return {
                "check": "great_expectations",
                "passed": False,
                "error": str(e)
            }
    
    def get_validation_summary(self) -> Dict:
        summary = {
            "total_tables": len(self.validation_results),
            "passed": sum(1 for r in self.validation_results.values() if r.get("status") == "passed"),
            "failed": sum(1 for r in self.validation_results.values() if r.get("status") == "failed"),
            "details": self.validation_results
        }
        return summary

class DataConsistencyChecker:
    def __init__(self):
        self.inconsistencies = []
    
    def check_cross_table_consistency(self, dataframes: Dict[str, pd.DataFrame]) -> List[Dict]:
        self.inconsistencies = []
        
        self._check_income_vs_cash_flow(dataframes)
        
        self._check_profit_margin(dataframes)
        
        return self.inconsistencies
    
    def _check_income_vs_cash_flow(self, dataframes: Dict[str, pd.DataFrame]):
        if "income_statement" not in dataframes or "cash_flow_statement" not in dataframes:
            return
        
        income_df = dataframes["income_statement"]
        cash_df = dataframes["cash_flow_statement"]
        
        if income_df.empty or cash_df.empty:
            return
        
        merged = pd.merge(
            income_df[["stock_code", "report_year", "report_period", "net_profit"]],
            cash_df[["stock_code", "report_year", "report_period", "operating_cf_net_amount"]],
            on=["stock_code", "report_year", "report_period"],
            how="inner"
        )
        
        if not merged.empty:
            large_diff = abs(merged["net_profit"] - merged["operating_cf_net_amount"]) > abs(merged["net_profit"]) * 2
            if large_diff.any():
                self.inconsistencies.append({
                    "type": "income_vs_cash_flow",
                    "message": f"Large difference between net profit and operating cash flow in {large_diff.sum()} records",
                    "severity": "warning"
                })
    
    def _check_profit_margin(self, dataframes: Dict[str, pd.DataFrame]):
        if "income_statement" not in dataframes:
            return
        
        income_df = dataframes["income_statement"]
        
        if income_df.empty:
            return
        
        if "total_operating_revenue" in income_df.columns and "net_profit" in income_df.columns:
            valid_data = income_df[income_df["total_operating_revenue"] > 0]
            if not valid_data.empty:
                profit_margin = valid_data["net_profit"] / valid_data["total_operating_revenue"]
                abnormal = (profit_margin > 1) | (profit_margin < -1)
                if abnormal.any():
                    self.inconsistencies.append({
                        "type": "profit_margin",
                        "message": f"Abnormal profit margin in {abnormal.sum()} records",
                        "severity": "warning"
                    })

if __name__ == "__main__":
    cleaner = DataCleaner()
    validator = DataValidator()
    
    test_df = pd.DataFrame({
        "stock_code": ["000999", "000999"],
        "stock_abbr": ["华润三九", "华润三九"],
        "report_year": [2023, 2023],
        "report_period": ["Q1", "Q1"],
        "total_assets": [1000000, 1000000],
        "total_liabilities": [300000, 300000],
        "total_equity": [700000, 700000]
    })
    
    cleaned_df = cleaner.clean_dataframe(test_df, "balance_sheet")
    print("Cleaned DataFrame:")
    print(cleaned_df)
    
    results = validator.validate_dataframe(cleaned_df, "balance_sheet")
    print("\nValidation Results:")
    print(results)
