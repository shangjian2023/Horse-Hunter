"""
知识库 - 向量存储和检索
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class KnowledgeChunk:
    """知识片段"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'embedding': self.embedding,
            'metadata': self.metadata or {}
        }


class KnowledgeBase:
    """向量知识库"""

    def __init__(self, persist_path: str = 'data/knowledge_base'):
        self.persist_path = persist_path
        self.chunks: List[KnowledgeChunk] = []
        self.index = None
        self.api_key = None
        self.api_base_url = None
        self._load_config()
        self._load_index()

    def _load_config(self):
        """加载配置"""
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.getenv('LLM_API_KEY', '')
        self.api_base_url = os.getenv('LLM_BASE_URL', '')

    def _load_index(self):
        """加载索引"""
        index_file = os.path.join(self.persist_path, 'index.json')
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.chunks = [
                    KnowledgeChunk(
                        id=item['id'],
                        content=item['content'],
                        metadata=item.get('metadata', {})
                    )
                    for item in data
                ]

    def _save_index(self):
        """保存索引"""
        os.makedirs(self.persist_path, exist_ok=True)
        index_file = os.path.join(self.persist_path, 'index.json')

        data = [chunk.to_dict() for chunk in self.chunks]
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_documents(self, documents: List[Dict], batch_size: int = 10) -> int:
        """
        添加文档到知识库

        Args:
            documents: 文档列表，每个文档包含 id, content, metadata
            batch_size: 批量处理大小

        Returns:
            添加的文档数量
        """
        added_count = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            for doc in batch:
                chunk = KnowledgeChunk(
                    id=doc.get('id', self._generate_id(doc['content'])),
                    content=doc['content'],
                    metadata=doc.get('metadata', {})
                )
                self.chunks.append(chunk)
                added_count += 1

            # 每批保存一次
            self._save_index()

        return added_count

    def _generate_id(self, content: str) -> str:
        """生成唯一 ID"""
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索相关知识片段

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关知识片段列表
        """
        if not self.chunks:
            return []

        # 使用语义相似度搜索
        results = self._semantic_search(query, top_k)

        # 如果没有语义搜索条件，使用关键词匹配
        if not results:
            results = self._keyword_search(query, top_k)

        return results

    def _semantic_search(self, query: str, top_k: int) -> List[Dict]:
        """语义搜索（需要 embedding）"""
        if not self.api_key:
            return []

        try:
            # 获取查询的 embedding
            query_embedding = self._get_embedding(query)

            if not query_embedding:
                return []

            # 计算余弦相似度
            scored_chunks = []
            for chunk in self.chunks:
                if chunk.embedding:
                    score = self._cosine_similarity(query_embedding, chunk.embedding)
                    scored_chunks.append((score, chunk))

            # 排序并返回 top_k
            scored_chunks.sort(key=lambda x: x[0], reverse=True)

            return [
                {
                    'id': chunk.id,
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'score': float(score)
                }
                for score, chunk in scored_chunks[:top_k]
            ]

        except Exception as e:
            print(f"语义搜索失败：{e}")
            return []

    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """关键词搜索"""
        query_terms = query.lower().split()

        scored_chunks = []
        for chunk in self.chunks:
            content_lower = chunk.content.lower()
            score = sum(1 for term in query_terms if term in content_lower)

            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                'id': chunk.id,
                'content': chunk.content,
                'metadata': chunk.metadata,
                'score': float(score)
            }
            for score, chunk in scored_chunks[:top_k]
        ]

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本 embedding"""
        if not self.api_key:
            return None

        import requests

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'text-embedding-v3',
            'input': text[:2000]  # 限制长度
        }

        try:
            response = requests.post(
                self.api_base_url + '/embeddings',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['embedding']

        except Exception as e:
            print(f"获取 embedding 失败：{e}")

        return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        return {
            'total_chunks': len(self.chunks),
            'sources': list(set(chunk.metadata.get('source', 'unknown') for chunk in self.chunks)),
            'persist_path': self.persist_path
        }

    def clear(self):
        """清空知识库"""
        self.chunks = []
        if os.path.exists(self.persist_path):
            index_file = os.path.join(self.persist_path, 'index.json')
            if os.path.exists(index_file):
                os.remove(index_file)
