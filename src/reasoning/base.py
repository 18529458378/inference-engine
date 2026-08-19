"""
推理结果基类
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ReasoningResult:
    """推理结果基类"""
    question: str
    answer: str
    method: str
    reasoning_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "method": self.method,
            "reasoning_steps": self.reasoning_steps,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    def __str__(self):
        return f"[{self.method}] {self.answer[:100]}..."
