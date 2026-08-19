#!/usr/bin/env python3
"""
推理增强演示
展示思维链、自我反思、多路径投票等推理增强技术
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sdk import InferenceClient


def main():
    print("=" * 60)
    print("推理增强演示")
    print("=" * 60)

    client = InferenceClient()

    # 测试问题
    question = "一个水池有两个进水管A和B，一个出水管C。单独开A管6小时注满，单独开B管8小时注满，单独开C管12小时放完。如果三管同时开，几小时能注满水池？"

    print(f"\n问题: {question}\n")

    # 1. 思维链推理
    print("--- 1. 思维链推理 (Chain-of-Thought) ---")
    cot_result = client.reasoning.chain_of_thought.reason(question, verbose=True)
    print(f"\n最终答案: {cot_result.answer}")
    print(f"推理步数: {len(cot_result.reasoning_steps)}")
    print(f"置信度: {cot_result.confidence:.2f}")

    # 2. 自我反思
    print("\n--- 2. 自我反思推理 (Self-Reflection) ---")
    reflection_result = client.reasoning.self_reflection.reason(
        question, max_iterations=2, verbose=True
    )
    print(f"\n最终答案: {reflection_result.answer[:200]}...")
    print(f"迭代次数: {len(reflection_result.iterations)}")
    print(f"最终评分: {reflection_result.confidence:.2f}")

    # 3. 多路径投票
    print("\n--- 3. 多路径投票 (Multi-Path Voting) ---")
    voting_result = client.reasoning.multi_path_voting.reason(
        question, num_paths=3, voting_method="majority", verbose=True
    )
    print(f"\n最终答案: {voting_result.answer[:200]}...")
    print(f"路径数量: {len(voting_result.paths)}")
    print(f"投票方法: {voting_result.voting_method}")
    print(f"整体置信度: {voting_result.confidence:.2f}")

    # 4. 置信度评估
    print("\n--- 4. 置信度评估 (Confidence Estimation) ---")
    confidence_result = client.reasoning.confidence.estimate(
        question, cot_result.answer, cot_result.reasoning_steps,
        method="self_evaluation"
    )
    print(f"整体置信度: {confidence_result.overall:.2f}")
    print(f"各维度: {confidence_result.components}")

    # 5. 规划执行
    print("\n--- 5. 规划执行 (Plan-and-Execute) ---")
    task = "写一个Python函数，实现快速排序算法，并包含测试用例"
    plan_result = client.reasoning.plan_and_execute.reason(
        task, verbose=True
    )
    print(f"\n最终答案: {plan_result.answer[:300]}...")
    print(f"子任务数量: {len(plan_result.subtasks)}")
    print(f"重规划次数: {plan_result.replans}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
