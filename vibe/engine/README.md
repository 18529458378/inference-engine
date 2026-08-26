# vibe/engine

本目录为“Vibe 引擎”（Engine）实现的位置，负责算法调度、模型接口、任务生命周期管理与运行时监控。

职责：
- 管理算法（vibe/algorithm）执行与输入输出（I/O）
- 提供与外部 LLM/模型的统一接口（如 DeepSeek）
- 暴露本地 CLI / MCP 集成点（hooks、CLI 命令、HTTP/IPC 接口）