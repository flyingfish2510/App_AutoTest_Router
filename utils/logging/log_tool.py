"""
企业级 Loguru 日志封装 - 支持时间命名
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from loguru import logger as _loguru_logger

from utils.logging.formatter import LogFileNameGenerator


class LoggerConfig:
    """日志配置管理类"""

    DEFAULT_CONFIG = {
        "logging": {
            "level": "DEBUG",
            "console_enabled": True,
            "file_enabled": True,
            "file_naming": {
                "prefix": "app",
                "time_format": "%Y-%m-%d",
                "suffix": ".log",
                "include_pid": False,
                "include_env": True,
                "separator": "_"
            },
            "log_dir": "./logs",
            "rotation": "00:00",
            "retention": "30 days",
            "compression": "zip",
            "format": {
                "console": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                          "<level>{level: <8}</level> | "
                          "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
                          "<cyan>{line}</cyan> - <level>{message}</level>",
                "file": "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                       "{level: <8} | "
                       "{name}:{function}:{line} - {message}"
            },
            "diagnose": True,
            "backtrace": True,
            "environment": "development"
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

    def _load_config(self, config_path: str) -> None:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith(('.yaml', '.yml')):
                    loaded_config = yaml.safe_load(f)
                else:
                    return

                if 'logging' in loaded_config:
                    self._deep_update(self.config['logging'], loaded_config['logging'])

        except Exception as e:
            _loguru_logger.info(f"加载配置文件失败: {e}")

    def _deep_update(self, base_dict: dict, update_dict: dict) -> None:
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    @property
    def logging_config(self) -> Dict[str, Any]:
        return self.config['logging']

    def get(self, key: str, default=None):
        return self.logging_config.get(key, default)


class EnterpriseLogger:
    """企业级日志管理器 - 支持时间命名"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return

        self.config_manager = LoggerConfig(config_path)
        self.config = self.config_manager.logging_config

        # 初始化文件名生成器
        naming_config = self.config.get('file_naming', {})
        self.filename_generator = LogFileNameGenerator(
            prefix=naming_config.get('prefix', 'app'),
            time_format=naming_config.get('time_format', '%Y-%m-%d'),
            suffix=naming_config.get('suffix', '.log'),
            include_pid=naming_config.get('include_pid', False),
            include_env=naming_config.get('include_env', True),
            environment=self.config.get('environment', 'development'),
            separator=naming_config.get('separator', '_')
        )

        self._setup_logger()
        self._initialized = True

    @staticmethod
    def _ensure_log_dir(log_dir: str) -> None:
        """确保日志目录存在"""
        log_path = Path(log_dir)
        if not log_path.exists():
            log_path.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self) -> str:
        """获取带时间的日志文件路径"""
        log_dir = self.config.get('log_dir', './logs')
        self._ensure_log_dir(log_dir)

        filename = self.filename_generator.generate_filename()
        return str(Path(log_dir) / filename)

    def _setup_logger(self) -> None:
        """配置 Loguru 日志系统"""
        _loguru_logger.remove()

        level = self.config.get('level', 'DEBUG')
        console_enabled = self.config.get('console_enabled', True)
        file_enabled = self.config.get('file_enabled', True)
        rotation = self.config.get('rotation', '00:00')
        retention = self.config.get('retention', '30 days')
        compression = self.config.get('compression', 'zip')
        console_format = self.config.get('format', {}).get('console')
        file_format = self.config.get('format', {}).get('file')
        diagnose = self.config.get('diagnose', True)
        backtrace = self.config.get('backtrace', True)
        environment = self.config.get('environment', 'development')

        # 控制台 handler
        if console_enabled:
            _loguru_logger.add(
                sys.stdout,
                level=level,
                format=console_format,
                colorize=True,
                diagnose=diagnose,
                backtrace=backtrace,
                enqueue=True,
                catch=True
            )

        # 文件 handler（时间命名）
        if file_enabled:
            log_file_path = self._get_log_file_path()

            _loguru_logger.add(
                log_file_path,
                level=level,
                format=file_format,
                rotation=rotation,           # 按时间轮转
                retention=retention,
                compression=compression,
                diagnose=diagnose,
                backtrace=backtrace,
                encoding='utf-8',
                enqueue=True,
                catch=True
            )

            _loguru_logger.info(f"日志系统初始化 | 文件: {log_file_path} | 环境: {environment}")

    @staticmethod
    def get_logger():
        return _loguru_logger

    def get_current_log_file(self) -> str:
        """获取当前日志文件路径"""
        return self._get_log_file_path()


def get_logger(config_path: Optional[str] = None):
    """获取日志实例"""
    enterprise_logger = EnterpriseLogger(config_path)
    return enterprise_logger.get_logger()


log = get_logger("config/log_settings.yaml")
