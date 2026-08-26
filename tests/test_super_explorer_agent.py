import os
import json
import tempfile
import shutil
import sys
from vibe.agents.super_explorer_agent.agent import SuperExplorerAgent, RepoMetadata


def write_dummy_toknife(path):
    scripts = os.path.join(path, 'toknife', 'scripts')
    os.makedirs(scripts, exist_ok=True)
    content = '''def compress_json_light(data):
    # 简单实现：把 JSON 列表转为 CSV 行（示例）
    if isinstance(data, list):
        keys = sorted(list(data[0].keys())) if data else []
        header = ','.join(keys)
        rows = []
        for item in data:
            rows.append(','.join(str(item.get(k, '')) for k in keys))
        return header + "\n" + "\n".join(rows)
    return str(data)
'''
    with open(os.path.join(scripts, 'json_compressor.py'), 'w', encoding='utf-8') as f:
        f.write(content)
    return scripts


def write_fake_repo(path):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, 'README.md'), 'w', encoding='utf-8') as f:
        f.write('# Fake Repo\n\nThis is a fake repo for smoke test')
    scripts = os.path.join(path, 'scripts')
    os.makedirs(scripts, exist_ok=True)
    # add a minimal json_compressor to emulate a real project
    with open(os.path.join(scripts, 'json_compressor.py'), 'w', encoding='utf-8') as f:
        f.write('def compress_json_light(data):\n    return "a,b\\n1,2"\n')


def test_run_smoke_and_compress():
    tmp = tempfile.mkdtemp(prefix='vibe_test_')
    try:
        # prepare agent work_dir with dummy toknife
        write_dummy_toknife(tmp)
        agent = SuperExplorerAgent(work_dir=tmp)

        # prepare fake repo and call run_smoke_test (bypass clone)
        fake_repo = os.path.join(tmp, 'fake_repo')
        write_fake_repo(fake_repo)
        meta = RepoMetadata(url='local/fake_repo', local_path=fake_repo)
        res = agent.run_smoke_test(meta)
        assert isinstance(res, dict)
        assert 'README found' in ''.join(res.get('notes', [])) or res.get('ok') is False

        # integrate tools should detect local toknife scripts
        integrations = agent.integrate_compress_tools()
        assert 'toknife' in integrations and integrations['toknife'] is True

        # compress payload with JSON -> should use toknife fallback and return compressed string
        payload = json.dumps([{"a":1, "b":2}])
        out = agent.compress_payload(payload)
        assert isinstance(out, dict)
        # either claw_compactor used or toknife; ensure compressed present
        assert 'compressed' in out
    finally:
        shutil.rmtree(tmp)
