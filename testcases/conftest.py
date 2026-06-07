# testcases/conftest.py
"""
pytest 夹具配置（支持单设备/多设备串行）
✅ 设备切换时清空屏幕尺寸缓存
✅ 使用本地定义的Allure常量
"""

import time
from typing import Generator, Dict, Any, List

import allure
import pytest

from common.base_page import BasePage
from common.driver_manager import AndroidDriverManager
from config.setting import app_config
from utils.logging.logger import logger

# =======================
# Allure相关常量（本地定义）
# =======================
ALLURE_EPIC = "Router"
ALLURE_FEATURE = "Device"


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--device",
        action="store",
        default=None,
        help="指定运行的设备名称"
    )

    parser.addini(
        "device_filter",
        type="string",
        default="all",
        help="默认设备过滤器"
    )


def get_enabled_devices() -> List[Dict[str, Any]]:
    devices = app_config.get("devices", {})
    enabled_devices = []

    for name, config in devices.items():
        if config.get("enabled", False):
            config["name"] = name
            enabled_devices.append(config)

    return enabled_devices


def filter_devices(devices: List[Dict[str, Any]], device_filter: str) -> List[Dict[str, Any]]:
    if device_filter.lower() == "all":
        return devices

    filtered = [d for d in devices if d["name"] == device_filter]
    if not filtered:
        logger.warning(f"⚠️ 未找到设备: {device_filter}")
        return devices

    return filtered


def pytest_generate_tests(metafunc):
    if "device_info" in metafunc.fixturenames:
        all_devices = get_enabled_devices()
        device_filter = metafunc.config.getoption("--device")

        if device_filter is None:
            device_filter = metafunc.config.getini("device_filter")

        devices = filter_devices(all_devices, device_filter)

        metafunc.parametrize(
            "device_info",
            devices,
            ids=[d["name"] for d in devices],
            scope="class"
        )


@pytest.fixture(scope="class")
def driver(request, device_info: Dict[str, Any]) -> Generator:
    device_name = device_info["name"]
    udid = device_info["udid"]

    # ✅ 使用本地定义的Allure常量
    allure.dynamic.epic(ALLURE_EPIC)
    allure.dynamic.feature(ALLURE_FEATURE)
    allure.dynamic.tag(f"Device:{device_name}")
    allure.dynamic.parameter("udid", udid)

    logger.info(f"🚀 启动设备: {device_name} ({udid})")

    manager = AndroidDriverManager(device_info)

    try:
        driver = manager.init_driver()
        request.cls.driver = driver
        logger.info(f"✅ 设备 {device_name} Driver 初始化成功")

        yield driver

    except Exception as e:
        logger.error(f"❌ 设备 {device_name} Driver 初始化失败: {e}")
        raise

    finally:
        logger.info(f"🛑 清理设备: {device_name}")
        # ✅ 清空屏幕尺寸缓存（关键）
        BasePage.clear_window_size_cache()
        manager.quit_driver()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        driver = _get_driver_from_item(item)
        if driver:
            screenshot_name = f"{item.name}_{int(time.time())}_failed"
            _attach_screenshot(driver, screenshot_name)


def _get_driver_from_item(item) -> Any:
    if hasattr(item.instance, "driver"):
        return item.instance.driver

    # 尝试从 page 对象中获取
    page_attrs = [
        "smarthome_page", "router_page", "device_page",
        "access_device_page", "online_device_page", "device_manage_page"
    ]

    for attr in page_attrs:
        if hasattr(item.instance, attr):
            page = getattr(item.instance, attr)
            if hasattr(page, "driver"):
                return page.driver

    return None


def _attach_screenshot(driver, name: str):
    try:
        screenshot = driver.get_screenshot_as_png()
        allure.attach(
            screenshot,
            name=name,
            attachment_type=allure.attachment_type.PNG
        )
    except Exception:
        pass


def pytest_sessionstart(session):
    logger.info("=" * 60)
    logger.info("🧪 自动化测试会话开始")
    logger.info("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    logger.info("=" * 60)
    logger.info(f"🏁 测试会话结束，退出码: {exitstatus}")
    logger.info("=" * 60)