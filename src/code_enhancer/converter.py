"""
代码转换器
在不同编程语言/框架/风格之间转换代码
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class ConversionResult:
    """代码转换结果"""
    source_language: str
    target_language: str
    original_code: str
    converted_code: str
    changes: List[str] = field(default_factory=list)
    notes: str = ""
    confidence: float = 0.0
    raw_response: str = ""

    @property
    def diff_summary(self) -> str:
        original_lines = len(self.original_code.split('\n'))
        converted_lines = len(self.converted_code.split('\n'))
        return f"{self.source_language}({original_lines}行) → {self.target_language}({converted_lines}行)"


class CodeConverter:
    """代码转换器"""

    # 支持的语言映射
    LANGUAGE_ALIASES = {
        'py': 'python', 'python': 'python',
        'js': 'javascript', 'javascript': 'javascript',
        'ts': 'typescript', 'typescript': 'typescript',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp', 'c++': 'cpp',
        'go': 'golang', 'golang': 'golang',
        'rs': 'rust', 'rust': 'rust',
        'rb': 'ruby', 'ruby': 'ruby',
        'php': 'php',
        'cs': 'csharp', 'csharp': 'csharp', 'c#': 'csharp',
        'kt': 'kotlin', 'kotlin': 'kotlin',
        'swift': 'swift',
        'scala': 'scala',
    }

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()

    def convert_file(self, filepath: str, target_language: str,
                     in_place: bool = False) -> ConversionResult:
        """转换代码文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        filename = os.path.basename(filepath)
        source_language = self._detect_language(filepath)
        target_language = self._normalize_language(target_language)

        result = self.convert_code(code, source_language, target_language, filename)

        if in_place and result.converted_code:
            # 生成新文件名
            new_ext = self._get_extension(target_language)
            base = os.path.splitext(filepath)[0]
            new_filepath = f"{base}.{new_ext}"

            backup_path = filepath + ".bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(code)
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(result.converted_code)

        return result

    def convert_code(self, code: str, source_language: str,
                     target_language: str, filename: str = "code") -> ConversionResult:
        """转换代码字符串"""
        source_language = self._normalize_language(source_language)
        target_language = self._normalize_language(target_language)

        if source_language == target_language:
            return ConversionResult(
                source_language=source_language,
                target_language=target_language,
                original_code=code,
                converted_code=code,
                changes=[],
                notes="源语言和目标语言相同，无需转换",
                confidence=1.0,
            )

        prompt = f"""请将以下{source_language}代码转换为{target_language}代码。

要求:
1. 保持原始代码的功能和逻辑完全一致
2. 使用{target_language}的惯用写法和最佳实践
3. 保留注释（翻译为{target_language}的注释风格）
4. 处理语言特有的差异（如类型系统、错误处理、内存管理）
5. 如果某些功能无法直接转换，添加注释说明

原始代码 ({source_language}):
```{source_language}
{code}
```

请输出转换后的{target_language}代码，用代码块包裹。
代码块后简要说明主要的转换变更点。"""

        response = self.llm.complete(prompt, temperature=0.2)

        # 解析转换结果
        converted_code, changes, notes = self._parse_conversion(response.content, target_language)

        # 计算置信度
        confidence = self._estimate_confidence(code, converted_code, source_language, target_language)

        return ConversionResult(
            source_language=source_language,
            target_language=target_language,
            original_code=code,
            converted_code=converted_code,
            changes=changes,
            notes=notes,
            confidence=confidence,
            raw_response=response.content,
        )

    def _parse_conversion(self, response: str, target_language: str) -> tuple:
        """解析转换结果"""
        converted_code = ""
        changes = []
        notes = ""

        # 提取代码块
        code_pattern = rf'```{target_language}\s*\n(.*?)```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)

        if code_matches:
            converted_code = code_matches[-1].strip()
        else:
            # 尝试通用代码块
            generic_matches = re.findall(r'```\s*\n(.*?)```', response, re.DOTALL)
            if generic_matches:
                converted_code = generic_matches[-1].strip()

        # 提取变更说明
        if converted_code:
            code_start = response.find(converted_code[:50])
            if code_start > 0:
                notes = response[:code_start].strip()
            code_end = response.find(converted_code[-50:]) + len(converted_code[-50:])
            if code_end < len(response):
                after_code = response[code_end:].strip()
                if after_code:
                    notes += "\n" + after_code

        # 提取变更点
        change_pattern = r'[\-\*]\s*(.+?)(?=\n[\-\*]|\n\n|$)'
        changes = [m.strip() for m in re.findall(change_pattern, notes) if len(m.strip()) > 10]

        if not converted_code:
            converted_code = response
            notes = "解析转换结果失败，请查看原始响应"

        return converted_code, changes, notes

    def _estimate_confidence(self, original: str, converted: str,
                             source: str, target: str) -> float:
        """估计转换置信度"""
        if not converted or converted == original:
            return 0.0

        # 基础分
        confidence = 0.5

        # 代码长度合理性
        original_lines = len(original.split('\n'))
        converted_lines = len(converted.split('\n'))
        if original_lines > 0:
            ratio = converted_lines / original_lines
            # 合理的长度比例在0.5-2.0之间
            if 0.5 <= ratio <= 2.0:
                confidence += 0.2
            elif ratio > 3.0 or ratio < 0.3:
                confidence -= 0.1

        # 语言对的转换难度
        easy_pairs = [('python', 'javascript'), ('javascript', 'typescript'),
                       ('c', 'cpp'), ('java', 'kotlin')]
        if (source, target) in easy_pairs or (target, source) in easy_pairs:
            confidence += 0.1

        # 转换后的代码是否有基本结构
        if any(keyword in converted for keyword in ['def ', 'function ', 'func ', 'fn ', 'void ', 'class ']):
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def _normalize_language(self, lang: str) -> str:
        """标准化语言名称"""
        lang_lower = lang.lower().strip()
        return self.LANGUAGE_ALIASES.get(lang_lower, lang_lower)

    def _detect_language(self, filename: str) -> str:
        """从文件名检测语言"""
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return self._normalize_language(ext)

    def _get_extension(self, language: str) -> str:
        """获取语言对应的文件扩展名"""
        ext_map = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'c': 'c', 'cpp': 'cpp',
            'golang': 'go', 'rust': 'rs', 'ruby': 'rb',
            'php': 'php', 'csharp': 'cs', 'kotlin': 'kt',
            'swift': 'swift', 'scala': 'scala',
        }
        return ext_map.get(language, language)

    def __call__(self, filepath: str, target_language: str, **kwargs) -> ConversionResult:
        return self.convert_file(filepath, target_language, **kwargs)
