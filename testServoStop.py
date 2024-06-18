from adafruit_servokit import ServoKit
kit = ServoKit(channels=16)
kit.servo[0].throttle = 0
kit.servo[1].throttle = 0

# print('s', kit.servo[0].angle)


quit()