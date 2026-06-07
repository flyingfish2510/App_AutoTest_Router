# common/base_page.py
"""
BasePage（最终稳定版 · 类型安全）
✅ 屏幕尺寸只获取一次
✅ 避免重复 Appium 通信
✅ 多设备串行安全
✅ 类型标注完整
✅ 异常捕获精确
"""

import time
import allure
from typing import Tuple

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.constants import (
    DEFAULT_TIMEOUT,
    SWIPE_DURATION,
    LONG_PRESS_DURATION,
    TAP_DURATION,
    SWIPE_RATIO_DEFAULT,
    SWIPE_UP_RATIO_START,
    SWIPE_DOWN_RATIO_START,
)
from common.exceptions import (
    ElementNotFoundException,
    ElementNotClickableException,
    ElementInputException,
)
from utils.logging.logger import logger

# =======================
# 本地常量定义
# =======================
DEFAULT_SHORT_WAIT = 1
XPATH_TEXT_EXACT_TEMPLATE = '//*[normalize-space(@text)="{}"]'
XPATH_TEXT_CONTAINS_TEMPLATE = '//*[contains(@text, "{}")]'


class BasePage:
    # ✅ 类变量：缓存屏幕尺寸（按 driver 缓存）
    _window_sizes: dict = {}

    def __init__(self, driver):
        self.driver = driver
        # ✅ 只获取一次屏幕尺寸（关键优化）
        self.width, self.height = self._get_cached_window_size()

    def _get_cached_window_size(self) -> Tuple[int, int]:
        """
        获取屏幕尺寸（带缓存）
        ✅ 每个 driver 只获取一次
        ✅ 避免重复调用 Appium Server
        """
        driver_id = id(self.driver)

        if driver_id not in self._window_sizes:
            with allure.step("获取屏幕尺寸（首次）"):
                size = self.driver.get_window_size()
                self._window_sizes[driver_id] = (size["width"], size["height"])
                logger.debug(f"📱 屏幕尺寸已缓存: {self._window_sizes[driver_id]}")

        return self._window_sizes[driver_id]

    @classmethod
    def clear_window_size_cache(cls):
        """清空屏幕尺寸缓存（用于多设备串行切换）"""
        cls._window_sizes.clear()
        logger.debug("🧹 屏幕尺寸缓存已清空")

    # =======================
    # 基础能力
    # =======================
    @allure.step("等待 {seconds} 秒")
    def sleep(self, seconds: int = DEFAULT_SHORT_WAIT):
        time.sleep(seconds)

    @allure.step("返回上一页")
    def back(self):
        self.driver.back()

    # =======================
    # 元素等待
    # =======================
    @allure.step("等待元素可见: {locator}")
    def wait_visible(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
        except TimeoutException:
            raise ElementNotFoundException(
                message="Element not visible within timeout",
                locator=locator,
                page=self.__class__.__name__,
                action="wait_visible",
                extra={"timeout": timeout}
            )

    @allure.step("等待元素可点击: {locator}")
    def wait_clickable(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
        except TimeoutException:
            raise ElementNotClickableException(
                message="Element not clickable within timeout",
                locator=locator,
                page=self.__class__.__name__,
                action="wait_clickable",
                extra={"timeout": timeout}
            )

    @allure.step("等待元素消失: {locator}")
    def wait_invisible(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
        except TimeoutException:
            raise ElementNotFoundException(
                message="Element still visible after timeout",
                locator=locator,
                page=self.__class__.__name__,
                action="wait_invisible",
                extra={"timeout": timeout}
            )

    @allure.step("等待元素列表可见: {locator}")
    def wait_all_visible(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> list:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*locator)) > 0
            )
            return self.driver.find_elements(*locator)
        except TimeoutException:
            raise ElementNotFoundException(
                message="No elements found within timeout",
                locator=locator,
                page=self.__class__.__name__,
                action="wait_all_visible",
                extra={"timeout": timeout}
            )

    # =======================
    # 元素操作
    # =======================
    @allure.step("点击元素: {locator}")
    def click(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT):
        try:
            self.wait_visible(locator, timeout).click()
        except TimeoutException:
            raise ElementNotClickableException(
                message="Element is not clickable",
                locator=locator,
                page=self.__class__.__name__,
                action="click"
            )

    @allure.step("安全点击元素: {locator}")
    def safe_click(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT):
        try:
            self.wait_clickable(locator, timeout).click()
        except TimeoutException:
            self.click(locator, timeout)

    @allure.step("输入文本: {locator} = {text}")
    def input(self, locator: Tuple[str, str], text: str, timeout: int = DEFAULT_TIMEOUT):
        try:
            el = self.wait_visible(locator, timeout)
            el.clear()
            el.send_keys(text)
        except TimeoutException:
            raise ElementInputException(
                message="Failed to input text into element",
                locator=locator,
                page=self.__class__.__name__,
                action="input",
                extra={"text": text}
            )

    @allure.step("清除输入框: {locator}")
    def clear_input(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT):
        try:
            self.wait_visible(locator, timeout).clear()
        except TimeoutException:
            raise ElementInputException(
                message="Failed to clear input",
                locator=locator,
                page=self.__class__.__name__,
                action="clear_input"
            )

    @allure.step("获取元素文本: {locator}")
    def get_text(self, locator: Tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> str:
        return self.wait_visible(locator, timeout).text

    @allure.step("获取元素属性: {locator} -> {attr}")
    def get_attribute(self, locator: Tuple[str, str], attr: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        return self.wait_visible(locator, timeout).get_attribute(attr)

    # =======================
    # 元素校验
    # =======================
    @allure.step("判断元素是否存在: {locator}")
    def is_element_exist(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        try:
            self.wait_visible(locator, timeout)
            return True
        except ElementNotFoundException:
            return False

    @allure.step("判断元素是否可见: {locator}")
    def is_visible(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        return self.is_element_exist(locator, timeout)

    @allure.step("获取元素数量: {locator}")
    def get_element_count(self, locator: Tuple[str, str]) -> int:
        return len(self.driver.find_elements(*locator))

    # =======================
    # 文本点击
    # =======================
    @allure.step("点击文本为「{text}」的元素")
    def click_by_text(self, text: str, *, exact_match: bool = False, timeout: int = DEFAULT_TIMEOUT):
        xpath = self._build_text_xpath(text, exact_match)
        locator = (AppiumBy.XPATH, xpath)
        self.safe_click(locator, timeout)

    # =======================
    # 滑动
    # =======================
    @allure.step("向上滑动屏幕")
    def swipe_up(self, ratio: float = SWIPE_RATIO_DEFAULT):
        start_y = int(self.height * SWIPE_UP_RATIO_START)
        end_y = int(self.height * (SWIPE_UP_RATIO_START - ratio))
        self.driver.swipe(self.width // 2, start_y, self.width // 2, end_y, SWIPE_DURATION)

    @allure.step("向下滑动屏幕")
    def swipe_down(self, ratio: float = SWIPE_RATIO_DEFAULT):
        start_y = int(self.height * SWIPE_DOWN_RATIO_START)
        end_y = int(self.height * (SWIPE_DOWN_RATIO_START + ratio))
        self.driver.swipe(self.width // 2, start_y, self.width // 2, end_y, SWIPE_DURATION)

    @allure.step("滑动查找元素: {locator}")
    def swipe_to_find(self, locator: Tuple[str, str], max_swipes: int = 5):
        for i in range(max_swipes):
            try:
                return self.wait_visible(locator, timeout=3)
            except ElementNotFoundException:
                self.swipe_up()
        raise ElementNotFoundException(
            message="Swipe to find element failed",
            locator=locator,
            page=self.__class__.__name__,
            action="swipe_to_find"
        )

    # =======================
    # 坐标 & 手势
    # =======================
    @allure.step("点击坐标 ({x_ratio}, {y_ratio})")
    def tap(self, x_ratio: float, y_ratio: float, duration: int = TAP_DURATION):
        x = int(self.width * x_ratio)
        y = int(self.height * y_ratio)
        self.driver.tap([(x, y)], duration)
        logger.debug(f"点击坐标: ({x}, {y})")

    @allure.step("长按元素: {locator}")
    def long_press(self, locator: Tuple[str, str], duration: int = LONG_PRESS_DURATION):
        """
        使用 W3C Actions 实现长按（Appium 2.x 推荐）
        """
        el = self.wait_visible(locator)

        actions = ActionBuilder(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions.add_pointer_input(pointer)

        actions.pointer_action.move_to(el).pointer_down()
        actions.pointer_action.pause(duration / 1000)  # 毫秒转秒
        actions.pointer_action.pointer_up()
        actions.perform()

    # =======================
    # 上下文切换
    # =======================
    @allure.step("切换到 WebView")
    def switch_to_webview(self):
        for ctx in self.driver.contexts:
            if "WEBVIEW" in ctx:
                self.driver.switch_to.context(ctx)
                return

    @allure.step("切换到 NATIVE_APP")
    def switch_to_native(self):
        self.driver.switch_to.context("NATIVE_APP")

    # =======================
    # 截图
    # =======================
    @allure.step("截图: {name}")
    def take_screenshot(self, name: str = "screenshot"):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = f"screenshots/{name}_{timestamp}.png"
        self.driver.save_screenshot(path)
        allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)

    # =======================
    # 私有方法
    # =======================
    @staticmethod
    def _build_text_xpath(text: str, exact_match: bool) -> str:
        if exact_match:
            return XPATH_TEXT_EXACT_TEMPLATE.format(text)
        return XPATH_TEXT_CONTAINS_TEMPLATE.format(text)