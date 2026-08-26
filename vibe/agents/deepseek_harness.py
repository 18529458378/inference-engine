"""deepseek_harness (dsh) scaffold

职责：用于深度检索、多源融合与高级检索任务的协调器，依赖外部检索/索引 MCP 工具。
"""
from typing import Dict, Any


class DeepSeekHarness:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

    def handle(self, query: str, project_namespace: str) -> Dict[str, Any]:
        if not self.orchestrator:
            return {'result': 'no_orchestrator', 'confidence': 0.0}
        return self.orchestrator.call_tool('deepseek_tool', {'query': query}, project_namespace)
