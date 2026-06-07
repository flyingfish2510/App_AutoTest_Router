# common/driver_manager.py
"""
Driver 管理器（不指定应用）
✅ 只启动到设备桌面
✅ 由测试用例控制应用启动
"""

import allure
from appium import webdriver
from appium.options.android import UiAutomator2Options

from common.exceptions import DriverInitException
from config.setting import app_config


class AndroidDriverManager:
    def __init__(self, device_info: dict):
        self.device_info = device_info
        self.driver = None

    @allure.step("初始化 Appium Driver（不指定应用）")
    def init_driver(self):
        """
        初始化 Driver，但不指定应用
        只启动到设备桌面，由测试用例自己启动应用
        """
        try:
            caps = {
                "platformName": "Android",
                "automationName": "UiAutomator2",
                "udid": self.device_info["udid"],
                "systemPort": self.device_info["system_port"],

                # ✅ 移除应用包名和活动配置（由测试用例控制）
                "noReset": True,
                "fullReset": False,
                "skipServerInstallation": True,
                "skipDeviceInitialization": True,
                "newCommandTimeout": 300,
                "chromedriverDisableBuildCheck": True,
            }

            options = UiAutomator2Options()
            for k, v in caps.items():
                setattr(options, k, v)

            self.driver = webdriver.Remote(
                command_executor=app_config["appium"]["server"],
                options=options
            )
            return self.driver

        except Exception as e:
            raise DriverInitException(
                message=f"Driver init failed: {str(e)}",
                extra={"device": self.device_info}
            )

    def quit_driver(self):
        if self.driver:
            self.driver.quit()