#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助商标审查分析

使用LLM进行深度语义分析，提升审查准确性
"""

import os
from typing import Dict, List, Optional
import json


class AITrademarkAnalyzer:
    """AI辅助商标分析器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化AI分析器

        Args:
            config: 配置字典，包含api_provider、api_key等
        """
        self.config = config or {}
        # 兼容历史键名（enable_ai_analysis/ai_provider/ai_model）与
        # config.yaml 现行键名（enabled/provider/model）
        self.enabled = bool(self.config.get(
            "enabled", self.config.get("enable_ai_analysis", False)))
        self.api_provider = (self.config.get("provider")
                             or self.config.get("ai_provider")
                             or "anthropic")
        self.model = (self.config.get("model")
                      or self.config.get("ai_model")
                      or "claude-3-5-sonnet-20241022")

        # 初始化客户端
        self.client = None
        if self.enabled:
            self._init_client()

    def _init_client(self):
        """初始化AI客户端"""
        try:
            if self.api_provider == "anthropic":
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY") or self.config.get("api_key")
                if api_key:
                    self.client = anthropic.Anthropic(api_key=api_key)
            elif self.api_provider == "openai":
                import openai
                api_key = os.getenv("OPENAI_API_KEY") or self.config.get("api_key")
                if api_key:
                    self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            print(f"⚠️  未安装 {self.api_provider} 库，AI分析功能不可用")
            self.enabled = False
        except Exception as e:
            print(f"⚠️  AI客户端初始化失败: {e}")
            self.enabled = False

    def analyze_geographic_name(self, trademark_name: str, geographic_keyword: str,
                                article_ref: str = "") -> Dict:
        """
        AI分析地名是否具有其他含义

        Args:
            trademark_name: 商标名称
            geographic_keyword: 检测到的地名
            article_ref: 条号引用（由调用方从 article_map 取得，本模块不硬编码）

        Returns:
            {
                "has_other_meaning": bool,
                "explanation": str,
                "confidence": float  # 0-1
            }
        """
        if not self.enabled or not self.client:
            return {
                "has_other_meaning": None,
                "explanation": "AI分析未启用",
                "confidence": 0.0
            }

        legal_basis = article_ref or "《商标法》关于县级以上行政区划地名的规定"
        prompt = f"""作为商标法专家，分析商标名称中的地名是否具有其他含义。

商标名称：{trademark_name}
地名：{geographic_keyword}

依据 {legal_basis}：县级以上行政区划的地名不得作为商标，但地名具有其他含义或者作为集体商标、证明商标组成部分的除外。

请判断：
1. "{geographic_keyword}"在"{trademark_name}"中是否有地名以外的含义？
2. 给出你的理由和置信度（0-1）

请以JSON格式回答：
{{
    "has_other_meaning": true/false,
    "explanation": "详细解释",
    "confidence": 0.0-1.0
}}"""

        try:
            if self.api_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            elif self.api_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                content = response.choices[0].message.content

            # 提取JSON
            result = json.loads(content.strip().strip('```json').strip('```').strip())
            return result

        except Exception as e:
            return {
                "has_other_meaning": None,
                "explanation": f"AI分析失败: {e}",
                "confidence": 0.0
            }

    def analyze_distinctiveness(self, trademark_name: str, classes: List[int],
                               basic_issues: List[Dict], article_ref: str = "") -> Dict:
        """
        AI深度分析商标显著性

        Args:
            trademark_name: 商标名称
            classes: 商标类别
            basic_issues: 基础规则检测到的问题

        Returns:
            {
                "ai_assessment": str,  # 低/中/高显著性
                "reasoning": str,
                "suggestions": List[str]
            }
        """
        if not self.enabled or not self.client:
            return {
                "ai_assessment": "未启用AI分析",
                "reasoning": "",
                "suggestions": []
            }

        issues_text = "\n".join([f"- {issue['description']}" for issue in basic_issues]) if basic_issues else "无"

        legal_basis = article_ref or "《商标法》关于显著特征的规定"
        prompt = f"""作为商标法专家，深度分析商标的显著性。

商标名称：{trademark_name}
申请类别：{', '.join(map(str, classes))}

基础规则检测结果：
{issues_text}

依据 {legal_basis}，下列标志不得作为商标注册：
1. 仅有本商品的通用名称、图形、型号的
2. 仅直接表示商品的质量、主要原料、功能、用途、重量、数量及其他特点的
3. 其他缺乏显著特征的

请综合分析：
1. 该商标的显著性等级（低/中/高）
2. 你的理由（考虑独创性、识别性、联想性）
3. 如果显著性不足，给出3条改进建议

以JSON格式回答：
{{
    "ai_assessment": "低/中/高",
    "reasoning": "详细分析",
    "suggestions": ["建议1", "建议2", "建议3"]
}}"""

        try:
            if self.api_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            elif self.api_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )
                content = response.choices[0].message.content

            result = json.loads(content.strip().strip('```json').strip('```').strip())
            return result

        except Exception as e:
            return {
                "ai_assessment": "分析失败",
                "reasoning": str(e),
                "suggestions": []
            }

    def semantic_similarity(self, trademark1: str, trademark2: str) -> Dict:
        """
        AI语义相似度分析（用于近似性判断）

        Args:
            trademark1: 商标1
            trademark2: 商标2

        Returns:
            {
                "similarity_score": float,  # 0-1
                "reasoning": str,
                "confusion_risk": str  # 低/中/高
            }
        """
        if not self.enabled or not self.client:
            return {
                "similarity_score": 0.0,
                "reasoning": "AI分析未启用",
                "confusion_risk": "未知"
            }

        prompt = f"""作为商标法专家，分析两个商标的语义相似度。

商标A：{trademark1}
商标B：{trademark2}

请从以下维度分析：
1. 字形相似度（外观）
2. 读音相似度（发音）
3. 含义相似度（语义）
4. 整体印象相似度

判断：消费者是否容易混淆？混淆风险等级？

以JSON格式回答：
{{
    "similarity_score": 0.0-1.0,
    "reasoning": "详细分析各维度",
    "confusion_risk": "低/中/高"
}}"""

        try:
            if self.api_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=600,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            elif self.api_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=600
                )
                content = response.choices[0].message.content

            result = json.loads(content.strip().strip('```json').strip('```').strip())
            return result

        except Exception as e:
            return {
                "similarity_score": 0.0,
                "reasoning": f"分析失败: {e}",
                "confusion_risk": "未知"
            }

    def generate_alternatives(self, trademark_name: str, issues: List[Dict],
                            classes: List[int]) -> List[str]:
        """
        AI生成修改建议

        Args:
            trademark_name: 原商标名称
            issues: 检测到的所有问题
            classes: 商标类别

        Returns:
            替代方案列表
        """
        if not self.enabled or not self.client:
            return []

        issues_summary = "\n".join([
            f"- {issue.get('description', issue.get('type', ''))}"
            for issue in issues
        ])

        prompt = f"""作为商标顾问，为客户提供商标修改建议。

原商标名称：{trademark_name}
申请类别：{', '.join(map(str, classes))}

存在的问题：
{issues_summary}

请提供5个修改建议，要求：
1. 保留原商标的核心识别要素
2. 规避所有法律风险
3. 保持商业吸引力
4. 易于记忆和传播

以JSON数组格式回答：
["建议1", "建议2", "建议3", "建议4", "建议5"]"""

        try:
            if self.api_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            elif self.api_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                content = response.choices[0].message.content

            result = json.loads(content.strip().strip('```json').strip('```').strip())
            return result if isinstance(result, list) else []

        except Exception as e:
            print(f"⚠️  AI生成建议失败: {e}")
            return []
