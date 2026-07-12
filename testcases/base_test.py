"""
测试用例基类（支持设备级日志隔离，与 conftest.py、log_tool.py 配套）
"""

import time
import traceback
from typing import Optional

import allure
import pytest
from appium.webdriver.webdriver import WebDriver

from utils.logging import log


class BaseTest:
    # =======================
    # ✅ IDE 类型识别声明
    # =======================
    driver: WebDriver
    secondary_manager: object
    device_logger: Optional[object] = None  # 设备级专属日志器（由 conftest 注入）
    secondary_logger: Optional[object] = None  # 副设备日志器（由 conftest 注入）

    @pytest.fixture(autouse=True)
    def auto_inject_fixtures(self, dynamic_driver, secondary_driver_manager, request):
        """自动注入 pytest 夹具到测试实例"""
        request.instance.driver = dynamic_driver
        request.instance.secondary_manager = secondary_driver_manager

        # 兜底：若 conftest 未注入设备日志器，使用默认全局日志
        if not hasattr(request.instance, 'device_logger') or request.instance.device_logger is None:
            request.instance.device_logger = log

        yield

    def setup_method(self):
        """测试方法前置钩子（子类可重写）"""
        self._log_step("🚀 开始初始化测试环境")
        self.setup()

    def teardown_method(self):
        """测试方法后置钩子（子类可重写）"""
        if self._test_failed():
            self._log_step("❌ 测试失败，跳过 teardown")
            return
        self._log_step("🧹 开始清理测试环境")
        self.teardown()

    def _test_failed(self) -> bool:
        """判断当前测试用例是否执行失败"""
        return hasattr(self, "rep_call") and self.rep_call.failed

    # =======================
    # 业务层钩子（子类按需重写）
    # =======================
    def setup(self):
        """测试前置逻辑（子类实现）"""
        pass

    def teardown(self):
        """测试后置逻辑（子类实现）"""
        pass

    # =======================
    # ✅ 日志器自动选择（优先设备专属日志）
    # =======================
    def _get_active_logger(self):
        """获取当前活跃的日志器：优先使用设备级日志，兜底用全局日志"""
        if self.device_logger:
            return self.device_logger
        return log

    def _log_step(self, message: str):
        """记录步骤级日志"""
        active_logger = self._get_active_logger()
        active_logger.info(message)

    def _log_debug(self, message: str):
        """记录调试级日志"""
        active_logger = self._get_active_logger()
        active_logger.debug(message)

    def _log_warning(self, message: str):
        """记录警告级日志"""
        active_logger = self._get_active_logger()
        active_logger.warning(message)

    def _log_error(self, message: str, exc_info: bool = False):
        """记录错误级日志"""
        active_logger = self._get_active_logger()
        if exc_info:
            active_logger.error(f"{message}\n{traceback.format_exc()}")
        else:
            active_logger.error(message)

    # =======================
    # ✅ Allure 步骤 + 日志联动
    # =======================
    def step(self, title: str):
        """记录测试步骤（同步写入 Allure 和日志）"""
        with allure.step(title):
            pass
        self._log_step(f"▶️ {title}")

    def checkpoint(self, title: str):
        """记录检查点（同步写入 Allure 和日志）"""
        with allure.step(f"🔍 {title}"):
            pass
        self._log_step(f"🔍 {title}")

    def sub_step(self, title: str):
        """记录子步骤（缩进展示）"""
        with allure.step(f"  ├─ {title}"):
            pass
        self._log_step(f"  ├─ {title}")

    def success(self, message: str):
        """记录成功信息"""
        with allure.step(f"✅ {message}"):
            pass
        self._log_step(f"✅ {message}")

    def failure(self, message: str, exc_info: bool = True):
        """记录失败信息"""
        with allure.step(f"❌ {message}"):
            pass
        self._log_error(f"❌ {message}", exc_info)

    # =======================
    # ✅ 业务场景日志包装
    # =======================
    def log_device_action(self, action: str, details: str = ""):
        """记录设备操作日志"""
        message = f"📱 [{action}]"
        if details:
            message += f" - {details}"
        self._log_step(message)

    def log_ui_action(self, action: str, locator: str = "", value: str = ""):
        """记录 UI 操作日志（点击/输入等）"""
        message = f"🖱️ [{action}]"
        if locator:
            message += f" - {locator}"
        if value:
            message += f" = '{value}'"
        self._log_debug(message)

    def log_assertion(self, expected, actual, message: str = ""):
        """记录断言日志"""
        log_msg = f"🔍 断言: {message}" if message else f"🔍 断言: 期望={expected}, 实际={actual}"
        self._log_debug(log_msg)

    # =======================
    # 常用辅助方法
    # =======================
    def sleep(self, seconds: int = 1):
        """等待（带日志记录）"""
        self._log_debug(f"⏱️ 等待 {seconds} 秒")
        time.sleep(seconds)

    def attach_text(self, name: str, content: str):
        """附加文本内容到 Allure 报告"""
        allure.attach(content, name=name, attachment_type=allure.attachment_type.TEXT)
        self._log_debug(f"📎 附加文本: {name}")

    def attach_html(self, name: str, content: str):
        """附加 HTML 内容到 Allure 报告"""
        allure.attach(content, name=name, attachment_type=allure.attachment_type.HTML)
        self._log_debug(f"📎 附加 HTML: {name}")

    # =======================
    # ✅ 多设备（副设备）支持
    # =======================
    def use_secondary_device(self) -> bool:
        """切换到副设备执行操作"""
        if not self.secondary_manager:
            self._log_warning("⚠️ 副设备管理器未初始化")
            return False

        if not hasattr(self, 'secondary_driver') or not self.secondary_driver:
            try:
                self.secondary_driver = self.secondary_manager.init_driver()
                self._log_step("📱 副设备 Driver 初始化成功")
            except Exception as e:
                self._log_error(f"❌ 副设备 Driver 初始化失败: {e}", exc_info=True)
                return False

        # 切换到副设备日志器
        if self.secondary_logger:
            self.device_logger = self.secondary_logger
            self._log_step("🔄 已切换到副设备日志")
        return True

    def switch_to_primary_device(self):
        """切换回主设备"""
        # 恢复原日志器（若之前保存过）
        if hasattr(self, '_primary_logger'):
            self.device_logger = self._primary_logger
            self._log_step("🔄 已切换回主设备日志")
        else:
            self.device_logger = log
            self._log_step("🔄 已切换回默认日志")

    # =======================
    # ✅ 副设备上下文管理器（优雅切换）
    # =======================
    class SecondaryDeviceContext:
        """副设备操作上下文管理器（内部类）"""
        def __init__(self, base_test_instance):
            self.base_test = base_test_instance
            self.original_logger = None

        def __enter__(self):
            # 保存原日志器
            self.original_logger = self.base_test.device_logger
            # 切换到副设备
            if not self.base_test.use_secondary_device():
                raise RuntimeError("无法切换到副设备")
            return self.base_test.secondary_driver

        def __exit__(self, exc_type, exc_val, exc_tb):
            # 恢复原日志器
            self.base_test.device_logger = self.original_logger
            self.base_test._log_step("🔄 已退出副设备上下文")

    def on_secondary_device(self):
        """
        副设备操作上下文管理器
        使用示例："""