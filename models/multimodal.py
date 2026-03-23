"""
多模态处理器 - 处理图片和文档输入
"""

import base64
from typing import Dict, Any, Optional


class MultimodalProcessor:
    """多模态处理器"""

    def __init__(self):
        self.api_base_url = None
        self.api_key = None
        self._load_config()

    def _load_config(self):
        """加载配置"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.api_base_url = os.getenv('LLM_BASE_URL', '')
        self.api_key = os.getenv('LLM_API_KEY', '')

    def analyze_image(self, image_path: str, question: str = "请分析这张图片") -> str:
        """
        分析图片内容

        Args:
            image_path: 图片路径
            question: 用户问题

        Returns:
            图片分析结果
        """
        # 读取并编码图片
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 检测图片类型
        media_type = self._detect_media_type(image_path)

        # 构建多模态请求
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ]

        return self._call_multimodal_api(messages)

    def _detect_media_type(self, path: str) -> str:
        """检测媒体类型"""
        if path.endswith('.png'):
            return 'image/png'
        elif path.endswith('.gif'):
            return 'image/gif'
        elif path.endswith('.webp'):
            return 'image/webp'
        else:
            return 'image/jpeg'

    def _call_multimodal_api(self, messages: list) -> str:
        """调用多模态 API"""
        if not self.api_key:
            return "API 未配置，无法分析图片"

        import requests

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'qwen-vl-plus',
            'messages': messages,
            'max_tokens': 1000
        }

        try:
            response = requests.post(
                self.api_base_url + '/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            if 'choices' in response.json():
                return response.json()['choices'][0]['message']['content']
            else:
                return "无法解析图片内容"

        except Exception as e:
            return f"图片分析失败：{str(e)}"

    def extract_table_from_image(self, image_path: str) -> Dict[str, Any]:
        """从图片中提取表格数据"""
        question = "请提取图片中的表格数据，以 JSON 格式返回，包含表头和数据行"

        result = self.analyze_image(image_path, question)

        # 尝试解析 JSON
        import json
        import re

        # 提取 JSON 部分
        json_match = re.search(r'\{.*\}|\[.*\]', result, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {'success': True, 'data': data}
            except:
                pass

        return {'success': False, 'raw': result}

    def analyze_financial_chart(self, image_path: str) -> Dict[str, Any]:
        """分析财务图表"""
        question = """请分析这张财务图表，提取以下信息：
1. 图表类型（折线图、柱状图、饼图等）
2. 时间范围
3. 涉及的公司或指标
4. 关键数据点和趋势
5. 以 JSON 格式返回结果"""

        result = self.analyze_image(image_path, question)

        return {'success': True, 'analysis': result}
