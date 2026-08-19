"""
置信度评估 (Confidence Estimation)
多种方法评估推理结果的置信度
"""

import re
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..llm.client import LLMClient
from ..config import Config


@dataclass
class ConfidenceResult:
    """置信度评估结果"""
    overall: float
    components: Dict[str, float]
    method: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict:
        return {
            "overall": self.overall,
            "components": self.components,
            "method": self.method,
            "details": self.details,
        }


class ConfidenceEstimator:
    """置信度评估器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.method = self.config.reasoning['confidence']['calibration_method']
        self.num_bootstrap = self.config.reasoning['confidence']['num_bootstrap']

    def estimate(self, question: str, answer: str,
                 reasoning: str = "", method: str = None) -> ConfidenceResult:
        """
        评估答案的置信度

        Args:
            question: 问题
            answer: 答案
            reasoning: 推理过程
            method: 评估方法 (self_evaluation / ensemble / bayesian / linguistic)

        Returns:
            ConfidenceResult 置信度结果
        """
        method = method or self.method

        components = {}

        # 1. 语言特征分析（总是执行，轻量）
        linguistic_conf = self._linguistic_analysis(answer, reasoning)
        components["linguistic"] = linguistic_conf

        # 2. 自我评估
        if method in ["self_evaluation", "ensemble", "bayesian"]:
            self_eval_conf = self._self_evaluation(question, answer, reasoning)
            components["self_evaluation"] = self_eval_conf

        # 3. 集成评估（多次采样）
        if method in ["ensemble", "bayesian"]:
            ensemble_conf = self._ensemble_evaluation(question)
            components["ensemble"] = ensemble_conf

        # 4. 贝叶斯校准
        if method == "bayesian":
            bayesian_conf = self._bayesian_calibration(components)
            components["bayesian"] = bayesian_conf

        # 计算整体置信度
        if method == "linguistic":
            overall = linguistic_conf
        elif method == "self_evaluation":
            overall = (linguistic_conf + components.get("self_evaluation", 0.5)) / 2
        elif method == "ensemble":
            weights = {"linguistic": 0.2, "self_evaluation": 0.3, "ensemble": 0.5}
            overall = sum(components.get(k, 0.5) * w for k, w in weights.items())
        elif method == "bayesian":
            overall = components.get("bayesian", 0.5)
        else:
            overall = sum(components.values()) / len(components) if components else 0.5

        overall = max(0.0, min(1.0, overall))

        return ConfidenceResult(
            overall=overall,
            components=components,
            method=method,
            details={
                "question": question[:100],
                "answer_length": len(answer),
                "reasoning_length": len(reasoning),
            }
        )

    def _linguistic_analysis(self, answer: str, reasoning: str = "") -> float:
        """
        基于语言特征的置信度分析
        分析：不确定性表述、断言强度、信息完整性
        """
        score = 0.7  # 基础分

        text = (answer + " " + reasoning).lower()

        # 不确定性表述（降低置信度）
        uncertainty_phrases = [
            "可能", "也许", "大概", "或许", "不确定", "应该是",
            "可能是", "我猜", "估计", "看样子", "似乎", "好像",
            "maybe", "perhaps", "probably", "possibly", "i think",
            "i guess", "it seems", "likely", "might be", "could be"
        ]
        uncertainty_count = sum(text.count(phrase) for phrase in uncertainty_phrases)
        score -= uncertainty_count * 0.05

        # 确定性表述（提高置信度）
        certainty_phrases = [
            "因此", "所以", "显然", "明显", "确定", "一定",
            "必然", "毫无疑问", "可以肯定", "事实是",
            "therefore", "thus", "clearly", "obviously",
            "definitely", "certainly", "undoubtedly"
        ]
        certainty_count = sum(text.count(phrase) for phrase in certainty_phrases)
        score += certainty_count * 0.03

        # 答案长度（适中的长度更可信）
        answer_len = len(answer)
        if answer_len < 20:
            score -= 0.15  # 太短
        elif answer_len > 2000:
            score -= 0.05  # 太长可能啰嗦
        elif 100 <= answer_len <= 500:
            score += 0.05  # 适中

        # 推理过程存在（提高置信度）
        if reasoning and len(reasoning) > 50:
            score += 0.05

        # 数字和具体信息（提高置信度）
        number_count = len(re.findall(r'\d+', answer))
        score += min(number_count * 0.01, 0.1)

        return max(0.0, min(1.0, score))

    def _self_evaluation(self, question: str, answer: str, reasoning: str = "") -> float:
        """LLM 自我评估置信度"""
        eval_prompt = f"""请作为一个严格的评审专家，评估以下答案的置信度。

问题: {question}

推理过程:
{reasoning or "（无）"}

答案:
{answer}

请从以下维度评估（每个维度0-1分）:
1. 事实准确性: 答案中的事实是否正确？
2. 逻辑严密性: 推理过程是否有漏洞？
3. 完整性: 是否回答了问题的所有方面？
4. 清晰度: 表达是否清晰明确？

最后给出整体置信度（0-1），只输出一个数字。"""

        response = self.llm.complete(eval_prompt, temperature=0.1)

        try:
            # 尝试提取最后一个数字
            numbers = re.findall(r'0?\.\d+|1\.0|1|0', response.content)
            if numbers:
                # 取最后一个数字作为整体置信度
                score = float(numbers[-1])
                return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            pass

        return 0.5

    def _ensemble_evaluation(self, question: str, num_samples: int = None) -> float:
        """
        集成评估：多次生成答案，计算一致性
        一致性越高，置信度越高
        """
        num_samples = num_samples or self.num_bootstrap
        answers = []

        for i in range(num_samples):
            temperature = 0.5 + (i / num_samples) * 0.5  # 温度从0.5到1.0
            response = self.llm.complete(
                prompt=f"请简洁回答以下问题：\n\n{question}",
                temperature=temperature,
                max_tokens=200
            )
            answers.append(response.content.strip())

        # 计算答案一致性（基于文本相似度）
        if len(answers) <= 1:
            return 0.5

        consistency_scores = []
        for i in range(len(answers)):
            for j in range(i + 1, len(answers)):
                similarity = self._text_similarity(answers[i], answers[j])
                consistency_scores.append(similarity)

        avg_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5

        # 一致性映射到置信度
        confidence = 0.3 + avg_consistency * 0.7
        return max(0.0, min(1.0, confidence))

    def _text_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度（Jaccard相似度）"""
        # 分词（简单按字符和空格）
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _bayesian_calibration(self, components: Dict[str, float]) -> float:
        """
        贝叶斯校准
        将多个置信度分量通过贝叶斯方式融合
        """
        if not components:
            return 0.5

        # 简化贝叶斯融合：对数几率加权平均
        log_odds_sum = 0.0
        total_weight = 0.0

        weights = {
            "linguistic": 0.3,
            "self_evaluation": 0.4,
            "ensemble": 0.3,
        }

        for component, value in components.items():
            if component in weights and 0 < value < 1:
                weight = weights[component]
                # 转换为对数几率
                log_odds = math.log(value / (1 - value))
                log_odds_sum += log_odds * weight
                total_weight += weight

        if total_weight == 0:
            return 0.5

        # 平均对数几率
        avg_log_odds = log_odds_sum / total_weight

        # 转换回概率
        probability = 1 / (1 + math.exp(-avg_log_odds))

        return probability
