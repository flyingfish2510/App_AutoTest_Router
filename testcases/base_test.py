# testcases/base_test.py
import pytest


class BaseTest:
    @pytest.fixture(autouse=True)
    def setup_dynamic_driver(self, dynamic_driver):
        """使用 dynamic_driver 夹具（支持多设备并发）"""
        self.driver = dynamic_driver

    @pytest.fixture(autouse=True)
    def setup_secondary_manager(self, secondary_driver_manager):
        """按需启动第二个设备的管理器"""
        self.secondary_manager = secondary_driver_manager