"""
多路径推理与投票 (Multi-Path Voting)
生成多条推理路径，通过投票或加权聚合得到最终答案
"""

import re
from typing import List, Dict, Any, Optional
from collections import Counter
from dataclasses import dataclass, field

from .base import ReasoningResult
from ..llm.client import LLMClient
from ..config import Config


@dataclass
class ReasoningPath:
    """单条推理路径"""
    id: int
    answer: str
    reasoning: str
    temperature: float
    confidence: float = 0.0
    vote_weight: float = 1.0


class VotingResult(ReasoningResult):
    """投票推理结果"""
    def __init__(self, question: str, answer: str, paths: List[ReasoningPath],
                 voting_method: str, vote_counts: Dict = None, **kwargs):
        super().__init__(
            question=question, answer=answer, method="multi_path_voting",
            reasoning_steps=[p.answer for p in paths], **kwargs
        )
        self.paths = paths
        self.voting_method = voting_method
        self.vote_counts = vote_counts or {}


class MultiPathVoting:
    """多路径推理与投票器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        mp_config = self.config.reasoning['multi_path_voting']
        self.num_paths = mp_config['num_paths']
        self.voting_method = mp_config['voting_method']
        self.temperature_variation = mp_config['temperature_variation']

    def reason(self, question: str, num_paths: int = None,
               voting_method: str = None, verbose: bool = False) -> VotingResult:
        """
        执行多路径推理与投票

        Args:
            question: 问题
            num_paths: 推理路径数量
            voting_method: 投票方法 (majority / weighted / bayesian)
            verbose: 是否打印过程

        Returns:
            VotingResult 投票结果
        """
        num_paths = num_paths or self.num_paths
        voting_method = voting_method or self.voting_method

        if verbose:
            print(f"多路径推理: {num_paths} 条路径, 投票方法: {voting_method}")

        # 1. 生成多条推理路径
        paths = []
        base_temperature = self.llm.temperature

        for i in range(num_paths):
            # 不同路径使用不同温度
            temp_variation = (i - num_paths / 2) * self.temperature_variation
            temperature = max(0.1, min(1.5, base_temperature + temp_variation))

            if verbose:
                print(f"\n路径 {i+1}/{num_paths} (temperature={temperature:.2f}):")

            answer, reasoning = self._generate_path(question, temperature)

            path = ReasoningPath(
                id=i,
                answer=answer,
                reasoning=reasoning,
                temperature=temperature
            )
            paths.append(path)

            if verbose:
                print(f"  答案: {answer[:80]}...")

        # 2. 评估每条路径的置信度
        for path in paths:
            path.confidence = self._evaluate_confidence(question, path.answer)
            # 加权投票：置信度高的路径权重更大
            path.vote_weight = path.confidence

        # 3. 投票聚合
        if voting_method == "majority":
            final_answer, vote_counts = self._majority_vote(paths)
        elif voting_method == "weighted":
            final_answer, vote_counts = self._weighted_vote(paths)
        elif voting_method == "bayesian":
            final_answer, vote_counts = self._bayesian_vote(paths)
        else:
            final_answer, vote_counts = self._majority_vote(paths)

        # 4. 计算整体置信度
        if vote_counts:
            max_votes = max(vote_counts.values())
            total_votes = sum(vote_counts.values())
            overall_confidence = max_votes / total_votes if total_votes > 0 else 0.5
        else:
            overall_confidence = 0.5

        if verbose:
            print(f"\n投票结果: {final_answer[:80]}...")
            print(f"投票统计: {vote_counts}")
            print(f"整体置信度: {overall_confidence:.2f}")

        return VotingResult(
            question=question,
            answer=final_answer,
            paths=paths,
            voting_method=voting_method,
            vote_counts=vote_counts,
            confidence=overall_confidence,
            metadata={
                "num_paths": num_paths,
                "voting_method": voting_method,
                "path_confidences": [p.confidence for p in paths],
                "model": self.llm.model,
            }
        )

    def _generate_path(self, question: str, temperature: float) -> tuple:
        """生成单条推理路径"""
        system_prompt = "你是一位善于独立思考的推理专家。请给出你的推理过程和最终答案。"

        user_prompt = f"""请仔细思考以下问题，给出详细的推理过程和最终答案。

问题: {question}

请按以下格式回答:
推理过程:
[你的详细推理]

最终答案:
[你的最终答案]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.llm.chat(messages, temperature=temperature)
        content = response.content

        # 提取推理过程和最终答案
        reasoning = content
        answer = content

        answer_match = re.search(r'最终答案\s*[:：]\s*(.+)', content, re.DOTALL)
        if answer_match:
            answer = answer_match.group(1).strip()
            reasoning = content[:answer_match.start()].strip()

        return answer, reasoning

    def _evaluate_confidence(self, question: str, answer: str) -> float:
        """评估答案的置信度（0-1）"""
        eval_prompt = f"""请评估以下答案的置信度，给出0-1之间的分数。

问题: {question}
答案: {answer}

评估标准:
1. 答案是否正确？
2. 推理是否严密？
3. 是否有不确定的表述？

只输出一个数字（0-1），不要其他内容。"""

        response = self.llm.complete(eval_prompt, temperature=0.1)
        try:
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.5

    def _normalize_answer(self, answer: str) -> str:
        """标准化答案用于投票比较"""
        # 移除空白和标点，转小写
        normalized = re.sub(r'[\s\W_]+', '', answer.lower())
        # 取前100字符作为比较键
        return normalized[:100]

    def _majority_vote(self, paths: List[ReasoningPath]) -> tuple:
        """多数投票"""
        # 按标准化答案分组
        groups = {}
        for path in paths:
            key = self._normalize_answer(path.answer)
            if key not in groups:
                groups[key] = []
            groups[key].append(path)

        # 找出票数最多的组
        max_group = max(groups.values(), key=len)
        final_answer = max_group[0].answer

        # 投票统计
        vote_counts = {self._normalize_answer(p.answer)[:30]: len(g) for g in groups.values()}

        return final_answer, vote_counts

    def _weighted_vote(self, paths: List[ReasoningPath]) -> tuple:
        """加权投票（按置信度加权）"""
        groups = {}
        for path in paths:
            key = self._normalize_answer(path.answer)
            if key not in groups:
                groups[key] = {"paths": [], "total_weight": 0.0}
            groups[key]["paths"].append(path)
            groups[key]["total_weight"] += path.vote_weight

        # 找出权重最大的组
        max_group = max(groups.values(), key=lambda g: g["total_weight"])
        final_answer = max_group["paths"][0].answer

        vote_counts = {k[:30]: v["total_weight"] for k, v in groups.items()}

        return final_answer, vote_counts

    def _bayesian_vote(self, paths: List[ReasoningPath]) -> tuple:
        """贝叶斯投票（考虑先验和似然）"""
        # 简化版：使用置信度作为似然，均匀先验
        return self._weighted_vote(paths)

    def __call__(self, question: str, **kwargs) -> VotingResult:
        return self.reason(question, **kwargs)
