.PHONY: install test lint format coverage clean help

# 变量
PYTHON ?= python3
PIP ?= pip3
PKG = inference-engine

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	$(PIP) install -e ".[dev]"

test: ## 运行测试
	$(PYTHON) -m pytest tests/ -v

coverage: ## 运行测试并生成覆盖率报告
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint: ## 代码检查
	$(PYTHON) -m flake8 src/ tests/ --max-line-length=100
	$(PYTHON) -m mypy src/ --ignore-missing-imports

format: ## 代码格式化
	$(PYTHON) -m black src/ tests/ examples/
	$(PYTHON) -m isort src/ tests/ examples/

clean: ## 清理生成文件
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

demo-reasoning: ## 运行推理演示
	$(PYTHON) examples/reasoning_demo.py

demo-code: ## 运行代码审查演示
	$(PYTHON) examples/code_review_demo.py

demo-mcts: ## 运行MCTS算法演示
	$(PYTHON) examples/mcts_demo.py

cli-help: ## 查看CLI帮助
	$(PYTHON) -m src.cli --help
