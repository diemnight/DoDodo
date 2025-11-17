from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Iterable, Optional

DEFAULT_ROOT_MARKERS = {"dodo_train.py", ".git", "pyproject.toml", "setup.cfg", "requirements.txt"}

EXCLUDE_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__"}

def find_project_root(
    start: Optional[Path] = None,
    markers: Iterable[str] = DEFAULT_ROOT_MARKERS,
) -> Path:
    """
    Get the project root folder by walking from this file tile a root marker is found (a file that is always in the project root)
    """
    env_root = os.environ.get("DODO_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()

    if start is None:
        # Use the file location as start, fallback is cwd
        start = Path(__file__).resolve() if "__file__" in globals() else Path.cwd().resolve()

    cur = start if start.is_dir() else start.parent
    while True:
        if any((cur / m).exists() for m in markers):
            return cur.resolve()
        if cur.parent == cur:
            # system root reached
            return Path.cwd().resolve()
        cur = cur.parent


def find_dir(root: Path, name: str) -> Path:
    """
    Search the subfolder `name` inside of `root`.
    exclude unneccessary folder and choose the one with the shortest relevant path.
    """
    candidates = []
    for p in root.rglob(name):
        if not p.is_dir():
            continue
        
        parts = set(p.parts)
        if parts & EXCLUDE_DIRS:
            continue
        candidates.append(p.resolve())

    if not candidates:
        raise FileNotFoundError(f"Folder '{name}' not found under '{root}'.")
    
    candidates.sort(key=lambda p: len(p.relative_to(root).parts))
    return candidates[0]


def get_paths(
    required_dirs: Iterable[str] = ("dodo_robot", "dodobot_v3", "urdf"),
    extra_dirs: Iterable[str] = (),
) -> Dict[str, Path]:
    """
    Returns a Dict containing relevant paths, OS-independent:
    - 'project_root': project root
    - 'cwd': current working directory
    - per forldername -> absolute Path
    Throw FileNotFoundError, if required_dirs is missing.
    """
    project_root = find_project_root()
    result: Dict[str, Path] = {
        "project_root": project_root,
        "cwd": Path.cwd().resolve(),
    }

    # Required: must exist
    for name in required_dirs:
        result[name] = find_dir(project_root, name)

    # Optional: only add if they are found
    for name in extra_dirs:
        try:
            result[name] = find_dir(project_root, name)
        except FileNotFoundError:
            pass

    return result


# if __name__ == "__main__":
#     paths = get_paths()
#     print("relevant paths:")
#     for k, v in paths.items():
#         print(f"  {k}: {v}")

# if __name__ == "__main__":
#     paths = get_paths()
#     print(paths)


"""
Example return:
paths 0 = {
    'project_root': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo'), 
    'cwd': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo'), 
    'dodo_robot': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodo_robot'), 
    'dodobot_v3': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodobot_v3'), 
    'urdf': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodobot_v3/urdf')
    }
"""