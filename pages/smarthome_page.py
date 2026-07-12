# pages/smarthome_page.py
"""
智慧生活App页面对象（SmartHomePage）
⚠️ 职责边界：仅封装智慧生活App的业务逻辑，不涉及设备/系统操作
"""

import allure
from appium.webdriver.common.appiumby import AppiumBy as By

from common.base_page import BasePage
from common.device_controller import DeviceController
from common.exceptions import ElementNotFoundException
from common.page_validator import PageValidator
from utils.logging.log_tool import log


class SmartHomePage(BasePage):
    """智慧生活App主页面"""

    # ================= 常量定义（避免硬编码） =================
    JIAJU_LOCATOR = (By.ID, "com.huawei.smarthome:id/content")
    PACKAGE_NAME = "com.huawei.smarthome"

    def __init__(self, driver):
        super().__init__(driver)
        self.device = DeviceController(driver)
        self.validator = PageValidator(driver)

    @allure.step("启动并进入智慧生活App")
    def start_smarthome_app(self, timeout: int = 60) -> 'SmartHomePage':
        """启动智慧生活App并进入主页面"""
        log.debug(f"🚀 启动智慧生活App: {self.PACKAGE_NAME}")

        self.device.wake_up()
        self.device.go_home()
        self.device.restart_app(self.PACKAGE_NAME)

        log.debug("点击家居按钮")
        self.click(self.JIAJU_LOCATOR)

        try:
            self.validator.should_contain_element(self.JIAJU_LOCATOR, timeout=timeout)
            log.debug("✅ 成功进入智慧生活主页面")
        except ElementNotFoundException as e:
            log.error(f"❌ 进入智慧生活主页面失败: {e}")
            raise

        return self

    @allure.step("关闭智慧生活App")
    def stop_smarthome_app(self) -> 'SmartHomePage':
        """关闭智慧生活App"""
        log.debug(f"🛑 关闭智慧生活App: {self.PACKAGE_NAME}")
        self.sleep(1)
        self.device.kill_app(self.PACKAGE_NAME)
        log.debug("✅ 智慧生活App已关闭")
        return self

    @allure.step("点击名称为『{router_name}』的路由卡片")
    def click_router_card_by_name(self, router_name: str, timeout: int = 10) -> 'SmartHomePage':
        """
        在智慧生活主页面点击指定名称的路由卡片
        :param router_name: 路由卡片显示的名称（如"路由 BE3 Pro"）
        :param timeout: 等待超时时间（秒）
        :return: 自身实例（支持链式调用）
        """
        log.debug(f"🖱️ 点击路由卡片：{router_name}")

        try:
            # 复用BasePage的标准化文本点击
            self.click_by_text(router_name, timeout=timeout)
            log.debug(f"✅ 成功点击路由卡片：{router_name}")
        except ElementNotFoundException:
            log.error(f"❌ 未找到名称为『{router_name}』的路由卡片")
            raise

        return self

    @allure.step("进入指定路由器的管理页面")
    def enter_router_management(self, router_name: str, timeout: int = 30):
        """
        点击路由卡片并验证是否成功进入路由器管理页面
        :param router_name: 路由卡片显示的名称
        :param timeout: 页面加载超时时间（秒）
        :return: RouterPage实例
        """
        log.debug(f"🏠 进入路由器管理页面：{router_name}")

        # 点击路由卡片
        self.click_router_card_by_name(router_name, timeout=10)

        # 创建RouterPage实例并验证页面加载
        # router_page = RouterPage(self.driver)
        # router_page._validate_page_loaded(timeout=timeout)

        # logger.debug(f"✅ 成功进入路由器管理页面：{router_name}")
        return self

    @allure.step("检查指定路由卡片是否存在")
    def is_router_card_exist(self, router_name: str, timeout: int = 5) -> bool:
        """检查指定名称的路由卡片是否存在"""
        log.debug(f"检查路由卡片是否存在：{router_name}")
        xpath = f'//*[contains(@text, "{router_name}")]'
        locator = (By.XPATH, xpath)

        exists = self.is_element_exist(locator, timeout)
        log.debug(f"路由卡片『{router_name}』存在状态: {exists}")
        return exists

    @allure.step("获取路由卡片数量")
    def get_router_card_count(self, timeout: int = 10) -> int:
        """获取当前页面显示的路由卡片数量"""
        log.debug("获取路由卡片数量")

        router_card_xpath = '//*[contains(@resource-id, "device") or contains(@text, "路由")]'
        locator = (By.XPATH, router_card_xpath)

        try:
            cards = self.wait_all_visible(locator, timeout)
            count = len(cards)
            log.debug(f"当前页面共有 {count} 个路由卡片")
            return count
        except ElementNotFoundException:
            log.debug("当前页面没有路由卡片")
            return 0