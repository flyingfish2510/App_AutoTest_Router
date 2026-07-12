# common/page_validator.py
"""
页面校验工具类
⚠️ 职责边界：仅做页面状态校验，不涉及 UI 操作或设备控制
"""

from typing import Tuple, Literal

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.exceptions import PageSwitchFailedException  # ✅ 对齐 E2001 异常
from utils.logging.log_tool import log


class PageValidator:
    """页面状态校验器（仅校验，不操作）"""

    def __init__(self, driver):
        self.driver = driver

    # ================= 元素存在性校验 =================
    @allure.step("校验页面包含元素: {locator}")
    def should_contain_element(
        self,
        locator: Tuple,
        timeout: int = 10
    ) -> bool:
        """
        校验页面中存在可见元素
        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            log.debug(f"页面校验成功：包含元素 {locator}")
            return True
        except TimeoutException:
            raise PageSwitchFailedException(
                message=f"页面未包含元素 {locator}",
                locator=locator,
                page=self.__class__.__name__,
                action="should_contain_element",
                extra={"timeout": timeout}
            )

    @allure.step("校验页面不包含元素: {locator}")
    def should_not_contain_element(
        self,
        locator: Tuple,
        timeout: int = 5
    ) -> bool:
        """
        校验页面中不存在可见元素
        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        """
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.visibility_of_element_located(locator)
            )
            log.debug(f"页面校验成功：不包含元素 {locator}")
            return True
        except TimeoutException:
            raise PageSwitchFailedException(
                message=f"页面仍包含元素 {locator}",
                locator=locator,
                page=self.__class__.__name__,
                action="should_not_contain_element",
                extra={"timeout": timeout}
            )

    # ================= Activity 校验 =================
    @allure.step("校验当前 Activity 为: {expected_activity}")
    def should_match_activity(
        self,
        expected_activity: str,
        match_type: Literal["equals", "contains", "startswith", "endswith"] = "equals",
        timeout: int = 10
    ) -> bool:
        """
        校验当前 Activity 是否符合预期
        :param expected_activity: 预期 Activity
        :param match_type: 匹配类型（等于/包含/开头/结尾）
        :param timeout: 超时时间（秒）
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: self._check_activity(d, expected_activity, match_type)
            )
            log.debug(f"页面校验成功：Activity 匹配 {expected_activity}（类型：{match_type}）")
            return True
        except TimeoutException:
            current_activity = self.driver.current_activity
            raise PageSwitchFailedException(
                message=f"Activity 校验失败：预期 {expected_activity}（{match_type}），实际 {current_activity}",
                page=self.__class__.__name__,
                action="should_match_activity",
                extra={
                    "expected": expected_activity,
                    "actual": current_activity,
                    "match_type": match_type,
                    "timeout": timeout
                }
            )

    def _check_activity(self, driver, expected_activity: str, match_type: str) -> bool:
        """Activity 匹配逻辑（私有方法）"""
        current_activity = driver.current_activity
        if match_type == "equals":
            return current_activity == expected_activity
        elif match_type == "contains":
            return expected_activity in current_activity
        elif match_type == "startswith":
            return current_activity.startswith(expected_activity)
        elif match_type == "endswith":
            return current_activity.endswith(expected_activity)
        else:
            raise ValueError(f"不支持的 match_type: {match_type}")

    # ================= 页面标题校验 =================
    @allure.step("校验页面标题为: {expected_title}")
    def should_have_title(
        self,
        expected_title: str,
        exact_match: bool = True,
        timeout: int = 10
    ) -> bool:
        """
        校验页面标题是否符合预期
        :param expected_title: 预期标题
        :param exact_match: 是否精确匹配（默认 True）
        :param timeout: 超时时间（秒）
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: self._check_title(d, expected_title, exact_match)
            )
            log.debug(f"页面校验成功：标题匹配 {expected_title}（精确匹配：{exact_match}）")
            return True
        except TimeoutException:
            current_title = self.driver.title
            raise PageSwitchFailedException(
                message=f"标题校验失败：预期 {expected_title}（精确匹配：{exact_match}），实际 {current_title}",
                page=self.__class__.__name__,
                action="should_have_title",
                extra={
                    "expected": expected_title,
                    "actual": current_title,
                    "exact_match": exact_match,
                    "timeout": timeout
                }
            )

    def _check_title(self, driver, expected_title: str, exact_match: bool) -> bool:
        """标题匹配逻辑（私有方法）"""
        current_title = driver.title
        if exact_match:
            return current_title == expected_title
        else:
            return expected_title in current_title