"""
贝叶斯推理
置信度更新、概率推演、证据融合
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class BayesianState:
    """贝叶斯推理状态"""
    prior: float  # 先验概率 (0-1)
    likelihood: float  # 似然 (0-1)
    evidence: bool  # 是否观察到证据
    posterior: float = 0.0  # 后验概率

    def __post_init__(self):
        self.posterior = self._calculate_posterior()

    def _calculate_posterior(self) -> float:
        """计算后验概率"""
        if not self.evidence:
            return self.prior

        # 贝叶斯定理: P(H|E) = P(E|H) * P(H) / P(E)
        # P(E) = P(E|H)*P(H) + P(E|¬H)*P(¬H)
        p_e = self.likelihood * self.prior + (1 - self.likelihood) * (1 - self.prior)

        if p_e == 0:
            return self.prior

        posterior = (self.likelihood * self.prior) / p_e
        return max(0.0, min(1.0, posterior))


class BayesianInference:
    """
    贝叶斯推理器

    用法:
        bi = BayesianInference(prior=0.5)
        bi.update(likelihood=0.8, evidence=True)
        print(bi.posterior)  # 后验概率
    """

    def __init__(self, prior: float = 0.5):
        """
        初始化贝叶斯推理器

        Args:
            prior: 先验概率 (0-1)
        """
        self.prior = prior
        self.posterior = prior
        self.history: List[BayesianState] = []

    def update(self, likelihood: float, evidence: bool = True) -> float:
        """
        根据新证据更新后验概率

        Args:
            likelihood: 似然 P(E|H)，即假设成立时观察到证据的概率 (0-1)
            evidence: 是否观察到证据

        Returns:
            更新后的后验概率
        """
        state = BayesianState(
            prior=self.posterior,
            likelihood=likelihood,
            evidence=evidence
        )
        self.history.append(state)
        self.posterior = state.posterior
        return self.posterior

    def reset(self, prior: float = None):
        """重置推理器"""
        self.prior = prior if prior is not None else self.prior
        self.posterior = self.prior
        self.history.clear()

    @property
    def confidence(self) -> float:
        """置信度（后验概率）"""
        return self.posterior

    @property
    def odds(self) -> float:
        """几率 (posterior / (1-posterior))"""
        if self.posterior >= 1.0:
            return float('inf')
        if self.posterior <= 0.0:
            return 0.0
        return self.posterior / (1 - self.posterior)

    @property
    def log_odds(self) -> float:
        """对数几率"""
        odds = self.odds
        if odds <= 0:
            return float('-inf')
        return math.log(odds)

    def get_history(self) -> List[Dict]:
        """获取推理历史"""
        return [
            {
                "prior": s.prior,
                "likelihood": s.likelihood,
                "evidence": s.evidence,
                "posterior": s.posterior,
            }
            for s in self.history
        ]


class BayesianUpdater:
    """
    多假设贝叶斯更新器

    用法:
        hypotheses = {"A": 0.3, "B": 0.5, "C": 0.2}
        updater = BayesianUpdater(hypotheses)
        updater.update(likelihoods={"A": 0.9, "B": 0.5, "C": 0.1})
        print(updater.posteriors)
    """

    def __init__(self, hypotheses: Dict[str, float]):
        """
        初始化多假设贝叶斯更新器

        Args:
            hypotheses: {假设名: 先验概率}，概率之和应为1
        """
        self.hypotheses = hypotheses
        self.priors = dict(hypotheses)
        self.posteriors = dict(hypotheses)
        self.history: List[Dict] = []

    def update(self, likelihoods: Dict[str, float]) -> Dict[str, float]:
        """
        根据证据更新所有假设的后验概率

        Args:
            likelihoods: {假设名: P(E|H)}，即各假设下观察到证据的概率

        Returns:
            更新后的后验概率
        """
        # 计算证据的总概率 P(E) = Σ P(E|Hi) * P(Hi)
        p_evidence = sum(
            likelihoods.get(h, 0) * self.posteriors.get(h, 0)
            for h in self.posteriors
        )

        if p_evidence == 0:
            return self.posteriors

        # 更新每个假设的后验概率
        new_posteriors = {}
        for hypothesis in self.posteriors:
            likelihood = likelihoods.get(hypothesis, 0)
            prior = self.posteriors[hypothesis]
            posterior = (likelihood * prior) / p_evidence
            new_posteriors[hypothesis] = posterior

        # 归一化（确保总和为1）
        total = sum(new_posteriors.values())
        if total > 0:
            new_posteriors = {k: v / total for k, v in new_posteriors.items()}

        self.history.append({
            "likelihoods": likelihoods,
            "priors": dict(self.posteriors),
            "posteriors": dict(new_posteriors),
        })

        self.posteriors = new_posteriors
        return self.posteriors

    @property
    def best_hypothesis(self) -> Tuple[str, float]:
        """最可能的假设"""
        best = max(self.posteriors.items(), key=lambda x: x[1])
        return best

    def reset(self):
        """重置"""
        self.posteriors = dict(self.priors)
        self.history.clear()

    def get_history(self) -> List[Dict]:
        """获取更新历史"""
        return self.history


def bayesian_average(values: List[float], weights: List[float] = None) -> float:
    """
    贝叶斯加权平均

    Args:
        values: 数值列表
        weights: 权重列表（可选）

    Returns:
        加权平均值
    """
    if not values:
        return 0.0

    if weights is None:
        weights = [1.0] * len(values)

    if len(weights) != len(values):
        raise ValueError("values和weights长度必须相同")

    total_weight = sum(weights)
    if total_weight == 0:
        return sum(values) / len(values)

    return sum(v * w for v, w in zip(values, weights)) / total_weight


def calibrate_probability(probability: float, calibration_factor: float = 1.0) -> float:
    """
    概率校准（温度缩放）

    Args:
        probability: 原始概率 (0-1)
        calibration_factor: 校准因子（>1更自信，<1更保守）

    Returns:
        校准后的概率
    """
    if probability <= 0:
        return 0.0
    if probability >= 1:
        return 1.0

    # 对数几率空间校准
    log_odds = math.log(probability / (1 - probability))
    calibrated_log_odds = log_odds * calibration_factor

    # 转换回概率
    calibrated = 1 / (1 + math.exp(-calibrated_log_odds))
    return max(0.0, min(1.0, calibrated))
