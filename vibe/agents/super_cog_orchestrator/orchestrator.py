"""Super-Cog-Orchestrator 调度器（简化实现）

- 调度规则按用户要求实现映射与分派。
- 所有对外复杂能力必须走 MCP 工具（由外部注入到 tools 字典），并确保传入 project_namespace。
- 工具返回格式示例：{ 'result': ..., 'confidence': 0.0-1.0, 'warnings': [...] }
"""
from typing import Any, Callable, Dict, Optional


class ToolCallError(Exception):
    pass


class SuperCogOrchestrator:
    def __init__(self, tools: Optional[Dict[str, Callable]] = None):
        # tools: name -> callable(payload:dict) -> dict
        if tools is None:
            try:
                from vibe.adapters.register_adapters import get_default_tools
                self.tools = get_default_tools()
            except Exception:
                self.tools = {}
        else:
            self.tools = tools
        # role -> agent_name mapping (agent_name corresponds to module/agent scaffold)
        self.role_map = {
            'code': 'pi_agent',
            'research': 'hermes_agent',
            'search': 'hermes_agent',
            'math': 'math_modeler',
            'qa': 'qa_engineer',
            'reasoning': 'reasoning_engineer',
            'security': 'security_auditor',
            'trend': 'trend_insight_engineer',
            'laws': 'laws_principles_engineer',
            'philosophy': 'philosophy_psychologist',
            'knowledge': 'knowledge_architect',
            'data': 'data_engineer',
            'skill': 'skill_distiller',
            'evolution': 'evolution_engineer',
            'browser': 'browser_agent',
            'deepseek': 'deepseek_harness',
        }

    def ensure_namespace(self, project_namespace: Optional[str]):
        if not project_namespace or not isinstance(project_namespace, str):
            raise ToolCallError('project_namespace 必须是非空字符串')

    def call_tool(self, tool_name: str, payload: Dict[str, Any], project_namespace: str) -> Dict[str, Any]:
        """调用 MCP 工具的统一入口，强制检查 project_namespace 并处理置信度/标签。"""
        self.ensure_namespace(project_namespace)
        if tool_name not in self.tools:
            raise ToolCallError(f"未知工具: {tool_name}")
        # augment payload with namespace
        call_payload = dict(payload)
        call_payload['project_namespace'] = project_namespace
        res = self.tools[tool_name](call_payload)
        # normalize response
        confidence = res.get('confidence') if isinstance(res.get('confidence'), (int, float)) else None
        if confidence is None:
            # 未提供置信度，标记为猜想（最低置信）
            res.setdefault('warnings', []).append('missing_confidence_marked_as_guess')
            res['confidence'] = 0.0
            res['meta_guess'] = True
        else:
            # 若置信度低于0.4，标注为猜想
            if confidence < 0.4:
                res.setdefault('warnings', []).append('low_confidence_marked_as_guess')
                res['meta_guess'] = True
            else:
                res['meta_guess'] = False
        return res

    def super_cog_query(self, query: str, project_namespace: str) -> Dict[str, Any]:
        """简单事实查询走 super_cog_query 工具（示例映射到 mcp_query）"""
        return self.call_tool('mcp_query', {'query': query}, project_namespace)

    def super_cog_ask_agent(self, agent_role: str, task: str, project_namespace: str) -> Dict[str, Any]:
        """将明确领域的任务分配给对应 agent（或其工具）。"""
        agent = self.role_map.get(agent_role)
        if not agent:
            # 未知角色，使用协作分析
            return self.super_cog_collab_analyze(task, project_namespace)
        # 优先调用对应 agent 的 MCP 接口（约定：agent_name + '_tool'）
        tool_name = f"{agent}_tool"
        if tool_name in self.tools:
            return self.call_tool(tool_name, {'task': task, 'role': agent_role}, project_namespace)
        # 回退：返回指派信息（agent 模块可单独实现）
        return {'result': f'assigned_to_{agent}', 'confidence': 0.5, 'warnings': ['no_tool_for_agent']}

    def super_cog_collab(self, task: str, project_namespace: str) -> Dict[str, Any]:
        """复杂多步任务：示例实现为拆分并并行调用（此处简化为串行模拟），并在结束后触发校验与蒸馏。"""
        # 示例拆分规则（极简）
        parts = [task]
        results = []
        for i, p in enumerate(parts):
            # dispatch to analysis tool
            r = self.call_tool('mcp_workflow', {'step': i, 'payload': p}, project_namespace)
            results.append(r)
        # run validation
        val = self.call_tool('mcp_validator', {'results': results}, project_namespace)
        return {'stages': results, 'validation': val}

    def super_cog_collab_analyze(self, task: str, project_namespace: str) -> Dict[str, Any]:
        return self.call_tool('mcp_collab_analyze', {'task': task}, project_namespace)

    def super_cog_parallel_execute(self, tasks, project_namespace: str):
        # 并行执行示例（此处串行）
        out = []
        for t in tasks:
            out.append(self.super_cog_ask_agent(t.get('role'), t.get('task'), project_namespace))
        return out

    # 记忆/知识库相关封装
    def super_cog_remember_fact(self, fact: str, project_namespace: str) -> Dict[str, Any]:
        return self.call_tool('mcp_remember', {'fact': fact}, project_namespace)

    def super_cog_ingest_document(self, doc: Dict[str, Any], project_namespace: str) -> Dict[str, Any]:
        return self.call_tool('mcp_ingest', {'document': doc}, project_namespace)

    def super_cog_anchor_init_task(self, task_id: str, anchors: Dict[str, Any], project_namespace: str) -> Dict[str, Any]:
        return self.call_tool('mcp_anchor_init', {'task_id': task_id, 'anchors': anchors}, project_namespace)

    def super_cog_anchor_check_drift(self, task_id: str, project_namespace: str) -> Dict[str, Any]:
        return self.call_tool('mcp_anchor_check', {'task_id': task_id}, project_namespace)
