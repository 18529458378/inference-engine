"""Minimax Browser Adapter — 骨架实现（占位）

说明：此模块提供与 Minimax 内置 Browser 能力交互的抽象类与示例实现。
实际项目应实现底层传输（IPC/HTTP/CLI）以与运行中的 Minimax 交互。
"""
from typing import Dict, Any
import subprocess
import json


class MinimaxBrowserAdapter:
    """抽象适配器：方法为接口说明，返回 Python 原生对象。
    实现者需要根据运行时接口实现这些方法。
    """

    def inspect(self) -> Dict[str, Any]:
        """返回当前浏览器快照信息：{url, title, snapshotId, elements}
        占位返回示例结构，生产需替换为真实调用。"""
        # TODO: 实现 IPC/HTTP/CLI 调用，本处为示例
        return {
            "url": "",
            "title": "",
            "snapshotId": None,
            "elements": []
        }

    def query(self, kind: str, selector: str, maxChars: int = 20000) -> Dict[str, Any]:
        """查询页面内容，kind=text|dom|editable"""
        # TODO: 调用 runtime
        return {"text": "", "truncated": False}

    def action(self, action_name: str, input: Dict[str, Any]) -> Dict[str, Any]:
        """执行交互动作（click/type/navigate/screenshot 等），返回动作结果元数据"""
        # 示例：使用外部 CLI 调用（仅示例）
        # cmd = ["minimax-cli", "browser", action_name, json.dumps(input)]
        # subprocess.run(cmd, check=True)
        return {"status": "ok"}


# 简单示例：从 CLI 调用（如果存在）
class CLIProxyMinimaxAdapter(MinimaxBrowserAdapter):
    def __init__(self, cli_path: str = 'minimax-cli'):
        self.cli_path = cli_path

    def _call_cli(self, args) -> Dict[str, Any]:
        cmd = [self.cli_path] + args
        try:
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return json.loads(proc.stdout)
        except FileNotFoundError:
            raise RuntimeError('minimax-cli not found; please install or configure CLI path')
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'CLI call failed: {e.stdout}\n{e.stderr}')

    def inspect(self) -> Dict[str, Any]:
        return self._call_cli(['browser', 'inspect'])

    def query(self, kind: str, selector: str, maxChars: int = 20000) -> Dict[str, Any]:
        return self._call_cli(['browser', 'query', kind, selector, str(maxChars)])

    def action(self, action_name: str, input: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_cli(['browser', 'action', action_name, json.dumps(input)])
