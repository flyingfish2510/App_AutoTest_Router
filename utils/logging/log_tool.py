"""
企业级 Loguru 日志封装 - 支持时间命名 & 多设备隔离
✅ 修复 cache_key 不匹配问题
✅ 统一默认配置文件路径
✅ 暴露初始化失败的原始异常
"""

import os
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from loguru import logger as _loguru_logger

from utils.logging.formatter import LogFileNameGenerator

# =======================
# ✅ 全局常量：默认配置文件路径
# =======================
DEFAULT_CONFIG_PATH = "config/log_settings.yaml"

# =======================
# ✅ 项目根目录（启动时立即打印，方便调试）
# =======================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# print(f"\n[DEBUG] log_tool.py 加载成功")
# print(f"[DEBUG] PROJECT_ROOT = {PROJECT_ROOT}")
# print(f"[DEBUG] 默认配置文件路径 = {DEFAULT_CONFIG_PATH}")
# print(f"[DEBUG] 当前工作目录 = {os.getcwd()}\n")


# 全局默认日志实例（延迟初始化）
_default_logger = None
_default_logger_lock = threading.Lock()

# 按设备名缓存的日志实例
_device_loggers: Dict[str, Any] = {}
_device_loggers_lock = threading.Lock()


class LoggerConfig:
    """日志配置管理类（严格校验模式）"""

    def __init__(self, config_path: str):  # ✅ 强制传入config_path，不允许None
        self.config = self._get_default_config()
        self._load_config(config_path)  # ✅ 加载失败直接抛异常，不吞错
        self._resolve_paths()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置（直接使用绝对路径）"""
        return {
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
                # ✅ 直接用项目根目录拼接的绝对路径
                "log_dir": str(PROJECT_ROOT / "logs"),
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

    def _resolve_paths(self):
        """解析路径（仅做规范化，不再处理占位符）"""
        log_dir = self.config.get('log_dir', '')
        if log_dir:
            log_path = Path(log_dir)
            # 确保是绝对路径
            if not log_path.is_absolute():
                log_path = PROJECT_ROOT / log_path
            resolved = os.path.normpath(str(log_path))
            self.config['log_dir'] = resolved
            print(f"[DEBUG] 日志目录解析完成: {resolved}")

    def _load_config(self, config_path: str) -> None:
        """加载配置（失败立即抛异常，不降级）"""
        config_abs_path = Path(config_path)
        if not config_abs_path.is_absolute():
            config_abs_path = PROJECT_ROOT / config_abs_path

        # print(f"[DEBUG] 尝试加载配置文件: {config_abs_path}")

        if not config_abs_path.exists():
            raise FileNotFoundError(f"日志配置文件不存在: {config_abs_path}")

        try:
            with open(config_abs_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                if 'logging' not in loaded_config:
                    raise ValueError("YAML 缺少 'logging' 根节点")
                self._deep_update(self.config['logging'], loaded_config['logging'])
                # print(f"[DEBUG] 配置文件加载成功: {config_abs_path}")
        except Exception as e:
            raise RuntimeError(f"加载日志配置失败: {e}") from e

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
    """企业级日志管理器（线程安全单例 + 多设备支持）"""

    _instances: Dict[str, 'EnterpriseLogger'] = {}
    _lock = threading.Lock()

    def __new__(cls, config_path: str, device_name: Optional[str] = None):
        # ✅ 统一cache_key生成规则：config_path:device_name
        cache_key = f"{config_path}:{device_name or 'default'}"

        if cache_key not in cls._instances:
            with cls._lock:
                if cache_key not in cls._instances:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    instance._cache_key = cache_key
                    cls._instances[cache_key] = instance
                    # print(f"[DEBUG] 创建新的日志实例: {cache_key}")

        return cls._instances[cache_key]

    def __init__(self, config_path: str, device_name: Optional[str] = None):
        if self._initialized:
            return

        # print(f"[DEBUG] 初始化日志实例: {self._cache_key}")
        self.config_manager = LoggerConfig(config_path)
        self.config = self.config_manager.logging_config
        self.device_name = device_name or "default"

        naming_config = self.config.get('file_naming', {})
        self.filename_generator = LogFileNameGenerator(
            prefix=naming_config.get('prefix', 'app'),
            time_format=naming_config.get('time_format', '%Y-%m-%d'),
            suffix=naming_config.get('suffix', '.log'),
            include_pid=naming_config.get('include_pid', False),
            include_env=naming_config.get('include_env', True),
            environment=self.config.get('environment', 'development'),
            separator=naming_config.get('separator', '_'),
            device_name=self.device_name
        )

        try:
            self._setup_logger()
            self._initialized = True
            # print(f"[DEBUG] 日志实例初始化成功: {self._cache_key}")
        except Exception as e:
            # ✅ 初始化失败，从缓存中移除不完整的实例
            print(f"[ERROR] 日志实例初始化失败: {self._cache_key}, 错误: {e}")
            with self.__class__._lock:
                if self._cache_key in self.__class__._instances:
                    del self.__class__._instances[self._cache_key]
            raise  # 重新抛出异常，不让降级逻辑吞掉

    @staticmethod
    def _ensure_log_dir(log_dir: str) -> None:
        """确保日志目录存在且可写"""
        log_path = Path(log_dir).resolve()
        # print(f"[DEBUG] 检查日志目录: {log_path}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_path.mkdir(parents=True, exist_ok=True)
                # 测试可写性
                test_file = log_path / f".write_test_{os.getpid()}_{attempt}"
                test_file.touch()
                test_file.unlink()
                # print(f"[DEBUG] 日志目录可用: {log_path}")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"日志目录不可用: {log_path}, 错误: {e}") from e
                time.sleep(0.1 * (attempt + 1))

    def _get_log_file_path(self) -> str:
        log_dir = self.config.get('log_dir', './logs')
        self._ensure_log_dir(log_dir)
        filename = self.filename_generator.generate_filename()
        return str(Path(log_dir) / filename)

    def _setup_logger(self) -> None:
        """配置Loguru（初始化失败直接抛异常，不降级）"""
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

        if file_enabled:
            log_file_path = self._get_log_file_path()
            # print(f"[DEBUG] 尝试创建日志文件: {log_file_path}")

            _loguru_logger.add(
                log_file_path,
                level=level,
                format=file_format,
                rotation=rotation,
                retention=retention,
                compression=compression,
                diagnose=diagnose,
                backtrace=backtrace,
                encoding='utf-8',
                enqueue=True,
                catch=True
            )

            device_info = f"设备: {self.device_name}" if self.device_name != "default" else ""
            _loguru_logger.info(
                f"📝 日志系统初始化成功 | 文件: {log_file_path} | "
                f"环境: {environment} | {device_info}"
            )

    def get_logger(self):
        return _loguru_logger

    def get_current_log_file(self) -> str:
        return self._get_log_file_path()

    def health_check(self) -> Dict[str, Any]:
        """健康检查（确保所有字段都有值）"""
        log_file = self._get_log_file_path()
        log_dir = self.config.get('log_dir', './logs')

        return {
            "device": self.device_name,
            "log_file": log_file,
            "log_dir_exists": os.path.exists(log_dir),
            "log_file_writable": os.access(log_file, os.W_OK),
            "current_level": self.config.get('level'),
            "environment": self.config.get('environment'),
            "project_root": str(PROJECT_ROOT),
            "cwd": os.getcwd(),
            "config_path": self.config_manager.config.get('_config_path', 'unknown')
        }


def get_logger(config_path: Optional[str] = None, device_name: Optional[str] = None):
    """
    获取日志实例（工厂函数）
    ✅ 统一默认config_path为DEFAULT_CONFIG_PATH
    """
    # ✅ 所有None的config_path都替换为默认路径
    resolved_config_path = config_path or DEFAULT_CONFIG_PATH

    # 默认日志器（无设备名）
    if device_name is None and config_path is None:
        global _default_logger
        if _default_logger is None:
            with _default_logger_lock:
                if _default_logger is None:
                    enterprise_logger = EnterpriseLogger(resolved_config_path, None)
                    _default_logger = enterprise_logger.get_logger()
        return _default_logger

    # 设备日志器（按cache_key缓存）
    cache_key = f"{resolved_config_path}:{device_name or 'default'}"
    with _device_loggers_lock:
        if cache_key not in _device_loggers:
            enterprise_logger = EnterpriseLogger(resolved_config_path, device_name)
            _device_loggers[cache_key] = enterprise_logger.get_logger()

    return _device_loggers[cache_key]


# 默认日志实例
log = get_logger()


def get_device_logger(device_name: str, config_path: Optional[str] = None):
    """获取设备日志器（快捷方式）"""
    if not device_name:
        raise ValueError("device_name不能为空")
    return get_logger(config_path, device_name)


def set_log_level(level: str) -> None:
    """动态调整日志级别"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    default_instance = EnterpriseLogger._instances.get(f"{DEFAULT_CONFIG_PATH}:default")
    if default_instance:
        default_instance.set_level(level)


def check_log_health(device_name: Optional[str] = None) -> Dict[str, Any]:
    """
    检查日志健康状态
    ✅ 和get_logger使用相同的cache_key生成规则
    """
    cache_key = f"{DEFAULT_CONFIG_PATH}:{device_name or 'default'}"
    instance = EnterpriseLogger._instances.get(cache_key)
    if instance:
        return instance.health_check()
    # ✅ 找不到实例时返回详细错误信息，而不是全None
    return {
        "device": device_name or "default",
        "log_file": None,
        "log_dir_exists": False,
        "log_file_writable": False,
        "current_level": None,
        "environment": None,
        "project_root": str(PROJECT_ROOT),
        "cwd": os.getcwd(),
        "error": f"未找到日志实例，cache_key={cache_key}，已存在的实例：{list(EnterpriseLogger._instances.keys())}"
    }