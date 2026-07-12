import fnmatch
import os


def load_gitignore_patterns(gitignore_path=".gitignore"):
    """读取 .gitignore 并返回忽略模式列表"""
    patterns = set()
    if not os.path.exists(gitignore_path):
        return patterns

    with open(gitignore_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            # 去掉行尾注释
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            patterns.add(line)
    return patterns


def is_ignored(path, name, patterns, root):
    """判断是否应被忽略（兼容 .gitignore 规则）"""
    # 1. 直接匹配文件名
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True

    # 2. 匹配相对路径（如 logs/、config/*.yaml）
    rel_path = os.path.relpath(path, root).replace(os.sep, "/")
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True

        # 目录模式（如 logs/）
        if pattern.endswith("/") and rel_path.startswith(pattern.rstrip("/")):
            return True

    return False


def print_tree(root, prefix="", gitignore_patterns=None):
    if gitignore_patterns is None:
        gitignore_patterns = set()

    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        return

    # 过滤忽略项
    entries = [
        e for e in entries
        if not is_ignored(os.path.join(root, e), e, gitignore_patterns, ".")
    ]

    for idx, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(prefix + connector + name)

        if os.path.isdir(path):
            extension = "    " if idx == len(entries) - 1 else "│   "
            print_tree(path, prefix + extension, gitignore_patterns)


if __name__ == "__main__":
    gitignore_patterns = load_gitignore_patterns()
    print(".")
    print_tree(".", gitignore_patterns=gitignore_patterns)