探索工程师（Super Explorer Agent）

目的：
该 agent 作为“超级探索/配置工程师”，用于自动化拉取、分析并整合外部优质资源（例如 GitHub 上的 toknife 与 claw-compactor），并将这些能力作为 Vibe Coding 范式的一部分纳入本项目。它负责：

- 持续抓取与同步许可的远端代码仓库与数据集；
- 运行静态分析与轻量自检（import / smoke tests）；
- 将外部库包装为本地可调用的适配器（Adapter pattern）；
- 提供压缩/去噪/路由工具（集成 claw-compactor / toknife）供其它 agent 与 engine 使用；
- 记录与管理资源元数据（来源、版本、许可证、hash）；
- 在受控环境中（自托管 runner）执行集成测试与数据抽取任务。

使用方式（示例）：
- 在本地交互式运行：
  python -m vibe.agents.super_explorer_agent.agent --help

注意事项：
- 默认不自动向外网推送任何代码变更；所有远端拉取需用户授权（或使用预先配置的 gh CLI token）。
- 本 agent 仅包含 scaffold 与集成入口，实际生产部署需配置凭证、存储、调度与安全策略。