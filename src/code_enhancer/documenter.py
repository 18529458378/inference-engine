"""
文档生成器
自动生成代码文档、注释、API说明、使用示例
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class DocResult:
    """文档生成结果"""
    filename: str
    language: str
    style: str
    original_code: str
    documented_code: str
    documentation: str = ""
    functions_documented: List[str] = field(default_factory=list)
    raw_response: str = ""


class DocumentGenerator:
    """文档生成器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.style = self.config.code_enhancer['documentation']['style']

    def generate_for_file(self, filepath: str, style: str = None,
                           in_place: bool = False) -> DocResult:
        """为文件生成文档"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)
        style = style or self.style

        result = self.generate_for_code(code, filename, language, style)

        if in_place and result.documented_code:
            backup_path = filepath + ".bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(code)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result.documented_code)

        return result

    def generate_for_code(self, code: str, filename: str = "module.py",
                          language: str = None, style: str = None) -> DocResult:
        """为代码生成文档"""
        language = language or self._detect_language(filename)
        style = style or self.style

        prompt = PromptLibrary.get("DOCUMENTATION_GENERATION").format(
            filename=filename,
            language=language,
            style=style,
            code=code
        )

        response = self.llm.complete(prompt, temperature=0.3)

        # 解析文档结果
        documented_code, documentation, functions = self._parse_docs(response.content, language)

        return DocResult(
            filename=filename,
            language=language,
            style=style,
            original_code=code,
            documented_code=documented_code,
            documentation=documentation,
            functions_documented=functions,
            raw_response=response.content,
        )

    def _parse_docs(self, response: str, language: str) -> tuple:
        """解析文档结果"""
        import re

        documented_code = ""
        documentation = ""
        functions = []

        # 提取代码块（带文档注释的代码）
        code_pattern = rf'```{language}\s*\n(.*?)```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)

        if code_matches:
            documented_code = code_matches[-1].strip()
        else:
            generic_matches = re.findall(r'```\s*\n(.*?)```', response, re.DOTALL)
            if generic_matches:
                documented_code = generic_matches[-1].strip()

        # 提取文档说明
        if documented_code:
            code_start = response.find(documented_code[:50])
            if code_start > 0:
                documentation = response[:code_start].strip()

        # 提取已文档化的函数
        if language == "python":
            functions = re.findall(r'def\s+(\w+)', documented_code)

        if not documented_code:
            documented_code = response
            documentation = "解析文档结果失败，请查看原始响应"

        return documented_code, documentation, functions

    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> DocResult:
        return self.generate_for_file(filepath, **kwargs)
