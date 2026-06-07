from utils.tools.run_cmd import safe_cmd


def get_platformVersion():
    cmd = 'adb shell getprop ro.build.version.release'
    return safe_cmd(cmd)

def get_sn():
    cmd = 'adb get-serialno'
    return safe_cmd(cmd)


if __name__ == '__main__':
    print(get_sn())