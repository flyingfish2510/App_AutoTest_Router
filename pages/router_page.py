# pages/router_page.py
"""
路由器主页面对象（RouterPage）
⚠️ 职责边界：仅封装路由器相关业务逻辑，不涉及设备/系统操作
"""

import allure
from appium.webdriver.common.appiumby import AppiumBy as By

from common.base_page import BasePage
from common.exceptions import ElementNotFoundException
from common.page_validator import PageValidator
from utils.logging.logger import logger


class RouterPage(BasePage):
    """路由器主页面"""

    # ================= 常量定义（避免硬编码） =================
    PAGE_INDICATOR = (By.ID, "com.huawei.router:id/home_main_title_auto_text")
    EXPECTED_ACTIVITY = ".loader.a.ActivityP9NRTS"  # 预期Activity

    # 设备页面标题
    DEVICE_TAB = (By.XPATH, '//*[contains(@text, "设备")]')  # 设备选项卡

    def __init__(self, driver):
        super().__init__(driver)
        self.validator = PageValidator(driver)  # ✅ 页面校验委托给PageValidator

    def _validate_page_loaded(self, timeout: int = 30):
        """校验路由器页面是否加载成功（内部方法）"""
        # 优先校验页面指示器元素（更可靠）
        try:
            self.validator.should_contain_element(self.PAGE_INDICATOR, timeout=timeout)
            logger.debug("✅ 路由器主页面加载成功（通过元素校验）")
            return
        except ElementNotFoundException:
            logger.warning("⚠️ 未找到页面指示器元素，尝试校验Activity")

        # 备选：校验Activity（兼容旧逻辑）
        try:
            self.validator.should_match_activity(
                expected_activity=self.EXPECTED_ACTIVITY,
                match_type="contains",
                timeout=timeout
            )
            logger.debug("✅ 路由器主页面加载成功（通过Activity校验）")
        except ElementNotFoundException as e:
            logger.error(f"❌ 路由器主页面加载失败：{e.message}")
            raise

    @allure.step("进入设备页面")
    def switch_to_device_table(self, timeout: int = 30):
        """
        切换到设备页面并验证
        :param timeout: 页面加载超时时间（秒）
        :return: 自身实例（支持链式调用）
        """
        logger.debug("📱 进入设备页面")
        try:
            # 方式1：点击设备选项卡（如果存在）
            # self.click(self.DEVICE_TAB)
            self.sleep(3)
            self.tap(0.5, 0.533)
            logger.debug("✅ 点击设备选项卡")
        except ElementNotFoundException:
            # 方式2：使用坐标点击（备用方案）
            logger.warning("⚠️ 未找到设备选项卡，使用坐标点击")
            self.tap(0.5, 0.65)

        # # 验证设备页面是否加载成功
        # try:
        #     device_page = DevicePage(self.driver)
        #     device_page._validate_page_loaded(timeout=timeout)
        #     logger.debug("✅ 成功进入设备页面")
        # except ElementNotFoundException as e:
        #     logger.error(f"❌ 进入设备页面失败: {e}")
        #     raise

        return self
