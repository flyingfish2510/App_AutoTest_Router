# -*- coding:utf8 -*-
import json

from config.setting import project_config


class ModifyReportTitle:

    def __init__(self,  path):
        super().__init__()
        self.report_path = path

    # 获取 summary.json 文件的数据内容
    @staticmethod
    def get_json_data(name, title_filepath):
        with open(title_filepath, 'rb') as f:
            params = json.load(f)
            params['reportName'] = name
            data = params
        f.close()
        return data

    # 修改 summary.json 文件的数据内容
    @staticmethod
    def write_json_data(dict_data, title_filepath):
        with open(title_filepath, 'w', encoding="utf-8") as r:
            json.dump(dict_data, r, ensure_ascii=False, indent=4)
        r.close()

    # 自定义测试报告标题
    def set_report_title(self, new_title, title_filepath):
        report_title = self.get_json_data(new_title, title_filepath)
        self.write_json_data(report_title, title_filepath)

    # 设置报告窗口的标题
    @staticmethod
    def set_windows_title(new_title, windows_title_filepath):
        """  设置打开的 Allure 报告的浏览器窗口标题文案
        :param new_title:
        :param windows_title_filepath: HTML测试报告的路径
        """
        # 定义为只读模型，并定义名称为: f
        with open(windows_title_filepath, 'r+', encoding="utf-8") as f:
            # 读取当前文件的所有内容
            all_the_lines = f.readlines()
            f.seek(0)
            f.truncate()
            # 循环遍历每一行的内容，将 "Allure Report" 全部替换为 → new_title(新文案)
            for line in all_the_lines:
                f.write(line.replace("Allure Report", new_title))
            # 关闭文件
            f.close()

    def run(self):
        # 修改测试报告窗口标题
        self.set_windows_title(project_config['windows_title'], self.report_path + "/index.html")
        # 修改测试报告标题
        self.set_report_title(project_config['report_title'], self.report_path + "/widgets/summary.json")
