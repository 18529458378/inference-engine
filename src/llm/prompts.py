"""
提示词模板库
包含推理增强和代码增强的专业提示词模板
"""

from typing import Dict, Any, Optional


class PromptTemplate:
    """提示词模板"""

    def __init__(self, template: str, variables: list = None):
        self.template = template
        self.variables = variables or []

    def format(self, **kwargs) -> str:
        """格式化模板"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing = e.args[0]
            raise ValueError(f"模板缺少变量: {missing}")

    def __str__(self):
        return self.template


class PromptLibrary:
    """提示词模板库"""

    # ========== 推理增强提示词 ==========

    CHAIN_OF_THOUGHT = PromptTemplate("""你是一位擅长深度推理的专家。
请逐步思考以下问题，每一步都要清晰、有逻辑。

问题: {question}

请按以下格式回答:
步骤1: [第一步思考]
步骤2: [第二步思考]
...
最终答案: [最终结论]

要求:
1. 每一步都要有明确的推理过程
2. 如果某一步不确定，请说明
3. 最终答案要简洁明确""")

    TREE_OF_THOUGHTS_GENERATE = PromptTemplate("""你是一位创意推理专家。
针对以下问题，请生成 {breadth} 种不同的思考路径或解决方案。

问题: {question}
当前思考深度: {depth}
之前的思路: {previous_thought}

请为每种思路提供:
1. 思路名称
2. 核心观点
3. 下一步推理方向

格式:
思路1: [名称]
- 核心: [观点]
- 下一步: [方向]

思路2: [名称]
...""")

    TREE_OF_THOUGHTS_EVALUATE = PromptTemplate("""你是一位严格的评审专家。
请评估以下推理思路的质量和正确性。

问题: {question}
待评估思路: {thought}

请从以下维度评分（0-10分）:
1. 正确性 (correctness): 思路是否正确？
2. 完整性 (completeness): 是否覆盖了关键方面？
3. 可行性 (feasibility): 是否可执行？
4. 创新性 (creativity): 是否有新颖之处？

请输出JSON格式:
{{"correctness": 分数, "completeness": 分数, "feasibility": 分数, "creativity": 分数, "overall": 综合分, "reason": "评分理由"}}""")

    SELF_REFLECTION_CRITIQUE = PromptTemplate("""你是一位严格的批判性评审专家。
请对以下答案进行深度批判，找出所有问题和改进空间。

问题: {question}
当前答案: {answer}

请从以下维度批判:
1. 事实准确性: 是否有事实错误？
2. 逻辑严密性: 推理是否有漏洞？
3. 完整性: 是否遗漏了重要方面？
4. 清晰度: 表达是否清晰？
5. 深度: 是否足够深入？

请输出具体的批判意见和改进建议，不要泛泛而谈。""")

    SELF_REFLECTION_REVISE = PromptTemplate("""你是一位善于改进的专家。
请根据以下批判意见，改进你的答案。

问题: {question}
原答案: {answer}
批判意见: {critique}

请输出改进后的完整答案，要求:
1. 解决所有批判指出的问题
2. 保持答案的完整性和清晰度
3. 如果某些批判不成立，请说明理由""")

    PLAN_AND_EXECUTE_PLANNER = PromptTemplate("""你是一位任务规划专家。
请将以下复杂任务分解为可执行的子任务列表。

任务: {task}
约束条件: {constraints}

请输出JSON格式的计划:
{{
  "goal": "总体目标",
  "subtasks": [
    {{"id": 1, "name": "子任务名称", "description": "详细描述", "depends_on": [], "estimated_complexity": "low/medium/high"}},
    ...
  ],
  "success_criteria": "成功标准"
}}

要求:
1. 子任务数量不超过 {max_subtasks} 个
2. 每个子任务应该是可独立执行的
3. 正确设置依赖关系""")

    # ========== 代码增强提示词 ==========

    CODE_REVIEW = PromptTemplate("""你是一位资深代码审查专家。
请对以下代码进行全面审查。

文件: {filename}
语言: {language}

代码:
```{language}
{code}
```

请从以下维度审查，并输出JSON格式:
{{
  "overall_score": 0-100,
  "summary": "总体评价",
  "issues": [
    {{
      "id": 1,
      "category": "security/performance/style/bug/maintainability",
      "severity": "critical/high/medium/low/info",
      "title": "问题标题",
      "description": "详细描述",
      "location": "行号或代码片段",
      "suggestion": "修复建议",
      "fixed_code": "修复后的代码（可选）"
    }}
  ],
  "strengths": ["优点1", "优点2"],
  "recommendations": ["改进建议1", "改进建议2"]
}}

要求:
1. 只报告真实存在的问题，不要误报
2. 每个问题都要有具体的修复建议
3. 严重程度要准确""")

    CODE_REFACTOR = PromptTemplate("""你是一位代码重构专家。
请对以下代码进行重构，目标是: {target}。

文件: {filename}
语言: {language}
重构目标: {target}

原代码:
```{language}
{code}
```

请输出:
1. 重构说明（做了哪些改动，为什么）
2. 重构后的完整代码

要求:
1. 保持代码行为不变（除非性能优化需要）
2. 遵循最佳实践和设计模式
3. 保持代码的可读性和可维护性
4. 添加必要的注释""")

    TEST_GENERATION = PromptTemplate("""你是一位测试专家。
请为以下代码生成单元测试。

文件: {filename}
语言: {language}
测试框架: {framework}
目标覆盖率: {coverage}%

待测试代码:
```{language}
{code}
```

请输出完整的测试代码，要求:
1. 覆盖正常路径、边界条件、错误处理
2. 使用 {framework} 框架
3. 测试命名清晰，使用 given_when_then 风格
4. 添加必要的注释说明测试目的
5. 包含 setup/teardown 如需要""")

    CODE_OPTIMIZE = PromptTemplate("""你是一位性能优化专家。
请分析并优化以下代码的性能。

文件: {filename}
语言: {language}
优化重点: {focus}

原代码:
```{language}
{code}
```

请输出:
1. 性能分析（瓶颈在哪里，时间/空间复杂度）
2. 优化方案（具体做了什么优化）
3. 优化后的完整代码
4. 预期性能提升（量化）

要求:
1. 保持代码功能正确
2. 优先优化算法复杂度，然后是常数因子
3. 不要为了微优化牺牲可读性""")

    COMPLEXITY_ANALYSIS = PromptTemplate("""你是一位代码复杂度分析专家。
请分析以下代码的复杂度和技术债务。

文件: {filename}
语言: {language}

代码:
```{language}
{code}
```

请输出JSON格式的分析报告:
{{
  "overall_quality": "excellent/good/fair/poor",
  "metrics": {{
    "cyclomatic_complexity": 数值,
    "halstead_volume": 数值,
    "maintainability_index": 0-100,
    "cognitive_complexity": 数值,
    "lines_of_code": 数值,
    "comment_ratio": 百分比
  }},
  "complexity_analysis": "复杂度分析说明",
  "technical_debt": [
    {{"type": "类型", "description": "描述", "severity": "high/medium/low", "effort": "修复工作量"}}
  ],
  "risk_areas": ["高风险区域1", "高风险区域2"],
  "recommendations": ["改进建议1", "改进建议2"]
}}""")

    DOCUMENTATION_GENERATION = PromptTemplate("""你是一位技术文档专家。
请为以下代码生成文档和注释。

文件: {filename}
语言: {language}
文档风格: {style}

代码:
```{language}
{code}
```

请输出:
1. 文件级文档说明（模块用途、主要类/函数）
2. 每个函数/方法的文档字符串（参数、返回值、异常、示例）
3. 复杂逻辑的行内注释
4. 使用示例（如适用）

要求:
- 使用 {style} 风格的文档字符串
- 文档要准确、简洁、有用
- 不要添加冗余注释""")

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """获取模板"""
        template = getattr(cls, name, None)
        if template is None:
            raise ValueError(f"模板不存在: {name}")
        return template

    @classmethod
    def list_templates(cls) -> list:
        """列出所有模板"""
        return [name for name in dir(cls)
                if isinstance(getattr(cls, name), PromptTemplate)]
