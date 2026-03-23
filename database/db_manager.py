import pandas as pd
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime

from config.settings import DATABASE_CONFIG, DATABASE_URL
from models.database import (
    Base, BalanceSheet, IncomeStatement, 
    CashFlowStatement, KeyMetrics, get_engine, get_session
)

class DatabaseManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or DATABASE_URL
        self.engine = None
        self.session = None
    
    def connect(self):
        try:
            self.engine = create_engine(self.db_url)
            self.session = sessionmaker(bind=self.engine)()
            print("Database connection established")
            return True
        except SQLAlchemyError as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        print("Database connection closed")
    
    def create_database(self, db_name: str = "financial_reports"):
        try:
            default_url = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/postgres"
            engine = create_engine(default_url, isolation_level="AUTOCOMMIT")
            
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
                if not result.fetchone():
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    print(f"Database '{db_name}' created successfully")
                else:
                    print(f"Database '{db_name}' already exists")
            
            engine.dispose()
            return True
        except SQLAlchemyError as e:
            print(f"Error creating database: {e}")
            return False
    
    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            print("Tables created successfully")
            return True
        except SQLAlchemyError as e:
            print(f"Error creating tables: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

class DataLoader:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def load_balance_sheet(self, df: pd.DataFrame) -> int:
        if df.empty:
            print("Balance sheet DataFrame is empty")
            return 0
        
        records_loaded = 0
        
        for _, row in df.iterrows():
            try:
                existing = self.db_manager.session.query(BalanceSheet).filter(
                    BalanceSheet.stock_code == row.get('stock_code'),
                    BalanceSheet.report_year == row.get('report_year'),
                    BalanceSheet.report_period == row.get('report_period')
                ).first()
                
                if existing:
                    self._update_record(existing, row, BalanceSheet)
                else:
                    record = self._create_record(row, BalanceSheet)
                    self.db_manager.session.add(record)
                
                records_loaded += 1
            except Exception as e:
                print(f"Error loading balance sheet record: {e}")
                continue
        
        self.db_manager.session.commit()
        print(f"Loaded {records_loaded} balance sheet records")
        return records_loaded
    
    def load_income_statement(self, df: pd.DataFrame) -> int:
        if df.empty:
            print("Income statement DataFrame is empty")
            return 0
        
        records_loaded = 0
        
        for _, row in df.iterrows():
            try:
                existing = self.db_manager.session.query(IncomeStatement).filter(
                    IncomeStatement.stock_code == row.get('stock_code'),
                    IncomeStatement.report_year == row.get('report_year'),
                    IncomeStatement.report_period == row.get('report_period')
                ).first()
                
                if existing:
                    self._update_record(existing, row, IncomeStatement)
                else:
                    record = self._create_record(row, IncomeStatement)
                    self.db_manager.session.add(record)
                
                records_loaded += 1
            except Exception as e:
                print(f"Error loading income statement record: {e}")
                continue
        
        self.db_manager.session.commit()
        print(f"Loaded {records_loaded} income statement records")
        return records_loaded
    
    def load_cash_flow_statement(self, df: pd.DataFrame) -> int:
        if df.empty:
            print("Cash flow statement DataFrame is empty")
            return 0
        
        records_loaded = 0
        
        for _, row in df.iterrows():
            try:
                existing = self.db_manager.session.query(CashFlowStatement).filter(
                    CashFlowStatement.stock_code == row.get('stock_code'),
                    CashFlowStatement.report_year == row.get('report_year'),
                    CashFlowStatement.report_period == row.get('report_period')
                ).first()
                
                if existing:
                    self._update_record(existing, row, CashFlowStatement)
                else:
                    record = self._create_record(row, CashFlowStatement)
                    self.db_manager.session.add(record)
                
                records_loaded += 1
            except Exception as e:
                print(f"Error loading cash flow statement record: {e}")
                continue
        
        self.db_manager.session.commit()
        print(f"Loaded {records_loaded} cash flow statement records")
        return records_loaded
    
    def load_key_metrics(self, df: pd.DataFrame) -> int:
        if df.empty:
            print("Key metrics DataFrame is empty")
            return 0
        
        records_loaded = 0
        
        for _, row in df.iterrows():
            try:
                existing = self.db_manager.session.query(KeyMetrics).filter(
                    KeyMetrics.stock_code == row.get('stock_code'),
                    KeyMetrics.report_year == row.get('report_year'),
                    KeyMetrics.report_period == row.get('report_period')
                ).first()
                
                if existing:
                    self._update_record(existing, row, KeyMetrics)
                else:
                    record = self._create_record(row, KeyMetrics)
                    self.db_manager.session.add(record)
                
                records_loaded += 1
            except Exception as e:
                print(f"Error loading key metrics record: {e}")
                continue
        
        self.db_manager.session.commit()
        print(f"Loaded {records_loaded} key metrics records")
        return records_loaded
    
    def load_all_tables(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        results = {}
        
        results['balance_sheet'] = self.load_balance_sheet(dataframes.get('balance_sheet', pd.DataFrame()))
        results['income_statement'] = self.load_income_statement(dataframes.get('income_statement', pd.DataFrame()))
        results['cash_flow_statement'] = self.load_cash_flow_statement(dataframes.get('cash_flow_statement', pd.DataFrame()))
        results['key_metrics'] = self.load_key_metrics(dataframes.get('key_metrics', pd.DataFrame()))
        
        return results
    
    def _create_record(self, row: pd.Series, model_class):
        record = model_class()
        
        for column in model_class.__table__.columns.keys():
            if column in ['serial_number', 'created_at', 'updated_at']:
                continue
            
            if column in row.index:
                value = row[column]
                if pd.notna(value):
                    setattr(record, column, value)
        
        return record
    
    def _update_record(self, record, row: pd.Series, model_class):
        for column in model_class.__table__.columns.keys():
            if column in ['serial_number', 'created_at']:
                continue
            
            if column in row.index:
                value = row[column]
                if pd.notna(value):
                    setattr(record, column, value)
        
        record.updated_at = datetime.now()

class DataExporter:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def export_to_csv(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        balance_sheet_df = pd.read_sql_table('balance_sheet', self.db_manager.engine)
        balance_sheet_df.to_csv(os.path.join(output_dir, 'balance_sheet.csv'), index=False, encoding='utf-8-sig')
        
        income_statement_df = pd.read_sql_table('income_statement', self.db_manager.engine)
        income_statement_df.to_csv(os.path.join(output_dir, 'income_statement.csv'), index=False, encoding='utf-8-sig')
        
        cash_flow_df = pd.read_sql_table('cash_flow_statement', self.db_manager.engine)
        cash_flow_df.to_csv(os.path.join(output_dir, 'cash_flow_statement.csv'), index=False, encoding='utf-8-sig')
        
        key_metrics_df = pd.read_sql_table('key_metrics', self.db_manager.engine)
        key_metrics_df.to_csv(os.path.join(output_dir, 'key_metrics.csv'), index=False, encoding='utf-8-sig')
        
        print(f"Data exported to {output_dir}")
    
    def export_to_excel(self, output_file: str):
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            balance_sheet_df = pd.read_sql_table('balance_sheet', self.db_manager.engine)
            balance_sheet_df.to_excel(writer, sheet_name='资产负债表', index=False)
            
            income_statement_df = pd.read_sql_table('income_statement', self.db_manager.engine)
            income_statement_df.to_excel(writer, sheet_name='利润表', index=False)
            
            cash_flow_df = pd.read_sql_table('cash_flow_statement', self.db_manager.engine)
            cash_flow_df.to_excel(writer, sheet_name='现金流量表', index=False)
            
            key_metrics_df = pd.read_sql_table('key_metrics', self.db_manager.engine)
            key_metrics_df.to_excel(writer, sheet_name='核心业绩指标', index=False)
        
        print(f"Data exported to {output_file}")

if __name__ == "__main__":
    db_manager = DatabaseManager()
    
    db_manager.create_database()
    
    if db_manager.connect():
        db_manager.create_tables()
        
        db_manager.disconnect()
