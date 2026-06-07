import subprocess


def safe_cmd(cmd, timeout=30):
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    try:
        out, err = proc.communicate(timeout=timeout)
        text = out.decode("gbk", errors="replace")
        return text
    except subprocess.TimeoutExpired:
        proc.kill()
        return -1, "timeout"
