# common/constants.py
"""
项目通用常量定义
✅ 仅包含跨模块共享的通用常量
"""
from config.setting import FILE_PATH
from utils.data.yaml_reader import read_yaml
from utils.logging.log_tool import log

# =======================
# 时间相关常量
# =======================
DEFAULT_TIMEOUT = 10          # 默认显式等待超时时间（秒）
SWIPE_DURATION = 800         # 滑动持续时间（毫秒）
LONG_PRESS_DURATION = 2000    # 长按持续时间（毫秒）
SHORT_WAIT = 1                # 短等待时间（秒）
MEDIUM_WAIT = 3               # 中等等待时间（秒）
LONG_WAIT = 5                 # 长等待时间（秒）

# =======================
# 滑动相关常量
# =======================
SWIPE_RATIO_DEFAULT = 0.8      # 默认滑动比例
SWIPE_UP_RATIO_START = 0.8      # 向上滑动起始位置比例
SWIPE_DOWN_RATIO_START = 0.2    # 向下滑动起始位置比例

# =======================
# 坐标点击相关常量
# =======================
TAP_DURATION = 100             # 点击持续时间（毫秒）

# =======================
# 设备相关常量
# =======================
DEVICE_PORT_BASE = 8200        # 设备端口基值
MAX_DEVICES = 10               # 最大设备数量

# =======================
# 异常相关常量
# =======================
EXCEPTION_CODE_BASE = "E3001"               # 基础异常代码
ELEMENT_NOT_FOUND_CODE = "E1001"            # 元素未找到异常代码
ELEMENT_NOT_CLICKABLE_CODE = "E1003"       # 元素不可点击异常代码
ELEMENT_INPUT_FAILED_CODE = "E1004"        # 元素输入失败异常代码
PAGE_SWITCH_FAILED_CODE = "E2001"          # 页面切换失败异常代码
DRIVER_INIT_FAILED_CODE = "E3001"           # Driver初始化失败异常代码
DEVICE_OPERATION_FAILED_CODE = "E3002"      # 设备操作失败异常代码

class MYG:
    ROUTER_NAME = None
    PHONE_NAME = None
    PHONE_NEW_NAME = None

    def __init__(self):
        try:
            data = read_yaml(FILE_PATH['user_config'])
            self.ROUTER_NAME = data['router_name']
            self.PHONE_NAME = data['phone_name']
            self.PHONE_NEW_NAME = data['phone_new_name']  # 修正这里：使用 phone_new_name
        except Exception as e:
            # 添加异常处理，防止配置文件读取失败导致程序崩溃
            log.warning(f"警告: 加载 user_config.yaml 失败 - {e}")
            log.warning("将使用默认配置")
            self.ROUTER_NAME = "默认路由器"
            self.PHONE_NAME = "默认手机"
            self.PHONE_NEW_NAME = "默认手机新名称"

# 创建单例实例
MYG = MYG()