Super-Cog-Orchestrator

概述：
Super-Cog-Orchestrator 是上层调度代理（Super-Cog-Orchestrator），负责将任务路由到 16 个专业 Agent 或调用 134 个 MCP 工具（通过工具接口）。

核心原则（实现约束）：
- 所有复杂推理、记忆检索、数学建模等必须调用 MCP 工具；调度器不直接模拟这些行为。
- 每次调用工具/启动新任务，必须传入合法的 project_namespace（用于隔离与审计）。
- 尊重工具返回的置信等级（confidence）、冲突/边界警告；低置信度输出应标注为“猜想”。

调度规则（映射表示例）：
- 简单事实查询 -> super_cog_query
- 明确专家领域任务 -> super_cog_ask_agent(agent_role, task)
  - code -> pi_agent
  - research/search -> hermes_agent
  - …（见 orchestrator 的 role_map）
- 复杂多步任务 -> super_cog_collab

文件说明：
- orchestrator.py: 核心调度实现（Python）。
- pi_agent.py / deepseek_harness.py / hermes_agent.py: Agent scaffold，与 orchestrator 协作。
