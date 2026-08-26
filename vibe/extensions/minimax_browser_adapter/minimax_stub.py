"""MiniMax FileExchange stub responder (增强版)

功能：
- 监视 request_dir 下的 req_*.json 请求，并写入对应 res_*.json 响应
- 支持常见 Browser 操作模拟：inspect、query、action、navigate、get-dom、html-to-markdown、screenshot、wait-for
- 支持简单延迟/错误注入（通过请求字段模拟），便于集成测试校准

注意：仅用于本地测试与 CI 上的 self-hosted runner。不会执行任何真实浏览器操作。
"""
import os
import time
import json
import glob
import base64
from typing import Any

REQ_DIR = os.environ.get('MINIMAX_REQUEST_DIR')
if not REQ_DIR:
    REQ_DIR = os.path.join(os.getcwd(), 'minimax_requests')
os.makedirs(REQ_DIR, exist_ok=True)
print(f"MiniMax stub watching: {REQ_DIR}")

POLL = float(os.environ.get('MINIMAX_STUB_POLL', '0.25'))
DEFAULT_SNAPSHOT_ID = 'stub-snapshot-1'


def _dummy_screenshot_b64() -> str:
    # 返回极短的占位 base64 PNG（1x1 transparent pixel）
    return 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='


def _html_to_markdown(html: str) -> str:
    # 极简转换：去掉标签
    import re
    text = re.sub(r'<[^>]+>', '', html)
    return text.strip()


def _handle_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return {"error": "invalid payload"}
    op = payload.get('op')
    # optional test controls
    if payload.get('inject_delay'):
        try:
            time.sleep(float(payload['inject_delay']))
        except Exception:
            pass
    if payload.get('inject_error'):
        return {"error": payload.get('inject_error')}

    if op == 'inspect':
        return {
            "url": payload.get('url', 'https://example.com'),
            "title": payload.get('title', 'Example Page'),
            "snapshotId": payload.get('snapshotId', DEFAULT_SNAPSHOT_ID),
            "elements": payload.get('elements', []),
            "truncated": False,
            "success": True
        }
    if op == 'query':
        return {"text": payload.get('text', '示例页面内容'), "truncated": False}
    if op == 'action':
        name = payload.get('name')
        return {"status": "ok", "action": name, "detail": payload.get('detail', 'stubbed')}
    if op == 'navigate':
        return {"success": True, "navigated": payload.get('url', 'https://example.com')}
    if op == 'get-dom' or op == 'getDOM':
        return {"dom": payload.get('dom', '<html><body>示例</body></html>'), "success": True}
    if op == 'html-to-markdown' or op == 'htmlToMarkdown':
        html = payload.get('html', '<p>示例</p>')
        return {"markdown": _html_to_markdown(html), "success": True}
    if op == 'screenshot' or op == 'get-screenshot':
        return {"b64png": _dummy_screenshot_b64(), "success": True}
    if op == 'wait-for':
        # 模拟成功等待
        return {"success": True}
    # fallback
    return {"error": "unknown op", "op": op}


try:
    while True:
        reqs = glob.glob(os.path.join(REQ_DIR, 'req_*.json'))
        for req in reqs:
            try:
                with open(req, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
            except Exception as e:
                payload = {"error": f"failed to read request: {e}"}
            ts = os.path.splitext(os.path.basename(req))[0].split('_', 1)[1]
            res_path = os.path.join(REQ_DIR, f'res_{ts}.json')
            resp = _handle_payload(payload)
            try:
                with open(res_path, 'w', encoding='utf-8') as f:
                    json.dump(resp, f, ensure_ascii=False)
            except Exception as e:
                print(f"Failed writing response {res_path}: {e}")
            # remove request file to signal handled
            try:
                os.remove(req)
            except Exception:
                pass
        time.sleep(POLL)
except KeyboardInterrupt:
    print('stub exiting')
