"""
代码解释器
解释代码功能、逻辑、算法、设计意图
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class ExplanationResult:
    """代码解释结果"""
    filename: str
    language: str
    level: str  # beginner / intermediate / advanced
    summary: str = ""
    overall_purpose: str = ""
    key_components: List[Dict] = field(default_factory=list)
    algorithm_explanation: str = ""
    data_flow: str = ""
    edge_cases: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    raw_response: str = ""

    def to_dict(self) -> Dict:
        return {
            "filename": self.filename,
            "language": self.language,
            "level": self.level,
            "summary": self.summary,
            "overall_purpose": self.overall_purpose,
            "key_components": self.key_components,
            "algorithm_explanation": self.algorithm_explanation,
            "data_flow": self.data_flow,
            "edge_cases": self.edge_cases,
            "potential_issues": self.potential_issues,
        }


class CodeExplainer:
    """代码解释器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()

    def explain_file(self, filepath: str, level: str = "intermediate") -> ExplanationResult:
        """解释代码文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        language = self._detect_language(filepath)

        return self.explain_code(code, filename, language, level)

    def explain_code(self, code: str, filename: str = "code.py",
                     language: str = None, level: str = "intermediate") -> ExplanationResult:
        """解释代码字符串"""
        language = language or self._detect_language(filename)

        prompt = f"""请详细解释以下代码，面向{level}水平的读者。

文件: {filename}
语言: {language}

代码:
```{language}
{code}
```

请按以下结构解释（用中文）：

## 1. 总体概述
一句话总结这段代码的作用。

## 2. 核心组件
列出代码中的关键函数/类/模块，每个说明：
- 名称
- 职责
- 输入输出

## 3. 算法/逻辑详解
详细解释代码的核心算法或业务逻辑，包括：
- 处理步骤
- 关键决策点
- 数据结构使用

## 4. 数据流
描述数据如何在代码中流动和转换。

## 5. 边界情况
列出代码处理或未处理的边界情况。

## 6. 潜在问题
指出代码中可能存在的问题或改进空间。

请用清晰的Markdown格式输出。"""

        response = self.llm.complete(prompt, temperature=0.3)

        # 解析解释结果
        result = self._parse_explanation(response.content, filename, language, level)
        result.raw_response = response.content

        return result

    def _parse_explanation(self, response: str, filename: str,
                            language: str, level: str) -> ExplanationResult:
        """解析解释结果"""
        result = ExplanationResult(
            filename=filename,
            language=language,
            level=level,
            summary=response[:200],
        )

        # 提取各部分
        sections = self._extract_sections(response)

        if "总体概述" in sections:
            result.summary = sections["总体概述"]
            result.overall_purpose = sections["总体概述"]

        if "核心组件" in sections:
            result.key_components = self._parse_components(sections["核心组件"])

        if "算法" in sections or "逻辑详解" in sections:
            key = "算法" if "算法" in sections else "逻辑详解"
            result.algorithm_explanation = sections[key]

        if "数据流" in sections:
            result.data_flow = sections["数据流"]

        if "边界情况" in sections:
            result.edge_cases = self._parse_list(sections["边界情况"])

        if "潜在问题" in sections:
            result.potential_issues = self._parse_list(sections["潜在问题"])

        return result

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """提取Markdown章节"""
        sections = {}
        current_section = None
        current_content = []

        for line in text.split('\n'):
            # 匹配 ## 标题
            match = re.match(r'^#{1,3}\s*(.+?)(?:\s*$)', line)
            if match:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _parse_components(self, text: str) -> List[Dict]:
        """解析核心组件列表"""
        components = []
        # 简单解析：按项目符号分割
        items = re.split(r'\n[-*]\s*', text)
        for item in items:
            if item.strip():
                components.append({"description": item.strip()[:200]})
        return components[:10]

    def _parse_list(self, text: str) -> List[str]:
        """解析列表"""
        items = re.findall(r'[-*]\s*(.+?)(?=\n[-*]|\n\n|$)', text, re.DOTALL)
        return [item.strip() for item in items if item.strip()][:10]

    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.c': 'c', '.cpp': 'cpp',
            '.go': 'go', '.rs': 'rust',
        }
        return lang_map.get(ext, 'text')

    def __call__(self, filepath: str, **kwargs) -> ExplanationResult:
        return self.explain_file(filepath, **kwargs)
