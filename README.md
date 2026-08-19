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

## 命令行接口 (CLI)

安装后可直接使用 `inference-engine` 命令：

```bash
# 推理增强
inference-engine reasoning cot "复杂问题"
inference-engine reasoning reflection "问题" --iterations 3
inference-engine reasoning tot "问题" --breadth 3 --depth 3
inference-engine reasoning plan "复杂任务"
inference-engine reasoning voting "问题" --paths 5 --method weighted

# 代码增强
inference-engine code review path/to/code.py
inference-engine code refactor path/to/code.py --target clean_code
inference-engine code test path/to/module.py --framework pytest
inference-engine code complexity path/to/code.py
inference-engine code optimize path/to/code.py
inference-engine code docs path/to/code.py --style google

# 算法
inference-engine algo bayes 0.1 --likelihood 0.9
```

或直接运行：
```bash
python -m src.cli reasoning cot "问题"
```

## 新增功能

### ReAct 推理 (Reasoning + Acting)
结合推理和行动，先思考再执行工具，观察结果后继续推理：

```python
tools = {
    "calculate": {"description": "数学计算", "function": eval},
    "search": {"description": "搜索", "function": search_func},
}
result = client.reasoning.react.reason("问题", tools=tools, verbose=True)
print(result.steps)  # 思考-行动-观察步骤
print(result.tools_used)
```

### 代码解释
自动解释代码功能、逻辑、算法、设计意图：

```python
explanation = client.code.explain("path/to/code.py", level="intermediate")
print(explanation.algorithm_explanation)
print(explanation.key_components)
```

### 代码转换
在不同编程语言之间转换代码（Python/JavaScript/Java/Go/Rust等）：

```python
result = client.code.convert("script.py", target_language="javascript")
print(result.converted_code)
print(result.confidence)
```

## 测试

```bash
# 运行全部测试
make test
# 或
pytest tests/ -v

# 覆盖率报告
make coverage
```

当前测试覆盖：MCTS、HTN Planner、贝叶斯推理、投票聚合等算法层（40个测试用例）。

## 开发

```bash
# 安装开发依赖
make install

# 代码格式化
make format

# 代码检查
make lint

# 运行演示
make demo-reasoning
make demo-code
make demo-mcts
```

## 项目结构

```
inference-engine/
├── src/
│   ├── reasoning/          # 推理增强模块
│   │   ├── chain_of_thought.py
│   │   ├── tree_of_thoughts.py
│   │   ├── self_reflection.py
│   │   ├── plan_execute.py
│   │   ├── multi_path.py
│   │   ├── confidence.py
│   │   └── react.py        # ReAct推理+行动
│   ├── code_enhancer/      # 代码增强模块
│   │   ├── reviewer.py
│   │   ├── refactorer.py
│   │   ├── tester.py
│   │   ├── optimizer.py
│   │   ├── complexity.py
│   │   ├── documenter.py
│   │   ├── explainer.py    # 代码解释
│   │   └── converter.py    # 代码转换
│   ├── algorithms/         # 算法层
│   │   ├── mcts.py
│   │   ├── planner.py
│   │   ├── bayesian.py
│   │   └── voting.py
│   ├── llm/                # LLM接口
│   ├── sdk/                # 统一SDK
│   ├── cli.py              # 命令行接口
│   └── config.py
├── tests/                  # 单元测试
├── examples/               # 示例脚本
├── config.yaml
├── pyproject.toml
├── Makefile
└── README.md
```

## License

MIT
