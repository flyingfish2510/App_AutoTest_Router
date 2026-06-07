# testcases/base_test.py
import pytest


class BaseTest:
    @pytest.fixture(autouse=True)
    def setup_default_driver(self, default_driver):
        self.driver = default_driver

    @pytest.fixture(autouse=True)
    def setup_secondary_manager(self, secondary_driver_manager):
        self.secondary_manager = secondary_driver_manager