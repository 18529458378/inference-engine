"""
算法层单元测试
MCTS / HTN Planner / Bayesian / Voting
"""

import pytest
import math
from src.algorithms import (
    MCTS, MCTSNode,
    HTNPlanner, Task, DecompositionMethod,
    BayesianInference, BayesianUpdater,
    bayesian_average, calibrate_probability,
    VotingEngine, Vote, MajorityVote, WeightedVote, BayesianVote,
    rank_aggregation,
)


# ========== MCTS 测试 ==========

class TestMCTSNode:
    """MCTS节点测试"""

    def test_node_creation(self):
        node = MCTSNode(state="test")
        assert node.state == "test"
        assert node.visits == 0
        assert node.value == 0.0
        assert node.children == []
        assert node.parent is None

    def test_is_fully_expanded(self):
        node = MCTSNode(state="test", untried_actions=[])
        assert node.is_fully_expanded is True

        node2 = MCTSNode(state="test", untried_actions=["a", "b"])
        assert node2.is_fully_expanded is False

    def test_uct_value_unvisited(self):
        parent = MCTSNode(state="parent", visits=10)
        child = MCTSNode(state="child", parent=parent, visits=0)
        assert child.uct_value() == float('inf')

    def test_uct_value_visited(self):
        parent = MCTSNode(state="parent", visits=100)
        child = MCTSNode(state="child", parent=parent, visits=10, value=8.0)
        uct = child.uct_value(exploration_constant=1.414)
        # exploitation = 8/10 = 0.8
        # exploration = 1.414 * sqrt(log(100)/10)
        expected = 0.8 + 1.414 * math.sqrt(math.log(100) / 10)
        assert abs(uct - expected) < 0.001

    def test_best_child(self):
        parent = MCTSNode(state="parent", visits=100)
        # 相同访问次数，child2价值更高 → UCT更高
        child1 = MCTSNode(state="c1", parent=parent, visits=20, value=5.0)
        child2 = MCTSNode(state="c2", parent=parent, visits=20, value=18.0)
        parent.children = [child1, child2]
        assert parent.best_child() == child2

    def test_most_visited_child(self):
        parent = MCTSNode(state="parent")
        child1 = MCTSNode(state="c1", visits=5)
        child2 = MCTSNode(state="c2", visits=15)
        parent.children = [child1, child2]
        assert parent.most_visited_child() == child2


class TestMCTS:
    """MCTS搜索测试"""

    @pytest.fixture
    def simple_game(self):
        """简单的21点游戏：从0开始，每次加1-3，先到21者输"""
        def get_actions(state):
            return [1, 2, 3]

        def take_action(state, action):
            return state + action

        def is_terminal(state):
            return state >= 21

        def evaluate(state):
            # 状态越接近21但不超过，价值越高
            if state >= 21:
                return 0.0
            return 1.0 - (state / 21.0)

        return get_actions, take_action, is_terminal, evaluate

    def test_mcts_search_returns_action(self, simple_game):
        get_actions, take_action, is_terminal, evaluate = simple_game
        mcts = MCTS(get_actions, take_action, is_terminal, evaluate)
        action = mcts.search(initial_state=0, iterations=100)
        assert action in [1, 2, 3]

    def test_mcts_search_terminal_state(self, simple_game):
        get_actions, take_action, is_terminal, evaluate = simple_game
        mcts = MCTS(get_actions, take_action, is_terminal, evaluate)
        # 从终止状态开始，应该返回None
        action = mcts.search(initial_state=21, iterations=10)
        assert action is None

    def test_mcts_get_action_stats(self, simple_game):
        get_actions, take_action, is_terminal, evaluate = simple_game
        mcts = MCTS(get_actions, take_action, is_terminal, evaluate)
        stats = mcts.get_action_stats(initial_state=0, iterations=100)
        assert isinstance(stats, dict)
        assert all(action in stats for action in [1, 2, 3])
        for action, stat in stats.items():
            assert "visits" in stat
            assert "value" in stat
            assert "win_rate" in stat
            assert 0 <= stat["win_rate"] <= 1

    def test_mcts_backpropagation(self, simple_game):
        get_actions, take_action, is_terminal, evaluate = simple_game
        mcts = MCTS(get_actions, take_action, is_terminal, evaluate)

        root = MCTSNode(state=0, untried_actions=[1, 2, 3])
        child = MCTSNode(state=1, parent=root)
        root.children.append(child)

        mcts._backpropagate(child, 0.8)

        assert child.visits == 1
        assert child.value == 0.8
        assert root.visits == 1
        assert root.value == 0.8


# ========== HTN Planner 测试 ==========

class TestHTNPlanner:
    """HTN规划器测试"""

    @pytest.fixture
    def simple_planner(self):
        planner = HTNPlanner()

        # 复合任务：做早餐
        planner.add_task(Task(
            name="make_breakfast",
            task_type="compound",
            description="做早餐",
            methods=[DecompositionMethod(
                name="standard",
                subtasks=["toast_bread", "fry_egg", "pour_coffee"]
            )]
        ))

        # 原始任务
        planner.add_task(Task(name="toast_bread", task_type="primitive", description="烤面包"))
        planner.add_task(Task(name="fry_egg", task_type="primitive", description="煎鸡蛋"))
        planner.add_task(Task(name="pour_coffee", task_type="primitive", description="倒咖啡"))

        return planner

    def test_plan_generation(self, simple_planner):
        plan = simple_planner.plan("make_breakfast")
        assert plan.goal == "make_breakfast"
        assert plan.total_steps == 3
        assert len(plan.steps) == 3
        assert plan.steps[0].task_name == "toast_bread"
        assert plan.steps[1].task_name == "fry_egg"
        assert plan.steps[2].task_name == "pour_coffee"

    def test_plan_complexity(self, simple_planner):
        plan = simple_planner.plan("make_breakfast")
        assert plan.estimated_complexity == "low"  # 3步 <= 3

    def test_nested_planning(self):
        """测试嵌套任务分解"""
        planner = HTNPlanner()

        planner.add_task(Task(
            name="build_project",
            task_type="compound",
            methods=[DecompositionMethod(
                name="standard",
                subtasks=["setup", "develop", "test", "deploy"]
            )]
        ))

        planner.add_task(Task(
            name="develop",
            task_type="compound",
            methods=[DecompositionMethod(
                name="standard",
                subtasks=["write_code", "code_review"]
            )]
        ))

        planner.add_task(Task(name="setup", task_type="primitive"))
        planner.add_task(Task(name="write_code", task_type="primitive"))
        planner.add_task(Task(name="code_review", task_type="primitive"))
        planner.add_task(Task(name="test", task_type="primitive"))
        planner.add_task(Task(name="deploy", task_type="primitive"))

        plan = planner.plan("build_project")
        # setup + write_code + code_review + test + deploy = 5
        assert plan.total_steps == 5

    def test_plan_to_dict(self, simple_planner):
        plan = simple_planner.plan("make_breakfast")
        d = plan.to_dict()
        assert "goal" in d
        assert "total_steps" in d
        assert "steps" in d
        assert len(d["steps"]) == 3


# ========== Bayesian 测试 ==========

class TestBayesianInference:
    """贝叶斯推理测试"""

    def test_initialization(self):
        bi = BayesianInference(prior=0.5)
        assert bi.prior == 0.5
        assert bi.posterior == 0.5
        assert bi.confidence == 0.5

    def test_update_with_evidence(self):
        bi = BayesianInference(prior=0.1)
        # 似然0.9，观察到证据
        posterior = bi.update(likelihood=0.9, evidence=True)
        assert posterior > 0.1  # 后验应该大于先验
        assert 0 <= posterior <= 1

    def test_update_without_evidence(self):
        bi = BayesianInference(prior=0.5)
        # 未观察到证据，后验不变
        posterior = bi.update(likelihood=0.9, evidence=False)
        assert posterior == 0.5

    def test_multiple_updates(self):
        bi = BayesianInference(prior=0.01)
        # 疾病检测场景
        bi.update(likelihood=0.95, evidence=True)  # 第一次阳性
        first = bi.posterior
        bi.update(likelihood=0.95, evidence=True)  # 第二次阳性
        second = bi.posterior
        assert second > first  # 多次阳性应该增加置信度

    def test_odds_calculation(self):
        bi = BayesianInference(prior=0.5)
        assert bi.odds == 1.0  # 0.5/(1-0.5) = 1

        bi2 = BayesianInference(prior=0.75)
        assert bi2.odds == 3.0  # 0.75/0.25 = 3

    def test_log_odds(self):
        bi = BayesianInference(prior=0.5)
        assert abs(bi.log_odds) < 0.001  # log(1) = 0

    def test_reset(self):
        bi = BayesianInference(prior=0.3)
        bi.update(likelihood=0.8, evidence=True)
        assert bi.posterior != 0.3
        bi.reset()
        assert bi.posterior == 0.3
        assert len(bi.history) == 0

    def test_get_history(self):
        bi = BayesianInference(prior=0.5)
        bi.update(likelihood=0.8, evidence=True)
        history = bi.get_history()
        assert len(history) == 1
        assert "prior" in history[0]
        assert "likelihood" in history[0]
        assert "posterior" in history[0]


class TestBayesianUpdater:
    """多假设贝叶斯更新器测试"""

    def test_initialization(self):
        hypotheses = {"A": 0.3, "B": 0.5, "C": 0.2}
        updater = BayesianUpdater(hypotheses)
        assert updater.posteriors == hypotheses

    def test_update(self):
        hypotheses = {"A": 0.3, "B": 0.5, "C": 0.2}
        updater = BayesianUpdater(hypotheses)
        likelihoods = {"A": 0.9, "B": 0.5, "C": 0.1}
        posteriors = updater.update(likelihoods)
        assert sum(posteriors.values()) == pytest.approx(1.0, abs=0.01)
        assert posteriors["A"] > 0.3  # A的似然最高，后验应该增加

    def test_best_hypothesis(self):
        hypotheses = {"A": 0.3, "B": 0.5, "C": 0.2}
        updater = BayesianUpdater(hypotheses)
        best, prob = updater.best_hypothesis
        assert best == "B"
        assert prob == 0.5


class TestBayesianUtils:
    """贝叶斯工具函数测试"""

    def test_bayesian_average(self):
        values = [1.0, 2.0, 3.0]
        weights = [1.0, 1.0, 1.0]
        assert bayesian_average(values, weights) == 2.0

        weights2 = [3.0, 0.0, 0.0]
        assert bayesian_average(values, weights2) == 1.0

    def test_bayesian_average_no_weights(self):
        values = [2.0, 4.0, 6.0]
        assert bayesian_average(values) == 4.0

    def test_calibrate_probability(self):
        # 校准因子1.0应该不变
        assert abs(calibrate_probability(0.5, 1.0) - 0.5) < 0.001

        # 校准因子>1应该更自信（向0或1移动）
        calibrated = calibrate_probability(0.7, 2.0)
        assert calibrated > 0.7

        # 边界情况
        assert calibrate_probability(0.0) == 0.0
        assert calibrate_probability(1.0) == 1.0


# ========== Voting 测试 ==========

class TestVoting:
    """投票测试"""

    @pytest.fixture
    def sample_votes(self):
        return [
            Vote("v1", "A", weight=1.0, confidence=0.9),
            Vote("v2", "A", weight=1.0, confidence=0.8),
            Vote("v3", "B", weight=1.0, confidence=0.95),
            Vote("v4", "C", weight=1.0, confidence=0.7),
            Vote("v5", "A", weight=1.0, confidence=0.85),
        ]

    def test_majority_vote(self, sample_votes):
        result = MajorityVote().vote(sample_votes)
        assert result.winner == "A"
        assert result.method == "majority"
        assert result.total_votes == 5
        assert result.vote_counts["A"] == 3

    def test_weighted_vote(self, sample_votes):
        result = WeightedVote().vote(sample_votes)
        assert result.winner == "A"
        assert result.method == "weighted"

    def test_weighted_vote_with_confidence(self, sample_votes):
        engine = WeightedVote(use_confidence=True)
        result = engine.vote(sample_votes)
        assert result.winner == "A"
        # A的加权分应该更高
        assert result.vote_counts["A"] > result.vote_counts["B"]

    def test_bayesian_vote(self, sample_votes):
        result = BayesianVote(prior=None, reliability=0.7).vote(sample_votes)
        assert result.winner == "A"
        assert result.method == "bayesian"
        assert sum(result.vote_counts.values()) == pytest.approx(1.0, abs=0.01)

    def test_voting_engine(self, sample_votes):
        engine = VotingEngine(method="majority")
        result = engine.vote(sample_votes)
        assert result.winner == "A"

    def test_voting_engine_invalid_method(self):
        with pytest.raises(ValueError):
            VotingEngine(method="invalid")

    def test_compare_methods(self, sample_votes):
        results = VotingEngine.compare_methods(sample_votes)
        assert "majority" in results
        assert "weighted" in results
        assert "bayesian" in results
        assert all(r.winner == "A" for r in results.values())

    def test_voting_result_to_dict(self, sample_votes):
        result = MajorityVote().vote(sample_votes)
        d = result.to_dict()
        assert "winner" in d
        assert "vote_counts" in d
        assert "method" in d


class TestRankAggregation:
    """排名聚合测试"""

    def test_borda_count(self):
        rankings = [
            ["A", "B", "C"],
            ["A", "C", "B"],
            ["B", "A", "C"],
        ]
        result = rank_aggregation(rankings, method="borda")
        assert result[0] == "A"  # A应该排名第一

    def test_copeland_method(self):
        rankings = [
            ["A", "B", "C"],
            ["A", "B", "C"],
            ["C", "B", "A"],
        ]
        result = rank_aggregation(rankings, method="copeland")
        assert result[0] in ["A", "B"]  # A或B应该排名第一

    def test_empty_rankings(self):
        assert rank_aggregation([]) == []

    def test_invalid_method(self):
        with pytest.raises(ValueError):
            rank_aggregation([["A", "B"]], method="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
