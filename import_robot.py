########################## dodo robot ##########################
import numpy as np
import genesis as gs
from dodo_env import DodoEnv
import os_workarounds
import os

gs.init(backend=gs.gpu)

paths = os_workarounds.get_paths()
manual_stepping = False
robot_file: str = "urdf" #TODO: write 'urdf' or 'xml' whatever you want to do
jnt_names = None

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos    = (0, -2.0, 1.0),
        camera_lookat = (0.0,  0.0, 0.5),
        camera_fov    = 40,
        max_FPS       = 60,
    ),
    sim_options=gs.options.SimOptions(
        dt       = 0.01,   # 100 Hz
        substeps = 2,
    ),
    show_viewer=True,
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

if robot_file == "urdf":
    dodo = scene.add_entity(
    gs.morphs.URDF(      
        file  = str(os.path.join(paths['urdf'], "dodobot_v3.urdf")),
        fixed = False,
        pos   = (0, 0, 0.5),
        euler = (0, 0, 0),
        )
    )
    jnt_names = ["left_joint_1","right_joint_1","left_joint_2","right_joint_2", "left_joint_3","right_joint_3","left_joint_4","right_joint_4"]

elif robot_file == "xml":
    dodo = scene.add_entity(
        gs.morphs.MJCF(
            file  = str(os.path.join(paths['dodo_robot'], "dodo.xml")),
            pos   = (0, 0, 0.5),
            euler = (0, 0, 0),
        )
    )
    jnt_names = ["Left_HIP_AA","Right_HIP_AA","Left_THIGH_FE","Right_THIGH_FE", "Left_KNEE_FE","Right_SHIN_FE","Left_FOOT_ANKLE","Right_FOOT_ANKLE"]

else:
    print("Neither 'URDF' nor 'XML' file was loaded. Therefore No robot is loaded into the simulation")


scene.build(n_envs=1)

dofs_idx  = [dodo.get_joint(name).dof_idx_local for name in jnt_names]

n_dofs    = len(dofs_idx)
q_amp  = 0.5
freq   = 2
omega  = 2 * np.pi * freq
kp     = 200.0  * np.ones(n_dofs, dtype=np.float32)
kv     = 2.0*np.sqrt(kp) 
dodo.set_dofs_kp(kp, dofs_idx)
dodo.set_dofs_kv(kv, dofs_idx)

dodo.set_dofs_force_range(
    lower = -100*np.ones(n_dofs, dtype=np.float32),
    upper =  100*np.ones(n_dofs, dtype=np.float32),
    dofs_idx_local = dofs_idx,
)

total_steps = 2000
dt = scene.sim_options.dt

try:
    for step in range(total_steps):
        t = step * dt
        q_des = q_amp * np.sin(omega * t) * np.ones(n_dofs, dtype=np.float32)
        dodo.control_dofs_position(q_des, dofs_idx)
        if manual_stepping:
            input("enter to continue…")   # keep this to step manually
        base_pos = dodo.get_pos()
        if manual_stepping:
            print(f"[pos ctrl] step {step:4d} → base height = {base_pos[0,2]:.4f} m")
        scene.step()
except gs.GenesisException as e:
    if "Viewer closed" in str(e):
        print("Viewer closed – simulation finished.")
    else:
        raise

# for step in range(total_steps):
#     t = step * dt
#     q_des = q_amp * np.sin(omega * t) * np.ones(n_dofs, dtype=np.float32)
#     dodo.control_dofs_position(q_des, dofs_idx)
#     input("enter to continue…")
#     base_pos = dodo.get_pos()
#     print(f"[torque ctrl] step {step:4d} → base height = {base_pos[0,2]:.4f} m")
#     scene.step()

# torque_amp = 5.0 

# for step in range(total_steps):
#     t = step * dt
#     torque = torque_amp * np.sin(omega * t) * np.ones(n_dofs, dtype=np.float32)
#     dodo.control_dofs_force(torque, dofs_idx)
#     scene.step()
