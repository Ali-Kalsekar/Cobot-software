import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtWidgets
from ui_main import Ui_MainWindow
import functions #Ctypes functions

# Global variables
ROBOT_NAME = "MyRobot"
ROBOT_IP = "192.168.3.15"
ROBOT_PORT = "6001"
wspeed = 30  # default speed

# For Action Tab
current_step_index = 0
program_running = False

#ICONS
on_path = "E:/Ajaxx/Projects/cobot/Icons/on.svg"
off_path = "E:/Ajaxx/Projects/cobot/Icons/off.svg"
lock_path = "E:/Ajaxx/Projects/cobot/Icons/Lock.svg"
unlock_path = "E:/Ajaxx/Projects/cobot/Icons/unlock.svg"
# Class to redirect print statements to QPlainTextEdit
class EmittingStream:
    def __init__(self, text_edit):
        self.text_edit = text_edit  # QPlainTextEdit object

    def write(self, text):
        if text.strip() != "":
            self.text_edit.appendPlainText(text.strip())
            # Scroll to the bottom automatically
            self.text_edit.verticalScrollBar().setValue(
                self.text_edit.verticalScrollBar().maximum()
            )

    def flush(self):
        pass  # Needed for compatibility with sys.stdout

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        
        # Redirect stdout to the terminal QPlainTextEdit
        sys.stdout = EmittingStream(self.ui.terminal)
        sys.stderr = EmittingStream(self.ui.terminal)  # optional: capture errors too

        #============/Button Mappings\============#
        # Save config button
        self.ui.config_btn.clicked.connect(self.save_config) 

        #Connect/Disconnect button
        self.connected = False  # Connection state
        self.ui.on_off.setIcon(QIcon("E:/Ajaxx/Projects/cobot/Icons/onOff.svg"))  # initial blue
        self.ui.on_off.clicked.connect(self.toggle_connection) # Connect/Disconnect button

        #Lock/Unlock button
        self.ui.lock.setIcon(QIcon(lock_path))  # initial red
        self.servo_locked = True # Lock state
        self.ui.lock.setEnabled(False)  # no lock control until connected
        self.ui.lock.clicked.connect(self.toggle_servo_lock) # Connect/Disconnect button

        # Emergency Stop button
        self.ui.stop.clicked.connect(self.on_estop_click)

        # Speed Control
        self.ui.current_speed.setText(str(wspeed))
        self.ui.speed_slider.setValue(wspeed)
        self.ui.speed_slider.setMinimum(0)
        self.ui.speed_slider.setMaximum(100)

            #----Connect slider change
        self.ui.speed_slider.valueChanged.connect(self.slider_changed)

            #----Connect buttons
        self.ui.s_m1.clicked.connect(lambda: self.change_speed(-1))
        self.ui.s_m5.clicked.connect(lambda: self.change_speed(-5))
        self.ui.s_m15.clicked.connect(lambda: self.change_speed(-15))
        self.ui.s_m25.clicked.connect(lambda: self.change_speed(-25))

        self.ui.s_p1.clicked.connect(lambda: self.change_speed(1))
        self.ui.s_p5.clicked.connect(lambda: self.change_speed(5))
        self.ui.s_p15.clicked.connect(lambda: self.change_speed(15))
        self.ui.s_p25.clicked.connect(lambda: self.change_speed(25))

        # Control Buttons
            # --------------------
            # Joint Jog Buttons
            # --------------------
        self.ui.j1_p_btn.clicked.connect(lambda: self.jog_joint(0, +1))
        self.ui.j1_n_btn.clicked.connect(lambda: self.jog_joint(0, -1))

        self.ui.j2_p_btn.clicked.connect(lambda: self.jog_joint(1, +1))
        self.ui.j2_n_btn.clicked.connect(lambda: self.jog_joint(1, -1))

        self.ui.j3_p_btn.clicked.connect(lambda: self.jog_joint(2, +1))
        self.ui.j3_n_btn.clicked.connect(lambda: self.jog_joint(2, -1))

        # self.ui.joint4_pos.clicked.connect(lambda: self.jog_joint(3, +1))
        # self.ui.joint4_neg.clicked.connect(lambda: self.jog_joint(3, -1))

        # self.ui.joint5_pos.clicked.connect(lambda: self.jog_joint(4, +1))
        # self.ui.joint5_neg.clicked.connect(lambda: self.jog_joint(4, -1))

        # self.ui.joint6_pos.clicked.connect(lambda: self.jog_joint(5, +1))
        # self.ui.joint6_neg.clicked.connect(lambda: self.jog_joint(5, -1))

            # --------------------
            # Linear Jog Buttons
            # --------------------
        self.ui.x_pos.clicked.connect(lambda: self.jog_linear(0, +1))
        self.ui.x_neg.clicked.connect(lambda: self.jog_linear(0, -1))

        self.ui.y_pos.clicked.connect(lambda: self.jog_linear(1, +1))
        self.ui.y_neg.clicked.connect(lambda: self.jog_linear(1, -1))

        self.ui.z_pos.clicked.connect(lambda: self.jog_linear(2, +1))
        self.ui.z_neg.clicked.connect(lambda: self.jog_linear(2, -1))

        # self.ui.rx_pos.clicked.connect(lambda: self.jog_linear(3, +1))
        # self.ui.rx_neg.clicked.connect(lambda: self.jog_linear(3, -1))

        # self.ui.ry_pos.clicked.connect(lambda: self.jog_linear(4, +1))
        # self.ui.ry_neg.clicked.connect(lambda: self.jog_linear(4, -1))

        # self.ui.rz_pos.clicked.connect(lambda: self.jog_linear(5, +1))
        # self.ui.rz_neg.clicked.connect(lambda: self.jog_linear(5, -1))


        # Go Home button
        self.ui.home_btn.clicked.connect(lambda: self.go_home(use_library_home=False))


        # Clear Error button
        self.ui.clear_error_btn.clicked.connect(self.on_clear_error_click)

        #======|Actions Tab|======#
            # Button connections
        self.ui.save_btn.clicked.connect(self.save_step)
        self.ui.edit_btn.clicked.connect(self.edit_step)
        self.ui.insert_btn.clicked.connect(self.insert_step)
        self.ui.delete_btn.clicked.connect(self.delete_step)
        self.ui.run_btn.clicked.connect(self.run_program)

            # Timer for polling robot state
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.check_robot_state)

        

        # Initialize labels with defaults
        #self.ui.status_label.setText("Not Connected")

        print("Application started...")  # Test print

    #============/Functions\============#
    # --- Save Configuration Button ---
    def save_config(self):
        global ROBOT_NAME, ROBOT_IP, ROBOT_PORT

        # Replace only if the user entered something
        name = self.ui.robot_name.text().strip()
        ip   = self.ui.ip_address.text().strip()
        port = self.ui.port_no.text().strip()

        if name: ROBOT_NAME = name
        if ip:   ROBOT_IP   = ip
        if port: ROBOT_PORT = port

        print(f"Configuration Saved:")
        print(f"ROBOT_NAME = {ROBOT_NAME}")
        print(f"ROBOT_IP   = {ROBOT_IP}")
        print(f"ROBOT_PORT = {ROBOT_PORT}")
   
    # --- Connect/Disconnect Button ---
    def toggle_connection(self):
        if not self.connected:
            print("Connecting...")
            status = functions.connect_robot(ROBOT_IP, ROBOT_PORT, ROBOT_NAME)
            if status == 0:
                print("✅ Robot connected")
                self.connected = True
                self.ui.on_off.setIcon(QIcon(on_path))   # green
                # assume safe state after connect = locked (power OFF) until user unlocks
                self.servo_locked = True
                functions.set_servo_state(0, ROBOT_NAME)
                functions.set_servo_poweroff(ROBOT_NAME)
                self.ui.lock.setEnabled(True)
                self.ui.lock.setIcon(QIcon(lock_path))
            else:
                print("❌ Connect failed")
                self.connected = False
                self.ui.on_off.setIcon(QIcon(off_path))  # red
                self.servo_locked = True
                self.ui.lock.setEnabled(False)
                self.ui.lock.setIcon(QIcon(lock_path))
        else:
            # on disconnect, force lock (power OFF), then disconnect
            try:
                functions.set_servo_state(0, ROBOT_NAME)
                functions.set_servo_poweroff(ROBOT_NAME)
            except Exception as e:
                print(f"⚠️ Power-off during disconnect failed: {e}")

            functions.disconnect_robot(ROBOT_NAME)
            print("Robot disconnected")
            self.connected = False
            self.ui.on_off.setIcon(QIcon(off_path))      # red
            self.servo_locked = True
            self.ui.lock.setEnabled(False)
            self.ui.lock.setIcon(QIcon(lock_path))

    # --- Lock/Unlock Button ---
    def toggle_servo_lock(self):
        if not self.connected:
            print("⚠️ Cannot toggle lock: robot not connected.")
            return

        try:
            if self.servo_locked:
                # UNLOCK = allow motion
                functions.set_servo_state(1, ROBOT_NAME)
                functions.set_servo_poweron(ROBOT_NAME)
                print("🔓 Servo UNLOCKED (power ON)")
                self.servo_locked = False
                self.ui.lock.setIcon(QIcon(unlock_path))
            else:
                # LOCK = stop motion
                functions.set_servo_state(0, ROBOT_NAME)
                functions.set_servo_poweroff(ROBOT_NAME)
                print("🔒 Servo LOCKED (power OFF)")
                self.servo_locked = True
                self.ui.lock.setIcon(QIcon(lock_path
                ))
        except Exception as e:
            print(f"⚠️ Servo lock toggle failed: {e}")

    # --- Emergency Stop Button ---
    def on_estop_click(self):
        if not self.connected:
            print("Cannot use Emergency Stop: Not connected")
            return

        if not hasattr(self, "stop_engaged"):  # Initialize state if not set
            self.stop_engaged = False

        if not self.stop_engaged:
            # Engage stop: Lock servos
            functions.set_servo_state(0, ROBOT_NAME)
            functions.set_servo_poweroff(ROBOT_NAME)
            print("Emergency Stop ENGAGED: Servos Locked")

            # Add red border
            self.stop.setStyleSheet("border: 2px solid red;")
            self.stop_engaged = True
        else:
            # Release stop: Unlock servos
            functions.set_servo_poweron(ROBOT_NAME)
            functions.set_servo_state(1, ROBOT_NAME)
            print("Emergency Stop RELEASED: Servos Unlocked")

            # Remove border (reset style so global stylesheet applies again)
            self.stop.setStyleSheet("")
            self.stop_engaged = False

    # --- Speed Control ---
    def slider_changed(self, value):
        """Update wspeed when slider is moved"""
        global wspeed
        wspeed = value
        self.ui.current_speed.setText(str(wspeed))

    def change_speed(self, delta):
        """Increment/decrement wspeed from buttons"""
        global wspeed
        wspeed += delta
        # Clamp value between 0 and 100
        if wspeed < 0:
            wspeed = 0
        elif wspeed > 100:
            wspeed = 100
        # Update UI
        self.ui.current_speed.setText(str(wspeed))
        self.ui.speed_slider.setValue(wspeed)

    # --- Control Buttons ---
        # --- generic joint jog ---
    def jog_joint(self, joint_index: int, direction: int):
        """
        Jog a single joint by +/-10 units
        """
        try:
            status = functions.move_joint_relative(
                joint_index=joint_index,
                delta=10.0 * direction,
                vel=wspeed,        # use global speed
                acc=30,
                dec=30,
                robot_name=ROBOT_NAME
            )
            if status == 0:
                print(f"✅ Joint {joint_index+1} moved {10*direction}")
            else:
                print(f"❌ robot_movej failed with code {status}")
        except Exception as e:
            print(f"Error moving Joint {joint_index}:", e)
        
        # Update labels after jog
        self.update_robot_labels()

        # --- generic linear jog ---
    
    def jog_linear(self, axis_index: int, direction: int):
        """
        Jog linearly along X/Y/Z axis by +/-50 units
        """
        try:
            functions.linear_jog(
                axis_index=axis_index,
                delta=50.0 * direction,
                vel=wspeed * 5,   # linear jog is usually faster, scale it
                acc=30,
                dec=30,
                robot_name=ROBOT_NAME
            )
            axis_name = ["X", "Y", "Z"][axis_index]
            print(f"✅ {axis_name} {50*direction} units")
        except Exception as e:
            print(f"Error moving axis {axis_index}:", e)

        # Update labels after jog
        self.update_robot_labels()

    # --- Update Robot Position Labels ---
    def update_robot_labels(self):
            if not self.connected:
                return  # don’t try if robot isn’t connected

            try:
                # --- Joint positions ---
                joints = functions.get_current_position(ROBOT_NAME, coord=0)  # 0 = joint
                self.ui.label_num_j1.setText(f"{joints[0]:.2f}")
                self.ui.label_num_j2.setText(f"{joints[1]:.2f}")
                self.ui.label_num_j3.setText(f"{joints[2]:.2f}")
                self.ui.label_num_j4.setText(f"{joints[3]:.2f}")
                self.ui.label_num_j5.setText(f"{joints[4]:.2f}")
                self.ui.label_num_j6.setText(f"{joints[5]:.2f}")

                # --- Cartesian coords ---
                cart = functions.get_current_position(ROBOT_NAME, coord=1)  # 1 = Cartesian
                self.ui.label_num_x.setText(f"{cart[0]:.2f}")
                self.ui.label_num_y.setText(f"{cart[1]:.2f}")
                self.ui.label_num_z.setText(f"{cart[2]:.2f}")
                self.ui.label_num_rx.setText(f"{cart[3]:.2f}")
                self.ui.label_num_ry.setText(f"{cart[4]:.2f}")
                self.ui.label_num_rz.setText(f"{cart[5]:.2f}")

            except Exception as e:
                print(f"⚠️ Failed to update robot labels: {e}")
            
    # --- Go Home Button ---        
    def go_home(self, use_library_home=False):
        if not self.connected:
            print("Robot not connected")
            return

        try:
            if use_library_home:
                functions.robot_go_home(ROBOT_NAME)
                print("✅ Robot moved to home using library function")
            else:
                pos = [0.0]*7
                functions.robot_movej(pos, vel=60, coord=0, acc=30, dec=30, robot_name=ROBOT_NAME)
                print("✅ Robot moved to home (all-zero joints)")
            
            self.update_robot_labels()
        except Exception as e:
            print(f"❌ Failed to move to home: {e}")

    # --- Clear Error Button ---
    def on_clear_error_click(self):
        if not self.connected:
            print("❌ Robot not connected, cannot clear errors")
            return

        try:
            status = functions.clear_error(ROBOT_NAME)
            if status == 0:
                print("✅ Robot errors cleared successfully")
            else:
                print(f"❌ Failed to clear errors, code: {status}")
        except Exception as e:
            print(f"⚠️ Exception while clearing errors: {e}")

    #=======|Action Tab|=======#
        # --- Save Current Position as New Step ---
    def save_step(self):
        if not self.connected:
            print("❌ Cannot save step: robot not connected.")
            return
        else:
            row = self.ui.programTable.rowCount()
            self.ui.programTable.insertRow(row)

            step_no = row + 1
            pos = functions.get_current_position()

            self.ui.programTable.setItem(row, 0, QtWidgets.QTableWidgetItem(str(step_no)))
            for i, val in enumerate(pos, start=1):
                self.ui.programTable.setItem(row, i, QtWidgets.QTableWidgetItem(f"{val:.2f}"))
            print(f"Step {step_no} saved.")

        # --- Edit Selected Row ---
    def edit_step(self):
        if not self.connected:
            print("❌ Cannot edit step: robot not connected.")
            return
        else:
            row = self.ui.programTable.currentRow()
            if row < 0:
                print(self, "No Selection", "Please select a row to edit.")
                return
            pos = functions.get_current_position()
            for i, val in enumerate(pos, start=1):
                self.ui.programTable.setItem(row, i, QtWidgets.QTableWidgetItem(f"{val:.2f}"))

        # --- Insert Below Selected Row ---
    def insert_step(self):
        if not self.connected:
            print("❌ Cannot insert step: robot not connected.")
            return
        else:
            row = self.ui.programTable.currentRow()
            if row < 0: row = self.ui.programTable.rowCount() - 1
            self.ui.programTable.insertRow(row + 1)

            pos = functions.get_current_position()
            self.ui.programTable.setItem(row + 1, 0, QtWidgets.QTableWidgetItem(str(row + 2)))
            for i, val in enumerate(pos, start=1):
                self.ui.programTable.setItem(row + 1, i, QtWidgets.QTableWidgetItem(f"{val:.2f}"))

            self.renumber_steps()

        # --- Delete Selected Row ---
    def delete_step(self):
        if not self.connected:
            print("❌ Cannot delete step: robot not connected.")
            return
        else:
            row = self.ui.programTable.currentRow()
            if row >= 0:
                self.ui.programTable.removeRow(row)
                self.renumber_steps()

        # --- Renumber Steps ---
    def renumber_steps(self):
        for row in range(self.ui.programTable.rowCount()):
            self.ui.programTable.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row + 1)))

        # --- Run Program ---
    def run_program(self):
        if not self.connected:
            print("❌ Cannot save step: robot not connected.")
            return
        else:
            global current_step_index, program_running
            if self.ui.programTable.rowCount() == 0:
                print(self, "No Program", "No steps available.")
                return
        
            program_running = True
            current_step_index = 0
            self.execute_step(current_step_index)
            self.run_timer.start(200)  # poll every 200 ms

        # --- Execute Step ---
    def execute_step(self, index):
        row = index
        pos = []
        for col in range(1, 8):  # J1..Gripper
            val = float(self.ui.programTable.item(row, col).text())
            pos.append(val)

        # Send command to robot
        functions.robot_movej(pos, vel=wspeed, coord=0, acc=30, dec=30, robot_name=ROBOT_NAME)

        # --- Poll Robot State ---
    def check_robot_state(self):
        if not self.connected:
            print("❌ Cannot check robot state: robot not connected.")
            return
        else:
            global current_step_index, program_running
            if not program_running:
                self.run_timer.stop()
                return

            state = functions.get_robot_running_state(ROBOT_NAME)  # 0=idle,1=running (assumed)
            if state == 0:  # finished current move
                current_step_index += 1
                if current_step_index < self.ui.programTable.rowCount():
                    self.execute_step(current_step_index)
                else:
                    program_running = False
                    self.run_timer.stop()
                    print(self, "Program Done", "All steps executed!")



# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
