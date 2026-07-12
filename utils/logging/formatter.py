# utils/logging/formatter.py
import datetime
import os
import time
from typing import Optional

# =======================
# 日志相关常量（本地定义）
# =======================
LOG_PREFIX = "app"
LOG_TIME_FORMAT = "%Y-%m-%d"
LOG_SUFFIX = ".log"
LOG_RETENTION_DAYS = 30


class LogFileNameGenerator:
    """
    日志文件名生成器（支持设备级隔离）
    ✅ 支持按设备、环境、日期生成唯一文件名
    ✅ 支持多设备并行日志隔离
    ✅ 支持日志轮转
    """

    def __init__(
            self,
            prefix: str = LOG_PREFIX,
            time_format: str = LOG_TIME_FORMAT,
            suffix: str = LOG_SUFFIX,
            include_pid: bool = False,
            include_env: bool = True,
            environment: str = "development",
            separator: str = "_",
            device_name: Optional[str] = None  # ✅ 设备名参数
    ):
        """
        初始化日志文件名生成器
        """
        self.prefix = prefix
        self.time_format = time_format
        self.suffix = suffix
        self.include_pid = include_pid
        self.include_env = include_env
        self.environment = environment
        self.separator = separator
        self.device_name = device_name or "default"  # ✅ 默认设备名

    def generate_filename(self, timestamp: Optional[float] = None) -> str:
        """
        生成日志文件名（包含设备名）
        """
        if timestamp is None:
            timestamp = time.time()

        time_str = datetime.datetime.fromtimestamp(timestamp).strftime(self.time_format)

        parts = [self.prefix]

        # ✅ 设备名放在最前面，便于识别和筛选
        if self.device_name != "default":
            parts.append(self.device_name)

        parts.append(time_str)

        if self.include_env:
            parts.append(self.environment)

        if self.include_pid:
            parts.append(str(os.getpid()))

        filename = self.separator.join(parts) + self.suffix

        return filename

    def generate_daily_filename(self) -> str:
        """生成按天滚动的文件名"""
        return self.generate_filename()

    def generate_hourly_filename(self) -> str:
        """生成按小时滚动的文件名"""
        timestamp = time.time()
        hour_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H")

        parts = [self.prefix]
        if self.device_name != "default":
            parts.append(self.device_name)
        parts.append(hour_str)
        if self.include_env:
            parts.append(self.environment)

        return self.separator.join(parts) + self.suffix