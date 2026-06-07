# common/popup_handler.py
"""
弹窗处理器（专注权限/系统/应用内弹窗）
⚠️ 职责边界：仅处理弹窗交互，不涉及业务逻辑或设备操作
"""

from typing import Literal

import allure
from appium.webdriver.common.appiumby import AppiumBy

from common.base_page import BasePage
from common.exceptions import ElementNotFoundException  # ✅ 对齐 E1001 异常
from utils.logging.logger import logger


class PopupHandler:
    """弹窗处理器（基于 Appium 原生 API）"""

    # 常见弹窗按钮文本（支持多语言/多版本）
    PERMISSION_ALLOW_TEXTS = [
        "允许", "允许始终", "允许此次", "Allow", "Allow always", "Allow this time"
    ]
    PERMISSION_DENY_TEXTS = [
        "拒绝", "拒绝此次", "Deny", "Deny this time"
    ]
    SYSTEM_POPUP_CLOSE_TEXTS = [
        "关闭", "取消", "Close", "Cancel"
    ]

    def __init__(self, driver):
        self.driver = driver
        self.base_page = BasePage(driver)  # 复用 BasePage 的等待逻辑

    @allure.step("处理权限弹窗（允许/拒绝）")
    def handle_permission_popup(
        self,
        allow: Literal[True, False] = True,
        timeout: int = 5
    ) -> bool:
        """
        处理 Android 权限弹窗（如相机、存储、位置权限）
        :param allow: True=点击允许，False=点击拒绝
        :param timeout: 弹窗检测超时时间（秒）
        :return: 是否处理了弹窗
        """
        target_texts = self.PERMISSION_ALLOW_TEXTS if allow else self.PERMISSION_DENY_TEXTS
        logger.debug(f"开始检测权限弹窗（目标：{'允许' if allow else '拒绝'}）")

        for text in target_texts:
            try:
                # 用 BasePage 的 wait_visible 复用异常体系
                locator = (AppiumBy.XPATH, f'//*[contains(@text, "{text}")]')
                self.base_page.wait_visible(locator, timeout=timeout)
                self.base_page.click(locator)
                logger.info(f"成功处理权限弹窗：点击「{text}」")
                return True
            except ElementNotFoundException:
                continue  # 尝试下一个可能的文本

        logger.debug("未检测到权限弹窗")
        return False

    @allure.step("处理系统弹窗（关闭/取消）")
    def handle_system_popup(
        self,
        timeout: int = 3
    ) -> bool:
        """
        处理系统级弹窗（如更新提示、网络错误提示）
        :param timeout: 弹窗检测超时时间（秒）
        :return: 是否处理了弹窗
        """
        logger.debug("开始检测系统弹窗")
        for text in self.SYSTEM_POPUP_CLOSE_TEXTS:
            try:
                locator = (AppiumBy.XPATH, f'//*[contains(@text, "{text}")]')
                self.base_page.wait_visible(locator, timeout=timeout)
                self.base_page.click(locator)
                logger.info(f"成功处理系统弹窗：点击「{text}」")
                return True
            except ElementNotFoundException:
                continue

        logger.debug("未检测到系统弹窗")
        return False

    @allure.step("处理应用内弹窗（指定文本）")
    def handle_custom_popup(
        self,
        button_text: str,
        timeout: int = 5
    ) -> bool:
        """
        处理应用内自定义弹窗（如引导页、活动提示）
        :param button_text: 弹窗按钮文本（如“我知道了”）
        :param timeout: 弹窗检测超时时间（秒）
        :return: 是否处理了弹窗
        """
        logger.debug(f"开始检测应用内弹窗（目标按钮：{button_text}）")
        locator = (AppiumBy.XPATH, f'//*[contains(@text, "{button_text}")]')
        try:
            self.base_page.wait_visible(locator, timeout=timeout)
            self.base_page.click(locator)
            logger.info(f"成功处理应用内弹窗：点击「{button_text}」")
            return True
        except ElementNotFoundException:
            logger.debug(f"未检测到应用内弹窗（按钮：{button_text}）")
            return False

    @allure.step("批量处理常见弹窗")
    def handle_all_common_popups(self) -> None:
        """一键处理所有常见弹窗（权限+系统+应用内）"""
        self.handle_permission_popup(allow=True)
        self.handle_system_popup()
        self.handle_custom_popup("我知道了")
        self.handle_custom_popup("下次再说")