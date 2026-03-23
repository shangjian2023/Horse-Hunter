"""
LLM API 客户端 - 支持多家国产大模型

支持：
- DeepSeek
- 阿里云通义千问
- 百度文心一言
- 智谱 GLM
- Moonshot (Kimi)
- 零一万物
"""

import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API 配置"""
    api_key: str
    base_url: str
    model: str


class LLMClient:
    """LLM API 客户端"""

    # 预设模型配置
    PRESET_MODELS = {
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'models': ['deepseek-chat', 'deepseek-coder']
        },
        'aliyun': {
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'models': ['qwen-plus', 'qwen-max', 'qwen-turbo']
        },
        'baidu': {
            'base_url': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1',
            'models': ['ernie-4.0', 'ernie-3.5']
        },
        'zhipu': {
            'base_url': 'https://open.bigmodel.cn/api/paas/v4',
            'models': ['glm-4', 'glm-3-turbo']
        },
        'moonshot': {
            'base_url': 'https://api.moonshot.cn/v1',
            'models': ['moonshot-v1-8k', 'moonshot-v1-32k']
        },
        'lingyi': {
            'base_url': 'https://api.lingyiwanwu.com/v1',
            'models': ['yi-large', 'yi-medium']
        }
    }

    def __init__(self, config: Optional[APIConfig] = None):
        """
        初始化客户端

        Args:
            config: API 配置
        """
        self.config = config
        self.session = requests.Session()

    @classmethod
    def from_preset(cls, provider: str, api_key: str, model: str = None) -> 'LLMClient':
        """
        从预设创建客户端

        Args:
            provider: 提供商名称
            api_key: API Key
            model: 模型名称

        Returns:
            LLMClient 实例
        """
        if provider not in cls.PRESET_MODELS:
            raise ValueError(f"未知提供商：{provider}")

        preset = cls.PRESET_MODELS[provider]
        if model is None:
            model = preset['models'][0]

        config = APIConfig(
            api_key=api_key,
            base_url=preset['base_url'],
            model=model
        )

        return cls(config)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "你是一个专业的助手。",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度
            max_tokens: 最大 token 数

        Returns:
            生成的文本
        """
        if not self.config:
            return self._mock_generate(prompt)

        # 构建请求
        url = self._build_api_url()
        headers = self._build_headers()
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens)

        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return self._parse_response(result)
        except requests.exceptions.RequestException as e:
            return f"API 调用失败：{e}"
        except json.JSONDecodeError as e:
            return f"响应解析失败：{e}"

    def _build_api_url(self) -> str:
        """构建 API URL"""
        base = self.config.base_url.rstrip('/')
        if base.endswith('/chat/completions'):
            return base
        return f"{base}/chat/completions"

    def _build_headers(self) -> Dict:
        """构建请求头"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        }

    def _build_payload(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """构建请求体"""
        return {
            'model': self.config.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens
        }

    def _parse_response(self, result: Dict) -> str:
        """解析响应"""
        if 'choices' in result and result['choices']:
            return result['choices'][0].get('message', {}).get('content', '')
        if 'data' in result:
            return str(result['data'])
        return str(result)

    def _mock_generate(self, prompt: str) -> str:
        """模拟生成（无 API 配置时）"""
        # 简单关键词匹配
        if 'SQL' in prompt or 'sql' in prompt.lower():
            return "SELECT company_name, net_profit FROM financial_reports ORDER BY net_profit DESC LIMIT 10"
        return "这是一个模拟响应。请配置 API Key 以获取真实响应。"

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            result = self.generate("请回复'测试成功'以确认 API 正常工作。")
            return '测试成功' in result or '成功' in result
        except Exception:
            return False


def create_client(
    provider: str = 'deepseek',
    api_key: str = None,
    model: str = None
) -> LLMClient:
    """
    创建 LLM 客户端

    Args:
        provider: 提供商
        api_key: API Key
        model: 模型

    Returns:
        LLMClient 实例
    """
    # 从环境变量读取 API Key
    if api_key is None:
        import os
        api_key = os.getenv('LLM_API_KEY', '')

    if not api_key:
        # 返回无配置的客户端（模拟模式）
        return LLMClient()

    return LLMClient.from_preset(provider, api_key, model)


# 导出
__all__ = ['LLMClient', 'APIConfig', 'create_client']
