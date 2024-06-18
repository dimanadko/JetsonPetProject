import cv2
import time
import threading
import random

class CSICamera:
    def __init__(self, sensor_id=0, capture_width=1640, capture_height=1232, display_width=1640, display_height=1232, framerate=30, flip_method=0, middleware=None):
        self.sensor_id = sensor_id
        self.capture_width = capture_width
        self.capture_height = capture_height
        self.display_width = display_width
        self.display_height = display_height
        self.framerate = framerate
        self.flip_method = flip_method
        self.window_title = "CSI Camera"
        self.video_capture = None
        self.running = False
        self.middleware=middleware

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

    def start(self):
        self.video_capture = cv2.VideoCapture(self.gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        if self.video_capture.isOpened():
            self.running = True
            threading.Thread(target=self._capture_video).start()
        else:
            print("Error: Unable to open camera")

    def _capture_video(self):
        cv2.namedWindow(self.window_title, cv2.WINDOW_AUTOSIZE)
        while self.running:
            ret_val, frame = self.video_capture.read()
            if not ret_val:
                break

            if self.middleware:
                            frame = self.middleware(frame)

            if cv2.getWindowProperty(self.window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                cv2.imshow(self.window_title, frame)
            else:
                break
            keyCode = cv2.waitKey(10) & 0xFF
            if keyCode == 27 or keyCode == ord('q'):
                self.stop()
                break
        self.stop()

    def stop(self):
        self.running = False
        if self.video_capture:
            self.video_capture.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    def example_middleware(frame):
        # Example: Convert frame to grayscale
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
    def center_dot_with_random_number(frame):
        # Get frame dimensions
        height, width, _ = frame.shape
        
        # Calculate center coordinates
        center_x, center_y = width // 2, height // 2
        
        # Draw a dot at the center of the frame
        dot_color = (0, 255, 0)  # Green color
        dot_radius = 5
        cv2.circle(frame, (center_x, center_y), dot_radius, dot_color, -1)
        
        # Generate a random number
        random_number = random.randint(0, 100)
        
        # Draw the random number next to the dot
        text_position = (center_x + 10, center_y)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (255, 255, 255)  # White color
        thickness = 2
        cv2.putText(frame, str(random_number), text_position, font, font_scale, font_color, thickness)
        
        return frame


    camera = CSICamera(capture_width=1280, capture_height=720, display_width=1280, display_height=720, framerate=60, flip_method=6, middleware=center_dot_with_random_number)
    camera.start()
    time.sleep(5)
    camera.stop()
