"""
思维链推理 (Chain-of-Thought)
逐步分解问题，显式展示推理过程
"""

import re
from typing import List, Dict, Any, Optional

from .base import ReasoningResult
from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


class CoTResult(ReasoningResult):
    """思维链推理结果"""
    def __init__(self, question: str, answer: str, steps: List[str],
                 step_details: List[Dict] = None, **kwargs):
        super().__init__(
            question=question, answer=answer, method="chain_of_thought",
            reasoning_steps=steps, **kwargs
        )
        self.step_details = step_details or []


class ChainOfThought:
    """思维链推理器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.max_steps = self.config.reasoning['chain_of_thought']['max_steps']

    def reason(self, question: str, system_prompt: str = None,
               max_steps: int = None, verbose: bool = False) -> CoTResult:
        """
        执行思维链推理

        Args:
            question: 问题
            system_prompt: 可选的系统提示
            max_steps: 最大推理步数
            verbose: 是否打印中间步骤

        Returns:
            CoTResult 推理结果
        """
        max_steps = max_steps or self.max_steps

        # 构建提示词
        prompt = PromptLibrary.get("CHAIN_OF_THOUGHT").format(question=question)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 调用 LLM
        response = self.llm.chat(messages, temperature=0.3)
        raw_answer = response.content

        # 解析推理步骤
        steps, final_answer = self._parse_steps(raw_answer)

        if verbose:
            for i, step in enumerate(steps, 1):
                print(f"步骤 {i}: {step[:100]}...")
            print(f"最终答案: {final_answer[:100]}...")

        # 简单置信度：基于推理步骤的完整性
        confidence = min(0.5 + len(steps) * 0.1, 0.95) if steps else 0.3

        return CoTResult(
            question=question,
            answer=final_answer,
            steps=steps,
            confidence=confidence,
            metadata={
                "raw_response": raw_answer,
                "num_steps": len(steps),
                "max_steps": max_steps,
                "model": self.llm.model,
            }
        )

    def _parse_steps(self, response: str) -> tuple:
        """解析推理步骤和最终答案"""
        steps = []
        final_answer = response

        # 尝试匹配 "步骤N:" 格式
        step_pattern = r'步骤\s*(\d+)\s*[:：]\s*(.+?)(?=\n步骤\s*\d+\s*[:：]|\n最终答案|$)'
        matches = re.findall(step_pattern, response, re.DOTALL)

        if matches:
            for _, step_text in matches:
                cleaned = step_text.strip()
                if cleaned:
                    steps.append(cleaned)

        # 提取最终答案
        answer_match = re.search(r'最终答案\s*[:：]\s*(.+)', response, re.DOTALL)
        if answer_match:
            final_answer = answer_match.group(1).strip()

        # 如果没有解析到步骤，将整个回答作为一步
        if not steps:
            # 尝试按 "---" 分割
            parts = response.split('---')
            if len(parts) > 1:
                steps = [p.strip() for p in parts if p.strip()]
                final_answer = steps[-1] if steps else response
            else:
                steps = [response]
                final_answer = response

        return steps, final_answer

    def __call__(self, question: str, **kwargs) -> CoTResult:
        return self.reason(question, **kwargs)
