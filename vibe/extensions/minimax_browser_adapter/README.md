# Minimax Browser Adapter（适配器）

目的：将 Minimax 内置的“Control In-App Browser”能力适配到本项目（vibe 引擎）的扩展点，提供统一的 inspect/query/interaction 接口。该适配器为骨架实现，便于按需实现与 Minimax 运行时的 IPC/CLI 调用。

注意：Minimax 的完整源码为打包产物，已从本机提取部分运行时代码（示例：open-browser.js）和 skill 定义（control-in-app-browser）。本适配器为安全的占位实现，避免直接引入未授权二进制/闭源代码。

快速开始：
1. 在运行环境中确保 Minimax 应用正在运行并且提供可调用的本地接口（IPC / socket / CLI）。
2. 在本适配器中实现 `MinimaxBrowserAdapter` 的底层方法（inspect/query/click/type/screenshot），可根据实际接口选择：
   - 通过启动 Minimax 自带 CLI 并传参（子进程）
   - 使用本地 socket / HTTP（如果 Minimax 暴露）
   - 使用文件交换（临时 JSON 请求/响应）作为兜底方案
3. 为敏感凭证或会话信息使用环境变量或安全密钥文件，不要提交到仓库。

接口示例（Python）：
- inspect() -> 返回 { url, title, snapshotId, elements }
- query(kind, selector, maxChars)
- action(action_name, input)

集成建议：将此适配器作为 vibe/extensions 插件加载点，engine 在选择技能时可通过配置切换到 Minimax 适配器。