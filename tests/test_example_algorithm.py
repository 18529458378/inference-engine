from vibe.algorithm.example_algorithm import score_chinese_vibe


def test_score_non_empty():
    text = '我喜欢中文的 vibe，感觉很好。'
    score = score_chinese_vibe(text)
    assert score > 0.0


def test_empty():
    assert score_chinese_vibe('') == 0.0
