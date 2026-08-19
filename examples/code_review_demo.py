#!/usr/bin/env python3
"""
代码增强演示
展示代码审查、重构、测试生成、复杂度分析等
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sdk import InferenceClient


# 示例代码（有一些问题）
SAMPLE_CODE = '''
def find_max(numbers):
    # 这个函数有一些问题
    max = 0
    for i in range(len(numbers)):
        if numbers[i] > max:
            max = numbers[i]
    return max

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total = total + n
    avg = total / len(numbers)
    return avg

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
'''


def main():
    print("=" * 60)
    print("代码增强演示")
    print("=" * 60)

    client = InferenceClient()

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(SAMPLE_CODE)
        temp_path = f.name

    print(f"\n示例代码文件: {temp_path}")
    print("\n原始代码:")
    print("-" * 40)
    print(SAMPLE_CODE)
    print("-" * 40)

    # 1. 代码审查
    print("\n--- 1. 代码审查 (Code Review) ---")
    review = client.code.review(temp_path)
    print(f"总体评分: {review.overall_score}/100")
    print(f"摘要: {review.summary}")
    print(f"\n发现 {len(review.issues)} 个问题:")
    for issue in review.issues[:5]:
        print(f"  [{issue.severity.upper()}] {issue.category}: {issue.title}")
        if issue.suggestion:
            print(f"    建议: {issue.suggestion[:100]}")

    print(f"\n优点: {review.strengths}")
    print(f"建议: {review.recommendations}")

    # 2. 代码重构
    print("\n--- 2. 代码重构 (Refactor) ---")
    refactored = client.code.refactor(temp_path, target="clean_code")
    print(f"重构目标: {refactored.target}")
    print(f"变更摘要: {refactored.diff_summary}")
    print(f"\n重构说明: {refactored.explanation[:200]}...")
    print(f"\n重构后代码:")
    print("-" * 40)
    print(refactored.refactored_code[:500])
    print("..." if len(refactored.refactored_code) > 500 else "")
    print("-" * 40)

    # 3. 测试生成
    print("\n--- 3. 测试生成 (Test Generation) ---")
    tests = client.code.generate_tests(temp_path, framework="pytest")
    print(f"测试框架: {tests.framework}")
    print(f"生成测试用例: {len(tests.test_cases)} 个")
    print(f"测试文件名: {tests.test_filename}")
    print(f"\n测试代码预览:")
    print("-" * 40)
    print(tests.test_code[:500])
    print("..." if len(tests.test_code) > 500 else "")
    print("-" * 40)

    # 4. 复杂度分析
    print("\n--- 4. 复杂度分析 (Complexity Analysis) ---")
    complexity = client.code.analyze_complexity(temp_path)
    print(f"整体质量: {complexity.overall_quality}")
    print(f"复杂度指标: {complexity.metrics}")
    print(f"技术债务: {len(complexity.technical_debt)} 项")
    print(f"高风险区域: {complexity.risk_areas}")
    print(f"改进建议: {complexity.recommendations}")

    # 5. 性能优化
    print("\n--- 5. 性能优化 (Optimization) ---")
    optimized = client.code.optimize(temp_path, focus=["time_complexity", "space_complexity"])
    print(f"优化重点: {optimized.focus}")
    print(f"变更摘要: {optimized.diff_summary}")
    print(f"\n性能分析: {optimized.analysis[:200]}...")
    print(f"优化点数量: {len(optimized.optimizations)}")

    # 6. 文档生成
    print("\n--- 6. 文档生成 (Documentation) ---")
    docs = client.code.generate_docs(temp_path, style="google")
    print(f"文档风格: {docs.style}")
    print(f"已文档化函数: {docs.functions_documented}")
    print(f"\n带文档的代码预览:")
    print("-" * 40)
    print(docs.documented_code[:400])
    print("..." if len(docs.documented_code) > 400 else "")
    print("-" * 40)

    # 清理临时文件
    os.unlink(temp_path)

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
