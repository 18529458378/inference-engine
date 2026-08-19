"""
规划执行推理 (Plan-and-Execute)
先规划子任务，再逐个执行，支持动态重规划
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .base import ReasoningResult
from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class SubTask:
    """子任务"""
    id: int
    name: str
    description: str
    depends_on: List[int] = field(default_factory=list)
    status: str = "pending"  # pending / in_progress / completed / failed
    result: str = ""
    estimated_complexity: str = "medium"


class PlanResult(ReasoningResult):
    """规划执行推理结果"""
    def __init__(self, question: str, answer: str, plan: Dict,
                 subtasks: List[SubTask], replans: int = 0, **kwargs):
        super().__init__(
            question=question, answer=answer, method="plan_and_execute",
            reasoning_steps=[f"{t.name}: {t.status}" for t in subtasks], **kwargs
        )
        self.plan = plan
        self.subtasks = subtasks
        self.replans = replans


class PlanAndExecute:
    """规划执行推理器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        pe_config = self.config.reasoning['plan_and_execute']
        self.max_subtasks = pe_config['max_subtasks']
        self.replan_on_failure = pe_config['replan_on_failure']
        self.max_replans = 3

    def reason(self, task: str, constraints: str = "",
               max_subtasks: int = None, verbose: bool = False) -> PlanResult:
        """
        执行规划执行推理

        Args:
            task: 任务描述
            constraints: 约束条件
            max_subtasks: 最大子任务数
            verbose: 是否打印执行过程

        Returns:
            PlanResult 推理结果
        """
        max_subtasks = max_subtasks or self.max_subtasks
        total_replans = 0

        for attempt in range(self.max_replans + 1):
            # 1. 规划
            if verbose:
                print(f"\n=== 规划阶段 (尝试 {attempt+1}) ===")

            plan = self._plan(task, constraints, max_subtasks)
            subtasks = self._parse_plan(plan)

            if verbose:
                for st in subtasks:
                    print(f"  [{st.id}] {st.name} (依赖: {st.depends_on})")

            # 2. 执行
            if verbose:
                print(f"\n=== 执行阶段 ===")

            execution_context = ""
            all_success = True

            for st in subtasks:
                # 检查依赖
                if not self._check_dependencies(st, subtasks):
                    st.status = "failed"
                    all_success = False
                    if verbose:
                        print(f"  ✗ [{st.id}] {st.name} - 依赖未满足")
                    continue

                st.status = "in_progress"
                if verbose:
                    print(f"  → [{st.id}] {st.name}...")

                # 执行子任务
                try:
                    result = self._execute_subtask(st, task, execution_context)
                    st.result = result
                    st.status = "completed"
                    execution_context += f"\n\n## {st.name}\n{result}"

                    if verbose:
                        print(f"  ✓ [{st.id}] {st.name} - 完成")
                except Exception as e:
                    st.status = "failed"
                    st.result = str(e)
                    all_success = False

                    if verbose:
                        print(f"  ✗ [{st.id}] {st.name} - 失败: {e}")

                    if self.replan_on_failure:
                        break

            # 3. 如果全部成功，生成最终答案
            if all_success:
                final_answer = self._synthesize(task, subtasks, execution_context)
                confidence = 0.8 + 0.04 * len([s for s in subtasks if s.status == "completed"])
                confidence = min(confidence, 0.98)

                return PlanResult(
                    question=task,
                    answer=final_answer,
                    plan=plan,
                    subtasks=subtasks,
                    replans=total_replans,
                    confidence=confidence,
                    metadata={
                        "num_subtasks": len(subtasks),
                        "completed": len([s for s in subtasks if s.status == "completed"]),
                        "constraints": constraints,
                        "model": self.llm.model,
                    }
                )

            # 4. 重规划
            if attempt < self.max_replans and self.replan_on_failure:
                total_replans += 1
                if verbose:
                    print(f"\n⚠ 执行失败，重规划中... (重规划次数: {total_replans})")
                continue
            else:
                # 达到最大重规划次数，返回部分结果
                final_answer = self._synthesize_partial(task, subtasks)
                return PlanResult(
                    question=task,
                    answer=final_answer,
                    plan=plan,
                    subtasks=subtasks,
                    replans=total_replans,
                    confidence=0.4,
                    metadata={
                        "num_subtasks": len(subtasks),
                        "completed": len([s for s in subtasks if s.status == "completed"]),
                        "partial": True,
                        "model": self.llm.model,
                    }
                )

    def _plan(self, task: str, constraints: str, max_subtasks: int) -> Dict:
        """生成计划"""
        prompt = PromptLibrary.get("PLAN_AND_EXECUTE_PLANNER").format(
            task=task,
            constraints=constraints or "无特殊约束",
            max_subtasks=max_subtasks
        )

        response = self.llm.complete(prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # 返回默认计划
            return {
                "goal": task,
                "subtasks": [{"id": 1, "name": "完成任务", "description": task, "depends_on": [], "estimated_complexity": "high"}],
                "success_criteria": "任务完成"
            }

    def _parse_plan(self, plan: Dict) -> List[SubTask]:
        """解析计划为子任务列表"""
        subtasks = []
        for st_data in plan.get("subtasks", []):
            st = SubTask(
                id=st_data.get("id", len(subtasks) + 1),
                name=st_data.get("name", f"任务{len(subtasks)+1}"),
                description=st_data.get("description", ""),
                depends_on=st_data.get("depends_on", []),
                estimated_complexity=st_data.get("estimated_complexity", "medium")
            )
            subtasks.append(st)
        return subtasks

    def _check_dependencies(self, subtask: SubTask, all_subtasks: List[SubTask]) -> bool:
        """检查依赖是否满足"""
        for dep_id in subtask.depends_on:
            dep = next((s for s in all_subtasks if s.id == dep_id), None)
            if not dep or dep.status != "completed":
                return False
        return True

    def _execute_subtask(self, subtask: SubTask, overall_task: str,
                          context: str) -> str:
        """执行单个子任务"""
        prompt = f"""你正在执行一个复杂任务的子任务。

总体任务: {overall_task}

当前子任务: {subtask.name}
子任务描述: {subtask.description}

之前的执行结果:
{context if context else "（无）"}

请执行这个子任务，给出详细的结果和结论。"""

        response = self.llm.complete(prompt, temperature=0.4)
        return response.content

    def _synthesize(self, task: str, subtasks: List[SubTask], context: str) -> str:
        """综合所有子任务结果，生成最终答案"""
        prompt = f"""请综合以下所有子任务的执行结果，给出任务的最终答案。

总体任务: {task}

子任务执行结果:
{context}

请给出完整、结构化的最终答案。"""

        response = self.llm.complete(prompt, temperature=0.3)
        return response.content

    def _synthesize_partial(self, task: str, subtasks: List[SubTask]) -> str:
        """综合部分结果"""
        completed = [s for s in subtasks if s.status == "completed"]
        failed = [s for s in subtasks if s.status == "failed"]

        result = f"任务部分完成（{len(completed)}/{len(subtasks)} 个子任务成功）\n\n"
        result += "已完成的子任务:\n"
        for st in completed:
            result += f"- {st.name}: {st.result[:200]}...\n"

        if failed:
            result += "\n失败的子任务:\n"
            for st in failed:
                result += f"- {st.name}: {st.result[:100]}\n"

        return result

    def __call__(self, task: str, **kwargs) -> PlanResult:
        return self.reason(task, **kwargs)
