import allure

from common.constants import MYG
from pages.access_device_manage_page import AccessDeviceManagePage
from pages.access_device_page import AccessDevicePage
from pages.device_manage_page import DeviceManagePage
from pages.device_page import DevicePage
from pages.router_page import RouterPage
from pages.smarthome_page import SmartHomePage
from testcases.base_test import BaseTest


@allure.epic("Router")
@allure.feature("Device")
class Test01(BaseTest):

    def setup(self):
        # 主设备 Page 对象（device_01 已默认启动）
        self.smarthome_page = SmartHomePage(self.driver)
        self.router_page = RouterPage(self.driver)
        self.device_page = DevicePage(self.driver)
        self.access_device_page = AccessDevicePage(self.driver)
        self.online_device_page = AccessDeviceManagePage(self.driver)
        self.device_manage_page = DeviceManagePage(self.driver)

        # 初始化副设备 Driver（未启动）
        self.secondary_driver = None

    def test_01(self):
        # ========== 主设备操作（device_01 已启动） ==========
        self.step('步骤1：进入路由卡片页')
        self.smarthome_page.start_smarthome_app()
        self.smarthome_page.enter_router_management(MYG.ROUTER_NAME)

        self.step('步骤2：进入在线设备页面')
        self.router_page.switch_to_device_table()
        self.device_page.switch_to_access_device_page()
        self.access_device_page.switch_to_online_device_page()

        self.step(f'步骤3：进入{MYG.PHONE_NAME}的设备管理页面')
        self.online_device_page.switch_to_device_manage_page(MYG.PHONE_NAME)

        self.step(f'步骤4：修改{MYG.PHONE_NAME}的设备名称为{MYG.PHONE_NEW_NAME}')
        self.device_manage_page.edit_devicename(MYG.PHONE_NEW_NAME)

        self.checkpoint(f'检查点4：检查设备名称修改是否成功')
        assert MYG.PHONE_NEW_NAME == self.device_manage_page.get_device_name()

        # ========== 按需启动 device_02 ==========
        # if self.secondary_manager:
        #     logger.info("📱 在用例中启动 device_02")
        #     self.secondary_driver = self.secondary_manager.init_driver()
        #     self.secondary_smarthome_page = SmartHomePage(self.secondary_driver)
        #     self.secondary_smarthome_page.start_smarthome_app()
        #     self.secondary_smarthome_page.stop_smarthome_app()

    def teardown(self):
        self.step("后置处理1：恢复设备名称")
        self.device_manage_page.edit_devicename(MYG.PHONE_NAME)
        self.step("后置处理2：关闭智慧生活")
        self.smarthome_page.stop_smarthome_app()