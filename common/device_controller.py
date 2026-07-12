# common/device_controller.py
"""
设备与系统级操作控制器
⚠️ 职责边界：仅做设备/系统操作，不涉及任何 UI 元素交互
"""

import time
from typing import Optional

import allure
from appium.webdriver.webdriver import WebDriver

from common.exceptions import DeviceOperationException  # ✅ 对齐 E3002 异常
from utils.logging.log_tool import log

# Android KeyCode 常量（避免魔法数字）
KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_WAKEUP = 224


class DeviceController:
    """Android 设备控制器（Appium Native API Only）"""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    # ================= 屏幕与电源 =================
    @allure.step("检测屏幕是否点亮")
    def is_screen_on(self) -> bool:
        """检测屏幕是否点亮"""
        try:
            result = self.driver.execute_script(
                "mobile: shell",
                {"command": "dumpsys", "args": ["power"]}
            )
            return "mWakefulness=Awake" in result or "mScreenOn=true" in result
        except Exception as e:
            log.warning(f"检测屏幕状态失败: {e}")
            return False

    @allure.step("唤醒屏幕")
    def wake_up(self):
        """唤醒屏幕"""
        if not self.is_screen_on():
            self.driver.press_keycode(KEYCODE_WAKEUP)
            log.debug("屏幕已唤醒")
        else:
            log.debug("屏幕已是唤醒状态")

    @allure.step("解锁屏幕（PIN码: {pin_code}）")
    def unlock(self, pin_code: Optional[str] = None):
        """解锁屏幕（支持 PIN 码）"""
        self.wake_up()
        if pin_code:
            for digit in pin_code:
                self.driver.press_keycode(int(digit))
                time.sleep(0.1)  # 模拟真实输入间隔
            log.debug(f"PIN 解锁完成")

    # ================= 应用生命周期 =================
    @allure.step("返回桌面")
    def go_home(self):
        """返回桌面"""
        self.driver.press_keycode(KEYCODE_HOME)
        log.debug("已返回桌面")

    @allure.step("启动应用: {package}")
    def start_app(self, package: str):
        """启动应用"""
        try:
            self.driver.activate_app(package)
            log.info(f"应用已启动: {package}")
        except Exception as e:
            raise DeviceOperationException(
                message=f"启动应用 {package} 失败",
                action="start_app",
                extra={"package": package, "error": str(e)}
            )

    @allure.step("终止应用: {package}")
    def kill_app(self, package: str):
        """强制停止应用"""
        try:
            self.driver.terminate_app(package)
        except Exception as e:
            log.warning(f"Terminate app 失败: {e}，尝试 shell 命令")
            try:
                self.driver.execute_script(
                    "mobile: shell",
                    {"command": "am", "args": ["force-stop", package]}
                )
            except Exception as e:
                raise DeviceOperationException(
                    message=f"终止应用 {package} 失败",
                    action="kill_app",
                    extra={"package": package, "error": str(e)}
                )
        log.info(f"应用已终止: {package}")

    @allure.step("重启应用: {package}")
    def restart_app(self, package: str, wait: int = 2):
        """重启应用"""
        self.kill_app(package)
        time.sleep(wait)
        self.start_app(package)

    # ================= 导航操作 =================
    @allure.step("点击返回键")
    def press_back(self):
        """模拟物理返回键"""
        self.driver.press_keycode(KEYCODE_BACK)
        log.debug("点击返回键")

    # ================= 系统信息 =================
    @allure.step("获取当前 Activity")
    def get_current_activity(self) -> str:
        """获取当前 Activity"""
        try:
            return self.driver.current_activity
        except Exception as e:
            log.warning(f"获取 Activity 失败: {e}")
            raise DeviceOperationException(
                message="获取当前 Activity 失败",
                action="get_current_activity",
                extra={"error": str(e)}
            )

    @allure.step("获取设备时间")
    def get_device_time(self) -> str:
        """获取设备时间"""
        return self.driver.device_time

    # ================= 高级操作 =================
    @allure.step("清除应用数据: {package}")
    def clear_app_data(self, package: str):
        """清除应用数据（非重置）"""
        try:
            self.driver.execute_script(
                "mobile: shell",
                {"command": "pm", "args": ["clear", package]}
            )
            log.info(f"已清除应用数据: {package}")
        except Exception as e:
            raise DeviceOperationException(
                message=f"清除应用数据 {package} 失败",
                action="clear_app_data",
                extra={"package": package, "error": str(e)}
            )