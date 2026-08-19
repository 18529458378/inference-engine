"""
代码性能优化器
时间复杂度优化、空间复杂度优化、IO优化、并发优化
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class OptimizationResult:
    """性能优化结果"""
    filename: str
    language: str
    focus: List[str]
    original_code: str
    optimized_code: str
    analysis: str = ""
    optimizations: List[Dict] = field(default_factory=list)
    expected_improvement: str = ""
    raw_response: str = ""

    @property
    def diff_summary(self) -> str:
        original_lines = len(self.original_code.split('\n'))
        optimized_lines = len(self.optimized_code.split('\n'))
        return f"原始: {original_lines}行 → 优化后: {optimized_lines}行"


class CodeOptimizer:
    """代码性能优化器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.focus = self.config.code_enhancer['optimization']['focus']

    def optimize_file(self, filepath: str, focus: List[str] = None,
                      in_place: bool = False) -> OptimizationResult:
        """优化单个文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)
        focus = focus or self.focus

        result = self.optimize_code(code, filename, language, focus)

        if in_place and result.optimized_code:
            backup_path = filepath + ".bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(code)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result.optimized_code)

        return result

    def optimize_code(self, code: str, filename: str = "code.py",
                      language: str = None, focus: List[str] = None) -> OptimizationResult:
        """优化代码字符串"""
        language = language or self._detect_language(filename)
        focus = focus or self.focus
        focus_str = ", ".join(focus)

        prompt = PromptLibrary.get("CODE_OPTIMIZE").format(
            filename=filename,
            language=language,
            focus=focus_str,
            code=code
        )

        response = self.llm.complete(prompt, temperature=0.3)

        # 解析优化结果
        optimized_code, analysis, optimizations = self._parse_optimization(response.content, language)

        return OptimizationResult(
            filename=filename,
            language=language,
            focus=focus,
            original_code=code,
            optimized_code=optimized_code,
            analysis=analysis,
            optimizations=optimizations,
            raw_response=response.content,
        )

    def _parse_optimization(self, response: str, language: str) -> tuple:
        """解析优化结果"""
        import re

        optimized_code = ""
        analysis = ""
        optimizations = []

        # 提取代码块
        code_pattern = rf'```{language}\s*\n(.*?)```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)

        if code_matches:
            optimized_code = code_matches[-1].strip()
        else:
            generic_matches = re.findall(r'```\s*\n(.*?)```', response, re.DOTALL)
            if generic_matches:
                optimized_code = generic_matches[-1].strip()

        # 提取分析说明
        if optimized_code:
            code_start = response.find(optimized_code[:50])
            if code_start > 0:
                analysis = response[:code_start].strip()

        # 提取优化点
        opt_pattern = r'[\-\*]\s*(.+?)(?=\n[\-\*]|\n\n|$)'
        optimizations = [m.strip() for m in re.findall(opt_pattern, analysis) if len(m.strip()) > 10]

        if not optimized_code:
            optimized_code = response
            analysis = "解析优化结果失败，请查看原始响应"

        return optimized_code, analysis, optimizations

    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.c': 'c', '.cpp': 'cpp',
            '.go': 'go', '.rs': 'rust',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> OptimizationResult:
        return self.optimize_file(filepath, **kwargs)
