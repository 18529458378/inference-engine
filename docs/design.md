# 中文 Vibe 部署设计（文本架构图）

总体架构（文本图，便于快速阅读与版本控制）：

```
[CLI / MCP] -> [vibe/kernel] -> [vibe/engine] -> [vibe/algorithm]
                       |              \
                       |               -> [vibe/skills]
                       -> [vibe/extensions]
                       -> [vibe/tools]
```

组件职责：
- CLI / MCP（命令行 / 管理控制面板）
  - 启动/停止任务、查看日志、触发技能与部署扩展（与用户交互）。
- vibe/kernel（运行内核）
  - 管理任务队列、并发、权限、插件加载与生命周期（隔离运行）。
- vibe/engine（执行引擎）
  - 调度算法、封装模型调用、处理输入/输出（转换格式、批处理）。
- vibe/algorithm（算法）
  - 算法实现（思维链、蒙特卡洛、评分器等），提供可测试的最小接口（输入 -> 输出）。
- vibe/skills（技能）
  - 将算法与工具组合成上层能力（如“中文 Vibe 风格化”）。
- vibe/extensions（扩展）
  - 第三方适配器、评估函数、外部资源连接器（按需加载）。
- vibe/tools（工具）
  - 本地/系统工具（文件、音频、外部命令）封装。

数据流（示例）：
- 用户（CLI/MCP）发起请求（文本/音频）
- kernel 接收并入队 -> engine 拉取任务 -> 选择算法（algorithm）与技能（skills）
- algorithm 执行并调用 tools 或 extensions（必要时）
- 输出返回 engine -> kernel -> CLI/MCP 或持久化（日志/结果存储）

扩展点与集成说明：
- CLI/CLI 插件接口：建议提供 JSON-RPC 或简单的 CLI 子命令（如 `vibe run --skill chinese-vibe`）。
- MCP 集成：通过插件或 webhook 将任务下发到 kernel（推荐在 self-hosted runner 上运行以保证离线能力）。
- 安全与凭证：所有需要凭证的扩展应以环境变量或密钥文件形式注入，且不应直接写入仓库。

部署建议：
- 本地开发：使用 self-hosted runner 或本地 Python 环境（示例中使用 Python 脚本与 pytest）
- 生产/集成：将 kernel 部署在受控环境（有权限隔离）并配置 extensions 与 tools 的访问策略。