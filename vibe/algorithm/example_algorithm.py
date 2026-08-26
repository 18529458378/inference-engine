"""
示例算法脚手架：中文 Vibe 简单文本评分算法（可运行示例）

说明：该文件为轻量可运行示例（纯 Python），用于展示如何将算法封装为可测试函数。
"""

def score_chinese_vibe(text: str) -> float:
    """对输入文本计算一个简单的“Vibe”分数（0.0-1.0）。

    规则（示例）：
    - 包含情感词（如“好”“爱”）加分
    - 包含关键词“中文”或“vibe”加分
    - 长度适中（5-200 字）得分更高
    """
    if not text:
        return 0.0
    s = text.lower()
    score = 0.0
    for w in ['好','爱','喜欢','开心','愉快']:
        if w in text:
            score += 0.2
    if '中文' in text or 'vibe' in s:
        score += 0.2
    length = len(text)
    if 5 <= length <= 200:
        score += 0.2
    return min(1.0, score)


if __name__ == '__main__':
    demo = '我很喜欢这个中文 vibe 的风格，感觉很愉快。'
    print('示例输入：', demo)
    print('Vibe 分数：', score_chinese_vibe(demo))
