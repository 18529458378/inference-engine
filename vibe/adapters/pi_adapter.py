"""PI Adapter - pi_agent 的工具实现（代码/脚本处理）
安全原则：不直接执行不可信 shell；仅提供静态分析或返回可执行计划供 operator 审核。
"""
from typing import Dict, Any
import ast


def pi_agent_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    # payload: {'task': str, 'project_namespace': str}
    task = payload.get('task', '')
    # 尝试解析为 Python 片段并返回 AST 摘要作为静态分析
    try:
        tree = ast.parse(task)
        nodes = [type(n).__name__ for n in ast.walk(tree)][:20]
        summary = {
            'node_types_preview': nodes,
            'lines': len(task.splitlines())
        }
        return {'result': summary, 'confidence': 0.85, 'warnings': []}
    except Exception as e:
        # 非 Python 内容，返回任务长度与提示
        return {'result': {'preview': str(task)[:400]}, 'confidence': 0.4, 'warnings': ['non_python_fallback']}
