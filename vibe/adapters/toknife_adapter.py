"""Toknife Adapter - 集成本地或系统安装的 toknife 脚本/库
尝试顺序：
1. 若环境变量 TOKNIFE_PY_PATH 指向脚本目录，则将其加入 sys.path 并导入 json_compressor
2. 若包已安装（unlikely），直接导入
3. 回退到轻量模拟实现
"""
from typing import Dict, Any
import os
import sys


def toknife_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = payload.get('data') or payload.get('task') or payload.get('payload') or ''
    # 如果是 JSON 字符串，尝试压缩
    try:
        # 1. check env var
        p = os.environ.get('TOKNIFE_PY_PATH')
        if p and os.path.isdir(p):
            if p not in sys.path:
                sys.path.insert(0, p)
            try:
                from json_compressor import compress_json_light
                import json
                parsed = json.loads(data) if isinstance(data, str) else data
                return {'result': compress_json_light(parsed), 'confidence': 0.9, 'warnings': []}
            except Exception:
                pass
        # 2. try import as installed package
        try:
            from json_compressor import compress_json_light
            import json
            parsed = json.loads(data) if isinstance(data, str) else data
            return {'result': compress_json_light(parsed), 'confidence': 0.9, 'warnings': []}
        except Exception:
            pass
    except Exception:
        pass
    # fallback: return original data marked as uncompressed
    return {'result': data, 'confidence': 0.3, 'warnings': ['toknife_not_available_fallback']}
