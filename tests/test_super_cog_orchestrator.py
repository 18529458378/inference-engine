import pytest
from vibe.agents.super_cog_orchestrator.orchestrator import SuperCogOrchestrator, ToolCallError


class DummyTool:
    def __init__(self, name, confidence=0.9):
        self.name = name
        self.confidence = confidence

    def __call__(self, payload):
        # echo back with configured confidence
        return {'result': f"{self.name}_ok", 'confidence': self.confidence, 'warnings': []}


def test_call_tool_requires_namespace():
    orch = SuperCogOrchestrator(tools={'mcp_query': DummyTool('mcp_query')})
    with pytest.raises(ToolCallError):
        orch.super_cog_query('who', project_namespace=None)


def test_super_cog_query_and_confidence_labeling():
    # tool returns low confidence
    orch = SuperCogOrchestrator(tools={'mcp_query': DummyTool('mcp_query', confidence=0.2)})
    res = orch.super_cog_query('fact?', project_namespace='proj-1')
    assert res['result'] == 'mcp_query_ok'
    assert res['confidence'] == pytest.approx(0.2)
    assert res['meta_guess'] is True


def test_super_cog_ask_agent_assigns_agent_tool_when_available():
    tools = {
        'hermes_agent_tool': DummyTool('hermes_agent_tool', confidence=0.8)
    }
    orch = SuperCogOrchestrator(tools=tools)
    out = orch.super_cog_ask_agent('research', 'find papers on X', project_namespace='ns-1')
    assert out['result'] == 'hermes_agent_tool_ok'
    assert out['meta_guess'] is False


def test_super_cog_ask_unknown_role_triggers_collab_analyze():
    tools = {'mcp_collab_analyze': DummyTool('mcp_collab_analyze', confidence=0.7)}
    orch = SuperCogOrchestrator(tools=tools)
    out = orch.super_cog_ask_agent('unknown_role', 'do something', project_namespace='ns-2')
    assert out['result'] == 'mcp_collab_analyze_ok'


def test_super_cog_remember_and_ingest():
    tools = {
        'mcp_remember': DummyTool('mcp_remember', confidence=0.95),
        'mcp_ingest': DummyTool('mcp_ingest', confidence=0.92),
    }
    orch = SuperCogOrchestrator(tools=tools)
    r = orch.super_cog_remember_fact('Alice is a data scientist', project_namespace='kn-1')
    assert r['result'] == 'mcp_remember_ok'
    i = orch.super_cog_ingest_document({'title': 'doc'}, project_namespace='kn-1')
    assert i['result'] == 'mcp_ingest_ok'
