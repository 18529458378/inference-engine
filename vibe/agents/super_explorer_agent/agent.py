# Super Explorer Agent - scaffold 实现（中文注释）
# 目的：自动抓取/整合外部资源（如 toknife、claw-compactor），并暴露本地适配器接口供 Vibe 引擎使用。

import os
import subprocess
import shutil
import tempfile
import json
from dataclasses import dataclass
from typing import Optional

# 轻量日志
def _log(msg: str):
    print(f"[super-explorer] {msg}")

@dataclass
class RepoMetadata:
    url: str
    local_path: str
    commit: Optional[str] = None
    license: Optional[str] = None

class SuperExplorerAgent:
    """简单 scaffold：提供 clone、静态检查、导入自检与包装接口。"""
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = work_dir or os.path.join(os.getcwd(), "vibe_external")
        os.makedirs(self.work_dir, exist_ok=True)
        _log(f"工作目录: {self.work_dir}")

    def clone_repo(self, repo: str) -> RepoMetadata:
        """使用 gh CLI（已授权）克隆到临时目录并返回元数据。"""
        name = repo.split('/')[-1]
        dest = os.path.join(self.work_dir, name)
        if os.path.exists(dest):
            _log(f"已存在，先删除: {dest}")
            shutil.rmtree(dest)
        _log(f"克隆 {repo} -> {dest}")
        subprocess.check_call(["gh", "repo", "clone", repo, dest])
        # 获取最新 commit
        try:
            out = subprocess.check_output(["git", "-C", dest, "rev-parse", "HEAD"], text=True)
            commit = out.strip()
        except Exception:
            commit = None
        return RepoMetadata(url=repo, local_path=dest, commit=commit)

    def run_smoke_test(self, repo_meta: RepoMetadata) -> dict:
        """对已克隆仓库运行轻量自检：查看 README、尝试 import 或运行提供的示例命令。返回结果字典。
        注意：真实安装可能需要网络或额外权限，本函数仅做尽可能无害的自检。"""
        res = {"repo": repo_meta.url, "ok": False, "notes": []}
        readme = os.path.join(repo_meta.local_path, "README.md")
        if os.path.exists(readme):
            with open(readme, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(2000)
            res["notes"].append("README found")
        else:
            res["notes"].append("README not found")
        # 尝试按 README 指南做一个安全的导入测试（例如 toknife 的 scripts/json_compressor）
        scripts_dir = os.path.join(repo_meta.local_path, "scripts")
        if os.path.isdir(scripts_dir):
            # 不修改系统路径永久配置，尝试用 subprocess 调用 python -c 导入并运行最小示例
            cmd = ["python", "-c", (
                f"import sys; sys.path.insert(0, r'{scripts_dir}');\n"
                "try:\n"
                "  from json_compressor import compress_json_light; print('IMPORT_OK')\n"
                "except Exception as e:\n"
                "  print('IMPORT_FAIL', e)\n"
            )]
            try:
                out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
                res["notes"].append(out.strip())
                if 'IMPORT_OK' in out:
                    res["ok"] = True
            except subprocess.CalledProcessError as e:
                res["notes"].append(f"smoke test failed: {e.output[:1000]}")
        else:
            res["notes"].append("no scripts/ for quick import test")
        return res

    def integrate_compress_tools(self):
        """示例：检测并加载 claw-compactor（已安装为包）以及库形式的 toknife（如在本地脚本目录）。"""
        integrations = {"claw_compactor": False, "toknife": False}
        try:
            import claw_compactor
            integrations["claw_compactor"] = True
            _log("claw_compactor 可用")
        except Exception as e:
            _log(f"claw_compactor 不可用: {e}")
        # toknife: 检查是否在工作目录下有 toknife 脚本
        toknife_path = os.path.join(self.work_dir, "toknife", "scripts")
        if os.path.isdir(toknife_path):
            integrations["toknife"] = True
            _log("toknife scripts 可用（可直接导入）")
        return integrations

    def compress_payload(self, payload: str) -> dict:
        """示例封装：根据可用工具选择压缩器（优先 claw_compactor, 否则 toknife 脚本）。返回 { tool, compressed }。"""
        # 优先使用 claw_compactor（如果 import 可用）
        try:
            import claw_compactor
            # 简短示例：调用 API 的压缩入口（具体接口请依据实际包实现）
            try:
                result = claw_compactor.compress_text(payload)
            except Exception:
                # 回退到示例 API 名称
                result = claw_compactor.compress(payload)
            return {"tool": "claw_compactor", "compressed": result}
        except Exception:
            # 回退到 toknife 的轻量脚本（如果存在）
            scripts_path = os.path.join(self.work_dir, "toknife", "scripts")
            if os.path.isdir(scripts_path):
                import sys
                sys.path.insert(0, scripts_path)
                try:
                    from json_compressor import compress_json_light
                    # 假设 payload 是 JSON 字符串或可解析为 JSON
                    try:
                        parsed = json.loads(payload)
                        comp = compress_json_light(parsed)
                        return {"tool": "toknife.json_compressor", "compressed": comp}
                    except Exception:
                        # 非 JSON 文本，返回原文标记
                        return {"tool": "toknife", "compressed": payload}
                except Exception as e:
                    _log(f"toknife 调用失败: {e}")
        return {"tool": None, "compressed": payload}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Super Explorer Agent - scaffold')
    p.add_argument('--clone', help='要克隆的 repo，比如 momogigi123/toknife', nargs='*')
    args = p.parse_args()
    agent = SuperExplorerAgent()
    if args.clone:
        results = []
        for r in args.clone:
            meta = agent.clone_repo(r)
            res = agent.run_smoke_test(meta)
            results.append(res)
        print('\nSUMMARY:')
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print('可用命令示例：--clone momogigi123/toknife open-compress/claw-compactor')
