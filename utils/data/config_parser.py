import configparser

from config.setting import FILE_PATH
from utils.logging.logger import logger


class ConfigParse:
    """
    解析.ini后缀的配置文件
    """

    def __init__(self, file_path=FILE_PATH['ini']):
        self.file_path = file_path
        self.config = configparser.ConfigParser()
        self.read_config()

    def read_config(self):
        self.config.read(self.file_path)

    def get_value(self, section, option):
        """
        获取配置文件的值
        :param section: 头参数
        :param option: 下级参数key值
        :return:
        """
        try:
            return self.config.get(section, option)
        except Exception as e:
            logger.error(f'解析配置文件出现异常，原因：{e}')

    def get_host(self, option):
        """
        专门获取接口的服务器ip地址信息
        :param option:
        :return:
        """
        return self.get_value('Host', option)

    def get_mysql_conf(self, option):
        """
        获取MySQL数据库的配置参数值
        :return:
        """
        return self.get_value('MySQL', option)
