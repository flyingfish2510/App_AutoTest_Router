# testcases/base_test.py
import time

import allure
import pytest
from appium.webdriver.webdriver import WebDriver

from utils.logging.log_tool import log


class BaseTest:
    # =======================
    # ✅ 给 IDE 看的类型声明
    # =======================
    driver: WebDriver
    secondary_manager: object

    @pytest.fixture(autouse=True)
    def auto_inject_fixtures(self, dynamic_driver, secondary_driver_manager, request):
        request.instance.driver = dynamic_driver
        request.instance.secondary_manager = secondary_driver_manager
        yield

    def setup_method(self):
        log.info("🚀 开始初始化测试环境")
        self.setup()

    def teardown_method(self):
        if self._test_failed():
            log.info("❌ 测试失败，跳过 teardown")
            return
        self.teardown()

    def _test_failed(self) -> bool:
        return hasattr(self, "rep_call") and self.rep_call.failed

    # =======================
    # 业务层（子类重写）
    # =======================
    def setup(self):
        pass

    def teardown(self):
        pass

    # =======================
    # ✅ 纯文本 Step / Checkpoint
    # =======================
    def step(self, title: str):
        with allure.step(title):
            pass
        log.info(f"▶️ {title}")

    def checkpoint(self, title: str):
        with allure.step(title):
            pass
        log.info(f"🔍 {title}")

    def sleep(self, seconds: int = 1):
        time.sleep(seconds)