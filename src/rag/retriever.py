"""
RAG - 检索增强生成模块

将附件 5 中的个股和行业研报 PDF 进行向量化处理，搭建 RAG 系统：
- 文档加载与分块
- 向量嵌入
- 相似度检索
- 归因分析（references 字段）
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pickle

import numpy as np


@dataclass
class DocumentChunk:
    """文档分块"""
    chunk_id: str
    content: str
    source_path: str
    page_num: Optional[int] = None
    section_title: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: DocumentChunk
    similarity_score: float
    rank: int


class SimpleVectorStore:
    """简单向量存储（不依赖外部向量数据库）"""

    def __init__(self, embedding_dim: int = 768):
        """
        初始化向量存储

        Args:
            embedding_dim: 向量维度
        """
        self.embedding_dim = embedding_dim
        self.chunks: List[DocumentChunk] = []
        self.vectors: np.ndarray = None

    def add_chunk(self, chunk: DocumentChunk) -> None:
        """添加文档分块"""
        self.chunks.append(chunk)

        # 更新向量矩阵
        if chunk.embedding is not None:
            if self.vectors is None:
                self.vectors = np.array([chunk.embedding])
            else:
                self.vectors = np.vstack([self.vectors, chunk.embedding])

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """批量添加文档分块"""
        embeddings = [c.embedding for c in chunks if c.embedding is not None]
        if embeddings:
            new_vectors = np.array(embeddings)
            if self.vectors is None:
                self.vectors = new_vectors
            else:
                self.vectors = np.vstack([self.vectors, new_vectors])
        self.chunks.extend(chunks)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        相似度检索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if self.vectors is None or len(self.chunks) == 0:
            return []

        # 计算余弦相似度
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        vectors_norm = self.vectors / (np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-8)

        similarities = np.dot(vectors_norm, query_norm)

        # 获取 top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append(RetrievalResult(
                chunk=self.chunks[idx],
                similarity_score=float(similarities[idx]),
                rank=rank
            ))

        return results

    def save(self, path: str) -> None:
        """保存向量存储"""
        data = {
            'chunks': self.chunks,
            'vectors': self.vectors,
            'embedding_dim': self.embedding_dim
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str) -> 'SimpleVectorStore':
        """加载向量存储"""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        store = cls(embedding_dim=data['embedding_dim'])
        store.chunks = data['chunks']
        store.vectors = data['vectors']
        return store


class DocumentLoader:
    """文档加载器 - 支持 PDF 研报加载"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文档加载器

        Args:
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_pdf(self, pdf_path: str) -> List[str]:
        """
        加载 PDF 文件

        Args:
            pdf_path: PDF 文件路径

        Returns:
            文本分块列表
        """
        try:
            import pdfplumber

            chunks = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        # 按页面分块
                        page_chunks = self._split_text(text, page_num, pdf_path)
                        chunks.extend(page_chunks)

            return chunks
        except ImportError:
            # pdfplumber 未安装时返回空
            return []
        except Exception as e:
            print(f"加载 PDF 失败 {pdf_path}: {e}")
            return []

    def load_directory(self, directory: str, pattern: str = '*.pdf') -> List[DocumentChunk]:
        """
        加载目录中的所有 PDF 文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            文档分块列表
        """
        directory = Path(directory)
        if not directory.exists():
            return []

        all_chunks = []
        pdf_files = list(directory.glob(pattern))

        # 递归查找子目录
        for subdirectory in directory.glob('**/*.pdf'):
            if subdirectory not in pdf_files:
                pdf_files.append(subdirectory)

        for pdf_file in pdf_files:
            print(f"加载文档：{pdf_file.name}")
            text_chunks = self.load_pdf(str(pdf_file))

            for text in text_chunks:
                chunk = DocumentChunk(
                    chunk_id=self._generate_chunk_id(str(pdf_file), text),
                    content=text,
                    source_path=str(pdf_file),
                    metadata={
                        'filename': pdf_file.name,
                        'type': self._infer_doc_type(pdf_file.name)
                    }
                )
                all_chunks.append(chunk)

        return all_chunks

    def _split_text(
        self,
        text: str,
        page_num: int,
        source_path: str
    ) -> List[str]:
        """
        分割文本

        Args:
            text: 原始文本
            page_num: 页码
            source_path: 源文件路径

        Returns:
            分块列表
        """
        # 按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _generate_chunk_id(self, source_path: str, content: str) -> str:
        """生成 chunk ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        filename = Path(source_path).stem
        return f"{filename}_{content_hash}"

    def _infer_doc_type(self, filename: str) -> str:
        """推断文档类型"""
        filename_lower = filename.lower()

        if '行业' in filename or '行业' in filename:
            return 'industry_report'
        elif '个股' in filename or '公司' in filename:
            return 'company_report'
        elif '策略' in filename:
            return 'strategy_report'
        else:
            return 'unknown'


class EmbeddingGenerator:
    """嵌入向量生成器"""

    def __init__(self, model_name: str = 'bge-small-zh'):
        """
        初始化嵌入生成器

        Args:
            model_name: 嵌入模型名称
        """
        self.model_name = model_name
        self.model = None

    def load_model(self) -> None:
        """加载嵌入模型"""
        try:
            from FlagEmbedding import FlagModel
            self.model = FlagModel(
                'BAAI/bge-small-zh-v1.5',
                query_instruction_for_retrieval="为这个句子生成表示以用于检索："
            )
        except ImportError:
            print("FlagEmbedding 未安装，使用简单词袋模型作为 fallback")
            self.model = None

    def generate(self, text: str) -> np.ndarray:
        """
        生成文本向量

        Args:
            text: 输入文本

        Returns:
            向量表示
        """
        if self.model is not None:
            try:
                return self.model.encode(text)
            except Exception:
                pass

        # Fallback: 简单词袋模型
        return self._bag_of_words(text)

    def _bag_of_words(self, text: str) -> np.ndarray:
        """词袋模型向量（fallback）"""
        # 简单分词
        words = text.lower().split()

        # 创建 768 维向量（简化实现）
        vector = np.zeros(768)

        # 使用前 768 个词的哈希值填充向量
        for i, word in enumerate(words[:768]):
            vector[i] = hash(word) % 10000 / 10000.0

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector


class RAGRetriever:
    """RAG 检索器"""

    def __init__(
        self,
        knowledge_base_path: str = './data/knowledge_base',
        vector_store_path: str = './data/vector_store.pkl'
    ):
        """
        初始化 RAG 检索器

        Args:
            knowledge_base_path: 知识库路径
            vector_store_path: 向量存储路径
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.vector_store_path = Path(vector_store_path)

        self.document_loader = DocumentLoader()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store: Optional[SimpleVectorStore] = None

        self.initialized = False

    def initialize(self) -> bool:
        """
        初始化 RAG 系统

        Returns:
            是否成功初始化
        """
        # 尝试加载已有向量存储
        if self.vector_store_path.exists():
            print("加载已有向量存储...")
            self.vector_store = SimpleVectorStore.load(str(self.vector_store_path))
            self.initialized = True
            return True

        # 从文档构建向量存储
        if not self.knowledge_base_path.exists():
            print(f"知识库路径不存在：{self.knowledge_base_path}")
            return False

        print("构建向量存储...")
        return self.build_vector_store()

    def build_vector_store(self) -> bool:
        """
        构建向量存储

        Returns:
            是否成功构建
        """
        # 加载文档
        chunks = self.document_loader.load_directory(str(self.knowledge_base_path))

        if not chunks:
            print("未找到任何文档")
            return False

        print(f"加载了 {len(chunks)} 个文档分块")

        # 生成向量
        print("生成向量表示...")
        self.embedding_generator.load_model()

        for chunk in chunks:
            chunk.embedding = self.embedding_generator.generate(chunk.content)

        # 创建向量存储
        self.vector_store = SimpleVectorStore()
        self.vector_store.add_chunks(chunks)

        # 保存到磁盘
        self.vector_store.save(str(self.vector_store_path))

        self.initialized = True
        print("向量存储构建完成")
        return True

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if not self.initialized:
            if not self.initialize():
                return []

        # 生成查询向量
        query_embedding = self.embedding_generator.generate(query)

        # 检索
        results = self.vector_store.search(query_embedding, top_k)

        return results

    def retrieve_and_answer(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict:
        """
        检索并生成答案

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            包含答案和 references 的字典
        """
        # 检索文档
        results = self.retrieve(query, top_k)

        if not results:
            return {
                'answer': '未找到相关文档',
                'references': []
            }

        # 构建 references
        references = []
        context_parts = []

        for result in results:
            ref = {
                'source': result.chunk.source_path,
                'page': result.chunk.page_num,
                'content': result.chunk.content[:200] + '...' if len(result.chunk.content) > 200 else result.chunk.content,
                'similarity': result.similarity_score
            }
            references.append(ref)
            context_parts.append(result.chunk.content)

        # 构建上下文
        context = "\n\n".join(context_parts)

        # 生成答案（这里简化实现，实际应该调用 LLM）
        answer = self._generate_answer(query, context)

        return {
            'answer': answer,
            'references': references
        }

    def _generate_answer(self, query: str, context: str) -> str:
        """
        基于上下文生成答案

        Args:
            query: 查询
            context: 相关文档上下文

        Returns:
            答案
        """
        # 简化实现：直接返回上下文摘要
        # 实际应该调用 LLM 生成

        if not context:
            return "抱歉，未找到相关信息。"

        # 提取关键信息
        context_preview = context[:500] + '...' if len(context) > 500 else context

        return f"根据检索到的资料：\n\n{context_preview}\n\n以上是相关文档内容。"


# 导出公共接口
__all__ = [
    'DocumentChunk',
    'RetrievalResult',
    'SimpleVectorStore',
    'DocumentLoader',
    'EmbeddingGenerator',
    'RAGRetriever'
]
