"""
投票与聚合算法
多数投票、加权投票、贝叶斯投票、排名聚合
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import math


@dataclass
class Vote:
    """投票"""
    voter_id: str
    choice: Any
    weight: float = 1.0
    confidence: float = 1.0
    ranking: List[Any] = field(default_factory=list)  # 排名（可选）


@dataclass
class VotingResult:
    """投票结果"""
    winner: Any
    vote_counts: Dict[Any, float]
    method: str
    total_votes: int
    margin: float = 0.0  # 领先优势

    def to_dict(self) -> Dict:
        return {
            "winner": self.winner,
            "vote_counts": self.vote_counts,
            "method": self.method,
            "total_votes": self.total_votes,
            "margin": self.margin,
        }


class MajorityVote:
    """
    多数投票

    用法:
        votes = [Vote("v1", "A"), Vote("v2", "A"), Vote("v3", "B")]
        result = MajorityVote().vote(votes)
        print(result.winner)  # "A"
    """

    def vote(self, votes: List[Vote]) -> VotingResult:
        """执行多数投票"""
        counter = Counter()
        for vote in votes:
            counter[vote.choice] += 1

        winner, count = counter.most_common(1)[0]
        total = sum(counter.values())

        # 计算领先优势
        if len(counter) > 1:
            second = counter.most_common(2)[1][1]
            margin = (count - second) / total
        else:
            margin = 1.0

        return VotingResult(
            winner=winner,
            vote_counts=dict(counter),
            method="majority",
            total_votes=total,
            margin=margin,
        )


class WeightedVote:
    """
    加权投票

    用法:
        votes = [Vote("v1", "A", weight=0.8), Vote("v2", "B", weight=1.2)]
        result = WeightedVote().vote(votes)
    """

    def __init__(self, use_confidence: bool = False):
        """
        Args:
            use_confidence: 是否使用置信度作为权重
        """
        self.use_confidence = use_confidence

    def vote(self, votes: List[Vote]) -> VotingResult:
        """执行加权投票"""
        scores = defaultdict(float)

        for vote in votes:
            weight = vote.weight
            if self.use_confidence:
                weight *= vote.confidence
            scores[vote.choice] += weight

        winner = max(scores.items(), key=lambda x: x[1])[0]
        total = sum(scores.values())

        # 计算领先优势
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            margin = (sorted_scores[0] - sorted_scores[1]) / total if total > 0 else 0
        else:
            margin = 1.0

        return VotingResult(
            winner=winner,
            vote_counts=dict(scores),
            method="weighted",
            total_votes=len(votes),
            margin=margin,
        )


class BayesianVote:
    """
    贝叶斯投票

    将每个投票者的选择视为证据，通过贝叶斯更新计算各选项的后验概率
    """

    def __init__(self, prior: Dict[Any, float] = None,
                 reliability: float = 0.7):
        """
        Args:
            prior: 各选项的先验概率（可选，默认均匀分布）
            reliability: 投票者的平均可靠性 (0-1)
        """
        self.prior = prior
        self.reliability = reliability

    def vote(self, votes: List[Vote], choices: List[Any] = None) -> VotingResult:
        """执行贝叶斯投票"""
        # 确定所有选项
        if choices is None:
            choices = list(set(v.choice for v in votes))

        # 初始化先验
        if self.prior:
            posteriors = dict(self.prior)
        else:
            posteriors = {c: 1.0 / len(choices) for c in choices}

        # 逐个投票者更新
        for vote in votes:
            reliability = self.reliability * vote.confidence

            # 计算证据概率
            p_evidence = sum(
                (reliability if c == vote.choice else (1 - reliability) / (len(choices) - 1))
                * posteriors[c]
                for c in choices
            )

            if p_evidence == 0:
                continue

            # 更新后验
            new_posteriors = {}
            for c in choices:
                likelihood = reliability if c == vote.choice else (1 - reliability) / (len(choices) - 1)
                new_posteriors[c] = (likelihood * posteriors[c]) / p_evidence

            posteriors = new_posteriors

        # 归一化
        total = sum(posteriors.values())
        if total > 0:
            posteriors = {k: v / total for k, v in posteriors.items()}

        winner = max(posteriors.items(), key=lambda x: x[1])[0]

        # 计算领先优势
        sorted_probs = sorted(posteriors.values(), reverse=True)
        margin = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 1.0

        return VotingResult(
            winner=winner,
            vote_counts=posteriors,
            method="bayesian",
            total_votes=len(votes),
            margin=margin,
        )


class VotingEngine:
    """
    投票引擎（统一接口）

    用法:
        engine = VotingEngine(method="weighted")
        result = engine.vote(votes)
    """

    METHODS = {
        "majority": MajorityVote,
        "weighted": WeightedVote,
        "bayesian": BayesianVote,
    }

    def __init__(self, method: str = "majority", **kwargs):
        """
        Args:
            method: 投票方法 (majority / weighted / bayesian)
            **kwargs: 传递给具体投票器的参数
        """
        if method not in self.METHODS:
            raise ValueError(f"不支持的投票方法: {method}，支持: {list(self.METHODS.keys())}")

        self.method = method
        self.voter = self.METHODS[method](**kwargs)

    def vote(self, votes: List[Vote], **kwargs) -> VotingResult:
        """执行投票"""
        return self.voter.vote(votes, **kwargs)

    @classmethod
    def compare_methods(cls, votes: List[Vote], methods: List[str] = None) -> Dict[str, VotingResult]:
        """
        比较多种投票方法的结果

        Args:
            votes: 投票列表
            methods: 要比较的方法列表（默认全部）

        Returns:
            {方法名: 投票结果}
        """
        methods = methods or list(cls.METHODS.keys())
        results = {}

        for method in methods:
            try:
                engine = cls(method=method)
                results[method] = engine.vote(votes)
            except Exception as e:
                results[method] = VotingResult(
                    winner=None, vote_counts={}, method=method,
                    total_votes=len(votes), margin=0.0
                )

        return results


def rank_aggregation(rankings: List[List[Any]], method: str = "borda") -> List[Any]:
    """
    排名聚合

    Args:
        rankings: 排名列表的列表（每个列表是从最好到最差的排序）
        method: 聚合方法 (borda / copeland)

    Returns:
        聚合后的排名
    """
    if not rankings:
        return []

    all_items = list(set(item for ranking in rankings for item in ranking))

    if method == "borda":
        # Borda计数：每个排名位置得分
        scores = defaultdict(float)
        for ranking in rankings:
            n = len(ranking)
            for i, item in enumerate(ranking):
                scores[item] += (n - i)

        return sorted(all_items, key=lambda x: scores[x], reverse=True)

    elif method == "copeland":
        # Copeland方法：两两比较
        scores = defaultdict(int)
        for i, item1 in enumerate(all_items):
            for item2 in all_items[i+1:]:
                wins = 0
                for ranking in rankings:
                    if item1 in ranking and item2 in ranking:
                        if ranking.index(item1) < ranking.index(item2):
                            wins += 1
                        else:
                            wins -= 1
                if wins > 0:
                    scores[item1] += 1
                    scores[item2] -= 1
                elif wins < 0:
                    scores[item1] -= 1
                    scores[item2] += 1

        return sorted(all_items, key=lambda x: scores[x], reverse=True)

    else:
        raise ValueError(f"不支持的排名聚合方法: {method}")
