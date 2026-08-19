"""
蒙特卡洛树搜索 (MCTS)
用于推理路径探索、决策优化、问题求解
"""

import math
import random
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class MCTSNode:
    """MCTS 节点"""
    state: Any
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    untried_actions: List[Any] = field(default_factory=list)
    action_taken: Any = None  # 从父节点到当前节点采取的动作

    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    @property
    def is_terminal(self) -> bool:
        return len(self.children) == 0 and len(self.untried_actions) == 0

    def uct_value(self, exploration_constant: float = 1.414) -> float:
        """UCT (Upper Confidence Bound for Trees) 值"""
        if self.visits == 0:
            return float('inf')

        exploitation = self.value / self.visits
        exploration = exploration_constant * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploitation + exploration

    def best_child(self, exploration_constant: float = 1.414) -> 'MCTSNode':
        """选择UCT值最高的子节点"""
        return max(self.children, key=lambda c: c.uct_value(exploration_constant))

    def most_visited_child(self) -> 'MCTSNode':
        """选择访问次数最多的子节点（最终决策用）"""
        return max(self.children, key=lambda c: c.visits)


class MCTS:
    """
    蒙特卡洛树搜索

    用法:
        def get_actions(state):
            return [...]

        def take_action(state, action):
            return new_state

        def is_terminal(state):
            return True/False

        def evaluate(state):
            return score  # 0-1

        mcts = MCTS(get_actions, take_action, is_terminal, evaluate)
        best_action = mcts.search(initial_state, iterations=1000)
    """

    def __init__(self,
                 get_actions: Callable[[Any], List[Any]],
                 take_action: Callable[[Any, Any], Any],
                 is_terminal: Callable[[Any], bool],
                 evaluate: Callable[[Any], float],
                 exploration_constant: float = 1.414,
                 max_depth: int = 20):
        """
        初始化MCTS

        Args:
            get_actions: 获取当前状态的可用动作
            take_action: 执行动作，返回新状态
            is_terminal: 判断是否为终止状态
            evaluate: 评估状态价值（0-1）
            exploration_constant: 探索常数（默认sqrt(2)）
            max_depth: 最大搜索深度
        """
        self.get_actions = get_actions
        self.take_action = take_action
        self.is_terminal = is_terminal
        self.evaluate = evaluate
        self.exploration_constant = exploration_constant
        self.max_depth = max_depth

    def search(self, initial_state: Any, iterations: int = 1000,
               verbose: bool = False) -> Any:
        """
        执行MCTS搜索

        Args:
            initial_state: 初始状态
            iterations: 迭代次数
            verbose: 是否打印进度

        Returns:
            最优动作
        """
        root = MCTSNode(
            state=initial_state,
            untried_actions=self.get_actions(initial_state)
        )

        for i in range(iterations):
            if verbose and i % 100 == 0:
                print(f"迭代 {i}/{iterations}, 根节点访问次数: {root.visits}")

            # 1. 选择 (Selection)
            node = self._select(root)

            # 2. 扩展 (Expansion)
            if not self.is_terminal(node.state) and not node.is_fully_expanded:
                node = self._expand(node)

            # 3. 模拟 (Simulation)
            value = self._simulate(node.state)

            # 4. 反向传播 (Backpropagation)
            self._backpropagate(node, value)

        # 返回访问次数最多的子节点对应的动作
        if root.children:
            best_child = root.most_visited_child()
            return best_child.action_taken
        return None

    def _select(self, node: MCTSNode) -> MCTSNode:
        """选择阶段：从根节点向下选择UCT值最高的节点"""
        while node.is_fully_expanded and not node.is_terminal:
            node = node.best_child(self.exploration_constant)
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """扩展阶段：选择一个未尝试的动作，创建子节点"""
        action = random.choice(node.untried_actions)
        node.untried_actions.remove(action)

        new_state = self.take_action(node.state, action)
        child = MCTSNode(
            state=new_state,
            parent=node,
            action_taken=action,
            untried_actions=self.get_actions(new_state)
        )
        node.children.append(child)
        return child

    def _simulate(self, state: Any) -> float:
        """
        模拟阶段：从当前状态进行随机模拟，直到终止或达到最大深度
        返回最终状态的评估值
        """
        current_state = state
        depth = 0

        while not self.is_terminal(current_state) and depth < self.max_depth:
            actions = self.get_actions(current_state)
            if not actions:
                break
            action = random.choice(actions)
            current_state = self.take_action(current_state, action)
            depth += 1

        return self.evaluate(current_state)

    def _backpropagate(self, node: MCTSNode, value: float):
        """反向传播阶段：从叶节点向上更新访问次数和价值"""
        while node is not None:
            node.visits += 1
            node.value += value
            node = node.parent

    def get_action_stats(self, initial_state: Any, iterations: int = 1000) -> Dict[Any, Dict]:
        """
        获取所有动作的统计信息

        Returns:
            {action: {"visits": int, "value": float, "win_rate": float}}
        """
        root = MCTSNode(
            state=initial_state,
            untried_actions=self.get_actions(initial_state)
        )

        for _ in range(iterations):
            node = self._select(root)
            if not self.is_terminal(node.state) and not node.is_fully_expanded:
                node = self._expand(node)
            value = self._simulate(node.state)
            self._backpropagate(node, value)

        stats = {}
        for child in root.children:
            stats[child.action_taken] = {
                "visits": child.visits,
                "value": child.value,
                "win_rate": child.value / child.visits if child.visits > 0 else 0
            }
        return stats
