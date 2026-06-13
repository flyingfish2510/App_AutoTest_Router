# testcases/conftest.py
"""
pytest 夹具配置（支持多设备并发）
✅ 单设备默认启动
✅ 多设备并发执行
✅ 设备动态分配
✅ 失败自动截图
"""

import os
import time
from typing import Generator, Dict, Any, List

import allure
import pytest

from common.base_page import BasePage
from common.driver_manager import AndroidDriverManager
from config.setting import app_config
from utils.logging.logger import logger

# =======================
# Allure 相关常量
# =======================
ALLURE_EPIC = "Router"
ALLURE_FEATURE = "Device"


def pytest_addoption(parser):
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
    """获取所有启用的设备配置"""
    devices = app_config.get("devices", {})
    enabled_devices = []
    for device_key, config in devices.items():
        if config.get("enabled", False):
            config["name"] = device_key
            enabled_devices.append(config)
    return enabled_devices


def filter_devices(devices: List[Dict[str, Any]], device_filter: str) -> List[Dict[str, Any]]:
    """按名称过滤设备"""
    if device_filter.lower() == "all":
        return devices
    filtered = [d for d in devices if d.get("name") == device_filter]
    return filtered if filtered else devices


def get_worker_id() -> int:
    """获取当前 worker 的 ID（用于多设备并发分配）"""
    # 尝试从环境变量获取 worker ID
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')
    if worker_id:
        # worker_id 格式通常是 "gw0", "gw1" 等
        try:
            return int(worker_id.replace('gw', ''))
        except (ValueError, AttributeError):
            pass

    # 默认返回 0
    return 0


def assign_device_to_worker(devices: List[Dict[str, Any]], worker_id: int) -> Dict[str, Any]:
    """根据 worker ID 分配设备"""
    if not devices:
        raise RuntimeError("没有可用的设备")

    # 循环分配设备
    device_index = worker_id % len(devices)
    return devices[device_index]


def pytest_generate_tests(metafunc):
    """参数化设备配置"""
    if "device_info" in metafunc.fixturenames:
        all_devices = get_enabled_devices()
        device_filter = metafunc.config.getoption("--device") or metafunc.config.getini("device_filter")
        devices = filter_devices(all_devices, device_filter)

        metafunc.parametrize(
            "device_info",
            devices,
            ids=[d["name"] for d in devices],
            scope="class"
        )


# =======================
# 核心夹具：动态设备分配（支持单设备和多设备并发）
# =======================
@pytest.fixture(scope="class")
def dynamic_driver(request) -> Generator:
    """动态分配设备（支持单设备和多设备并发）"""
    enabled_devices = get_enabled_devices()
    if not enabled_devices:
        raise RuntimeError("没有启用的设备")

    # 获取当前 worker ID
    worker_id = get_worker_id()

    # 分配设备
    device_info = assign_device_to_worker(enabled_devices, worker_id)
    device_name = device_info["name"]
    udid = device_info["udid"]

    allure.dynamic.epic(ALLURE_EPIC)
    allure.dynamic.feature(ALLURE_FEATURE)
    allure.dynamic.tag(f"Device:{device_name}")
    allure.dynamic.parameter("udid", udid)
    allure.dynamic.parameter("worker_id", worker_id)

    logger.info(f"🚀 Worker {worker_id} 启动设备: {device_name} ({udid})")

    manager = AndroidDriverManager(device_info)

    try:
        drv = manager.init_driver()
        request.cls.driver = drv
        logger.info(f"✅ 设备 {device_name} Driver 初始化成功")
        yield drv
    except Exception as e:
        logger.error(f"❌ 设备 {device_name} Driver 初始化失败: {e}")
        raise
    finally:
        logger.info(f"🛑 清理设备: {device_name}")
        BasePage.clear_window_size_cache()
        manager.quit_driver()


# =======================
# 按需夹具：手动启动 device_02
# =======================
@pytest.fixture(scope="class")
def secondary_driver_manager(request):
    """按需启动第二个设备的管理器（device_02）"""
    enabled_devices = get_enabled_devices()
    if len(enabled_devices) < 2:
        logger.warning("⚠️ 未配置第二个设备，无法启动 device_02")
        yield None
        return

    device_info = enabled_devices[1]  # device_02
    manager = AndroidDriverManager(device_info)

    yield manager

    # 测试结束后清理（仅当device_02启用且Driver已初始化时）
    if manager.driver:
        logger.info(f"🛑 清理设备: {device_info['name']}")
        BasePage.clear_window_size_cache()
        manager.quit_driver()


# =======================
# 失败截图钩子
# =======================
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
    return None


def _attach_screenshot(driver, name: str):
    try:
        screenshot = driver.get_screenshot_as_png()
        allure.attach(screenshot, name=name, attachment_type=allure.attachment_type.PNG)
    except Exception:
        pass


# =======================
# 会话生命周期日志
# =======================
def pytest_sessionstart(session):
    logger.info("=" * 60)
    logger.info("🧪 自动化测试会话开始")
    logger.info("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    logger.info("=" * 60)
    logger.info(f"🏁 测试会话结束，退出码: {exitstatus}")
    logger.info("=" * 60)