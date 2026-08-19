#!/usr/bin/env python3
"""
MCTS 算法演示
使用蒙特卡洛树搜索解决简单决策问题
"""

import sys
import os
import random
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms import MCTS, BayesianInference, VotingEngine, Vote


# ========== 示例1: 数字猜谜游戏 ==========

class NumberGuessingGame:
    """数字猜谜游戏：猜1-100之间的数字"""

    def __init__(self, target: int = None):
        self.target = target or random.randint(1, 100)
        self.guesses = []
        self.feedback = []  # "higher" / "lower" / "correct"

    def get_actions(self, state):
        """获取可用动作（猜测的数字）"""
        low, high = state
        return list(range(low, high + 1))

    def take_action(self, state, action):
        """执行动作（猜测数字）"""
        low, high = state
        guess = action

        if guess == self.target:
            return (guess, guess)  # 终止状态
        elif guess < self.target:
            return (guess + 1, high)  # 缩小范围
        else:
            return (low, guess - 1)  # 缩小范围

    def is_terminal(self, state):
        """判断是否终止"""
        low, high = state
        return low == high  # 范围缩小到一个数字

    def evaluate(self, state):
        """评估状态价值（范围越小越好）"""
        low, high = state
        range_size = high - low + 1
        # 范围越小，价值越高
        return max(0.0, 1.0 - (range_size - 1) / 100.0)


def demo_number_guessing():
    """演示数字猜谜游戏"""
    print("=" * 60)
    print("MCTS 演示: 数字猜谜游戏")
    print("=" * 60)

    game = NumberGuessingGame(target=42)
    print(f"目标数字: {game.target}（MCTS不知道）")

    mcts = MCTS(
        get_actions=game.get_actions,
        take_action=game.take_action,
        is_terminal=game.is_terminal,
        evaluate=game.evaluate,
        exploration_constant=1.414,
        max_depth=10
    )

    initial_state = (1, 100)
    current_state = initial_state
    steps = 0

    while not game.is_terminal(current_state) and steps < 10:
        steps += 1
        print(f"\n--- 第 {steps} 步 ---")
        print(f"当前范围: {current_state[0]} - {current_state[1]}")

        # MCTS搜索
        best_guess = mcts.search(current_state, iterations=500)
        print(f"MCTS猜测: {best_guess}")

        # 执行猜测
        current_state = game.take_action(current_state, best_guess)
        game.guesses.append(best_guess)

        # 反馈
        if best_guess < game.target:
            print("反馈: 猜小了")
        elif best_guess > game.target:
            print("反馈: 猜大了")
        else:
            print("反馈: 猜对了！")
            break

    print(f"\n总共猜测: {steps} 次")
    print(f"猜测历史: {game.guesses}")

    # 获取动作统计
    print("\n动作统计（最后状态）:")
    stats = mcts.get_action_stats(current_state, iterations=200)
    for action, stat in sorted(stats.items(), key=lambda x: x[1]["visits"], reverse=True)[:5]:
        print(f"  动作 {action}: 访问{stat['visits']}次, 胜率{stat['win_rate']:.2f}")


# ========== 示例2: 贝叶斯推理 ==========

def demo_bayesian():
    """演示贝叶斯推理"""
    print("\n" + "=" * 60)
    print("贝叶斯推理演示")
    print("=" * 60)

    # 场景：检测某种疾病
    # 先验概率：1%的人患病
    # 检测准确率：95%（患病者检测阳性的概率）
    # 假阳性率：5%（未患病者检测阳性的概率）

    print("\n场景：疾病检测")
    print("- 疾病患病率（先验）: 1%")
    print("- 检测准确率（真阳性）: 95%")
    print("- 假阳性率: 5%")

    bi = BayesianInference(prior=0.01)
    print(f"\n初始患病概率: {bi.posterior:.4f} ({bi.posterior*100:.2f}%)")

    # 第一次检测阳性
    print("\n--- 第一次检测阳性 ---")
    # 似然：P(阳性|患病) = 0.95
    bi.update(likelihood=0.95, evidence=True)
    print(f"更新后患病概率: {bi.posterior:.4f} ({bi.posterior*100:.2f}%)")
    print(f"几率: {bi.odds:.2f}")

    # 第二次检测阳性
    print("\n--- 第二次检测阳性 ---")
    bi.update(likelihood=0.95, evidence=True)
    print(f"更新后患病概率: {bi.posterior:.4f} ({bi.posterior*100:.2f}%)")

    # 第三次检测阴性
    print("\n--- 第三次检测阴性 ---")
    # 似然：P(阴性|患病) = 0.05 (1-准确率)
    bi.update(likelihood=0.05, evidence=True)
    print(f"更新后患病概率: {bi.posterior:.4f} ({bi.posterior*100:.2f}%)")

    print(f"\n推理历史:")
    for i, state in enumerate(bi.get_history()):
        print(f"  步骤{i+1}: 先验={state['prior']:.4f}, 似然={state['likelihood']:.2f}, "
              f"后验={state['posterior']:.4f}")


# ========== 示例3: 投票聚合 ==========

def demo_voting():
    """演示投票聚合"""
    print("\n" + "=" * 60)
    print("投票聚合演示")
    print("=" * 60)

    # 5个投票者对3个选项投票
    votes = [
        Vote("voter1", "A", weight=1.0, confidence=0.9),
        Vote("voter2", "A", weight=1.0, confidence=0.8),
        Vote("voter3", "B", weight=1.0, confidence=0.95),
        Vote("voter4", "C", weight=1.0, confidence=0.7),
        Vote("voter5", "A", weight=1.0, confidence=0.85),
    ]

    print("\n投票情况:")
    for v in votes:
        print(f"  {v.voter_id}: 选择{v.choice}, 权重{v.weight}, 置信度{v.confidence}")

    # 比较多种投票方法
    print("\n--- 多种投票方法比较 ---")
    results = VotingEngine.compare_methods(votes)

    for method, result in results.items():
        print(f"\n{method.upper()}投票:")
        print(f"  获胜者: {result.winner}")
        print(f"  票数: {result.vote_counts}")
        print(f"  领先优势: {result.margin:.2%}")

    # 加权投票（使用置信度）
    print("\n--- 置信度加权投票 ---")
    weighted_engine = VotingEngine(method="weighted", use_confidence=True)
    weighted_result = weighted_engine.vote(votes)
    print(f"获胜者: {weighted_result.winner}")
    print(f"加权票数: {weighted_result.vote_counts}")


def main():
    demo_number_guessing()
    demo_bayesian()
    demo_voting()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
