"""
自我反思推理 (Self-Reflection)
生成答案 → 批判 → 改进，迭代优化
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .base import ReasoningResult
from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class ReflectionIteration:
    """单次反思迭代"""
    iteration: int
    answer: str
    critique: str
    improvements: List[str] = field(default_factory=list)
    score: float = 0.0


class ReflectionResult(ReasoningResult):
    """自我反思推理结果"""
    def __init__(self, question: str, answer: str, iterations: List[ReflectionIteration],
                 **kwargs):
        super().__init__(
            question=question, answer=answer, method="self_reflection",
            reasoning_steps=[it.answer for it in iterations], **kwargs
        )
        self.iterations = iterations
        self.final_iteration = iterations[-1] if iterations else None


class SelfReflection:
    """自我反思推理器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.max_iterations = self.config.reasoning['self_reflection']['max_iterations']
        self.improvement_threshold = self.config.reasoning['self_reflection']['improvement_threshold']

    def reason(self, question: str, max_iterations: int = None,
               initial_answer: str = None, verbose: bool = False) -> ReflectionResult:
        """
        执行自我反思推理

        Args:
            question: 问题
            max_iterations: 最大迭代次数
            initial_answer: 可选的初始答案
            verbose: 是否打印迭代过程

        Returns:
            ReflectionResult 推理结果
        """
        max_iterations = max_iterations or self.max_iterations
        iterations = []
        current_answer = initial_answer

        for i in range(1, max_iterations + 1):
            if verbose:
                print(f"\n=== 迭代 {i}/{max_iterations} ===")

            # 1. 生成初始答案（如果没有）
            if current_answer is None:
                current_answer = self._generate_answer(question)
                if verbose:
                    print(f"生成答案: {current_answer[:100]}...")

            # 2. 批判当前答案
            critique = self._critique(question, current_answer)
            if verbose:
                print(f"批判意见: {critique[:100]}...")

            # 3. 评估当前答案质量
            score = self._evaluate(question, current_answer)
            if verbose:
                print(f"质量评分: {score:.2f}")

            # 记录迭代
            iteration = ReflectionIteration(
                iteration=i,
                answer=current_answer,
                critique=critique,
                score=score
            )
            iterations.append(iteration)

            # 4. 如果质量足够高，停止
            if score >= 0.9:
                if verbose:
                    print("质量达标，提前停止")
                break

            # 5. 根据批判改进答案
            improved_answer = self._revise(question, current_answer, critique)
            if verbose:
                print(f"改进答案: {improved_answer[:100]}...")

            # 6. 检查改进幅度
            improvement = self._calculate_improvement(current_answer, improved_answer)
            if improvement < self.improvement_threshold and i > 1:
                if verbose:
                    print(f"改进幅度不足 ({improvement:.3f})，停止迭代")
                current_answer = improved_answer
                break

            current_answer = improved_answer

        # 最终答案取最后一次迭代的答案
        final_answer = iterations[-1].answer if iterations else current_answer

        # 置信度取最后一次评分
        confidence = iterations[-1].score if iterations else 0.5

        return ReflectionResult(
            question=question,
            answer=final_answer,
            iterations=iterations,
            confidence=confidence,
            metadata={
                "num_iterations": len(iterations),
                "max_iterations": max_iterations,
                "final_score": iterations[-1].score if iterations else 0,
                "model": self.llm.model,
            }
        )

    def _generate_answer(self, question: str) -> str:
        """生成初始答案"""
        response = self.llm.complete(
            prompt=f"请回答以下问题，给出详细、准确的答案：\n\n{question}",
            system_prompt="你是一位知识渊博、善于推理的专家。",
            temperature=0.5
        )
        return response.content

    def _critique(self, question: str, answer: str) -> str:
        """批判答案"""
        prompt = PromptLibrary.get("SELF_REFLECTION_CRITIQUE").format(
            question=question, answer=answer
        )
        response = self.llm.complete(prompt, temperature=0.3)
        return response.content

    def _revise(self, question: str, answer: str, critique: str) -> str:
        """改进答案"""
        prompt = PromptLibrary.get("SELF_REFLECTION_REVISE").format(
            question=question, answer=answer, critique=critique
        )
        response = self.llm.complete(prompt, temperature=0.4)
        return response.content

    def _evaluate(self, question: str, answer: str) -> float:
        """评估答案质量（0-1）"""
        eval_prompt = f"""请评估以下答案的质量，给出0-1之间的分数。

问题: {question}
答案: {answer}

评估维度:
1. 正确性 (40%)
2. 完整性 (25%)
3. 清晰度 (20%)
4. 深度 (15%)

只输出一个数字分数，不要其他内容。"""

        response = self.llm.complete(eval_prompt, temperature=0.1)
        try:
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.5

    def _calculate_improvement(self, old: str, new: str) -> float:
        """计算改进幅度（基于文本差异的简单指标）"""
        if not old:
            return 1.0
        # 简单的字符级差异率
        old_chars = set(old)
        new_chars = set(new)
        if not old_chars:
            return 1.0
        difference = len(new_chars - old_chars) / len(old_chars)
        return min(difference, 1.0)

    def __call__(self, question: str, **kwargs) -> ReflectionResult:
        return self.reason(question, **kwargs)
