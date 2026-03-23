"""
RAG 知识库初始化脚本
加载行业报告、企业信息等文档到知识库
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from models.rag.document_loader import DocumentLoader
from models.rag.knowledge_base import KnowledgeBase


def init_knowledge_base(data_dir: str = "B 题 - 示例数据/附件 5：行业报告"):
    """
    初始化知识库

    Args:
        data_dir: 文档数据目录路径
    """
    print("=" * 60)
    print("RAG 知识库初始化")
    print("=" * 60)

    # 检查目录是否存在
    if not os.path.exists(data_dir):
        print(f"警告：数据目录不存在：{data_dir}")
        print("请确认附件 5：行业报告 目录位置")
        return

    # 创建知识库
    kb = KnowledgeBase()

    # 创建文档加载器
    loader = DocumentLoader(chunk_size=500, chunk_overlap=50)

    print(f"\n正在扫描目录：{data_dir}")

    # 扫描所有支持的文档
    supported_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md', '.xlsx']
    all_chunks = []

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                file_path = os.path.join(root, file)
                print(f"  加载：{file}")

                try:
                    chunks = loader.load_and_chunk(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"    加载失败：{e}")

    print(f"\n共加载 {len(all_chunks)} 个文档片段")

    # 过滤掉太短的片段
    valid_chunks = [c for c in all_chunks if len(c['content']) > 50]
    print(f"有效片段：{len(valid_chunks)}")

    # 添加到知识库
    if valid_chunks:
        added = kb.add_documents(valid_chunks)
        print(f"已添加到知识库：{added} 条")

        # 显示统计信息
        stats = kb.get_stats()
        print("\n知识库统计:")
        print(f"  总片段数：{stats['total_chunks']}")
        print(f"  来源文件：{len(stats['sources'])} 个")

    print("\n" + "=" * 60)
    print("知识库初始化完成!")
    print("=" * 60)

    return kb


def test_retrieval(question: str = "医药行业有哪些重点企业？"):
    """
    测试检索功能

    Args:
        question: 测试问题
    """
    from models.rag.retriever import Retriever

    print("\n" + "=" * 60)
    print("检索测试")
    print("=" * 60)
    print(f"问题：{question}")

    retriever = Retriever()
    result = retriever.retrieve_and_answer(question)

    print(f"\n回答：{result['answer']}")

    if result['references']:
        print("\n参考来源:")
        for i, ref in enumerate(result['references'], 1):
            print(f"  [{i}] {ref['source']} (相关度：{ref['score']:.2f})")

    return result


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='RAG 知识库初始化工具')
    parser.add_argument('--data-dir', type=str, default='B 题 - 示例数据/附件 5：行业报告',
                        help='文档数据目录路径')
    parser.add_argument('--test', type=str, help='测试检索问题')
    parser.add_argument('--init', action='store_true', help='初始化知识库')

    args = parser.parse_args()

    if args.init or args.data_dir:
        kb = init_knowledge_base(args.data_dir)

    if args.test:
        test_retrieval(args.test)
    elif not args.init and not args.test:
        # 默认执行：初始化 + 测试
        kb = init_knowledge_base()
        test_retrieval()


if __name__ == "__main__":
    main()
