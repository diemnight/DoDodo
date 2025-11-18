from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Iterable, Optional
from enum import Enum
import genesis as gs
import xml.etree.ElementTree as ET

class FileFormatAndPaths():
    """
    This class solves all problems that usually appear when different people work
    on the same robotics project on different computers. Instead of hard-coding
    paths or joint names, FileFormatAndPaths automatically:

    1. finds the project root, no matter where the code is located,
    2. locates all important folders (urdf/, dodo_robot/, etc.),
    3. selects the correct robot file (URDF or XML),
    4. reads the robot file and extracts all joint names directly from it.

    As a result, everyone can run the project without manually adjusting paths or
    editing joint name lists. The class guarantees that the setup works everywhere
    and stays consistent even if file structures change.
    """
    class ChooseFileFormat(str, Enum):
        XML = 'xml'
        URDF = 'urdf'

    _DEFAULT_ROOT_MARKERS = {"dodo_train.py", ".git", "pyproject.toml", "setup.cfg", "requirements.txt"}
    _EXCLUDE_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__"}

    def __init__(self, robot_file_format: ChooseFileFormat):
        # public members
        self.robot_file_format: str = str(robot_file_format.value)
        self.relevant_paths_dict: Dict[str, Path] = self._get_paths()
        self.robot_file_path: Path = None
        self.joint_names: list[str] = self._extract_joint_names()

        # protected members
        

    def _find_project_root(self) -> Path:
        """
        Get the project root folder by walking from this file tile a root marker is found (a file that is always in the project root)
        """

        start: Optional[Path] = None
        markers: Iterable[str] = self._DEFAULT_ROOT_MARKERS    

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


    def _find_dir(self, root: Path, name: str) -> Path:
        """
        Search the subfolder `name` inside of `root`.
        exclude unneccessary folder and choose the one with the shortest relevant path.
        """
        candidates = []
        for p in root.rglob(name):
            if not p.is_dir():
                continue
            
            parts = set(p.parts)
            if parts & self._EXCLUDE_DIRS:
                continue
            candidates.append(p.resolve())

        if not candidates:
            raise FileNotFoundError(f"Folder '{name}' not found under '{root}'.")
        
        candidates.sort(key=lambda p: len(p.relative_to(root).parts))
        return candidates[0]


    def _get_paths(self) -> Dict[str, Path]:
        """
        Returns a Dict containing relevant paths, OS-independent:
        - 'project_root': project root
        - 'cwd': current working directory
        - per forldername -> absolute Path
        Throw FileNotFoundError, if required_dirs is missing.
        """

        required_dirs: Iterable[str] = ("dodo_robot", "dodobot_v3", "urdf")
        extra_dirs: Iterable[str] = ()

        project_root = self._find_project_root()
        result: Dict[str, Path] = {
            "project_root": project_root,
            "cwd": Path.cwd().resolve(),
        }

        # Required: must exist
        for name in required_dirs:
            result[name] = self._find_dir(project_root, name)

        # Optional: only add if they are found
        for name in extra_dirs:
            try:
                result[name] = self._find_dir(project_root, name)
            except FileNotFoundError:
                pass

        return result
    
    def _extract_joint_names(self):
        if self.robot_file_format == str(self.ChooseFileFormat.XML.value):
            self.robot_file_path = Path.joinpath(self.relevant_paths_dict["dodo_robot"], "dodo.xml")
            return self._extract_joints_from_xml()
        elif self.robot_file_format == str(self.ChooseFileFormat.URDF.value):
            self.robot_file_path = Path.joinpath(self.relevant_paths_dict["urdf"], "dodobot_v3.urdf")
            return self._extract_joints_from_urdf()
        else:
            print("ERROR while trying to extract joint names in <FileFormatAndPaths._extract_joint_names>")
            return None

        
    def _extract_joints_from_urdf(self) -> list[str]:
        path: Path = self.robot_file_path
        tree = ET.parse(path)
        root = tree.getroot()
        joint_names = []
        for joint in root.findall(".//joint"):
            name = joint.get("name")
            if name:
                joint_names.append(name)
        return joint_names
    
    def _extract_joints_from_xml(self) -> list[str]:
        path: Path = self.robot_file_path
        tree = ET.parse(path)
        root = tree.getroot()
        joint_names = []
        for joint in root.findall(".//joint"):
            name = joint.get("name")
            if name:
                joint_names.append(name)
        if joint_names.__contains__("root"): joint_names.remove("root")
        return joint_names



# testcase = FileFormatAndPaths(robot_file_format=FileFormatAndPaths.ChooseFileFormat.XML)

# print("dict: ", testcase.relevant_paths_dict)
# print("file format: ", testcase.robot_file_format)
# print("joint names: ", testcase.joint_names)
# print("robot file path: ", testcase.robot_file_path)


"""
Example return:
paths 0 = {
    'project_root': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo'), 
    'cwd': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo'), 
    'dodo_robot': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodo_robot'), 
    'dodobot_v3': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodobot_v3'), 
    'urdf': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodobot_v3/urdf')
"""