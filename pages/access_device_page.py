import allure

from appium.webdriver.common.appiumby import AppiumBy as By
from common.base_page import BasePage
from common.exceptions import ElementNotFoundException
from common.page_validator import PageValidator
from pages.access_device_manage_page import AccessDeviceManagePage
from utils.logging.logger import logger


class AccessDevicePage(BasePage):
    PAGE_INDICATOR = (By.XPATH, '//android.widget.TextView[@text="接入设备"]')
    ONLINE_DEVICE_LOCATOR = (By.XPATH, '//android.widget.TextView[contains(@text, "在线设备")]')
    OFFLINE_DEVICE_LOCATOR = (By.XPATH, '//android.widget.TextView[contains(@text, "离线设备")]')

    def __init__(self, driver):
        super().__init__(driver)
        self.validator = PageValidator(driver)  # ✅ 页面校验委托给PageValidator

    @allure.step("验证接入设备页面是否加载成功")
    def _validate_page_loaded(self, timeout: int = 30):
        """
        验证设备页面是否加载成功
        :param timeout: 页面加载超时时间（秒）
        :return: 自身实例（支持链式调用）
        """
        logger.info("🔍 验证接入设备页面加载状态")
        try:
            # 优先验证页面指示器
            self.validator.should_contain_element(self.PAGE_INDICATOR, timeout=timeout)
            logger.info("✅ 接入设备页面加载成功（通过页面指示器验证）")
        except ElementNotFoundException:
            logger.warning("⚠️ 未找到接入页面指示器")
            raise

        return self

    @allure.step("进入在线设备页面")
    def switch_to_online_device_page(self, timeout: int = 30):
        logger.info("📱 进入在线设备页面")
        self.click(self.ONLINE_DEVICE_LOCATOR, timeout=10)
        logger.debug("✅ 点击在线设备按钮")

        # 验证在线设备页面是否加载成功
        try:
            online_device_page = AccessDeviceManagePage(self.driver)
            online_device_page._validate_page_loaded(timeout=timeout)
            logger.info("✅ 成功进入在线设备页面")
        except ElementNotFoundException as e:
            logger.error(f"❌ 进入在线设备页面失败: {e}")
            raise

        return self

    @allure.step("进入离线设备页面")
    def switch_to_offline_device_page(self, timeout: int = 30):
        logger.info("📱 进入离线设备页面")
        self.click(self.OFFLINE_DEVICE_LOCATOR, timeout=10)
        logger.debug("✅ 点击离线设备按钮")

        # 验证在线设备页面是否加载成功
        try:
            online_device_page = AccessDeviceManagePage(self.driver)
            online_device_page._validate_page_loaded(timeout=timeout)
            logger.info("✅ 成功进入离线设备页面")
        except ElementNotFoundException as e:
            logger.error(f"❌ 进入离线设备页面失败: {e}")
            raise

        return self



