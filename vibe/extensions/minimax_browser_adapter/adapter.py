"""Minimax Browser Adapter — 骨架实现与多种运输示例

说明：此模块提供与 Minimax 内置 Browser 能力交互的抽象类与示例实现。
实现包含：
- CLIProxyMinimaxAdapter: 通过外部 CLI 调用（子进程）
- TCPMinimaxAdapter: 简单 TCP JSON RPC（本地 IPC 示例，需 Minimax 暴露对应端口）
- FileExchangeMinimaxAdapter: 通过临时文件请求/响应交换（兜底方案）

生产环境请根据 Minimax 提供的真实接口实现对应底层调用并做好凭证/会话管理。
"""
from typing import Dict, Any
import subprocess
import json
import socket
import time
import os


class MinimaxBrowserAdapter:
    """抽象适配器：方法为接口说明，返回 Python 原生对象。
    实现者需要根据运行时接口实现这些方法。
    """

    def inspect(self) -> Dict[str, Any]:
        """返回当前浏览器快照信息：{url, title, snapshotId, elements}
        占位返回示例结构，生产需替换为真实调用。"""
        return {
            "url": "",
            "title": "",
            "snapshotId": None,
            "elements": []
        }

    def query(self, kind: str, selector: str, maxChars: int = 20000) -> Dict[str, Any]:
        """查询页面内容，kind=text|dom|editable"""
        return {"text": "", "truncated": False}

    def action(self, action_name: str, input: Dict[str, Any]) -> Dict[str, Any]:
        """执行交互动作（click/type/navigate/screenshot 等），返回动作结果元数据"""
        return {"status": "ok"}


class CLIProxyMinimaxAdapter(MinimaxBrowserAdapter):
    """通过外部命令行工具与 Minimax 交互的代理实现（示例）

    依赖：minimax-cli 可执行文件，返回 JSON 到 stdout。
    """

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


class TCPMinimaxAdapter(MinimaxBrowserAdapter):
    """通过 TCP 向本地 Minimax 服务发送 JSON 请求并读取响应。

    协议（示例）：每次发送一行 JSON：{"op": "inspect"} 或 {"op":"action","name":"click","input":{...}}
    服务应以一行 JSON 响应返回。
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 45123, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def _send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload) + "\n"
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
            s.sendall(data.encode('utf-8'))
            # 读取到换行
            buf = b''
            s.settimeout(self.timeout)
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in chunk:
                    break
            if not buf:
                raise RuntimeError('No response from Minimax TCP service')
            line = buf.split(b"\n")[0]
            try:
                return json.loads(line.decode('utf-8'))
            except Exception as e:
                raise RuntimeError(f'Invalid JSON response: {e}')

    def inspect(self) -> Dict[str, Any]:
        return self._send_request({"op": "inspect"})

    def query(self, kind: str, selector: str, maxChars: int = 20000) -> Dict[str, Any]:
        return self._send_request({"op": "query", "kind": kind, "selector": selector, "max": maxChars})

    def action(self, action_name: str, input: Dict[str, Any]) -> Dict[str, Any]:
        return self._send_request({"op": "action", "name": action_name, "input": input})


class FileExchangeMinimaxAdapter(MinimaxBrowserAdapter):
    """通过文件交换（请求/响应文件）与 Minimax 交互的兜底实现。

    用法：在配置中指定 request_dir（双方共享或 Minimax 监视的目录）。
    适用于无法建立直接 IPC 的场景，性能较差但实现简单。
    """

    def __init__(self, request_dir: str = None, poll_interval: float = 0.5, timeout: float = 10.0):
        self.request_dir = request_dir or os.path.join(os.getcwd(), 'minimax_requests')
        os.makedirs(self.request_dir, exist_ok=True)
        self.poll_interval = poll_interval
        self.timeout = timeout

    def _exchange(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ts = int(time.time() * 1000)
        req_path = os.path.join(self.request_dir, f'req_{ts}.json')
        res_path = os.path.join(self.request_dir, f'res_{ts}.json')
        with open(req_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False)
        # 等待响应文件出现
        waited = 0.0
        while waited < self.timeout:
            if os.path.exists(res_path):
                with open(res_path, 'r', encoding='utf-8') as f:
                    try:
                        return json.load(f)
                    finally:
                        try:
                            os.remove(req_path)
                            os.remove(res_path)
                        except Exception:
                            pass
            time.sleep(self.poll_interval)
            waited += self.poll_interval
        raise RuntimeError('Timeout waiting for Minimax response file')

    def inspect(self) -> Dict[str, Any]:
        return self._exchange({"op": "inspect"})

    def query(self, kind: str, selector: str, maxChars: int = 20000) -> Dict[str, Any]:
        return self._exchange({"op": "query", "kind": kind, "selector": selector, "max": maxChars})

    def action(self, action_name: str, input: Dict[str, Any]) -> Dict[str, Any]:
        return self._exchange({"op": "action", "name": action_name, "input": input})
