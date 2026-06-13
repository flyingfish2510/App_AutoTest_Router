import allure

from appium.webdriver.common.appiumby import AppiumBy as By
from common.base_page import BasePage
from common.exceptions import ElementNotFoundException
from common.page_validator import PageValidator
from pages.device_manage_page import DeviceManagePage
from utils.logging.logger import logger


class AccessDeviceManagePage(BasePage):
    PAGE_INDICATOR = (By.ID, 'com.huawei.router:id/list_title_text')


    def __init__(self, driver):
        super().__init__(driver)
        self.validator = PageValidator(driver)  # ✅ 页面校验委托给PageValidator

    @allure.step("验证接入设备管理页面是否加载成功")
    def _validate_page_loaded(self, timeout: int = 30):
        """
        验证设备页面是否加载成功
        :param timeout: 页面加载超时时间（秒）
        :return: 自身实例（支持链式调用）
        """
        logger.info("🔍 验证接入设备管理页面加载状态")
        try:
            # 优先验证页面指示器
            self.validator.should_contain_element(self.PAGE_INDICATOR, timeout=timeout)
            logger.info("✅ 接入设备管理页面加载成功（通过页面指示器验证）")
        except ElementNotFoundException:
            logger.warning("⚠️ 未找到接入设备管理页面指示器")
            raise

        return self

    @allure.step("进入名称为{phone_name}的下挂设备管理页面")
    def switch_to_device_manage_page(self, phone_name, timeout: int = 30):
        logger.info("📱 进入下挂设备管理页面")
        self.click_by_text(phone_name, timeout=10)
        logger.debug(f"✅ 点击指定下挂设备{phone_name}")

        # 验证设备管理页面是否加载成功
        try:
            device_manage_page = DeviceManagePage(self.driver)
            device_manage_page._validate_page_loaded(timeout=timeout)
            logger.info("✅ 成功进入下挂设备管理页面")
        except ElementNotFoundException as e:
            logger.error(f"❌ 进入下挂设备管理页面失败: {e}")
            raise

        return self




