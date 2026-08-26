"""DeepSeek Adapter - deepseek_harness 的工具实现（模拟/集成点）
"""
from typing import Dict, Any


def deepseek_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    # payload: {'query': str, 'project_namespace': str}
    query = payload.get('query')
    # 优先使用本地 FAISS 索引（由环境变量 DEEPSEEK_INDEX_PATH 指定），避免在代码中写入任何密钥
    index_path = os.environ.get('DEEPSEEK_INDEX_PATH')
    try:
        if index_path:
            # 动态导入 faiss，以免在 runner 不可用时代码导入失败
            try:
                import faiss
                import numpy as np
                # 这里假设已存在向量化映射与向量文件，示例为打开索引并做近邻检索
                idx = faiss.read_index(index_path)
                # 简单向量化：使用查询长度为示例（请替换为真正的向量化器）
                qvec = np.array([[len(str(query))]], dtype='float32')
                D, I = idx.search(qvec, 3)
                sources = []
                for score, iid in zip(D[0], I[0]):
                    sources.append({'source': f'faiss_idx_{index_path}', 'score': float(1.0 - (score / (1.0 + score))), 'id': int(iid)})
                result = {'sources': sources, 'summary': f'deepseek faiss results for {str(query)[:200]}'}
                return {'result': result, 'confidence': 0.9, 'warnings': []}
            except Exception:
                # 若 faiss 不可用或索引不适用，回退到模拟
                pass
        # 若未配置索引或索引不可用，允许使用受限的外部 API（通过环境变量 DEEPSEEK_API_KEY），但不将密钥写入仓库
        if os.environ.get('DEEPSEEK_API_KEY'):
            # 在这里仅读取键并传递给外部客户端（客户端需在运行时可用）；此处不实现网络调用以避免明文密钥泄露
            # 返回提示，说明已检测到外部 key，但不会在日志或文件中明文输出
            return {'result': f'external_deepseek_key_detected_but_not_used_in_tests', 'confidence': 0.6, 'warnings': ['external_key_present']}
    except Exception:
        pass
    # fallback: 返回一个模拟的多源聚合结果
    result = {
        'sources': [
            {'source': 'local_index', 'score': 0.55, 'snippet': f'fallback local for {str(query)[:80]}'},
            {'source': 'web_crawl', 'score': 0.45, 'snippet': f'fallback web for {str(query)[:80]}'}
        ],
        'summary': f'deepseek simulated aggregation for {str(query)[:200]}'
    }
    return {'result': result, 'confidence': 0.5, 'warnings': ['fallback_simulation']}
