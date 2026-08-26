"""Register adapters and expose get_default_tools()
返回 mapping: tool_name -> callable
"""
from typing import Dict, Callable

try:
    from .hermes_adapter import hermes_agent_tool
except Exception:
    hermes_agent_tool = None

try:
    from .deepseek_adapter import deepseek_tool
except Exception:
    deepseek_tool = None

try:
    from .pi_adapter import pi_agent_tool
except Exception:
    pi_agent_tool = None

try:
    from .toknife_adapter import toknife_tool
except Exception:
    toknife_tool = None


def get_default_tools() -> Dict[str, Callable]:
    tools = {}
    if hermes_agent_tool:
        tools['hermes_agent_tool'] = hermes_agent_tool
    if deepseek_tool:
        tools['deepseek_tool'] = deepseek_tool
    if pi_agent_tool:
        tools['pi_agent_tool'] = pi_agent_tool
    if toknife_tool:
        tools['toknife_tool'] = toknife_tool
    # lightweight mocks for other mcp endpoints useful for orchestrator flows
    def _mock(name):
        def f(payload):
            return {'result': f'{name}_ok', 'confidence': 0.7, 'warnings': []}
        return f

    for name in ['mcp_query','mcp_workflow','mcp_validator','mcp_collab_analyze','mcp_remember','mcp_ingest','mcp_anchor_init','mcp_anchor_check']:
        tools.setdefault(name, _mock(name))

    return tools
