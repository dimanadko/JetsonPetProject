import board
from adafruit_motor import servo as AdafruitServo
from adafruit_pca9685 import PCA9685
i2c = board.I2C()

class PanTilt:
    def __init__(self, channel_x, channel_y, i2c=i2c):
        self.pca = PCA9685(i2c)
        self.pca.frequency = 50

        self.servo_X = AdafruitServo.Servo(self.pca.channels[channel_x], min_pulse=500, max_pulse=2600, actuation_range=180)
        self.servo_Y = AdafruitServo.Servo(self.pca.channels[channel_y], min_pulse=500, max_pulse=2600, actuation_range=180)

    def set_pan_tilt(self, pan, tilt):
        self.servo_X.angle = pan
        self.servo_Y.angle = tilt

    def center(self):
        self.set_pan_tilt(90, 90)