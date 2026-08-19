"""
代码复杂度分析器
圈复杂度、Halstead复杂度、可维护性指数、认知复杂度
"""

import os
import re
import ast
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class ComplexityResult:
    """复杂度分析结果"""
    filename: str
    language: str
    overall_quality: str  # excellent / good / fair / poor
    metrics: Dict[str, Any] = field(default_factory=dict)
    complexity_analysis: str = ""
    technical_debt: List[Dict] = field(default_factory=list)
    risk_areas: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    raw_response: str = ""

    def to_dict(self) -> Dict:
        return {
            "filename": self.filename,
            "language": self.language,
            "overall_quality": self.overall_quality,
            "metrics": self.metrics,
            "complexity_analysis": self.complexity_analysis,
            "technical_debt": self.technical_debt,
            "risk_areas": self.risk_areas,
            "recommendations": self.recommendations,
        }


class ComplexityAnalyzer:
    """代码复杂度分析器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.metrics = self.config.code_enhancer['complexity']['metrics']
        self.thresholds = self.config.code_enhancer['complexity']['thresholds']

    def analyze_file(self, filepath: str) -> ComplexityResult:
        """分析单个文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)

        return self.analyze_code(code, filename, language)

    def analyze_code(self, code: str, filename: str = "code.py",
                     language: str = None) -> ComplexityResult:
        """分析代码字符串"""
        language = language or self._detect_language(filename)

        # 1. 静态分析（Python）
        static_metrics = {}
        if language == "python":
            static_metrics = self._analyze_python(code)

        # 2. LLM 深度分析
        prompt = PromptLibrary.get("COMPLEXITY_ANALYSIS").format(
            filename=filename,
            language=language,
            code=code
        )

        response = self.llm.complete(prompt, temperature=0.2)

        # 解析结果
        result = self._parse_analysis(response.content, filename, language)
        result.metrics.update(static_metrics)
        result.raw_response = response.content

        return result

    def _analyze_python(self, code: str) -> Dict:
        """Python 静态复杂度分析"""
        metrics = {
            "lines_of_code": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "code_lines": 0,
            "functions": 0,
            "classes": 0,
            "avg_function_length": 0,
            "max_function_length": 0,
            "avg_cyclomatic_complexity": 0,
            "max_cyclomatic_complexity": 0,
            "comment_ratio": 0.0,
        }

        lines = code.split('\n')
        metrics["lines_of_code"] = len(lines)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics["blank_lines"] += 1
            elif stripped.startswith('#'):
                metrics["comment_lines"] += 1
            else:
                metrics["code_lines"] += 1

        # AST 分析
        try:
            tree = ast.parse(code)

            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node)

            metrics["functions"] = len(functions)
            metrics["classes"] = len(classes)

            # 函数长度和圈复杂度
            function_lengths = []
            complexities = []

            for func in functions:
                # 函数长度（行数）
                if hasattr(func, 'end_lineno') and func.end_lineno:
                    length = func.end_lineno - func.lineno + 1
                    function_lengths.append(length)

                # 简单圈复杂度（决策点计数）
                complexity = 1
                for node in ast.walk(func):
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.And, ast.Or,
                                         ast.ExceptHandler, ast.With, ast.Assert)):
                        complexity += 1
                    elif isinstance(node, ast.BoolOp):
                        complexity += len(node.values) - 1
                complexities.append(complexity)

            if function_lengths:
                metrics["avg_function_length"] = sum(function_lengths) / len(function_lengths)
                metrics["max_function_length"] = max(function_lengths)

            if complexities:
                metrics["avg_cyclomatic_complexity"] = sum(complexities) / len(complexities)
                metrics["max_cyclomatic_complexity"] = max(complexities)

            # 注释率
            if metrics["lines_of_code"] > 0:
                metrics["comment_ratio"] = metrics["comment_lines"] / metrics["lines_of_code"]

        except SyntaxError:
            metrics["parse_error"] = True

        return metrics

    def _parse_analysis(self, response: str, filename: str, language: str) -> ComplexityResult:
        """解析分析结果"""
        import json

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                return ComplexityResult(
                    filename=filename,
                    language=language,
                    overall_quality=data.get("overall_quality", "fair"),
                    metrics=data.get("metrics", {}),
                    complexity_analysis=data.get("complexity_analysis", ""),
                    technical_debt=data.get("technical_debt", []),
                    risk_areas=data.get("risk_areas", []),
                    recommendations=data.get("recommendations", []),
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return ComplexityResult(
            filename=filename,
            language=language,
            overall_quality="unknown",
            complexity_analysis="解析分析结果失败，请查看原始响应",
        )

    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.c': 'c', '.cpp': 'cpp',
            '.go': 'go', '.rs': 'rust',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> ComplexityResult:
        return self.analyze_file(filepath, **kwargs)
