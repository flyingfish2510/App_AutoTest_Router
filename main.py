# main.py
import os
import shutil
import subprocess
import pytest

from config.setting import project_config
from common.appium_server import appium_server_context
from utils.logging.logger import logger

# =======================
# Allure 历史报告配置（官方推荐工作流）
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "report", "allure-results")
REPORT_DIR = os.path.join(BASE_DIR, "report", "allure-report")
HISTORY_BACKUP_DIR = os.path.join(BASE_DIR, "allure_history")


def ensure_directories():
    """确保所有必要的目录存在"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(HISTORY_BACKUP_DIR, exist_ok=True)
    logger.info("✅ 目录检查完成")


def clean_results_directory():
    """清理旧的测试结果目录"""
    if os.path.exists(RESULTS_DIR):
        logger.info(f"🗑️ 清理旧的结果目录: {RESULTS_DIR}")
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(RESULTS_DIR, exist_ok=True)


def inject_history_data():
    """
    注入历史数据到结果目录
    Allure 必须从 results 目录读取 history 才能生成趋势图
    """
    current_history = os.path.join(RESULTS_DIR, "history")

    if os.path.exists(HISTORY_BACKUP_DIR) and os.listdir(HISTORY_BACKUP_DIR):
        os.makedirs(current_history, exist_ok=True)
        for f in os.listdir(HISTORY_BACKUP_DIR):
            src = os.path.join(HISTORY_BACKUP_DIR, f)
            dst = os.path.join(current_history, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        logger.info("✅ 成功注入历史趋势数据")
    else:
        logger.info("ℹ️ 首次运行或无历史数据（正常）")


def run_pytest_tests():
    """运行 pytest 测试并收集结果"""
    logger.info(f"🧪 开始执行 {project_config['project_name']} 项目...")

    pytest_args = [
        "-s",
        f"--alluredir={RESULTS_DIR}"
    ]

    exit_code = pytest.main(pytest_args)
    if exit_code != 0:
        logger.warning(f"⚠️ pytest 运行结束，但存在失败用例，退出码：{exit_code}")

    return exit_code


def generate_allure_report():
    """生成 Allure 报告"""
    logger.info("📊 生成 Allure 报告...")

    cmd = f'allure generate "{RESULTS_DIR}" -o "{REPORT_DIR}" --clean'
    logger.info(f"🛠️ 执行命令：{cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"❌ Allure 报告生成失败：{result.stderr}")
        return False

    logger.info(result.stdout)
    return True


def backup_history_data():
    """备份最新的 history 文件夹供下次使用"""
    new_history = os.path.join(REPORT_DIR, "history")

    if os.path.exists(new_history):
        if os.path.exists(HISTORY_BACKUP_DIR):
            shutil.rmtree(HISTORY_BACKUP_DIR)
        shutil.copytree(new_history, HISTORY_BACKUP_DIR)
        logger.info("✅ 成功备份本次历史趋势数据")
        return True
    else:
        logger.warning("⚠️ 未在报告中找到 history 文件夹")
        return False


def print_report_location():
    """打印报告位置信息"""
    abs_path = os.path.abspath(REPORT_DIR)
    logger.info(f"🎉 报告生成完毕！请打开以下文件查看：\n   file:///{abs_path}/index.html")


def main():
    """主执行流程"""
    # 使用 Appium Server 上下文管理器（自动启动/关闭）
    with appium_server_context():
        # 1. 确保目录存在
        ensure_directories()

        # 2. 清理旧的结果目录
        clean_results_directory()

        # 3. 注入历史数据
        inject_history_data()

        # 4. 运行测试
        run_pytest_tests()

        # 5. 生成报告
        if generate_allure_report():
            # 6. 备份历史数据
            backup_history_data()
            # 7. 打印报告位置
            print_report_location()
        else:
            logger.error("❌ 报告生成失败，跳过历史备份")


if __name__ == "__main__":
    main()