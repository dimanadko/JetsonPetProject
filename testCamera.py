import cv2

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
            try:
                window_handle = cv2.namedWindow(self.window_title, cv2.WINDOW_AUTOSIZE)
                while True:
                    ret_val, frame = self.video_capture.read()
                    if cv2.getWindowProperty(self.window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                        cv2.imshow(self.window_title, frame)
                    else:
                        break 
                    keyCode = cv2.waitKey(10) & 0xFF
                    if keyCode == 27 or keyCode == ord('q'):
                        break
            finally:
                self.stop()
        else:
            print("Error: Unable to open camera")

    def stop(self):
        if self.video_capture:
            self.video_capture.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    camera = CSICamera(flip_method=6)
    camera.start()
