"""
命令行工具 - 财报数据处理和查询
用于现场演示和快速操作
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_process(args):
    """处理财报文件"""
    from parsers.pdf_parser import ReportBatchParser
    from utils.data_validator import DataCleaner

    print("=" * 60)
    print("财报数据处理工具")
    print("=" * 60)

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else Path("./data/processed")

    if not input_path.exists():
        print(f"错误：路径不存在 - {input_path}")
        return

    # 批量解析
    parser = ReportBatchParser()

    if input_path.is_dir():
        print(f"\n扫描目录：{input_path}")
        reports = parser.parse_directory(str(input_path))
        print(f"找到 {len(reports)} 个财报文件")
    else:
        print(f"\n解析文件：{input_path}")
        report = parser.parse_file(str(input_path))
        reports = [report] if report else []

    # 转换为 DataFrame
    if reports:
        print("\n转换为表格数据...")
        dataframes = parser.parse_reports_to_dataframe(reports)

        for table_name, df in dataframes.items():
            print(f"  {table_name}: {len(df)} 条记录")

        # 数据清洗
        print("\n清洗数据...")
        cleaner = DataCleaner()
        cleaned_data = {}
        for table_name, df in dataframes.items():
            cleaned_df = cleaner.clean_dataframe(df, table_name)
            cleaned_data[table_name] = cleaned_df
            print(f"  {table_name}: 清洗后 {len(cleaned_df)} 条记录")

        # 导出
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n导出数据到：{output_dir}")

        for table_name, df in cleaned_data.items():
            csv_file = output_dir / f"{table_name}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  ✓ {table_name}.csv")

        print("\n" + "=" * 60)
        print("处理完成!")
        print("=" * 60)
    else:
        print("\n未找到可处理的数据")


def cmd_query(args):
    """查询数据"""
    print("=" * 60)
    print("数据查询工具")
    print("=" * 60)

    # TODO: 实现查询功能
    print("查询功能开发中...")


def cmd_demo(args):
    """演示模式"""
    print("=" * 60)
    print("演示模式 - 快速展示系统功能")
    print("=" * 60)

    # 演示数据处理流程
    demo_data_path = Path("./B 题 - 示例数据/示例数据/附件 2：财务报告")

    if demo_data_path.exists():
        print(f"\n使用示例数据：{demo_data_path}")

        # 设置参数
        class Args:
            input = str(demo_data_path)
            output = "./data/demo_output"

        cmd_process(Args())

        print("\n演示数据处理完成!")
        print(f"输出目录：./data/demo_output")
    else:
        print(f"示例数据路径不存在：{demo_data_path}")
        print("请先下载示例数据")


def main():
    parser = argparse.ArgumentParser(
        description='财报数据处理和查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s process -i ./reports/ -o ./output/    # 处理目录中的所有财报
  %(prog)s process -i report.pdf                  # 处理单个文件
  %(prog)s query -q "贵州茅台 2024 年净利润"      # 查询数据
  %(prog)s demo                                   # 演示模式
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # process 命令
    process_parser = subparsers.add_parser('process', help='处理财报文件')
    process_parser.add_argument('-i', '--input', required=True, help='输入文件或目录路径')
    process_parser.add_argument('-o', '--output', help='输出目录')
    process_parser.set_defaults(func=cmd_process)

    # query 命令
    query_parser = subparsers.add_parser('query', help='查询数据')
    query_parser.add_argument('-q', '--query', required=True, help='查询问题')
    query_parser.add_argument('--model', default='deepseek-chat', help='使用的模型')
    query_parser.set_defaults(func=cmd_query)

    # demo 命令
    demo_parser = subparsers.add_parser('demo', help='演示模式')
    demo_parser.set_defaults(func=cmd_demo)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
