"""
配置管理模块
支持 YAML 配置文件 + 环境变量覆盖
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()


def _resolve_env_vars(value: Any) -> Any:
    """解析配置中的 ${ENV_VAR} 占位符"""
    if isinstance(value, str):
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, value)
        for var in matches:
            env_value = os.getenv(var, "")
            value = value.replace(f"${{{var}}}", env_value)
        return value
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


class Config:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = self._default_config()

        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
            self._deep_update(self._config, file_config)

        self._config = _resolve_env_vars(self._config)

    def _default_config(self) -> Dict[str, Any]:
        return {
            'llm': {
                'provider': 'deepseek',
                'model': 'deepseek-reasoner',
                'base_url': 'https://api.deepseek.com',
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'temperature': 0.7,
                'max_tokens': 4096,
                'top_p': 0.95,
                'timeout': 120,
                'max_retries': 3,
            },
            'reasoning': {
                'chain_of_thought': {'max_steps': 10, 'verbose': True},
                'tree_of_thoughts': {'breadth': 3, 'depth': 3, 'pruning_threshold': 0.3},
                'self_reflection': {'max_iterations': 3, 'improvement_threshold': 0.1},
                'plan_and_execute': {'max_subtasks': 10, 'replan_on_failure': True},
                'multi_path_voting': {'num_paths': 5, 'voting_method': 'majority'},
                'confidence': {'calibration_method': 'bayesian', 'num_bootstrap': 10},
            },
            'code_enhancer': {
                'review': {'categories': ['security', 'performance', 'style', 'bug', 'maintainability']},
                'refactor': {'targets': ['clean_code', 'design_pattern', 'performance']},
                'test_generation': {'framework': 'pytest', 'coverage_target': 80},
                'documentation': {'style': 'google'},
                'optimization': {'focus': ['time_complexity', 'space_complexity']},
                'complexity': {'metrics': ['cyclomatic', 'halstead', 'maintainability']},
            },
            'algorithms': {
                'mcts': {'exploration_constant': 1.414, 'max_iterations': 1000, 'max_depth': 20},
                'bayesian': {'prior_type': 'uniform'},
                'planner': {'method': 'htn', 'max_depth': 10},
            },
            'logging': {'level': 'INFO', 'file': './inference.log'},
        }

    def _deep_update(self, base: Dict, update: Dict) -> Dict:
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
        return base

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def llm(self) -> Dict:
        return self._config['llm']

    @property
    def reasoning(self) -> Dict:
        return self._config['reasoning']

    @property
    def code_enhancer(self) -> Dict:
        return self._config['code_enhancer']

    @property
    def algorithms(self) -> Dict:
        return self._config['algorithms']
