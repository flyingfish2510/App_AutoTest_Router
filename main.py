# main.py
import os
import shutil
import subprocess

import pytest

from config.setting import project_config
from utils.logging.logger import logger

# 1. 使用固定目录名（Allure 官方推荐工作流）
# results 目录：存放每次跑完的测试数据（包含我们要保留的 history）
# report 目录：存放最终生成的 HTML 报告
RESULTS_DIR = os.path.join(".", "report", "allure-results")
REPORT_DIR = os.path.join(".", "report", "allure-report")


def run():
    logger.info(f"🚀 开始执行 {project_config['project_name']} 项目...")

    # 2. 准备目录：如果存在旧的 results，先删掉重建（比 --clean-alluredir 更安全可控）
    if os.path.exists(RESULTS_DIR):
        logger.info(f"🗑️ 清理旧的结果目录: {RESULTS_DIR}")
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # 3. 如果有备份的历史数据，注入到当前的结果目录中
    backup_history = os.path.join(".", "allure_history")
    current_history = os.path.join(RESULTS_DIR, "history")

    if os.path.exists(backup_history) and os.listdir(backup_history):
        os.makedirs(current_history, exist_ok=True)
        for f in os.listdir(backup_history):
            src = os.path.join(backup_history, f)
            dst = os.path.join(current_history, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        logger.info("✅ 成功注入历史趋势数据")
    else:
        logger.info("ℹ️ 首次运行或无历史数据（正常）")

    # 4. 运行 pytest 收集测试结果（注意：这里移除了 --clean-alluredir）
    pytest_args = [
        "-s",
        f"--alluredir={RESULTS_DIR}"
    ]
    exit_code = pytest.main(pytest_args)
    if exit_code != 0:
        logger.warning(f"⚠️ pytest 运行结束，但存在失败用例，退出码：{exit_code}")

    # 5. 生成 Allure 报告（使用固定报告目录，并加上 --clean）
    # 原理说明：
    # -o REPORT_DIR：每次都生成到同一个报告文件夹
    # --clean：让 Allure 在生成前清空 REPORT_DIR 里的旧静态文件，但因为有 -o，
    #          Allure 内部会先将旧报告中的 history 提取出来，与新 results 合并。
    cmd = f'allure generate "{RESULTS_DIR}" -o "{REPORT_DIR}" --clean'
    logger.info(f"🛠️ 执行命令：{cmd}")

    # 使用 subprocess 代替 os.system，避免 Windows 空格路径解析错误
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"❌ Allure 报告生成失败：{result.stderr}")
        return

    logger.info(result.stdout)

    # 6. 备份最新的 history 文件夹（供下次使用）
    new_history = os.path.join(REPORT_DIR, "history")
    if os.path.exists(new_history):
        if os.path.exists(backup_history):
            shutil.rmtree(backup_history)
        shutil.copytree(new_history, backup_history)
        logger.info("✅ 成功备份本次历史趋势数据")
    else:
        logger.warning("⚠️ 未在报告中找到 history 文件夹")

    logger.info(f"🎉 报告生成完毕！请打开以下文件查看：\n   file:///{os.path.abspath(REPORT_DIR)}/index.html")


if __name__ == "__main__":
    run()