"""
ReAct 推理器 (Reasoning + Acting)
结合推理和行动，先思考再行动，观察结果后继续思考
"""

import re
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config
from .base import ReasoningResult


@dataclass
class ReActStep:
    """ReAct 步骤"""
    step: int
    thought: str  # 思考
    action: str  # 行动名称
    action_input: str  # 行动输入
    observation: str = ""  # 观察结果
    is_final: bool = False


@dataclass
class ReActResult(ReasoningResult):
    """ReAct 推理结果"""
    steps: List[ReActStep] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "steps": [
                {
                    "step": s.step,
                    "thought": s.thought,
                    "action": s.action,
                    "action_input": s.action_input,
                    "observation": s.observation[:200] if s.observation else "",
                    "is_final": s.is_final,
                }
                for s in self.steps
            ],
            "tools_used": self.tools_used,
        }


# 内置工具
BUILTIN_TOOLS = {
    "calculate": {
        "description": "执行数学计算，输入为数学表达式",
        "function": lambda expr: str(eval(expr)),
    },
    "search_memory": {
        "description": "搜索内部记忆/知识库，输入为搜索关键词",
        "function": lambda query: f"记忆搜索结果: 未找到关于'{query}'的信息",
    },
}


class ReActReasoner:
    """
    ReAct 推理器 (Reasoning + Acting)

    用法:
        tools = {
            "search": {"description": "搜索网络", "function": search_func},
            "calculate": {"description": "计算", "function": calc_func},
        }
        reasoner = ReActReasoner(tools=tools)
        result = reasoner.reason("问题", verbose=True)
    """

    def __init__(self, llm: LLMClient = None, config: Config = None,
                 tools: Dict[str, Dict] = None, max_iterations: int = 10):
        """
        初始化 ReAct 推理器

        Args:
            llm: LLM 客户端
            config: 配置
            tools: 可用工具字典 {name: {"description": str, "function": callable}}
            max_iterations: 最大迭代次数
        """
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        self.max_iterations = max_iterations

        # 合并内置工具和自定义工具
        self.tools = dict(BUILTIN_TOOLS)
        if tools:
            self.tools.update(tools)

    def reason(self, question: str, verbose: bool = False) -> ReActResult:
        """
        执行 ReAct 推理

        Args:
            question: 问题
            verbose: 是否打印详细过程

        Returns:
            ReActResult
        """
        steps = []
        tools_used = []
        scratchpad = ""  # 思考-行动-观察的累积记录

        for iteration in range(1, self.max_iterations + 1):
            if verbose:
                print(f"\n--- 迭代 {iteration} ---")

            # 1. 生成思考和行动
            thought, action, action_input, is_final = self._generate_thought_action(
                question, scratchpad
            )

            if verbose:
                print(f"思考: {thought[:150]}...")
                print(f"行动: {action}({action_input[:50]})")

            # 2. 如果是最终答案，结束
            if is_final or action.lower() in ("finish", "final_answer", "answer"):
                step = ReActStep(
                    step=iteration,
                    thought=thought,
                    action="Finish",
                    action_input=action_input,
                    observation="",
                    is_final=True,
                )
                steps.append(step)
                break

            # 3. 执行行动
            observation = self._execute_action(action, action_input)
            tools_used.append(action)

            if verbose:
                print(f"观察: {observation[:150]}...")

            # 4. 记录步骤
            step = ReActStep(
                step=iteration,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation,
                is_final=False,
            )
            steps.append(step)

            # 5. 更新 scratchpad
            scratchpad += f"\n思考 {iteration}: {thought}\n"
            scratchpad += f"行动 {iteration}: {action}[{action_input}]\n"
            scratchpad += f"观察 {iteration}: {observation}\n"

        # 提取最终答案
        final_answer = self._extract_final_answer(steps, question)

        # 计算置信度（基于步骤数和工具使用）
        confidence = self._calculate_confidence(steps)

        return ReActResult(
            question=question,
            answer=final_answer,
            confidence=confidence,
            reasoning_steps=[s.thought for s in steps],
            steps=steps,
            tools_used=list(set(tools_used)),
        )

    def _generate_thought_action(self, question: str, scratchpad: str) -> tuple:
        """生成思考和行动"""
        tools_description = self._format_tools()

        prompt = f"""你是一个ReAct（推理+行动）智能体。你需要通过思考和使用工具来解决问题。

可用工具:
{tools_description}

问题: {question}

{scratchpad if scratchpad else "（这是第一步，还没有之前的思考和行动）"}

请按照以下格式输出:
思考: [你的推理过程]
行动: [工具名称]
行动输入: [工具的输入参数]

如果已经有足够信息回答问题，使用:
思考: [总结推理]
行动: Finish
行动输入: [最终答案]

注意: 只能使用上面列出的工具。"""

        response = self.llm.complete(prompt, temperature=0.2)

        # 解析思考、行动、行动输入
        thought = self._extract_field(response.content, "思考")
        action = self._extract_field(response.content, "行动")
        action_input = self._extract_field(response.content, "行动输入")

        # 判断是否为最终答案
        is_final = action.lower() in ("finish", "final_answer", "answer", "结束")

        if not thought:
            thought = response.content[:200]
        if not action:
            action = "Finish"
            action_input = response.content
            is_final = True

        return thought, action.strip(), action_input.strip(), is_final

    def _execute_action(self, action: str, action_input: str) -> str:
        """执行行动（调用工具）"""
        action = action.strip().lower()

        # 查找工具（不区分大小写）
        tool_name = None
        for name in self.tools:
            if name.lower() == action:
                tool_name = name
                break

        if tool_name is None:
            return f"错误: 未知工具 '{action}'。可用工具: {', '.join(self.tools.keys())}"

        try:
            result = self.tools[tool_name]["function"](action_input)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {str(e)}"

    def _format_tools(self) -> str:
        """格式化工具描述"""
        lines = []
        for name, info in self.tools.items():
            lines.append(f"- {name}: {info['description']}")
        return "\n".join(lines)

    def _extract_field(self, text: str, field_name: str) -> str:
        """从文本中提取字段"""
        # 尝试多种格式
        patterns = [
            rf'{field_name}[:：]\s*(.+?)(?=\n(?:思考|行动|行动输入|观察)[:：]|$)',
            rf'{field_name}\s*[:：]\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_final_answer(self, steps: List[ReActStep], question: str) -> str:
        """提取最终答案"""
        # 从最后一个步骤提取
        if steps:
            last = steps[-1]
            if last.is_final:
                return last.action_input
            # 如果没有明确的最终步骤，使用最后的观察
            if last.observation:
                return last.observation

        # 回退：让LLM总结
        prompt = f"基于以下推理过程，总结问题的最终答案：\n\n问题: {question}\n\n"
        for step in steps:
            prompt += f"步骤{step.step}: 思考={step.thought[:100]}, 行动={step.action}, 观察={step.observation[:100]}\n"
        prompt += "\n最终答案:"

        response = self.llm.complete(prompt, temperature=0.1)
        return response.content.strip()

    def _calculate_confidence(self, steps: List[ReActStep]) -> float:
        """计算置信度"""
        if not steps:
            return 0.0

        # 基于步骤数：步骤越少且有明确答案，置信度越高
        num_steps = len(steps)
        has_final = steps[-1].is_final if steps else False

        # 基础分
        confidence = 0.5

        # 有明确最终答案加分
        if has_final:
            confidence += 0.3

        # 步骤数适中加分（太多步骤可能表示不确定）
        if 1 <= num_steps <= 5:
            confidence += 0.1
        elif num_steps > 8:
            confidence -= 0.1

        # 工具执行成功加分
        success_rate = sum(1 for s in steps if not s.observation.startswith("错误")) / num_steps
        confidence += success_rate * 0.1

        return max(0.0, min(1.0, confidence))

    def __call__(self, question: str, **kwargs) -> ReActResult:
        return self.reason(question, **kwargs)
