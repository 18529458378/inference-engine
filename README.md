# Inference Engine — 推理增强与代码增强引擎

高阶推理与代码增强工具集，集成思维链/思维树推理、自我反思、规划执行、代码审查重构、蒙特卡洛树搜索等算法，基于 DeepSeek API。

## 核心能力

### 推理增强
| 算法 | 说明 |
|------|------|
| Chain-of-Thought (CoT) | 思维链推理，逐步分解问题 |
| Tree-of-Thoughts (ToT) | 思维树搜索，多路径探索与回溯 |
| Self-Reflection | 自我反思与纠错，迭代优化答案 |
| Plan-and-Execute | 先规划后执行，复杂任务分解 |
| Multi-Path Voting | 多路径推理 + 多数投票 |
| Confidence Estimation | 置信度评估与概率推演 |

### 代码增强
| 技能 | 说明 |
|------|------|
| Code Review | 代码审查：安全漏洞、性能问题、规范检查 |
| Refactor | 代码重构：设计模式、可维护性、可读性 |
| Test Generation | 自动生成单元测试、边界测试 |
| Documentation | 自动生成文档、注释、API 说明 |
| Optimization | 性能优化、复杂度分析、内存优化 |
| Complexity Analysis | 代码复杂度评估、技术债务分析 |

### 算法层
| 算法 | 用途 |
|------|------|
| MCTS | 蒙特卡洛树搜索，推理路径探索 |
| HTN Planner | 分层任务网络规划 |
| Bayesian Inference | 贝叶斯推理与置信度更新 |
| Voting & Aggregation | 多结果投票与聚合 |

## 架构

```
┌─────────────────────────────────────────────────┐
│              InferenceClient (统一 SDK)           │
├──────────────────┬──────────────────────────────┤
│   推理增强层       │        代码增强层              │
│  CoT/ToT/反思     │  审查/重构/测试/优化           │
│  规划/投票/置信度  │  文档/复杂度/性能              │
├──────────────────┴──────────────────────────────┤
│              算法层 (MCTS/规划/贝叶斯/投票)        │
├─────────────────────────────────────────────────┤
│              LLM 接口 (DeepSeek API)              │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置

设置环境变量（已配置你的 DeepSeek key）：

```bash
export DEEPSEEK_API_KEY="your-api-key"
```

### 推理增强

```python
from src.sdk import InferenceClient

client = InferenceClient()

# 思维链推理
result = client.reasoning.chain_of_thought(
    "一个水池有两个进水管和一个出水管..."
)
print(result.answer)
print(result.reasoning_steps)

# 思维树搜索
result = client.reasoning.tree_of_thoughts(
    "如何在3次称重内从12个球中找出次品？",
    breadth=3, depth=3
)

# 自我反思
result = client.reasoning.self_reflection(
    "写一个快速排序算法",
    max_iterations=3
)

# 规划执行
result = client.reasoning.plan_and_execute(
    "构建一个博客系统，包含用户注册、文章发布、评论功能"
)
```

### 代码增强

```python
# 代码审查
review = client.code.review("path/to/code.py")
print(review.issues)
print(review.score)

# 代码重构
refactored = client.code.refactor("path/to/code.py", target="clean_code")

# 生成测试
tests = client.code.generate_tests("path/to/module.py", framework="pytest")

# 性能优化
optimized = client.code.optimize("path/to/slow_code.py")

# 复杂度分析
analysis = client.code.analyze_complexity("path/to/code.py")
```

### 算法层

```python
from src.algorithms import MCTS, BayesianInference

# MCTS 推理路径搜索
mcts = MCTS(evaluation_function=your_eval_func)
best_path = mcts.search(initial_state, iterations=1000)

# 贝叶斯置信度更新
bayes = BayesianInference(prior=0.5)
bayes.update(likelihood=0.8, evidence=True)
print(bayes.posterior)
```

## 示例

- `examples/reasoning_demo.py` — 推理增强完整演示
- `examples/code_review_demo.py` — 代码审查与重构演示
- `examples/mcts_demo.py` — 蒙特卡洛树搜索算法演示

## 配置

编辑 `config.yaml`：

```yaml
llm:
  provider: deepseek
  model: deepseek-reasoner  # 推理模型
  base_url: https://api.deepseek.com
  temperature: 0.7
  max_tokens: 4096

reasoning:
  cot:
    max_steps: 10
  tot:
    breadth: 3
    depth: 3
  reflection:
    max_iterations: 3
  voting:
    num_paths: 5

code_enhancer:
  review:
    categories: [security, performance, style, bug]
  test:
    framework: pytest
    coverage: 80
```

## License

MIT
