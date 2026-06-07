import os

import pytest

from config.setting import project_config
from utils.logging.logger import logger


def run():
    # 从配置文件中获取项目名称
    logger.info("""开始执行{}项目...""".format(project_config['project_name']))
    pytest.main(['-s', '--alluredir', './report/tmp', "--clean-alluredir"])

    """
                   --reruns: 失败重跑次数
                   --count: 重复执行次数
                   -v: 显示错误位置以及错误的详细信息
                   -s: 等价于 pytest --capture=no 可以捕获print函数的输出
                   -q: 简化输出信息
                   -m: 运行指定标签的测试用例
                   -x: 一旦错误，则停止运行
                   -n: 多线程运行
                   --maxfail: 设置最大失败次数，当超出这个阈值时，则不会在执行测试用例
                    "--reruns=3", "--reruns-delay=2"
                   """
    os.system(r"allure generate ./report/tmp -o ./report/html --clean")



if __name__ == '__main__':
    "appium运行指令appium --relaxed-security"
    run()
