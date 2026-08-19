"""
规划算法
分层任务网络 (HTN) 规划、目标导向规划
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque


@dataclass
class Task:
    """任务"""
    name: str
    task_type: str = "primitive"  # primitive / compound / goal
    description: str = ""
    preconditions: List[Dict] = field(default_factory=list)
    effects: List[Dict] = field(default_factory=list)
    methods: List['DecompositionMethod'] = field(default_factory=list)
    action: Optional[Callable] = None


@dataclass
class DecompositionMethod:
    """任务分解方法"""
    name: str
    condition: Optional[Dict] = None  # 适用条件
    subtasks: List[str] = field(default_factory=list)  # 子任务名称列表


@dataclass
class PlanStep:
    """计划步骤"""
    task_name: str
    description: str
    order: int
    dependencies: List[int] = field(default_factory=list)
    status: str = "pending"  # pending / in_progress / completed / failed


@dataclass
class Plan:
    """计划"""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    total_steps: int = 0
    estimated_complexity: str = "medium"

    def to_dict(self) -> Dict:
        return {
            "goal": self.goal,
            "total_steps": self.total_steps,
            "estimated_complexity": self.estimated_complexity,
            "steps": [step.__dict__ for step in self.steps],
        }


class HTNPlanner:
    """
    分层任务网络 (HTN) 规划器

    用法:
        planner = HTNPlanner()
        planner.add_task(Task(name="build_blog", task_type="compound",
                              methods=[DecompositionMethod(name="standard",
                                  subtasks=["setup_env", "create_pages", "add_features", "deploy"])]))
        planner.add_task(Task(name="setup_env", task_type="primitive",
                              description="设置开发环境"))
        plan = planner.plan("build_blog")
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.state: Dict[str, Any] = {}

    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.name] = task

    def plan(self, goal_task_name: str, state: Dict = None) -> Plan:
        """
        生成计划

        Args:
            goal_task_name: 目标任务名称
            state: 初始状态

        Returns:
            Plan 计划
        """
        if state:
            self.state.update(state)

        plan = Plan(goal=goal_task_name)
        order_counter = [0]

        self._decompose(goal_task_name, plan, order_counter, [])

        plan.total_steps = len(plan.steps)
        plan.estimated_complexity = self._estimate_complexity(plan)

        return plan

    def _decompose(self, task_name: str, plan: Plan, order_counter: list,
                   dependencies: List[int]):
        """递归分解任务"""
        if task_name not in self.tasks:
            # 未知任务，作为原始任务处理
            step = PlanStep(
                task_name=task_name,
                description=f"执行: {task_name}",
                order=order_counter[0],
                dependencies=list(dependencies)
            )
            plan.steps.append(step)
            order_counter[0] += 1
            return

        task = self.tasks[task_name]

        if task.task_type == "primitive":
            # 原始任务，直接添加到计划
            step = PlanStep(
                task_name=task_name,
                description=task.description or f"执行: {task_name}",
                order=order_counter[0],
                dependencies=list(dependencies)
            )
            plan.steps.append(step)
            current_order = order_counter[0]
            order_counter[0] += 1
            return [current_order]

        elif task.task_type == "compound":
            # 复合任务，选择方法分解
            method = self._select_method(task)
            if method:
                new_deps = list(dependencies)
                for subtask_name in method.subtasks:
                    completed = self._decompose(subtask_name, plan, order_counter, new_deps)
                    if completed:
                        new_deps = completed

        elif task.task_type == "goal":
            # 目标任务，寻找实现方法
            method = self._select_method(task)
            if method:
                new_deps = list(dependencies)
                for subtask_name in method.subtasks:
                    completed = self._decompose(subtask_name, plan, order_counter, new_deps)
                    if completed:
                        new_deps = completed

        return []

    def _select_method(self, task: Task) -> Optional[DecompositionMethod]:
        """选择任务分解方法"""
        if not task.methods:
            return None

        # 简单策略：选择第一个满足条件的方法
        for method in task.methods:
            if method.condition is None:
                return method
            # 检查条件是否满足
            if self._check_condition(method.condition):
                return method

        return task.methods[0] if task.methods else None

    def _check_condition(self, condition: Dict) -> bool:
        """检查条件是否满足"""
        for key, value in condition.items():
            if self.state.get(key) != value:
                return False
        return True

    def _estimate_complexity(self, plan: Plan) -> str:
        """估计计划复杂度"""
        num_steps = len(plan.steps)
        if num_steps <= 3:
            return "low"
        elif num_steps <= 10:
            return "medium"
        else:
            return "high"

    def execute_plan(self, plan: Plan, action_handler: Callable = None) -> bool:
        """
        执行计划

        Args:
            plan: 计划
            action_handler: 动作处理函数

        Returns:
            是否全部成功
        """
        completed = set()

        for step in plan.steps:
            # 检查依赖
            if not all(dep in completed for dep in step.dependencies):
                step.status = "failed"
                continue

            step.status = "in_progress"

            try:
                if action_handler:
                    action_handler(step)
                step.status = "completed"
                completed.add(step.order)
            except Exception as e:
                step.status = "failed"
                step.description += f" (失败: {e})"

        return all(step.status == "completed" for step in plan.steps)


class Planner:
    """通用规划器（简化版）"""

    def __init__(self):
        self.htn = HTNPlanner()

    def plan(self, goal: str, tasks: List[Task] = None) -> Plan:
        """生成计划"""
        if tasks:
            for task in tasks:
                self.htn.add_task(task)
        return self.htn.plan(goal)
