
import yaml

from utils.logging.logger import logger


def read_yaml(yaml_path):
    """
    读取yaml文件数据
    :param yaml_path: 文件路径
    :return:
    """
    try:
        testcase_list = []
        with open(yaml_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            # 处理一个yaml文件多条测试用例的场景
            if len(data) <= 1:
                yaml_data = data[0]
                base_info = yaml_data.get('baseInfo')
                for ts in yaml_data.get('testCase'):
                    params = [base_info, ts]
                    testcase_list.append(params)
                return testcase_list
            else:
                return data
    except UnicodeDecodeError:
        logger.error(f'{yaml_path}文件编码格式错误，--尝试使用utf-8去解码YAML文件发生错误，请确保你的yaml文件是utf-8格式！')
    except yaml.YAMLError as e:
        logger.error(f'Error：读取yaml文件失败，请检查格式 -{yaml_path}，{e}')
    except Exception as e:
        logger.error(f'读取{yaml_path}文件时出现异常，原因：{e}')

