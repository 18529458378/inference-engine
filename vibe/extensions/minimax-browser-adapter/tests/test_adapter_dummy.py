from vibe.extensions.minimax_browser_adapter.adapter import MinimaxBrowserAdapter, CLIProxyMinimaxAdapter


def test_inspect_placeholder():
    adapter = MinimaxBrowserAdapter()
    res = adapter.inspect()
    assert isinstance(res, dict)


def test_cli_proxy_not_found():
    proxy = CLIProxyMinimaxAdapter(cli_path='nonexistent-minimax-cli')
    try:
        proxy.inspect()
    except RuntimeError as e:
        assert 'not found' in str(e)
    else:
        assert False, 'Expected RuntimeError when CLI missing' 
