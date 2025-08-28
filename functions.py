import ctypes
import os

# Load the DLL
lib_path = os.path.abspath("libnrc_host.dll")
nrc_lib = ctypes.CDLL(lib_path)

# --- connect_robot ---
nrc_lib.connect_robot.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
nrc_lib.connect_robot.restype = ctypes.c_int

def connect_robot(ip: str, port: str, robot_name: str) -> int:
    return nrc_lib.connect_robot(ip.encode("utf-8"),
                                 port.encode("utf-8"),
                                 robot_name.encode("utf-8"))

# --- disconnect_robot ---
nrc_lib.disconnect_robot.argtypes = [ctypes.c_char_p]
nrc_lib.disconnect_robot.restype = ctypes.c_int

def disconnect_robot(robot_name: str) -> int:
    return nrc_lib.disconnect_robot(robot_name.encode("utf-8"))

# --- set_servo_state ---
nrc_lib.set_servo_state.argtypes = [ctypes.c_int, ctypes.c_char_p]
nrc_lib.set_servo_state.restype = ctypes.c_int

def set_servo_state(state: int, robot_name: str) -> int:
    """
    state = 1 -> ON, 0 -> OFF
    """
    return nrc_lib.set_servo_state(state, robot_name.encode("utf-8"))

# --- set_servo_poweron ---
nrc_lib.set_servo_poweron.argtypes = [ctypes.c_char_p]
nrc_lib.set_servo_poweron.restype = ctypes.c_int

def set_servo_poweron(robot_name: str) -> int:
    return nrc_lib.set_servo_poweron(robot_name.encode("utf-8"))

# --- set_servo_poweroff ---
nrc_lib.set_servo_poweroff.argtypes = [ctypes.c_char_p]
nrc_lib.set_servo_poweroff.restype = ctypes.c_int

def set_servo_poweroff(robot_name: str) -> int:
    return nrc_lib.set_servo_poweroff(robot_name.encode("utf-8"))

# -------------------------
# get_current_position
# -------------------------
nrc_lib.get_current_position.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_char_p]
nrc_lib.get_current_position.restype = ctypes.c_int

def get_current_position(robot_name: str, coord: int = 0):
    """
    Returns the current robot position as a list of 7 floats
    coord: 0 = joint, 1 = Cartesian (based on your robot)
    """
    arr = (ctypes.c_double * 7)()
    status = nrc_lib.get_current_position(arr, coord, robot_name.encode("utf-8"))
    if status != 0:
        raise Exception(f"get_current_position failed with code {status}")
    return list(arr)

# -------------------------
# robot_movej
# -------------------------
nrc_lib.robot_movej.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
nrc_lib.robot_movej.restype = ctypes.c_int

def robot_movej(pos: list, vel: int, coord: int, acc: int, dec: int, robot_name: str) -> int:
    """
    Move robot to target position
    pos: list of 7 floats
    vel, acc, dec: motion parameters
    coord: 0 = joint, 1 = Cartesian
    """
    if len(pos) != 7:
        raise ValueError("pos must be a list of 7 floats")
    arr = (ctypes.c_double * 7)(*pos)
    return nrc_lib.robot_movej(arr, vel, coord, acc, dec, robot_name.encode("utf-8"))

# -------------------------
# Move single joint relative
# -------------------------
def move_joint_relative(joint_index: int, delta: float, vel: int, acc: int, dec: int, robot_name: str):
    """
    Move a single joint relative to its current position using DLL calls.
    joint_index: 0-based index (0=J1, 1=J2, ...)
    delta: amount to move (+/- degrees)
    vel, acc, dec: motion parameters
    """
    # 1. Get current positions from DLL
    pos = get_current_position(robot_name, coord=0)
    
    # 2. Modify only the selected joint
    if not (0 <= joint_index < len(pos)):
        raise ValueError("Invalid joint index")
    pos[joint_index] += delta

    # 3. Send full array back to DLL
    status = robot_movej(pos, vel, coord=0, acc=acc, dec=dec, robot_name=robot_name)
    if status != 0:
        raise Exception(f"robot_movej failed with code {status}")
    return status

# -------------------------
# robot_movel
# -------------------------
nrc_lib.robot_movel.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
nrc_lib.robot_movel.restype = ctypes.c_int

def robot_movel(pos: list, vel: int, coord: int, acc: int, dec: int, robot_name: str) -> int:
    """
    Move robot linearly to a target position.
    pos: list of 7 floats (only first 3 used for Cartesian movement)
    vel, acc, dec: motion parameters
    coord: 0=joint, 1=Cartesian
    """
    if len(pos) != 7:
        raise ValueError("pos must be a list of 7 floats")
    arr = (ctypes.c_double * 7)(*pos)
    return nrc_lib.robot_movel(arr, vel, coord, acc, dec, robot_name.encode("utf-8"))


# -------------------------
# Linear jog function
# -------------------------
def linear_jog(axis_index: int, delta: float, vel: int, acc: int, dec: int, robot_name: str):
    """
    Incrementally move the robot linearly along one Cartesian axis.
    axis_index: 0=X, 1=Y, 2=Z
    delta: amount to move (+/- in mm)
    vel, acc, dec: motion parameters
    """
    if not (0 <= axis_index <= 2):
        raise ValueError("Invalid axis index, must be 0=X,1=Y,2=Z")

    # 1. Get current position in Cartesian coordinates
    pos = get_current_position(robot_name, coord=1)  # coord=1 for Cartesian

    # 2. Increment only the selected axis
    pos[axis_index] += delta

    # 3. Move linearly
    status = robot_movel(pos, vel=vel, coord=1, acc=acc, dec=dec, robot_name=robot_name)
    if status != 0:
        raise Exception(f"robot_movel failed with code {status}")
    return status

#-------------------------
# clear_error
#-------------------------
# --- clear_error ---
nrc_lib.clear_error.argtypes = [ctypes.c_char_p]
nrc_lib.clear_error.restype = ctypes.c_int

def clear_error(robot_name: str) -> int:
    """
    Clear any active robot errors.
    Returns 0 on success, non-zero error code on failure.
    """
    return nrc_lib.clear_error(robot_name.encode("utf-8"))


# -------------------------
# get_robot_running_state
# -------------------------
nrc_lib.get_robot_running_state.argtypes = [ctypes.c_char_p]
nrc_lib.get_robot_running_state.restype = ctypes.c_int

def get_robot_running_state(robot_name: str) -> int:
    """
    Get the running state of the robot.
    Returns an integer status code.
    """
    return nrc_lib.get_robot_running_state(robot_name.encode("utf-8"))