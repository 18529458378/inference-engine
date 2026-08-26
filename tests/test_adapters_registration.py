from vibe.agents.super_cog_orchestrator.orchestrator import SuperCogOrchestrator


def test_default_tools_loaded():
    orch = SuperCogOrchestrator()  # no tools passed, should auto-load register_adapters
    # ensure key adapters/tools exist
    for name in ['hermes_agent_tool','deepseek_tool','pi_agent_tool','mcp_query']:
        assert name in orch.tools
        assert callable(orch.tools[name])
    # call a tool to ensure it returns expected dict shape
    res = orch.call_tool('mcp_query', {'query':'x'}, project_namespace='test-ns')
    assert 'result' in res and 'confidence' in res
