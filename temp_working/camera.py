import cv2

# 
from panTilt import PanTilt
from dualSense import DualShockController
controller = DualShockController('/dev/input/event9')


pan_tilt = PanTilt(channel_x=0, channel_y=1)
pan_tilt.center()


def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def joystick_callback(event_type, left_joystick, right_joystick):
    if event_type == 'joystick':
        x_value = map_value(left_joystick[1], 0, 255, 0, 180)
        y_value = map_value(right_joystick[0], 0, 255, 0, 180)
        pan_tilt.set_pan_tilt(x_value, y_value)
        print(f'Pan (X): {x_value}, Tilt (Y): {y_value}')

# 


class CSICamera:
    def __init__(self, sensor_id=0, capture_width=1640, capture_height=1232, display_width=1640, display_height=1232, framerate=30, flip_method=0):
        self.sensor_id = sensor_id
        self.capture_width = capture_width
        self.capture_height = capture_height
        self.display_width = display_width
        self.display_height = display_height
        self.framerate = framerate
        self.flip_method = flip_method
        self.window_title = "CSI Camera"
        self.video_capture = None
        self.show_video = False

    def gstreamer_pipeline(self):
        return (
            "nvarguscamerasrc sensor-id=%d ! "
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink drop=True"
            % (
                self.sensor_id,
                self.capture_width,
                self.capture_height,
                self.framerate,
                self.flip_method,
                self.display_width,
                self.display_height,
            )
        )
    

    def trigger_callback(self, event_type, trigger_event_type, value):
        if event_type == 'button':
            print(f'trigger {trigger_event_type} {value}')
            if trigger_event_type == 'R2':
                if value == "down":
                    cv2.namedWindow(self.window_title, cv2.WINDOW_AUTOSIZE)
                    self.show_video = True
                elif value == "up":
                    cv2.destroyWindow(self.window_title)
                    self.show_video = False

    def start(self):
        self.video_capture = cv2.VideoCapture(self.gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        if self.video_capture.isOpened():
            try:
                # cv2.namedWindow(self.window_title, cv2.WINDOW_AUTOSIZE)
                controller.register_callback(joystick_callback)
                controller.register_callback(self.trigger_callback)
                controller.start()
                
                while True:
                    ret_val, frame = self.video_capture.read()
                    if cv2.getWindowProperty(self.window_title, cv2.WND_PROP_AUTOSIZE) >= 0 and self.show_video:
                        cv2.imshow(self.window_title, frame)
                        
                        


                    # else:
                    #     break
                    keyCode = cv2.waitKey(10) & 0xFF
                    if keyCode == 27 or keyCode == ord('q'):
                        break
            finally:
                self.stop()
                controller.stop()
                print("Controller stopped.")
        else:
            print("Error: Unable to open camera")

    def stop(self):
        if self.video_capture:
            self.video_capture.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    camera = CSICamera(flip_method=6)
    camera.start()
