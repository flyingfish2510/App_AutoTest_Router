import allure

from pages.device_manage_page import DeviceManagePage
from pages.device_page import DevicePage
from pages.access_device_page import AccessDevicePage
from pages.online_device_page import OnlineDevicePage
from pages.router_page import RouterPage
from pages.smarthome_page import SmartHomePage
from testcases.base_test import BaseTest


@allure.epic("Router")
@allure.feature("Device")
class Test02(BaseTest):

    def setup_method(self):
        self.smarthome_page = SmartHomePage(self.driver)
        self.router_page = RouterPage(self.driver)
        self.device_page = DevicePage(self.driver)
        self.access_device_page = AccessDevicePage(self.driver)
        self.online_device_page = OnlineDevicePage(self.driver)
        self.device_manage_page = DeviceManagePage(self.driver)
        self.router_card_name = '路由 BE3 Pro'
        self.devicename = 'HUAWEI Mate 70'
        self.edit_devicename = '貂蝉西施Abc123@😊'


    def test_02(self):
        self.smarthome_page.start_smarthome_app()
        self.smarthome_page.enter_router_management(self.router_card_name)
        self.router_page.switch_to_device_table()
        self.device_page.switch_to_access_device_page()
        self.access_device_page.switch_to_online_device_page()
        self.online_device_page.switch_to_device_manage_page(self.devicename)
        self.device_manage_page.edit_devicename(self.edit_devicename)
        assert self.edit_devicename == self.device_manage_page.get_device_name()

    def teardown_method(self):
        with allure.step("后置处理：恢复设备名称"):
            self.device_manage_page.edit_devicename(self.devicename)
        self.smarthome_page.stop_smarthome_app()
