"""
统一推理引擎客户端
集成推理增强、代码增强、算法层
"""

from typing import Optional, Dict, Any

from ..config import Config
from ..llm.client import LLMClient
from ..reasoning import (
    ChainOfThought, TreeOfThoughts, SelfReflection,
    PlanAndExecute, MultiPathVoting, ConfidenceEstimator,
    ReActReasoner
)
from ..code_enhancer import (
    CodeReviewer, CodeRefactorer, TestGenerator,
    CodeOptimizer, ComplexityAnalyzer, DocumentGenerator,
    CodeExplainer, CodeConverter
)
from ..algorithms import MCTS, HTNPlanner, BayesianInference, VotingEngine


class InferenceClient:
    """
    统一推理引擎客户端

    用法:
        client = InferenceClient()

        # 推理增强
        result = client.reasoning.chain_of_thought("问题")
        result = client.reasoning.self_reflection("问题")
        result = client.reasoning.tree_of_thoughts("问题")
        result = client.reasoning.plan_and_execute("任务")
        result = client.reasoning.multi_path_voting("问题")

        # 代码增强
        review = client.code.review("path/to/code.py")
        refactored = client.code.refactor("path/to/code.py")
        tests = client.code.generate_tests("path/to/module.py")
        optimized = client.code.optimize("path/to/code.py")
        complexity = client.code.analyze_complexity("path/to/code.py")
        docs = client.code.generate_docs("path/to/code.py")

        # 算法层
        mcts = client.algorithms.mcts(...)
        planner = client.algorithms.planner
        bayes = client.algorithms.bayesian(prior=0.5)
        voting = client.algorithms.voting(method="weighted")
    """

    def __init__(self, config_path: str = None, config: Config = None):
        """
        初始化客户端

        Args:
            config_path: 配置文件路径
            config: 配置对象（优先于config_path）
        """
        self.config = config or Config(config_path)
        self.llm = LLMClient(self.config)

        # 推理增强模块
        self.reasoning = _ReasoningModule(self.llm, self.config)

        # 代码增强模块
        self.code = _CodeEnhancerModule(self.llm, self.config)

        # 算法层
        self.algorithms = _AlgorithmsModule()

    def set_model(self, model: str):
        """切换LLM模型"""
        self.llm.set_model(model)

    def set_temperature(self, temperature: float):
        """设置温度"""
        self.llm.set_temperature(temperature)


class _ReasoningModule:
    """推理增强模块"""

    def __init__(self, llm: LLMClient, config: Config):
        self.llm = llm
        self.config = config

        self._cot = None
        self._tot = None
        self._reflection = None
        self._plan = None
        self._voting = None
        self._confidence = None
        self._react = None

    @property
    def chain_of_thought(self) -> ChainOfThought:
        if self._cot is None:
            self._cot = ChainOfThought(self.llm, self.config)
        return self._cot

    @property
    def tree_of_thoughts(self) -> TreeOfThoughts:
        if self._tot is None:
            self._tot = TreeOfThoughts(self.llm, self.config)
        return self._tot

    @property
    def self_reflection(self) -> SelfReflection:
        if self._reflection is None:
            self._reflection = SelfReflection(self.llm, self.config)
        return self._reflection

    @property
    def plan_and_execute(self) -> PlanAndExecute:
        if self._plan is None:
            self._plan = PlanAndExecute(self.llm, self.config)
        return self._plan

    @property
    def multi_path_voting(self) -> MultiPathVoting:
        if self._voting is None:
            self._voting = MultiPathVoting(self.llm, self.config)
        return self._voting

    @property
    def confidence(self) -> ConfidenceEstimator:
        if self._confidence is None:
            self._confidence = ConfidenceEstimator(self.llm, self.config)
        return self._confidence

    @property
    def react(self) -> ReActReasoner:
        if self._react is None:
            self._react = ReActReasoner(self.llm, self.config)
        return self._react


class _CodeEnhancerModule:
    """代码增强模块"""

    def __init__(self, llm: LLMClient, config: Config):
        self.llm = llm
        self.config = config

        self._reviewer = None
        self._refactorer = None
        self._tester = None
        self._optimizer = None
        self._complexity = None
        self._documenter = None
        self._explainer = None
        self._converter = None

    @property
    def reviewer(self) -> CodeReviewer:
        if self._reviewer is None:
            self._reviewer = CodeReviewer(self.llm, self.config)
        return self._reviewer

    def review(self, filepath: str, **kwargs):
        """审查代码文件"""
        return self.reviewer.review_file(filepath, **kwargs)

    def review_code(self, code: str, filename: str = "code.py", **kwargs):
        """审查代码字符串"""
        return self.reviewer.review_code(code, filename, **kwargs)

    @property
    def refactorer(self) -> CodeRefactorer:
        if self._refactorer is None:
            self._refactorer = CodeRefactorer(self.llm, self.config)
        return self._refactorer

    def refactor(self, filepath: str, **kwargs):
        """重构代码文件"""
        return self.refactorer.refactor_file(filepath, **kwargs)

    @property
    def tester(self) -> TestGenerator:
        if self._tester is None:
            self._tester = TestGenerator(self.llm, self.config)
        return self._tester

    def generate_tests(self, filepath: str, **kwargs):
        """生成测试用例"""
        return self.tester.generate_for_file(filepath, **kwargs)

    @property
    def optimizer(self) -> CodeOptimizer:
        if self._optimizer is None:
            self._optimizer = CodeOptimizer(self.llm, self.config)
        return self._optimizer

    def optimize(self, filepath: str, **kwargs):
        """优化代码性能"""
        return self.optimizer.optimize_file(filepath, **kwargs)

    @property
    def complexity_analyzer(self) -> ComplexityAnalyzer:
        if self._complexity is None:
            self._complexity = ComplexityAnalyzer(self.llm, self.config)
        return self._complexity

    def analyze_complexity(self, filepath: str, **kwargs):
        """分析代码复杂度"""
        return self.complexity_analyzer.analyze_file(filepath, **kwargs)

    @property
    def documenter(self) -> DocumentGenerator:
        if self._documenter is None:
            self._documenter = DocumentGenerator(self.llm, self.config)
        return self._documenter

    def generate_docs(self, filepath: str, **kwargs):
        """生成代码文档"""
        return self.documenter.generate_for_file(filepath, **kwargs)

    @property
    def explainer(self) -> CodeExplainer:
        if self._explainer is None:
            self._explainer = CodeExplainer(self.llm, self.config)
        return self._explainer

    def explain(self, filepath: str, **kwargs):
        """解释代码"""
        return self.explainer.explain_file(filepath, **kwargs)

    @property
    def converter(self) -> CodeConverter:
        if self._converter is None:
            self._converter = CodeConverter(self.llm, self.config)
        return self._converter

    def convert(self, filepath: str, target_language: str, **kwargs):
        """转换代码语言"""
        return self.converter.convert_file(filepath, target_language, **kwargs)


class _AlgorithmsModule:
    """算法层模块"""

    def mcts(self, get_actions, take_action, is_terminal, evaluate, **kwargs) -> MCTS:
        """创建MCTS搜索器"""
        return MCTS(get_actions, take_action, is_terminal, evaluate, **kwargs)

    @property
    def planner(self) -> HTNPlanner:
        """获取HTN规划器"""
        return HTNPlanner()

    def bayesian(self, prior: float = 0.5) -> BayesianInference:
        """创建贝叶斯推理器"""
        return BayesianInference(prior=prior)

    def voting(self, method: str = "majority", **kwargs) -> VotingEngine:
        """创建投票引擎"""
        return VotingEngine(method=method, **kwargs)
