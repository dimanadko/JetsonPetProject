import time
import cv2
from dualSense import DualShockController
from panTilt import PanTilt
from camera import CSICamera
from lidar import TFMiniPlus


def center_dot_with_number(frame, number_value):
    height, width, _ = frame.shape
    center_x, center_y = width // 2, height // 2

    dot_color = (0, 255, 0)
    dot_radius = 5
    cv2.circle(frame, (center_x, center_y), dot_radius, dot_color, -1)

    text_position = (center_x + 10, center_y)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_color = (255, 255, 255)
    thickness = 2
    cv2.putText(frame, str(number_value), text_position, font, font_scale, font_color, thickness)

    return frame

class servoGampad:
    def __init__(self, pan_channel_x=0, pan_channel_y=1, camera_device="/dev/input/event9", lidar_port="/dev/ttyUSB0", baudrate=115200):
        self.pan_tilt = PanTilt(channel_x=pan_channel_x, channel_y=pan_channel_y)
        self.pan_tilt.center()

        self.tfm = TFMiniPlus()
        self.tfm.begin(lidar_port, baudrate)
        self.tfm.printStatus()

        self.camera = CSICamera(
            capture_width=1280, capture_height=720,
            display_width=1280, display_height=720, framerate=60,
            flip_method=6, middleware=self.frame_middleware
        )

        self.controller = DualShockController(camera_device)
        self.joystick_active = True

        self.controller.register_callback(self.joystick_callback)
        self.controller.register_callback(self.trigger_callback)
        self.controller.register_callback(self.joystick_activate_callback)
        
        self.controller.start()

    def frame_middleware(self, frame):


        if not self.joystick_active:
            self.pan_tilt.set_pan_tilt(90, 90)

        dataSuccess = self.tfm.getData()
        number_value = None
        if dataSuccess:
            number_value = self.tfm.dist
        else:
            number_value = self.tfm.printStatus()
        return center_dot_with_number(frame, number_value)

    def map_value(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

    def joystick_activate_callback(self, event_type, trigger_event_type, value):
        if event_type == 'button' and trigger_event_type == 'triangle' and value == "down":
            self.joystick_active = not self.joystick_active
            print('joystick_active', self.joystick_active)

    def joystick_callback(self, event_type, left_joystick, right_joystick):
        if event_type == 'joystick' and self.joystick_active:
            x_value = self.map_value(left_joystick[1], 0, 255, 0, 180)
            y_value = self.map_value(right_joystick[0], 0, 255, 0, 180)
            self.pan_tilt.set_pan_tilt(x_value, y_value)
            print(f'Pan (X): {x_value}, Tilt (Y): {y_value}, joystick_active: {self.joystick_active}')

    def trigger_callback(self, event_type, trigger_event_type, value):
        if event_type == 'button':
            print(f'trigger {trigger_event_type} {value}')
            if trigger_event_type == 'R2':
                if value == "down":
                    self.camera.start()
                elif value == "up":
                    self.camera.stop()

    def run(self):
        try:
            while True:
                time.sleep(0)
        except KeyboardInterrupt:
            self.controller.stop()
            if self.tfm.pStream:
                self.tfm.pStream.close()
            print("Controller stopped.")

if __name__ == '__main__':
    camera_controller = CameraController()
    camera_controller.run()
