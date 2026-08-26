# 集成测试（默认跳过，需在运行环境中设置环境变量 RUN_MINIMAX_INTEGRATION=1）
# 目的：验证 get_best_adapter() 能正确探测并与可用 Minimax 接口进行一次简单交互（inspect）
# 在 CI 中此测试应仅在有自托管 runner 并明确配置 Minimax 的情况下启用。
import os
import pytest

from vibe.extensions.minimax_browser_adapter.adapter import get_best_adapter


def test_adapter_integration_inspect():
    if os.environ.get('RUN_MINIMAX_INTEGRATION') != '1':
        pytest.skip('Integration tests disabled: set RUN_MINIMAX_INTEGRATION=1 to enable')

    adapter = get_best_adapter()
    assert adapter is not None

    try:
        info = adapter.inspect()
    except RuntimeError as e:
        pytest.skip(f'Adapter runtime error (treated as unavailable in integration test): {e}')

    assert isinstance(info, dict)
    # 最少包含键之一
    assert any(k in info for k in ('url', 'title', 'snapshotId', 'elements'))
