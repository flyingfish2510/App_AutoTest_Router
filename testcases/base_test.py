
import pytest


class BaseTest:
    @pytest.fixture(autouse=True)
    def setup_driver(self, driver):
        self.driver = driver