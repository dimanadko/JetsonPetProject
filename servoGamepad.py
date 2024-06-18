import time
import cv2
from dualSense import DualShockController
from panTilt import PanTilt
from camera import CSICamera
from lidar import TFMiniPlus

pan_tilt = PanTilt(channel_x=0, channel_y=1)
pan_tilt.center()

# Utils

def center_dot_with_number(frame, number_value):
    # Get frame dimensions
    height, width, _ = frame.shape
    
    # Calculate center coordinates
    center_x, center_y = width // 2, height // 2
    
    # Draw a dot at the center of the frame
    dot_color = (0, 255, 0)  # Green color
    dot_radius = 5
    cv2.circle(frame, (center_x, center_y), dot_radius, dot_color, -1)


    pan_tilt.set_pan_tilt(90,90)
    
    # Draw the random number next to the dot
    text_position = (center_x + 10, center_y)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_color = (255, 255, 255)  # White color
    thickness = 2
    cv2.putText(frame, str(number_value), text_position, font, font_scale, font_color, thickness)
    
    return frame

# 


tfm = TFMiniPlus()
tfm.begin("/dev/ttyUSB0", 115200)
tfm.printStatus()

def frame_middleware(frame):
    dataSuccess = tfm.getData()
    number_value = None
    if dataSuccess:
        number_value = tfm.dist
    else:
        number_value = tfm.printStatus()
    return center_dot_with_number(frame, number_value)


camera = CSICamera(
    capture_width=1280, capture_height=720, 
    display_width=1280, display_height=720, framerate=60, 
    flip_method=6, middleware=frame_middleware
    )
controller = DualShockController('/dev/input/event9')



def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

joystick_active = True

def joystick_activate_callback(event_type, trigger_event_type, value):
    if event_type == 'button' and trigger_event_type == 'triangle' and value == "down":
        joystick_active = not joystick_active


def joystick_callback(event_type, left_joystick, right_joystick):
    if event_type == 'joystick' and joystick_active:
        x_value = map_value(left_joystick[1], 0, 255, 0, 180)
        y_value = map_value(right_joystick[0], 0, 255, 0, 180)
        pan_tilt.set_pan_tilt(x_value, y_value)
        print(f'Pan (X): {x_value}, Tilt (Y): {y_value}')

def trigger_callback(event_type, trigger_event_type, value):
    if event_type == 'button':
        print(f'trigger {trigger_event_type} {value}')
        if trigger_event_type == 'R2':
            if value == "down":
                camera.start()
            elif value == "up":
                camera.stop()




if __name__ == '__main__':
    controller.register_callback(joystick_callback)
    controller.register_callback(trigger_callback)
    controller.register_callback(joystick_activate_callback)
    
    controller.start()

    try:
        while True:
            time.sleep(0)
    except KeyboardInterrupt:
        controller.stop()
        if tfm.pStream:
            tfm.pStream.close()
        print("Controller stopped.")
