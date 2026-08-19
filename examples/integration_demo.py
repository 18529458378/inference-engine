#!/usr/bin/env python3
"""
项目集成演示
展示 inference-engine 与 storage-stack、dev-skills-hub 的协同工作
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sdk import InferenceClient
from src.algorithms import MCTS, BayesianInference, VotingEngine, Vote


def demo_full_pipeline():
    """完整流水线演示：问题分析 → 推理 → 代码生成 → 审查 → 优化"""
    print("=" * 70)
    print("完整流水线演示")
    print("=" * 70)

    client = InferenceClient()

    # 1. 问题分析（思维链）
    print("\n[1/5] 问题分析（思维链推理）")
    print("-" * 40)
    question = "设计一个高效的Python函数，找出列表中第K大的元素"
    cot_result = client.reasoning.chain_of_thought.reason(question, verbose=False)
    print(f"问题: {question}")
    print(f"推理步数: {len(cot_result.reasoning_steps)}")
    print(f"分析结果: {cot_result.answer[:200]}...")

    # 2. 自我反思优化
    print("\n[2/5] 自我反思优化")
    print("-" * 40)
    reflection_result = client.reasoning.self_reflection.reason(
        question, max_iterations=2, verbose=False
    )
    print(f"迭代次数: {len(reflection_result.iterations)}")
    print(f"最终评分: {reflection_result.confidence:.2f}")

    # 3. 多路径投票验证
    print("\n[3/5] 多路径投票验证")
    print("-" * 40)
    voting_result = client.reasoning.multi_path_voting.reason(
        question, num_paths=3, voting_method="majority", verbose=False
    )
    print(f"路径数量: {len(voting_result.paths)}")
    print(f"投票统计: {voting_result.vote_counts}")
    print(f"整体置信度: {voting_result.confidence:.2f}")

    # 4. 算法层：贝叶斯置信度更新
    print("\n[4/5] 算法层：贝叶斯置信度更新")
    print("-" * 40)
    bi = BayesianInference(prior=0.5)
    print(f"初始置信度: {bi.posterior:.2f}")
    bi.update(likelihood=0.8, evidence=True)
    print(f"第一次验证后: {bi.posterior:.2f}")
    bi.update(likelihood=0.9, evidence=True)
    print(f"第二次验证后: {bi.posterior:.2f}")

    # 5. 算法层：投票聚合
    print("\n[5/5] 算法层：多方法投票聚合")
    print("-" * 40)
    votes = [
        Vote("cot", "方案A", weight=1.0, confidence=0.8),
        Vote("reflection", "方案A", weight=1.0, confidence=0.9),
        Vote("tot", "方案B", weight=1.0, confidence=0.7),
        Vote("voting", "方案A", weight=1.0, confidence=0.85),
    ]
    results = VotingEngine.compare_methods(votes)
    for method, result in results.items():
        print(f"  {method.upper()}: 获胜={result.winner}, 票数={result.vote_counts}")

    print("\n" + "=" * 70)
    print("流水线演示完成！")
    print("=" * 70)


def demo_code_enhancement_pipeline():
    """代码增强流水线：生成 → 审查 → 重构 → 测试 → 优化 → 文档"""
    print("\n" + "=" * 70)
    print("代码增强流水线演示")
    print("=" * 70)

    client = InferenceClient()

    # 示例代码
    sample_code = '''
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result

def find_item(items, target):
    for i in range(len(items)):
        if items[i] == target:
            return i
    return -1
'''

    print("\n原始代码:")
    print("-" * 40)
    print(sample_code)

    # 1. 代码审查
    print("\n[1/6] 代码审查")
    print("-" * 40)
    review = client.code.review_code(sample_code, filename="sample.py")
    print(f"总体评分: {review.overall_score}/100")
    print(f"发现问题: {len(review.issues)} 个")
    for issue in review.issues[:3]:
        print(f"  [{issue.severity.upper()}] {issue.title}")

    # 2. 复杂度分析
    print("\n[2/6] 复杂度分析")
    print("-" * 40)
    complexity = client.code.complexity_analyzer.analyze_code(
        sample_code, filename="sample.py"
    )
    print(f"整体质量: {complexity.overall_quality}")
    print(f"指标: {complexity.metrics}")

    # 3. 代码解释
    print("\n[3/6] 代码解释")
    print("-" * 40)
    explanation = client.code.explainer.explain_code(
        sample_code, filename="sample.py", level="beginner"
    )
    print(f"概述: {explanation.summary[:150]}...")

    # 4. 代码重构
    print("\n[4/6] 代码重构")
    print("-" * 40)
    refactored = client.code.refactorer.refactor_code(
        sample_code, filename="sample.py", target="clean_code"
    )
    print(f"重构说明: {refactored.explanation[:150]}...")

    # 5. 测试生成
    print("\n[5/6] 测试生成")
    print("-" * 40)
    tests = client.code.tester.generate_for_code(
        sample_code, filename="sample.py", framework="pytest"
    )
    print(f"测试用例数: {len(tests.test_cases)}")
    print(f"测试代码预览: {tests.test_code[:150]}...")

    # 6. 文档生成
    print("\n[6/6] 文档生成")
    print("-" * 40)
    docs = client.code.documenter.generate_for_code(
        sample_code, filename="sample.py", style="google"
    )
    print(f"已文档化函数: {docs.functions_documented}")

    print("\n" + "=" * 70)
    print("代码增强流水线演示完成！")
    print("=" * 70)


def main():
    demo_full_pipeline()
    demo_code_enhancement_pipeline()


if __name__ == "__main__":
    main()
