#!/usr/bin/env python3
"""
Inference Engine CLI
推理增强与代码增强引擎命令行接口

用法:
    inference-engine reasoning cot "问题"
    inference-engine reasoning reflection "问题" --iterations 3
    inference-engine code review path/to/code.py
    inference-engine code refactor path/to/code.py --target clean_code
    inference-engine code test path/to/module.py
    inference-engine code complexity path/to/code.py
"""

import os
import sys
import json

import click

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sdk import InferenceClient


def get_client():
    """获取客户端实例"""
    return InferenceClient()


def output_result(result, output_format="text"):
    """输出结果"""
    if output_format == "json":
        if hasattr(result, 'to_dict'):
            click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            click.echo(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        click.echo(str(result))


# ========== 主命令组 ==========

@click.group()
@click.option('--config', '-c', default=None, help='配置文件路径')
@click.option('--model', '-m', default=None, help='LLM模型名称')
@click.option('--temperature', '-t', default=None, type=float, help='生成温度')
@click.pass_context
def cli(ctx, config, model, temperature):
    """Inference Engine - 推理增强与代码增强引擎"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = InferenceClient(config_path=config)
    if model:
        ctx.obj['client'].set_model(model)
    if temperature is not None:
        ctx.obj['client'].set_temperature(temperature)


# ========== 推理增强命令组 ==========

@cli.group()
@click.pass_context
def reasoning(ctx):
    """推理增强命令"""
    pass


@reasoning.command()
@click.argument('question')
@click.option('--max-steps', default=10, type=int, help='最大推理步数')
@click.option('--verbose', '-v', is_flag=True, help='显示详细推理过程')
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text')
@click.pass_context
def cot(ctx, question, max_steps, verbose, output):
    """思维链推理 (Chain-of-Thought)"""
    client = ctx.obj['client']
    result = client.reasoning.chain_of_thought.reason(
        question, max_steps=max_steps, verbose=verbose
    )

    if output == "json":
        output_result(result, "json")
    else:
        click.echo(f"\n{'='*60}")
        click.echo("思维链推理结果")
        click.echo(f"{'='*60}")
        click.echo(f"\n问题: {question}")
        click.echo(f"\n推理步骤 ({len(result.reasoning_steps)} 步):")
        for i, step in enumerate(result.reasoning_steps, 1):
            click.echo(f"  {i}. {step[:100]}{'...' if len(step) > 100 else ''}")
        click.echo(f"\n最终答案:\n{result.answer}")
        click.echo(f"\n置信度: {result.confidence:.2f}")


@reasoning.command()
@click.argument('question')
@click.option('--iterations', '-i', default=3, type=int, help='最大迭代次数')
@click.option('--verbose', '-v', is_flag=True, help='显示详细过程')
@click.pass_context
def reflection(ctx, question, iterations, verbose):
    """自我反思推理 (Self-Reflection)"""
    client = ctx.obj['client']
    result = client.reasoning.self_reflection.reason(
        question, max_iterations=iterations, verbose=verbose
    )

    click.echo(f"\n{'='*60}")
    click.echo("自我反思推理结果")
    click.echo(f"{'='*60}")
    click.echo(f"\n问题: {question}")
    click.echo(f"\n迭代次数: {len(result.iterations)}")
    for it in result.iterations:
        click.echo(f"  迭代 {it.iteration}: 评分={it.score:.2f}")
    click.echo(f"\n最终答案:\n{result.answer[:500]}{'...' if len(result.answer) > 500 else ''}")
    click.echo(f"\n最终评分: {result.confidence:.2f}")


@reasoning.command()
@click.argument('question')
@click.option('--breadth', '-b', default=3, type=int, help='每节点分支数')
@click.option('--depth', '-d', default=3, type=int, help='搜索深度')
@click.option('--verbose', '-v', is_flag=True, help='显示搜索过程')
@click.pass_context
def tot(ctx, question, breadth, depth, verbose):
    """思维树搜索 (Tree-of-Thoughts)"""
    client = ctx.obj['client']
    result = client.reasoning.tree_of_thoughts.reason(
        question, breadth=breadth, depth=depth, verbose=verbose
    )

    click.echo(f"\n{'='*60}")
    click.echo("思维树搜索结果")
    click.echo(f"{'='*60}")
    click.echo(f"\n问题: {question}")
    click.echo(f"搜索参数: breadth={breadth}, depth={depth}")
    click.echo(f"叶子节点数: {len(result.all_leaves)}")
    click.echo(f"最优路径长度: {len(result.best_path)}")
    click.echo(f"\n最终答案:\n{result.answer[:500]}{'...' if len(result.answer) > 500 else ''}")
    click.echo(f"\n最优评分: {result.confidence:.2f}")


@reasoning.command()
@click.argument('task')
@click.option('--constraints', default='', help='约束条件')
@click.option('--verbose', '-v', is_flag=True, help='显示执行过程')
@click.pass_context
def plan(ctx, task, constraints, verbose):
    """规划执行 (Plan-and-Execute)"""
    client = ctx.obj['client']
    result = client.reasoning.plan_and_execute.reason(
        task, constraints=constraints, verbose=verbose
    )

    click.echo(f"\n{'='*60}")
    click.echo("规划执行结果")
    click.echo(f"{'='*60}")
    click.echo(f"\n任务: {task}")
    click.echo(f"子任务数: {len(result.subtasks)}")
    for st in result.subtasks:
        status_icon = "✓" if st.status == "completed" else "✗" if st.status == "failed" else "→"
        click.echo(f"  {status_icon} [{st.id}] {st.name} ({st.status})")
    click.echo(f"重规划次数: {result.replans}")
    click.echo(f"\n最终结果:\n{result.answer[:500]}{'...' if len(result.answer) > 500 else ''}")


@reasoning.command()
@click.argument('question')
@click.option('--paths', '-n', default=5, type=int, help='推理路径数量')
@click.option('--method', '-m', type=click.Choice(['majority', 'weighted', 'bayesian']),
              default='majority', help='投票方法')
@click.option('--verbose', '-v', is_flag=True, help='显示详细过程')
@click.pass_context
def voting(ctx, question, paths, method, verbose):
    """多路径投票 (Multi-Path Voting)"""
    client = ctx.obj['client']
    result = client.reasoning.multi_path_voting.reason(
        question, num_paths=paths, voting_method=method, verbose=verbose
    )

    click.echo(f"\n{'='*60}")
    click.echo("多路径投票结果")
    click.echo(f"{'='*60}")
    click.echo(f"\n问题: {question}")
    click.echo(f"路径数: {len(result.paths)}")
    click.echo(f"投票方法: {result.voting_method}")
    click.echo(f"投票统计: {result.vote_counts}")
    click.echo(f"\n最终答案:\n{result.answer[:500]}{'...' if len(result.answer) > 500 else ''}")
    click.echo(f"\n整体置信度: {result.confidence:.2f}")


# ========== 代码增强命令组 ==========

@cli.group()
@click.pass_context
def code(ctx):
    """代码增强命令"""
    pass


@code.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text')
@click.pass_context
def review(ctx, filepath, output):
    """代码审查"""
    client = ctx.obj['client']
    result = client.code.review(filepath)

    if output == "json":
        output_result(result, "json")
    else:
        click.echo(f"\n{'='*60}")
        click.echo("代码审查报告")
        click.echo(f"{'='*60}")
        click.echo(f"\n文件: {filepath}")
        click.echo(f"语言: {result.language}")
        click.echo(f"总体评分: {result.overall_score}/100")
        click.echo(f"摘要: {result.summary}")
        click.echo(f"\n发现 {len(result.issues)} 个问题:")
        for issue in result.issues:
            severity_color = {
                'critical': 'red', 'high': 'red',
                'medium': 'yellow', 'low': 'cyan', 'info': 'blue'
            }.get(issue.severity, 'white')
            click.echo(f"  [{click.style(issue.severity.upper(), fg=severity_color)}] "
                       f"{issue.category}: {issue.title}")
            if issue.suggestion:
                click.echo(f"    建议: {issue.suggestion[:100]}")
        click.echo(f"\n优点: {', '.join(result.strengths)}")
        click.echo(f"建议: {', '.join(result.recommendations)}")


@code.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--target', '-t', default='clean_code',
              type=click.Choice(['clean_code', 'design_pattern', 'performance', 'readability']),
              help='重构目标')
@click.option('--in-place', is_flag=True, help='原地修改文件（自动备份）')
@click.pass_context
def refactor(ctx, filepath, target, in_place):
    """代码重构"""
    client = ctx.obj['client']
    result = client.code.refactor(filepath, target=target, in_place=in_place)

    click.echo(f"\n{'='*60}")
    click.echo("代码重构结果")
    click.echo(f"{'='*60}")
    click.echo(f"\n文件: {filepath}")
    click.echo(f"重构目标: {result.target}")
    click.echo(f"变更摘要: {result.diff_summary}")
    click.echo(f"\n重构说明:\n{result.explanation[:300]}{'...' if len(result.explanation) > 300 else ''}")
    click.echo(f"\n重构后代码:\n{'-'*40}")
    click.echo(result.refactored_code[:1000])
    if len(result.refactored_code) > 1000:
        click.echo("...")
    if in_place:
        click.echo(f"\n✓ 文件已原地修改，备份: {filepath}.bak")


@code.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--framework', '-f', default='pytest',
              type=click.Choice(['pytest', 'unittest']), help='测试框架')
@click.option('--output', '-o', default=None, help='输出文件路径')
@click.pass_context
def test(ctx, filepath, framework, output):
    """生成测试用例"""
    client = ctx.obj['client']
    result = client.code.generate_tests(filepath, framework=framework)

    click.echo(f"\n{'='*60}")
    click.echo("测试生成结果")
    click.echo(f"{'='*60}")
    click.echo(f"\n源文件: {filepath}")
    click.echo(f"测试框架: {result.framework}")
    click.echo(f"生成测试用例: {len(result.test_cases)} 个")
    click.echo(f"测试文件名: {result.test_filename}")
    click.echo(f"\n测试代码:\n{'-'*40}")
    click.echo(result.test_code[:1000])
    if len(result.test_code) > 1000:
        click.echo("...")

    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result.test_code)
        click.echo(f"\n✓ 测试代码已保存到: {output}")


@code.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.pass_context
def complexity(ctx, filepath):
    """代码复杂度分析"""
    client = ctx.obj['client']
    result = client.code.analyze_complexity(filepath)

    click.echo(f"\n{'='*60}")
    click.echo("代码复杂度分析")
    click.echo(f"{'='*60}")
    click.echo(f"\n文件: {filepath}")
    click.echo(f"整体质量: {result.overall_quality}")
    click.echo(f"\n复杂度指标:")
    for key, value in result.metrics.items():
        click.echo(f"  {key}: {value}")
    click.echo(f"\n技术债务 ({len(result.technical_debt)} 项):")
    for debt in result.technical_debt[:5]:
        click.echo(f"  [{debt.get('severity', '?').upper()}] {debt.get('type', '?')}: {debt.get('description', '')[:80]}")
    click.echo(f"\n高风险区域: {', '.join(result.risk_areas)}")
    click.echo(f"改进建议: {', '.join(result.recommendations)}")


@code.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--in-place', is_flag=True, help='原地修改文件')
@click.pass_context
def optimize(ctx, filepath, in_place):
    """代码性能优化"""
    client = ctx.obj['client']
    result = client.code.optimize(filepath, in_place=in_place)

    click.echo(f"\n{'='*60}")
    click.echo("代码性能优化")
    click.echo(f"{'='*60}")
    click.echo(f"\n文件: {filepath}")
    click.echo(f"优化重点: {', '.join(result.focus)}")
    click.echo(f"变更摘要: {result.diff_summary}")
    click.echo(f"\n性能分析:\n{result.analysis[:300]}{'...' if len(result.analysis) > 300 else ''}")
    click.echo(f"\n优化点 ({len(result.optimizations)} 个):")
    for opt in result.optimizations[:5]:
        click.echo(f"  - {opt[:80]}")
    click.echo(f"\n优化后代码:\n{'-'*40}")
    click.echo(result.optimized_code[:800])
    if len(result.optimized_code) > 800:
        click.echo("...")


@code.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--style', '-s', default='google',
              type=click.Choice(['google', 'numpy', 'sphinx', 'javadoc']), help='文档风格')
@click.option('--in-place', is_flag=True, help='原地修改文件')
@click.pass_context
def docs(ctx, filepath, style, in_place):
    """生成代码文档"""
    client = ctx.obj['client']
    result = client.code.generate_docs(filepath, style=style, in_place=in_place)

    click.echo(f"\n{'='*60}")
    click.echo("代码文档生成")
    click.echo(f"{'='*60}")
    click.echo(f"\n文件: {filepath}")
    click.echo(f"文档风格: {result.style}")
    click.echo(f"已文档化函数: {', '.join(result.functions_documented)}")
    click.echo(f"\n带文档的代码:\n{'-'*40}")
    click.echo(result.documented_code[:800])
    if len(result.documented_code) > 800:
        click.echo("...")


# ========== 算法命令组 ==========

@cli.group()
@click.pass_context
def algo(ctx):
    """算法命令（MCTS/贝叶斯/投票）"""
    pass


@algo.command()
@click.argument('prior', type=float)
@click.option('--likelihood', '-l', type=float, default=0.8, help='似然 P(E|H)')
@click.option('--evidence/--no-evidence', default=True, help='是否观察到证据')
@click.pass_context
def bayes(ctx, prior, likelihood, evidence):
    """贝叶斯推理"""
    from src.algorithms import BayesianInference

    bi = BayesianInference(prior=prior)
    posterior = bi.update(likelihood=likelihood, evidence=evidence)

    click.echo(f"\n贝叶斯推理")
    click.echo(f"  先验 P(H): {prior:.4f} ({prior*100:.2f}%)")
    click.echo(f"  似然 P(E|H): {likelihood:.4f}")
    click.echo(f"  证据: {'观察到' if evidence else '未观察到'}")
    click.echo(f"  后验 P(H|E): {posterior:.4f} ({posterior*100:.2f}%)")
    click.echo(f"  几率: {bi.odds:.4f}")
    click.echo(f"  对数几率: {bi.log_odds:.4f}")


def main():
    cli()


if __name__ == "__main__":
    main()
