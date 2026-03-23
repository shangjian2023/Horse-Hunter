"""
对话管理器 - 管理多轮对话上下文
"""

from typing import List, Dict, Optional
from datetime import datetime


class ConversationManager:
    """对话上下文管理器"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.sessions: Dict[str, Dict] = {}
        self.current_session_id: Optional[str] = None

    def create_session(self, session_id: str) -> Dict:
        """创建新对话会话"""
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now(),
            'messages': [],
            'context': {}
        }
        self.current_session_id = session_id
        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取对话会话"""
        return self.sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str,
                    metadata: Optional[Dict] = None) -> None:
        """添加消息到对话历史"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }

        session = self.sessions[session_id]
        session['messages'].append(message)

        # 限制历史记录长度
        if len(session['messages']) > self.max_history:
            session['messages'] = session['messages'][-self.max_history:]

    def get_context(self, session_id: str) -> List[Dict]:
        """获取对话上下文"""
        session = self.sessions.get(session_id)
        if not session:
            return []

        # 返回最近的消息历史，用于 LLM 上下文
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in session['messages'][-self.max_history:]
        ]

    def update_context(self, session_id: str, context: Dict) -> None:
        """更新对话上下文"""
        if session_id not in self.sessions:
            self.create_session(session_id)

        self.sessions[session_id]['context'].update(context)

    def get_context_value(self, session_id: str, key: str, default=None):
        """获取上下文中的值"""
        session = self.sessions.get(session_id)
        if not session:
            return default
        return session['context'].get(key, default)

    def clear_session(self, session_id: str) -> None:
        """清空会话"""
        if session_id in self.sessions:
            self.sessions[session_id] = {
                'id': session_id,
                'created_at': datetime.now(),
                'messages': [],
                'context': {}
            }

    def delete_session(self, session_id: str) -> None:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_last_question(self, session_id: str) -> Optional[str]:
        """获取最后一个用户问题"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        for msg in reversed(session['messages']):
            if msg['role'] == 'user':
                return msg['content']

        return None

    def get_last_sql(self, session_id: str) -> Optional[str]:
        """获取最后生成的 SQL"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        for msg in reversed(session['messages']):
            if msg['role'] == 'assistant' and 'sql' in msg.get('metadata', {}):
                return msg['metadata']['sql']

        return None

    def list_sessions(self) -> List[str]:
        """列出所有会话 ID"""
        return list(self.sessions.keys())

    def export_session(self, session_id: str) -> Dict:
        """导出会话历史"""
        session = self.sessions.get(session_id)
        if not session:
            return {}

        return {
            'id': session['id'],
            'created_at': session['created_at'].isoformat(),
            'messages': [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'metadata': msg['metadata']
                }
                for msg in session['messages']
            ]
        }
