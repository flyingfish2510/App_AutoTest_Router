# main.py
"""
自动化测试主入口（长稳版本 + 多设备并发支持）
✅ Appium Server 自动管理
✅ Allure 历史趋势保留
✅ 多设备并发执行
✅ 通过配置文件控制并发开关
✅ 完善的错误处理
"""

import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime

import pytest

from common.appium_server import appium_server_context
from config.setting import project_config, app_config
from utils.logging.logger import logger

# =======================
# 配置常量
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Allure 目录配置
RESULTS_DIR = os.path.join(BASE_DIR, "report", "allure-results")
REPORT_DIR = os.path.join(BASE_DIR, "report", "allure-report")
HISTORY_BACKUP_DIR = os.path.join(BASE_DIR, "allure_history")

# 从配置文件读取并发配置
PARALLEL_CONFIG = app_config.get("parallel", {})
PARALLEL_ENABLED = PARALLEL_CONFIG.get("enabled", False)
PARALLEL_DEVICES = PARALLEL_CONFIG.get("devices", 2)
DEVICE_FILTER = PARALLEL_CONFIG.get("device_filter", "all")


class TestExecutionError(Exception):
    """测试执行异常"""
    pass


def setup_environment():
    """初始化测试环境"""
    logger.info("=" * 60)
    logger.info(f"🚀 启动 {project_config.get('project_name', '自动化测试')} 长稳版本")
    logger.info(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 项目路径: {BASE_DIR}")
    logger.info(f"🔄 并发模式: {'开启' if PARALLEL_ENABLED else '关闭'}")
    if PARALLEL_ENABLED:
        logger.info(f"📱 并发设备数: {PARALLEL_DEVICES}")
    logger.info(f"🔍 设备过滤: {DEVICE_FILTER}")
    logger.info("=" * 60)


def ensure_directories():
    """确保所有必要的目录存在"""
    directories = [RESULTS_DIR, REPORT_DIR, HISTORY_BACKUP_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    logger.info("✅ 目录初始化完成")


def clean_previous_results():
    """清理之前的测试结果"""
    try:
        if os.path.exists(RESULTS_DIR):
            logger.info(f"🗑️ 清理旧的结果目录: {RESULTS_DIR}")
            shutil.rmtree(RESULTS_DIR)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        logger.info("✅ 结果目录清理完成")
    except Exception as e:
        logger.error(f"❌ 清理结果目录失败: {e}")
        raise TestExecutionError("无法清理结果目录")


def inject_history_data() -> bool:
    """注入历史数据到结果目录"""
    current_history = os.path.join(RESULTS_DIR, "history")

    if os.path.exists(HISTORY_BACKUP_DIR) and os.listdir(HISTORY_BACKUP_DIR):
        try:
            os.makedirs(current_history, exist_ok=True)
            for f in os.listdir(HISTORY_BACKUP_DIR):
                src = os.path.join(HISTORY_BACKUP_DIR, f)
                dst = os.path.join(current_history, f)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            logger.info("✅ 历史趋势数据注入成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 注入历史数据失败: {e}")
            return False
    else:
        logger.info("ℹ️ 首次运行或无历史数据（正常）")
        return False


def build_pytest_args() -> list:
    """构建 pytest 参数"""
    pytest_args = ["-s", f"--alluredir={RESULTS_DIR}"]

    # 添加并发参数（从配置文件读取）
    if PARALLEL_ENABLED:
        pytest_args.extend(["-n", str(PARALLEL_DEVICES)])
        logger.info(f"🔄 启用多设备并发，设备数: {PARALLEL_DEVICES}")

    # 添加设备过滤参数（从配置文件读取）
    if DEVICE_FILTER != "all":
        pytest_args.extend(["--device", DEVICE_FILTER])

    return pytest_args


def run_tests(pytest_args: list) -> int:
    """运行 pytest 测试"""
    logger.info("🧪 开始执行测试用例...")
    logger.info(f"📋 Pytest 参数: {' '.join(pytest_args)}")

    try:
        exit_code = pytest.main(pytest_args)
        if exit_code == 0:
            logger.info("✅ 所有测试用例执行成功")
        else:
            logger.warning(f"⚠️ 测试用例执行完成，但存在失败用例（退出码: {exit_code}）")
        return exit_code
    except Exception as e:
        logger.error(f"❌ 测试执行异常: {e}")
        logger.error(traceback.format_exc())
        raise TestExecutionError("测试执行失败")


def generate_report() -> bool:
    """生成 Allure 报告"""
    logger.info("📊 生成 Allure 报告...")

    try:
        result = subprocess.run(
            f'allure generate "{RESULTS_DIR}" -o "{REPORT_DIR}" --clean',
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if result.returncode == 0:
            logger.info("✅ Allure 报告生成成功")
            return True
        else:
            logger.error(f"❌ Allure 报告生成失败（退出码: {result.returncode}）")
            logger.error(f"错误输出: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("❌ Allure 报告生成超时（超过5分钟）")
        return False
    except Exception as e:
        logger.error(f"❌ 生成报告时发生异常: {e}")
        logger.error(traceback.format_exc())
        return False


def backup_history_data() -> bool:
    """备份最新的 history 文件夹"""
    new_history = os.path.join(REPORT_DIR, "history")

    if os.path.exists(new_history):
        try:
            if os.path.exists(HISTORY_BACKUP_DIR):
                shutil.rmtree(HISTORY_BACKUP_DIR)
            shutil.copytree(new_history, HISTORY_BACKUP_DIR)
            logger.info("✅ 历史趋势数据备份成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 备份历史数据失败: {e}")
            return False
    else:
        logger.warning("⚠️ 未在报告中找到 history 文件夹")
        return False


def print_summary(exit_code: int, report_generated: bool):
    """打印执行摘要"""
    logger.info("=" * 60)
    logger.info("📋 执行摘要")
    logger.info("=" * 60)
    logger.info(f"🕐 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔄 并发模式: {'开启' if PARALLEL_ENABLED else '关闭'}")
    if PARALLEL_ENABLED:
        logger.info(f"📱 并发设备数: {PARALLEL_DEVICES}")
    logger.info(f"📊 测试结果: {'成功' if exit_code == 0 else '存在失败'}")
    logger.info(f"📈 报告状态: {'已生成' if report_generated else '生成失败'}")

    if report_generated:
        abs_path = os.path.abspath(REPORT_DIR)
        logger.info(f"📁 报告位置: file:///{abs_path}/index.html")

    logger.info("=" * 60)


def cleanup_resources():
    """清理临时资源"""
    logger.info("🧹 开始清理临时资源...")
    # 可以在这里添加额外的清理逻辑
    logger.info("✅ 资源清理完成")


def main():
    """主执行流程"""
    exit_code = 0
    report_generated = False

    try:
        # 1. 初始化环境
        setup_environment()

        # 2. 使用 Appium Server 上下文（自动管理生命周期）
        with appium_server_context():
            # 3. 准备目录
            ensure_directories()

            # 4. 清理旧结果
            clean_previous_results()

            # 5. 注入历史数据
            inject_history_data()

            # 6. 构建 pytest 参数（从配置文件读取并发配置）
            pytest_args = build_pytest_args()

            # 7. 运行测试
            exit_code = run_tests(pytest_args)

            # 8. 生成报告
            report_generated = generate_report()

            # 9. 备份历史数据（仅当报告生成成功时）
            if report_generated:
                backup_history_data()
            else:
                logger.warning("⚠️ 报告未生成，跳过历史数据备份")

    except TestExecutionError as e:
        logger.error(f"❌ 测试执行错误: {e}")
        exit_code = 1
    except KeyboardInterrupt:
        logger.warning("⚠️ 用户中断测试执行")
        exit_code = 130
    except Exception as e:
        logger.error(f"❌ 未知错误: {e}")
        logger.error(traceback.format_exc())
        exit_code = 1
    finally:
        # 10. 打印执行摘要
        print_summary(exit_code, report_generated)

        # 11. 清理资源
        cleanup_resources()

        # 12. 退出程序
        logger.info("🏁 测试执行结束")
        sys.exit(exit_code)


if __name__ == "__main__":
    # 确保项目根目录在 sys.path 中
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    main()