"""MiniMax FileExchange stub responder

监视 request_dir 下的 req_*.json 文件并写入对应 res_*.json 响应。
用于本地集成测试时模拟 Minimax 的文件交换响应。
"""
import os
import time
import json
import glob

REQ_GLOB = os.environ.get('MINIMAX_REQUEST_DIR')
if not REQ_GLOB:
    REQ_GLOB = os.path.join(os.getcwd(), 'minimax_requests')
os.makedirs(REQ_GLOB, exist_ok=True)
print(f"MiniMax stub watching: {REQ_GLOB}")

POLL = 0.2

try:
    while True:
        reqs = glob.glob(os.path.join(REQ_GLOB, 'req_*.json'))
        for req in reqs:
            try:
                with open(req, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
            except Exception:
                payload = None
            ts = os.path.splitext(os.path.basename(req))[0].split('_', 1)[1]
            res_path = os.path.join(REQ_GLOB, f'res_{ts}.json')
            if payload and isinstance(payload, dict):
                op = payload.get('op')
                # 简单模拟 inspect 返回
                if op == 'inspect':
                    resp = {"url": "https://example.com", "title": "Example", "snapshotId": "stub-1", "elements": [], "success": True}
                elif op == 'query':
                    resp = {"text": "示例页面内容", "truncated": False}
                elif op == 'action':
                    resp = {"status": "ok", "detail": "stubbed"}
                else:
                    resp = {"error": "unknown op", "payload": payload}
            else:
                resp = {"error": "invalid request"}
            with open(res_path, 'w', encoding='utf-8') as f:
                json.dump(resp, f, ensure_ascii=False)
            # remove request file to signal handled
            try:
                os.remove(req)
            except Exception:
                pass
        time.sleep(POLL)
except KeyboardInterrupt:
    print('stub exiting')
