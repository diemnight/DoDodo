from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, Optional
from enum import Enum
#import genesis as gs
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
        self.relevant_paths_dict: dict[str, Path] = self._get_paths()
        self.robot_file_path: Path = None
        self.joint_names: list[str] = self._extract_joint_names()
        self.foot_link_names: list[str] = self._get_foot_link_names()
        self.robot_file_path_relative: Path = self._get_relative_robot_file_path()

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


    def _get_paths(self) -> dict[str, Path]:
        """
        Returns a Dict containing relevant paths, OS-independent:
        - 'project_root': project root
        - 'cwd': current working directory
        - per forldername -> absolute Path
        Throw FileNotFoundError, if required_dirs is missing.
        
        Example return:
        paths 0 = {
            'project_root': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo'), 
            'cwd': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo'), 
            'dodo_robot': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodo_robot'), 
            'dodobot_v3': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodobot_v3'), 
            'urdf': WindowsPath('C:/Users/Liamb/SynologyDrive/TUM/3_Semester/dodo_alive/DoDodo/dodobot_v3/urdf')
        """

        required_dirs: Iterable[str] = ("dodo_robot", "dodobot_v3", "urdf")
        extra_dirs: Iterable[str] = ()

        project_root = self._find_project_root()
        result: dict[str, Path] = {
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
    
    """
    # these 3 fuctions return the list of joint names but not in the order that was hardcoded.
    #This should be no problem but to keep it consistent the new versions were implemented below this block

    # def _extract_joint_names(self):
    #     if self.robot_file_format == str(self.ChooseFileFormat.XML.value):
    #         self.robot_file_path = Path.joinpath(self.relevant_paths_dict["dodo_robot"], "dodo.xml")
    #         return self._extract_joints_from_xml()
    #     elif self.robot_file_format == str(self.ChooseFileFormat.URDF.value):
    #         self.robot_file_path = Path.joinpath(self.relevant_paths_dict["urdf"], "dodobot_v3.urdf")
    #         return self._extract_joints_from_urdf()
    #     else:
    #         print("ERROR while trying to extract joint names in <FileFormatAndPaths._extract_joint_names>")
    #         return None

        
    # def _extract_joints_from_urdf(self) -> list[str]:
    #     path: Path = self.robot_file_path
    #     tree = ET.parse(path)
    #     root = tree.getroot()
    #     joint_names = []
    #     for joint in root.findall(".//joint"):
    #         name = joint.get("name")
    #         if name:
    #             joint_names.append(name)
    #     return joint_names
    
    # def _extract_joints_from_xml(self) -> list[str]:
    #     path: Path = self.robot_file_path
    #     tree = ET.parse(path)
    #     root = tree.getroot()
    #     joint_names = []
    #     for joint in root.findall(".//joint"):
    #         name = joint.get("name")
    #         if name:
    #             joint_names.append(name)
    #     if joint_names.__contains__("root"): joint_names.remove("root")
    #     return joint_names

    """
    def _extract_joint_names(self) -> list[str]:
        if self.robot_file_format == str(self.ChooseFileFormat.XML.value):
            self.robot_file_path = Path.joinpath(self.relevant_paths_dict["dodo_robot"], "dodo.xml")
            return self._extract_joints_from_xml()
        elif self.robot_file_format == str(self.ChooseFileFormat.URDF.value):
            self.robot_file_path = Path.joinpath(self.relevant_paths_dict["urdf"], "dodobot_v3.urdf")
            return self._extract_joints_from_urdf()
        else:
            print("ERROR while trying to extract joint names in <FileFormatAndPaths._extract_joint_names>")
            return []
        
    def _extract_joints_from_urdf(self) -> list[str]:
        """Read all the joint_names from URDF and sort them according to the hardcoded version:
        ['left_joint_1','right_joint_1', ..., 'left_joint_4','right_joint_4'].
        """
        path: Path = self.robot_file_path
        tree = ET.parse(path)
        root = tree.getroot()

        raw_names: list[str] = []
        for joint in root.findall(".//joint"):
            name = joint.get("name")
            if name:
                raw_names.append(name)

        # Links / Rechts trennen und numerisch sortieren
        left = []
        right = []

        for name in raw_names:
            if name.startswith("left_joint_"):
                left.append(name)
            elif name.startswith("right_joint_"):
                right.append(name)

        # Nach der Ziffer sortieren, falls sie nicht schon 1..4 sind
        def joint_sort_key(n: str) -> int:
            # erwartet z.B. 'left_joint_3' -> 3
            try:
                return int(n.split("_")[-1])
            except ValueError:
                return 0  # Fallback, falls was komisches drin steht

        left.sort(key=joint_sort_key)
        right.sort(key=joint_sort_key)

        # Interleaved Reihenfolge wie früher: left1, right1, left2, right2, ...
        joint_names: list[str] = []
        for l, r in zip(left, right):
            joint_names.append(l)
            joint_names.append(r)

        # Falls aus irgendeinem Grund ungleiche Anzahl vorliegt, Rest anhängen
        if len(left) > len(right):
            joint_names.extend(left[len(right):])
        elif len(right) > len(left):
            joint_names.extend(right[len(left):])

        return joint_names


    def _extract_joints_from_xml(self) -> list[str]:
        """Read all the joint_names from XML/MJCF and sort them according to the hardcoded version:
        ['Left_HIP_AA','Right_HIP_AA', 'Left_THIGH_FE','Right_THIGH_FE', ...].
        """
        path: Path = self.robot_file_path
        tree = ET.parse(path)
        root = tree.getroot()

        raw_names: list[str] = []
        for joint in root.findall(".//joint"):
            name = joint.get("name")
            if name:
                raw_names.append(name)

        # 'root' ggf. rauswerfen
        raw_names = [n for n in raw_names if n != "root"]

        # Links / Rechts trennen, Reihenfolge innerhalb jeder Seite aus dem File übernehmen
        left = [n for n in raw_names if n.startswith("Left_")]
        right = [n for n in raw_names if n.startswith("Right_")]

        # Interleaved: Left_X, Right_X, Left_Y, Right_Y, ...
        joint_names: list[str] = []
        for l, r in zip(left, right):
            joint_names.append(l)
            joint_names.append(r)

        # Falls Dateien nicht perfekt symmetrisch sind, Rest anhängen
        if len(left) > len(right):
            joint_names.extend(left[len(right):])
        elif len(right) > len(left):
            joint_names.extend(right[len(left):])

        return joint_names
    

    def _get_foot_link_names(self):
        """
        Extract foot link names from the robot description file.

        XML/MJCF:
            - search all <body name="..."> and pick those that look like feet,
              e.g. contain 'FOOT' (Left_FOOT_FE, Right_FOOT_FE).
            - result is ordered left, then right if possible.

        URDF:
            - treat "feet" as end links of the kinematic chain:
              links that appear as <child link="..."> of some joint,
              but never as <parent link="...">.
            - result is ordered left, then right if possible.
        """
        if self.robot_file_path is None:
            raise RuntimeError("robot_file_path is not set before calling _get_foot_link_names().")

        path: Path = self.robot_file_path
        tree = ET.parse(path)
        root = tree.getroot()

        # --- XML / MJCF -----------------------------------------------------
        if self.robot_file_format == str(self.ChooseFileFormat.XML.value):
            # collect all bodies
            foot_candidates: list[str] = []
            for body in root.findall(".//body"):
                name = body.get("name")
                if not name:
                    continue
                # Heuristik: everythink that looks like a foot
                if "FOOT" in name or "foot" in name.lower():
                    foot_candidates.append(name)

            if not foot_candidates:
                raise RuntimeError(
                    f"No foot bodies found in XML/MJCF at {path}. "
                    "Make sure foot bodies contain 'FOOT' in their name."
                )

            # sort Left/right if possible
            left = [n for n in foot_candidates if "Left" in n or "left" in n]
            right = [n for n in foot_candidates if "Right" in n or "right" in n]

            if left or right:
                foot_link_names = left + right
            else:
                # Fallback: simple order from file
                foot_link_names = foot_candidates

            self.foot_link_names = foot_link_names
            return foot_link_names

        # --- URDF -----------------------------------------------------------
        elif self.robot_file_format == str(self.ChooseFileFormat.URDF.value):
            # Get all link names
            all_links: set[str] = set()
            for link in root.findall(".//link"):
                name = link.get("name")
                if name:
                    all_links.add(name)

            parent_links: set[str] = set()
            child_links: set[str] = set()

            for joint in root.findall(".//joint"):
                parent = joint.find("parent")
                child = joint.find("child")
                if parent is not None and parent.get("link"):
                    parent_links.add(parent.get("link"))
                if child is not None and child.get("link"):
                    child_links.add(child.get("link"))

            # End-Links: occur as childs but never as parents
            leaf_links = sorted(child_links - parent_links)

            if not leaf_links:
                raise RuntimeError(
                    f"No leaf links (end-effectors) found in URDF at {path}."
                )

            # Fordodobot: will probably be left_link_4 and right_link_4.
            left = [n for n in leaf_links if "left" in n.lower()]
            right = [n for n in leaf_links if "right" in n.lower()]

            if left or right:
                foot_link_names = left + right
            else:
                # Fallback: take all leaf-links as "feet"
                foot_link_names = leaf_links

            self.foot_link_names = foot_link_names
            return foot_link_names

        else:
            raise ValueError(
                f"Unknown robot_file_format '{self.robot_file_format}' in _get_foot_link_names()."
            )


    def set_default_joint_angles_dict(self, default_angles: list[float]):
        """
        Create dict for default joint angles. The order of the angles in the list is defined as:
        [
            "left hip",
            "right hip",
            "left thigh",
            "right thigh",
            "left knee",
            "right shin",
            "left foot ankle",
            "right foot ankle"
        ]
        """
        assert len(default_angles) == len(self.joint_names)

        joint_angles: dict[str, float]  = {} 
        for i, jnt_name in enumerate(self.joint_names):
            joint_angles[jnt_name] = float(default_angles[i])

        self.default_joint_angles = joint_angles
                               
        return joint_angles
    

    def _get_relative_robot_file_path(self) -> Path:
        """
        Return the relative robot file path
        """
        return self.robot_file_path.relative_to(
            self.relevant_paths_dict["project_root"]
        )
    

        
        


# testcase = FileFormatAndPaths(robot_file_format=FileFormatAndPaths.ChooseFileFormat.XML)
# jnt_angles = testcase.set_default_joint_angles_dict(default_angles=[0.0, 0.0, 0.6, 0.6, 1.1, 1.1, 0.0, 0.0])

# # print("dict: ", testcase.relevant_paths_dict)
# # print("file format: ", testcase.robot_file_format)
# print("robot file format: ", testcase.robot_file_format)
# print("joint names: ", testcase.joint_names)
# print("default joint angle 2: ", testcase.default_joint_angles)

# print("foot link names: ", testcase.foot_link_names)
# print("robot file path relative: ", testcase.robot_file_path_relative)


