"""
代码审查器
安全漏洞、性能问题、代码规范、Bug检测
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class CodeIssue:
    """代码问题"""
    id: int
    category: str  # security / performance / style / bug / maintainability
    severity: str  # critical / high / medium / low / info
    title: str
    description: str
    location: str = ""
    suggestion: str = ""
    fixed_code: str = ""


@dataclass
class ReviewResult:
    """代码审查结果"""
    filename: str
    language: str
    overall_score: float
    summary: str
    issues: List[CodeIssue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    raw_response: str = ""

    def to_dict(self) -> Dict:
        return {
            "filename": self.filename,
            "language": self.language,
            "overall_score": self.overall_score,
            "summary": self.summary,
            "issues": [issue.__dict__ for issue in self.issues],
            "strengths": self.strengths,
            "recommendations": self.recommendations,
        }

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "high")


class CodeReviewer:
    """代码审查器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.categories = self.config.code_enhancer['review']['categories']

    def review_file(self, filepath: str, categories: List[str] = None) -> ReviewResult:
        """审查单个文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)

        return self.review_code(code, filename, language, categories)

    def review_code(self, code: str, filename: str = "code.py",
                    language: str = None, categories: List[str] = None) -> ReviewResult:
        """审查代码字符串"""
        language = language or self._detect_language(filename)
        categories = categories or self.categories

        prompt = PromptLibrary.get("CODE_REVIEW").format(
            filename=filename,
            language=language,
            code=code
        )

        response = self.llm.complete(prompt, temperature=0.2)

        # 解析审查结果
        result = self._parse_review(response.content, filename, language)
        result.raw_response = response.content

        return result

    def _parse_review(self, response: str, filename: str, language: str) -> ReviewResult:
        """解析审查结果"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                issues = []
                for issue_data in data.get("issues", []):
                    issue = CodeIssue(
                        id=issue_data.get("id", len(issues) + 1),
                        category=issue_data.get("category", "style"),
                        severity=issue_data.get("severity", "info"),
                        title=issue_data.get("title", ""),
                        description=issue_data.get("description", ""),
                        location=issue_data.get("location", ""),
                        suggestion=issue_data.get("suggestion", ""),
                        fixed_code=issue_data.get("fixed_code", "")
                    )
                    issues.append(issue)

                return ReviewResult(
                    filename=filename,
                    language=language,
                    overall_score=data.get("overall_score", 70),
                    summary=data.get("summary", ""),
                    issues=issues,
                    strengths=data.get("strengths", []),
                    recommendations=data.get("recommendations", []),
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        # 解析失败，返回原始响应
        return ReviewResult(
            filename=filename,
            language=language,
            overall_score=50,
            summary="解析审查结果失败，请查看原始响应",
            raw_response=response
        )

    def _detect_language(self, filename: str) -> str:
        """根据文件名检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> ReviewResult:
        return self.review_file(filepath, **kwargs)
