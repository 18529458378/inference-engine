"""
测试用例生成器
自动生成单元测试、边界测试、错误处理测试
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class TestResult:
    """测试生成结果"""
    filename: str
    language: str
    framework: str
    original_code: str
    test_code: str
    test_cases: List[str] = field(default_factory=list)
    coverage_estimate: float = 0.0
    raw_response: str = ""

    @property
    def test_filename(self) -> str:
        """测试文件名"""
        base = os.path.splitext(self.filename)[0]
        if self.framework == "pytest":
            return f"test_{base}.py"
        elif self.framework == "unittest":
            return f"test_{base}.py"
        return f"{base}_test.{self.language}"


class TestGenerator:
    """测试用例生成器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.framework = self.config.code_enhancer['test_generation']['framework']
        self.coverage_target = self.config.code_enhancer['test_generation']['coverage_target']

    def generate_for_file(self, filepath: str, framework: str = None,
                           output_path: str = None) -> TestResult:
        """为文件生成测试"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)
        framework = framework or self.framework

        result = self.generate_for_code(code, filename, language, framework)

        # 保存测试文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.test_code)

        return result

    def generate_for_code(self, code: str, filename: str = "module.py",
                           language: str = None, framework: str = None) -> TestResult:
        """为代码生成测试"""
        language = language or self._detect_language(filename)
        framework = framework or self.framework

        prompt = PromptLibrary.get("TEST_GENERATION").format(
            filename=filename,
            language=language,
            framework=framework,
            coverage=self.coverage_target,
            code=code
        )

        response = self.llm.complete(prompt, temperature=0.3)

        # 解析测试代码
        test_code, test_cases = self._parse_tests(response.content, language)

        return TestResult(
            filename=filename,
            language=language,
            framework=framework,
            original_code=code,
            test_code=test_code,
            test_cases=test_cases,
            coverage_estimate=self.coverage_target / 100.0,
            raw_response=response.content,
        )

    def _parse_tests(self, response: str, language: str) -> tuple:
        """解析测试代码"""
        import re

        test_code = ""
        test_cases = []

        # 提取代码块
        code_pattern = rf'```{language}\s*\n(.*?)```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)

        if code_matches:
            test_code = code_matches[-1].strip()
        else:
            generic_matches = re.findall(r'```\s*\n(.*?)```', response, re.DOTALL)
            if generic_matches:
                test_code = generic_matches[-1].strip()

        # 提取测试用例名称
        if language == "python":
            test_funcs = re.findall(r'def\s+(test_\w+)', test_code)
            test_cases = test_funcs
        elif language in ["javascript", "typescript"]:
            test_funcs = re.findall(r'(?:it|test)\s*\(\s*[\'"]([^\'"]+)[\'"]', test_code)
            test_cases = test_funcs

        if not test_code:
            test_code = response
            test_cases = []

        return test_code, test_cases

    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> TestResult:
        return self.generate_for_file(filepath, **kwargs)
