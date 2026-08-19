"""
思维树推理 (Tree-of-Thoughts)
多路径探索 + 评估 + 回溯，搜索最优推理路径
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .base import ReasoningResult
from ..llm.client import LLMClient
from ..llm.prompts import PromptLibrary
from ..config import Config


@dataclass
class ThoughtNode:
    """思维树节点"""
    id: str
    depth: int
    thought: str
    score: float = 0.0
    scores: Dict[str, float] = field(default_factory=dict)
    children: List['ThoughtNode'] = field(default_factory=list)
    parent: Optional['ThoughtNode'] = None
    is_leaf: bool = False

    def path(self) -> List[str]:
        """获取从根到当前节点的路径"""
        path = []
        node = self
        while node:
            path.insert(0, node.thought)
            node = node.parent
        return path


class ToTResult(ReasoningResult):
    """思维树推理结果"""
    def __init__(self, question: str, answer: str, root: ThoughtNode,
                 best_path: List[ThoughtNode], all_leaves: List[ThoughtNode],
                 **kwargs):
        super().__init__(
            question=question, answer=answer, method="tree_of_thoughts",
            reasoning_steps=[n.thought for n in best_path], **kwargs
        )
        self.root = root
        self.best_path = best_path
        self.all_leaves = all_leaves
        self.best_leaf = best_path[-1] if best_path else None


class TreeOfThoughts:
    """思维树推理器"""

    def __init__(self, llm: LLMClient = None, config: Config = None):
        self.llm = llm or LLMClient(config)
        self.config = config or Config()
        tot_config = self.config.reasoning['tree_of_thoughts']
        self.breadth = tot_config['breadth']
        self.depth = tot_config['depth']
        self.pruning_threshold = tot_config['pruning_threshold']

    def reason(self, question: str, breadth: int = None, depth: int = None,
               verbose: bool = False) -> ToTResult:
        """
        执行思维树推理

        Args:
            question: 问题
            breadth: 每节点分支数
            depth: 搜索深度
            verbose: 是否打印搜索过程

        Returns:
            ToTResult 推理结果
        """
        breadth = breadth or self.breadth
        depth = depth or self.depth

        if verbose:
            print(f"思维树搜索: breadth={breadth}, depth={depth}")

        # 根节点
        root = ThoughtNode(id="root", depth=0, thought=question)
        root.score = 0.5

        # 逐层搜索
        current_level = [root]
        all_leaves = []

        for d in range(1, depth + 1):
            if verbose:
                print(f"\n--- 深度 {d}/{depth} ---")

            next_level = []

            for node in current_level:
                # 生成子节点
                children = self._generate_children(question, node, breadth, d)

                # 评估子节点
                for child in children:
                    child.score = self._evaluate_thought(question, child.thought)
                    child.parent = node

                node.children = children
                next_level.extend(children)

                if verbose:
                    for child in children:
                        print(f"  [{child.score:.2f}] {child.thought[:60]}...")

            # 剪枝：只保留评分最高的 top-k
            next_level.sort(key=lambda n: n.score, reverse=True)
            pruned = [n for n in next_level if n.score >= self.pruning_threshold]
            if len(pruned) < breadth:
                pruned = next_level[:breadth]

            if verbose:
                print(f"  剪枝后保留 {len(pruned)} 个节点")

            # 最后一层作为叶子
            if d == depth:
                all_leaves = pruned
            else:
                current_level = pruned

        # 选择最优路径
        if all_leaves:
            best_leaf = max(all_leaves, key=lambda n: n.score)
            best_path = best_leaf.path()
        else:
            best_leaf = root
            best_path = [root]

        # 生成最终答案
        final_answer = self._generate_final_answer(question, best_path)

        # 置信度取最优叶子评分
        confidence = best_leaf.score if best_leaf else 0.5

        return ToTResult(
            question=question,
            answer=final_answer,
            root=root,
            best_path=best_path,
            all_leaves=all_leaves,
            confidence=confidence,
            metadata={
                "breadth": breadth,
                "depth": depth,
                "num_leaves": len(all_leaves),
                "best_score": best_leaf.score if best_leaf else 0,
                "model": self.llm.model,
            }
        )

    def _generate_children(self, question: str, parent: ThoughtNode,
                           breadth: int, depth: int) -> List[ThoughtNode]:
        """生成子节点"""
        previous_thought = parent.thought if parent.depth > 0 else ""

        prompt = PromptLibrary.get("TREE_OF_THOUGHTS_GENERATE").format(
            question=question,
            breadth=breadth,
            depth=depth,
            previous_thought=previous_thought or "（初始状态）"
        )

        response = self.llm.complete(prompt, temperature=0.7)

        # 解析生成的思路
        thoughts = self._parse_thoughts(response.content, breadth)

        children = []
        for i, thought in enumerate(thoughts):
            node = ThoughtNode(
                id=f"{parent.id}_c{i}",
                depth=depth,
                thought=thought
            )
            children.append(node)

        return children

    def _parse_thoughts(self, response: str, expected: int) -> List[str]:
        """解析生成的思路列表"""
        thoughts = []

        # 尝试匹配 "思路N:" 格式
        import re
        pattern = r'思路\s*(\d+)\s*[:：]\s*(.+?)(?=\n思路\s*\d+\s*[:：]|$)'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            for _, thought in matches:
                cleaned = thought.strip()
                if cleaned:
                    thoughts.append(cleaned)

        # 如果解析失败，按换行分割
        if not thoughts:
            lines = [l.strip() for l in response.split('\n') if l.strip() and not l.startswith('#')]
            thoughts = lines[:expected]

        return thoughts[:expected]

    def _evaluate_thought(self, question: str, thought: str) -> float:
        """评估思路质量（0-1）"""
        prompt = PromptLibrary.get("TREE_OF_THOUGHTS_EVALUATE").format(
            question=question, thought=thought
        )

        response = self.llm.complete(prompt, temperature=0.1)

        try:
            data = json.loads(response.content)
            return float(data.get('overall', 0.5)) / 10.0
        except (json.JSONDecodeError, ValueError, KeyError):
            # 尝试提取数字
            import re
            numbers = re.findall(r'[\d.]+', response.content)
            if numbers:
                return min(float(numbers[0]) / 10.0, 1.0)
            return 0.5

    def _generate_final_answer(self, question: str, best_path: List[ThoughtNode]) -> str:
        """根据最优路径生成最终答案"""
        path_text = "\n".join([f"步骤{i+1}: {n.thought}" for i, n in enumerate(best_path)])

        prompt = f"""请根据以下最优推理路径，给出问题的最终答案。

问题: {question}

最优推理路径:
{path_text}

请给出简洁、准确的最终答案。"""

        response = self.llm.complete(prompt, temperature=0.3)
        return response.content

    def __call__(self, question: str, **kwargs) -> ToTResult:
        return self.reason(question, **kwargs)
