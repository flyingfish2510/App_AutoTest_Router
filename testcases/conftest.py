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
from utils.logging.log_tool import log

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
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')
    if worker_id:
        try:
            return int(worker_id.replace('gw', ''))
        except (ValueError, AttributeError):
            pass
    return 0


def assign_device_to_worker(devices: List[Dict[str, Any]], worker_id: int) -> Dict[str, Any]:
    """根据 worker ID 分配设备"""
    if not devices:
        raise RuntimeError("没有可用的设备")
    device_index = worker_id % len(devices)
    return devices[device_index]


# =======================
# ✅ 移除 pytest_generate_tests（不再需要）
# =======================

# =======================
# 核心夹具：动态设备分配（支持单设备和多设备并发）
# =======================
@pytest.fixture(scope="class")
def dynamic_driver(request) -> Generator:
    """动态分配设备（支持单设备和多设备并发）"""
    enabled_devices = get_enabled_devices()
    if not enabled_devices:
        raise RuntimeError("没有启用的设备")

    # ✅ 关键修改：获取设备过滤条件
    device_filter = request.config.getoption("--device") or request.config.getini("device_filter")

    # ✅ 过滤设备
    filtered_devices = filter_devices(enabled_devices, device_filter)
    if not filtered_devices:
        raise RuntimeError(f"没有找到匹配 '{device_filter}' 的设备")

    # ✅ 获取当前 worker ID
    worker_id = get_worker_id()

    # ✅ 从过滤后的设备中分配
    device_info = assign_device_to_worker(filtered_devices, worker_id)
    device_name = device_info["name"]
    udid = device_info["udid"]

    allure.dynamic.epic(ALLURE_EPIC)
    allure.dynamic.feature(ALLURE_FEATURE)
    allure.dynamic.tag(f"Device:{device_name}")
    allure.dynamic.parameter("udid", udid)
    allure.dynamic.parameter("worker_id", worker_id)
    allure.dynamic.parameter("device_filter", device_filter)

    log.info(f"🚀 Worker {worker_id} 启动设备: {device_name} ({udid})")
    log.info(f"📱 设备过滤条件: {device_filter}")
    log.info(f"📱 可用设备数: {len(filtered_devices)}")

    manager = AndroidDriverManager(device_info)

    try:
        drv = manager.init_driver()
        request.cls.driver = drv
        log.info(f"✅ 设备 {device_name} Driver 初始化成功")
        yield drv
    except Exception as e:
        log.error(f"❌ 设备 {device_name} Driver 初始化失败: {e}")
        raise
    finally:
        log.info(f"🛑 清理设备: {device_name}")
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
        log.warning("⚠️ 未配置第二个设备，无法启动 device_02")
        yield None
        return

    device_info = enabled_devices[1]  # device_02
    manager = AndroidDriverManager(device_info)

    yield manager

    if manager.driver:
        log.info(f"🛑 清理设备: {device_info['name']}")
        BasePage.clear_window_size_cache()
        manager.quit_driver()


# =======================
# 合并的 pytest_runtest_makereport 钩子
# =======================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when == "call" and rep.failed:
        driver = _get_driver_from_item(item)
        if driver:
            screenshot_name = f"{item.name}_{int(time.time())}_failed"
            _attach_screenshot(driver, screenshot_name)
            log.error(f"❌ 测试失败，已截图: {screenshot_name}")


def _get_driver_from_item(item) -> Any:
    if hasattr(item.instance, "driver"):
        return item.instance.driver
    return None


def _attach_screenshot(driver, name: str):
    try:
        screenshot = driver.get_screenshot_as_png()
        allure.attach(screenshot, name=name, attachment_type=allure.attachment_type.PNG)
    except Exception as e:
        log.warning(f"⚠️ 截图失败: {e}")


# =======================
# 用例筛选：根据 testcase.txt
# =======================
def pytest_collection_modifyitems(session, config, items):
    """
    根据项目根目录下的 testcase.txt 筛选测试用例
    ✅ 支持：test_01
    ✅ 支持：Test01::test_01
    ✅ 支持注释 #
    ✅ 支持空行
    """
    import os

    project_root = os.path.dirname(os.path.dirname(__file__))
    testcase_file = os.path.join(project_root, "testcase.txt")

    if not os.path.exists(testcase_file):
        log.warning("⚠️ testcase.txt 不存在，将运行所有用例")
        return

    with open(testcase_file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # 解析用例名（支持注释、去空行）
    selected_cases = set()
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        selected_cases.add(line)

    if not selected_cases:
        log.info("ℹ️ testcase.txt 为空，将运行所有用例")
        return

    selected = []
    deselected = []

    for item in items:
        # item.name = 测试函数名，如 test_01
        # item.nodeid = testcases/test_01.py::Test01::test_01
        if item.name in selected_cases:
            selected.append(item)
        elif "::".join(item.nodeid.split("::")[1:]) in selected_cases:
            selected.append(item)
        else:
            deselected.append(item)

    # 替换用例列表
    items[:] = selected

    # 通知 pytest 哪些用例被跳过（影响报告统计）
    config.hook.pytest_deselected(items=deselected)

    log.info(
        f"✅ 根据 testcase.txt 筛选：运行 {len(selected)} 条，跳过 {len(deselected)} 条"
    )

# =======================
# 会话生命周期日志
# =======================
def pytest_sessionstart(session):
    log.info("=" * 60)
    log.info("🧪 自动化测试会话开始")
    log.info("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    log.info("=" * 60)
    log.info(f"🏁 测试会话结束，退出码: {exitstatus}")
    log.info("=" * 60)