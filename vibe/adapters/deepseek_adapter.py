"""DeepSeek Adapter - deepseek_harness 的工具实现（模拟/集成点）
"""
from typing import Dict, Any


def deepseek_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    # payload: {'query': str, 'project_namespace': str}
    # 优先调用已安装的检索工具（示例：whoosh/elastic 等）——此处为模拟
    query = payload.get('query')
    # 返回一个模拟的多源聚合结果
    result = {
        'sources': [
            {'source': 'local_index', 'score': 0.92, 'snippet': f'found locally for {str(query)[:80]}'},
            {'source': 'web_crawl', 'score': 0.78, 'snippet': f'web result for {str(query)[:80]}'}
        ],
        'summary': f'deepseek simulated aggregation for {str(query)[:200]}'
    }
    return {'result': result, 'confidence': 0.88, 'warnings': []}
