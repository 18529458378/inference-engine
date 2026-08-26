"""pi_agent: 代码/脚本执行与生成 Agent scaffold

职责：处理代码/脚本/Shell 相关任务，负责把任务包装成安全的执行或代码生成请求并通常调用 MCP 工具来完成复杂分析与执行。
"""
from typing import Dict, Any


class PiAgent:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

    def handle(self, task: str, project_namespace: str) -> Dict[str, Any]:
        # 强制通过 orchestrator 的工具调用链来完成复杂工作
        if not self.orchestrator:
            return {'result': 'no_orchestrator', 'confidence': 0.0, 'warnings': ['no_orchestrator']}
        payload = {'task': task}
        return self.orchestrator.call_tool('pi_agent_tool', payload, project_namespace)
