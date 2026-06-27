import allure
from appium.webdriver.common.appiumby import AppiumBy as By

from common.base_page import BasePage
from common.exceptions import ElementNotFoundException
from common.page_validator import PageValidator
from utils.logging.logger import logger


class DeviceManagePage(BasePage):
    PAGE_INDICATOR = (By.ID, 'com.huawei.router:id/device_detail_brand_iv')
    DEVICE_NAME_LOCATOR = (By.XPATH, '//android.widget.RelativeLayout[@resource-id="com.huawei.router:id/device_detail_title"]/android.widget.TextView')
    EDIT_DEVICE_NAME_LOCATOR = (By.XPATH, '//android.widget.RelativeLayout[@resource-id="com.huawei.router:id/device_detail_title"]/android.widget.LinearLayout[2]/android.widget.ImageView')
    DEVICE_NAME_INPUT_LOCATOR = (By.ID, 'com.huawei.router:id/common_ui_name_edittext')
    OK_BUTTON_LOCATOR = (By.ID, 'com.huawei.router:id/common_ui_name_ok_btn')
    CANCLE_BUTTON_LOCATOR = (By.ID, 'com.huawei.router:id/common_ui_name_cancle_btn')

    def __init__(self, driver):
        super().__init__(driver)
        self.validator = PageValidator(driver)  # ✅ 页面校验委托给PageValidator

    @allure.step("验证设备管理页面是否加载成功")
    def _validate_page_loaded(self, timeout: int = 30):
        """
        验证设备管理页面是否加载成功
        :param timeout: 页面加载超时时间（秒）
        :return: 自身实例（支持链式调用）
        """
        logger.debug("🔍 验证设备管理设备页面加载状态")
        try:
            # 优先验证页面指示器
            self.validator.should_contain_element(self.PAGE_INDICATOR, timeout=timeout)
            logger.debug("✅ 设备管理页面加载成功（通过页面指示器验证）")
        except ElementNotFoundException:
            logger.warning("⚠️ 未找到接入页面指示器")
            raise

        return self

    @allure.step("修改下挂设备名称为{device_name}")
    def edit_devicename(self, device_name):
        logger.debug("点击下挂设备名称修改按钮")
        self.click(self.EDIT_DEVICE_NAME_LOCATOR)
        logger.debug(f"修改下挂设备名称为：{device_name}")
        self.input(self.DEVICE_NAME_INPUT_LOCATOR, device_name)
        logger.debug("点击确认按钮")
        self.click(self.OK_BUTTON_LOCATOR)

    @allure.step("获取下挂设备名称")
    def get_device_name(self):
        device_name = self.get_text(self.DEVICE_NAME_LOCATOR)
        logger.debug(f'当前下挂设备名称：{device_name}')
        return device_name




