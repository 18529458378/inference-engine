"""
代码重构器
代码重构、设计模式应用、可维护性提升
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class RefactorResult:
    """代码重构结果"""
    filename: str
    language: str
    target: str
    original_code: str
    refactored_code: str
    changes: List[str] = field(default_factory=list)
    explanation: str = ""
    raw_response: str = ""

    @property
    def diff_summary(self) -> str:
        """变更摘要"""
        original_lines = len(self.original_code.split('\n'))
        refactored_lines = len(self.refactored_code.split('\n'))
        return f"原始: {original_lines}行 → 重构后: {refactored_lines}行"


class CodeRefactorer:
    """代码重构器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.targets = self.config.code_enhancer['refactor']['targets']

    def refactor_file(self, filepath: str, target: str = "clean_code",
                       in_place: bool = False) -> RefactorResult:
        """重构单个文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)

        result = self.refactor_code(code, filename, language, target)

        # 原地修改
        if in_place and result.refactored_code:
            backup_path = filepath + ".bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(code)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result.refactored_code)

        return result

    def refactor_code(self, code: str, filename: str = "code.py",
                      language: str = None, target: str = "clean_code") -> RefactorResult:
        """重构代码字符串"""
        language = language or self._detect_language(filename)

        prompt = PromptLibrary.get("CODE_REFACTOR").format(
            filename=filename,
            language=language,
            target=target,
            code=code
        )

        response = self.llm.complete(prompt, temperature=0.3)

        # 解析重构结果
        refactored_code, explanation, changes = self._parse_refactor(response.content, language)

        return RefactorResult(
            filename=filename,
            language=language,
            target=target,
            original_code=code,
            refactored_code=refactored_code,
            changes=changes,
            explanation=explanation,
            raw_response=response.content,
        )

    def _parse_refactor(self, response: str, language: str) -> tuple:
        """解析重构结果"""
        import re

        refactored_code = ""
        explanation = ""
        changes = []

        # 提取代码块
        code_pattern = rf'```{language}\s*\n(.*?)```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)

        if code_matches:
            # 取最后一个代码块作为重构后的代码
            refactored_code = code_matches[-1].strip()
        else:
            # 尝试通用代码块
            generic_matches = re.findall(r'```\s*\n(.*?)```', response, re.DOTALL)
            if generic_matches:
                refactored_code = generic_matches[-1].strip()

        # 提取说明（代码块之前的文本）
        if refactored_code:
            code_start = response.find(refactored_code[:50])
            if code_start > 0:
                explanation = response[:code_start].strip()

        # 提取变更点
        change_pattern = r'[\-\*]\s*(.+?)(?=\n[\-\*]|\n\n|$)'
        changes = [m.strip() for m in re.findall(change_pattern, explanation) if len(m.strip()) > 10]

        # 如果没有解析到代码，返回原始响应
        if not refactored_code:
            refactored_code = response
            explanation = "解析重构结果失败，请查看原始响应"

        return refactored_code, explanation, changes

    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.c': 'c', '.cpp': 'cpp',
            '.go': 'go', '.rs': 'rust', '.rb': 'ruby',
            '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> RefactorResult:
        return self.refactor_file(filepath, **kwargs)
