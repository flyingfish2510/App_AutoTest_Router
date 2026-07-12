# pages/device_page.py
"""
设备页面对象（DevicePage）
⚠️ 职责边界：仅封装设备相关业务逻辑，不涉及设备/系统操作
"""


import allure
from appium.webdriver.common.appiumby import AppiumBy as By

from common.base_page import BasePage
from common.exceptions import ElementNotFoundException
from common.page_validator import PageValidator
from pages.access_device_page import AccessDevicePage
from utils.logging.log_tool import log


class DevicePage(BasePage):
    """设备页面（路由器下的设备管理页面）"""

    # ================= 常量定义（避免硬编码） =================
    PAGE_INDICATOR = (By.ID, "com.huawei.router:id/home_device_page_device_card_describe_text")  # 接入设备

    def __init__(self, driver):
        super().__init__(driver)
        self.validator = PageValidator(driver)  # ✅ 页面校验委托给PageValidator

    @allure.step("验证设备页面是否加载成功")
    def _validate_page_loaded(self, timeout: int = 30):
        """
        验证设备页面是否加载成功
        :param timeout: 页面加载超时时间（秒）
        :return: 自身实例（支持链式调用）
        """
        log.debug("🔍 验证设备页面加载状态")
        try:
            # 优先验证页面指示器
            self.validator.should_contain_element(self.PAGE_INDICATOR, timeout=timeout)
            log.debug("✅ 设备页面加载成功（通过页面指示器验证）")
        except ElementNotFoundException:
            log.warning("⚠️ 未找到页面指示器")
            raise

        return self


    @allure.step("进入接入设备页面")
    def switch_to_access_device_page(self, timeout: int = 30):
        log.debug("📱 进入接入设备页面")
        try:
            # 方式1：点击接入设备按钮（如果存在）
            # self.click(self.PAGE_INDICATOR)
            self.sleep(3)
            self.tap(0.5, 0.645)
            log.debug("✅ 点击接入设备按钮")
        except ElementNotFoundException:
            # 方式2：使用坐标点击（备用方案）
            log.warning("⚠️ 未找到接入设备按钮，使用坐标点击")
            self.tap(0.5, 0.645)

        # 验证接入设备页面是否加载成功
        try:
            access_device_page = AccessDevicePage(self.driver)
            access_device_page._validate_page_loaded(timeout=timeout)
            log.debug("✅ 成功进入接入设备页面")
        except ElementNotFoundException as e:
            log.error(f"❌ 进入接入设备页面失败: {e}")
            raise

        return self