"""
检索器 - 整合 RAG 检索和回答生成
"""

from typing import List, Dict, Optional, Any
from .knowledge_base import KnowledgeBase
from .document_loader import DocumentLoader


class Retriever:
    """RAG 检索器"""

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.kb = knowledge_base or KnowledgeBase()
        self.doc_loader = DocumentLoader()
        self.api_key = None
        self.api_base_url = None
        self._load_config()

    def _load_config(self):
        """加载配置"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.getenv('ANTHROPIC_AUTH_TOKEN', '')
        self.api_base_url = os.getenv('ANTHROPIC_BASE_URL', '')

    def load_knowledge_directory(self, directory: str) -> Dict:
        """
        加载目录下的知识文档

        Args:
            directory: 文档目录路径

        Returns:
            加载统计信息
        """
        chunks = self.doc_loader.load_and_chunk(directory)

        # 过滤掉太短的 chunk
        valid_chunks = [c for c in chunks if len(c['content']) > 50]

        added = self.kb.add_documents(valid_chunks)

        return {
            'total_files': len(chunks),
            'valid_chunks': len(valid_chunks),
            'added_to_kb': added
        }

    def retrieve_and_answer(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        检索相关知识并生成回答

        Args:
            question: 用户问题
            top_k: 检索的文档数量

        Returns:
            包含回答、引用来源的字典
        """
        # 检索相关知识
        retrieved = self.kb.search(question, top_k)

        if not retrieved:
            return {
                'answer': '抱歉，知识库中没有相关信息。',
                'references': [],
                'has_knowledge': False
            }

        # 构建上下文
        context = self._build_context(retrieved)

        # 生成回答
        answer = self._generate_answer(question, context)

        # 构建引用
        references = [
            {
                'source': doc.get('metadata', {}).get('source', '未知来源'),
                'content': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                'score': doc.get('score', 0)
            }
            for doc in retrieved
        ]

        return {
            'answer': answer,
            'references': references,
            'has_knowledge': True,
            'retrieved_count': len(retrieved)
        }

    def _build_context(self, retrieved: List[Dict]) -> str:
        """构建上下文"""
        context_parts = ["以下是相关知识库中的信息：\n"]

        for i, doc in enumerate(retrieved, 1):
            source = doc.get('metadata', {}).get('source', '未知来源')
            page = doc.get('metadata', {}).get('page', '')
            context_parts.append(
                f"[{i}] 来源：{source}" + (f" 第{page}页" if page else "") +
                f"\n{doc['content']}\n"
            )

        return '\n'.join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """生成回答"""
        system_prompt = """你是一个专业的问答助手。请根据提供的知识库信息回答用户问题。

要求：
1. 只基于提供的知识库信息回答，不要编造
2. 如果知识库信息不足以回答问题，如实告知
3. 回答要简洁准确
4. 必要时引用来源"""

        user_prompt = f"""{context}

用户问题：{question}

请根据以上知识库信息回答问题。"""

        return self._call_llm(system_prompt, user_prompt)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 生成回答"""
        if not self.api_key:
            return "API 未配置，无法生成回答"

        import requests

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'qwen-plus',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }

        try:
            response = requests.post(
                self.api_base_url + '/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            if 'choices' in response.json():
                return response.json()['choices'][0]['message']['content']
            else:
                return "无法生成回答"

        except Exception as e:
            return f"生成回答失败：{str(e)}"

    def multi_hop_retrieval(self, question: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        多跳推理检索

        Args:
            question: 用户问题
            max_hops: 最大推理跳数

        Returns:
            包含推理过程和回答的字典
        """
        reasoning_chain = []
        current_question = question

        for hop in range(max_hops):
            # 检索
            retrieved = self.kb.search(current_question, top_k=2)

            if not retrieved:
                break

            reasoning_chain.append({
                'hop': hop + 1,
                'question': current_question,
                'retrieved': [
                    {
                        'source': doc.get('metadata', {}).get('source'),
                        'content': doc['content'][:150]
                    }
                    for doc in retrieved
                ]
            })

            # 判断是否需要继续推理
            if self._should_continue_reasoning(retrieved, question):
                # 生成下一步问题
                current_question = self._generate_next_question(
                    question, retrieved
                )
            else:
                break

        # 生成最终回答
        all_context = []
        for step in reasoning_chain:
            for r in step['retrieved']:
                all_context.append({'content': r['content'], 'metadata': {}})

        answer = self._synthesize_answer(question, all_context)

        return {
            'answer': answer,
            'reasoning_chain': reasoning_chain,
            'total_hops': len(reasoning_chain)
        }

    def _should_continue_reasoning(self, retrieved: List[Dict], original_question: str) -> bool:
        """判断是否需要继续推理"""
        # 简单判断：如果检索到的文档相关性不够高，继续检索
        for doc in retrieved:
            if doc.get('score', 0) < 0.7:
                return True
        return False

    def _generate_next_question(self, original_question: str, retrieved: List[Dict]) -> str:
        """生成下一步检索问题"""
        prompt = f"""基于已检索到的信息，为了更好回答原始问题，下一步应该检索什么信息？

原始问题：{original_question}

已检索信息：
{chr(10).join([doc['content'][:100] for doc in retrieved])}

请生成一个更具体的检索问题："""

        return self._call_llm("", prompt)

    def _synthesize_answer(self, question: str, context: List[Dict]) -> str:
        """综合所有信息生成最终回答"""
        context_text = '\n'.join([doc['content'] for doc in context[:5]])

        return self._generate_answer(question, context_text)
