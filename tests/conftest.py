"""
pytest 配置和共享 fixtures
"""

import os
import sys
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_code():
    """示例Python代码"""
    return '''
def find_max(numbers):
    """找到列表中的最大值"""
    if not numbers:
        return None
    max_val = numbers[0]
    for n in numbers:
        if n > max_val:
            max_val = n
    return max_val

def quicksort(arr):
    """快速排序"""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
'''


@pytest.fixture
def sample_question():
    """示例问题"""
    return "一个水池有两个进水管A和B，一个出水管C。单独开A管6小时注满，单独开B管8小时注满，单独开C管12小时放完。如果三管同时开，几小时能注满水池？"


class MockLLMResponse:
    """模拟LLM响应"""
    def __init__(self, content="模拟响应内容", usage=None):
        self.content = content
        self.usage = usage or {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}


@pytest.fixture
def mock_llm():
    """模拟LLM客户端"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.complete.return_value = MockLLMResponse(
        content='{"answer": "模拟答案", "steps": ["步骤1", "步骤2"], "confidence": 0.85}'
    )
    mock.set_model.return_value = None
    mock.set_temperature.return_value = None
    return mock
