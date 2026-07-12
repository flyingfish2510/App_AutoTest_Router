import os
import shutil


def clean_pycache(root):
    """清理 __pycache__ 和 .pyc"""
    for root_dir, dirs, files in os.walk(root, topdown=False):
        # 删除 __pycache__ 目录
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root_dir, '__pycache__')
            print(f"🗑️ 删除: {pycache_path}")
            shutil.rmtree(pycache_path, ignore_errors=True)

        # 删除 .pyc 文件
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root_dir, file)
                print(f"🗑️ 删除: {pyc_path}")
                try:
                    os.remove(pyc_path)
                except:
                    pass


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"🧹 开始清理缓存: {project_root}")
    clean_pycache(project_root)
    print("✅ 清理完成")