# vibe/kernel

Kernel（内核）负责运行环境、任务队列、资源隔离与插件（extensions）加载。

职责：
- 提供任务调度与并发控制
- 管理扩展点（vibe/extensions）和运行时权限
- 提供与宿主系统（MCP/CLI）的安全交互层