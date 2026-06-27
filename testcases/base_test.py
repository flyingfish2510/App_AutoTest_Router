import allure
import pytest

from utils.logging.logger import logger


class BaseTest:

    @pytest.fixture(autouse=True)
    def auto_inject_fixtures(self, dynamic_driver, secondary_driver_manager, request):
        request.instance.driver = dynamic_driver
        request.instance.secondary_manager = secondary_driver_manager
        yield

    def setup_method(self):
        logger.info("🚀 开始初始化测试环境")
        self.setup()

    def teardown_method(self):
        if self._test_failed():
            logger.info("❌ 测试失败，跳过 teardown")
            return
        self.teardown()

    def _test_failed(self) -> bool:
        return hasattr(self, "rep_call") and self.rep_call.failed

    def setup(self):
        pass

    def teardown(self):
        pass

    # =======================
    # ✅ 关键修改：使用 dynamic.step
    # =======================
    def step(self, title: str):
        with allure.step(title):
            pass
        logger.info(f"▶️ {title}")

    def checkpoint(self, title: str):
        with allure.step(title):
            pass
        logger.info(f"🔍 {title}")