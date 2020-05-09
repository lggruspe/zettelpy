import os.path as op

def is_in_subdir(path: str) -> bool:
    curdir = op.abspath(op.curdir)
    paths = [op.abspath(path), curdir]
    return op.commonpath(paths) == curdir

def fix_path(path: str, src: str) -> str or None:
    target = op.relpath(op.join(op.dirname(src), path), op.curdir)
    if op.exists(target) and is_in_subdir(target):
        return target
    if op.exists(path) and is_in_subdir(path):
        return path
    return None
