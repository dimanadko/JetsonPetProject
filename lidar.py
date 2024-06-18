import time
import serial

class TFMiniPlus:
    TFMP_FRAME_SIZE = 9
    TFMP_COMMAND_MAX = 8
    TFMP_REPLY_SIZE = 8
    TFMP_MAX_READS = 20
    MAX_BYTES_BEFORE_HEADER = 20
    MAX_ATTEMPTS_TO_MEASURE = 20
    TFMP_DEFAULT_ADDRESS = 0x10

    TFMP_READY = 0
    TFMP_SERIAL = 1
    TFMP_HEADER = 2
    TFMP_CHECKSUM = 3
    TFMP_TIMEOUT = 4
    TFMP_PASS = 5
    TFMP_FAIL = 6
    TFMP_I2CREAD = 7
    TFMP_I2CWRITE = 8
    TFMP_I2CLENGTH = 9
    TFMP_WEAK = 10
    TFMP_STRONG = 11
    TFMP_FLOOD = 12
    TFMP_MEASURE = 13

    GET_FIRMWARE_VERSION = 0x00010407
    TRIGGER_DETECTION = 0x00040400
    SOFT_RESET = 0x00020405
    HARD_RESET = 0x00100405
    SAVE_SETTINGS = 0x00110405
    SET_FRAME_RATE = 0x00030606
    SET_BAUD_RATE = 0x00060808
    STANDARD_FORMAT_CM = 0x01050505
    PIXHAWK_FORMAT = 0x02050505
    STANDARD_FORMAT_MM = 0x06050505
    ENABLE_OUTPUT = 0x01070505
    DISABLE_OUTPUT = 0x00070505
    SET_I2C_ADDRESS = 0x100B0505
    SET_SERIAL_MODE = 0x000A0500
    SET_I2C_MODE = 0x010A0500
    I2C_FORMAT_CM = 0x01000500
    I2C_FORMAT_MM = 0x06000500

    BAUD_9600 = 0x002580
    BAUD_14400 = 0x003840
    BAUD_19200 = 0x004B00
    BAUD_56000 = 0x00DAC0
    BAUD_115200 = 0x01C200
    BAUD_460800 = 0x070800
    BAUD_921600 = 0x0E1000

    FRAME_0 = 0x0000
    FRAME_1 = 0x0001
    FRAME_2 = 0x0002
    FRAME_5 = 0x0005
    FRAME_10 = 0x000A
    FRAME_20 = 0x0014
    FRAME_25 = 0x0019
    FRAME_50 = 0x0032
    FRAME_100 = 0x0064
    FRAME_125 = 0x007D
    FRAME_200 = 0x00C8
    FRAME_250 = 0x00FA
    FRAME_500 = 0x01F4
    FRAME_1000 = 0x03E8

    def __init__(self):
        self.status = 0
        self.dist = 0
        self.flux = 0
        self.temp = 0
        self.version = bytearray(3)
        self.pStream = None
        self.frame = bytearray(self.TFMP_FRAME_SIZE)
        self.reply = bytearray(self.TFMP_REPLY_SIZE)

    def begin(self, port, rate):
        self.pStream = serial.Serial(port, rate)
        time.sleep(0.2)
        if self.pStream.inWaiting() > 0:
            self.status = self.TFMP_READY
            return True
        else:
            self.status = self.TFMP_SERIAL
            return False

    def getData(self):
        self.status, self.dist, self.flux, self.temp = 0, 0, 0, 0
        serialTimeout = time.time() + 1
        while self.pStream.inWaiting() > self.TFMP_FRAME_SIZE:
            self.pStream.read()
        self.frame = bytearray(self.TFMP_FRAME_SIZE)
        while self.frame[0] != 0x59 or self.frame[1] != 0x59:
            if self.pStream.inWaiting():
                self.frame.append(self.pStream.read()[0])
                self.frame = self.frame[1:]
            if time.time() > serialTimeout:
                self.status = self.TFMP_HEADER
                return False
        chkSum = sum(self.frame[:-1]) & 0xFF
        if chkSum != self.frame[-1]:
            self.status = self.TFMP_CHECKSUM
            return False
        self.dist = (self.frame[3] << 8) + self.frame[2]
        self.flux = (self.frame[5] << 8) + self.frame[4]
        self.temp = (((self.frame[7] << 8) + self.frame[6]) >> 3 )- 256
        if self.dist == -1:
            self.status = self.TFMP_WEAK
        elif self.flux == -1:
            self.status = self.TFMP_STRONG
        elif self.dist == -4:
            self.status = self.TFMP_FLOOD
        else:
            self.status = self.TFMP_READY
        return self.status == self.TFMP_READY

    def sendCommand(self, cmnd, param):
        cmndData = bytearray(cmnd.to_bytes(self.TFMP_COMMAND_MAX, byteorder='little'))
        replyLen, cmndLen = cmndData[0], cmndData[1]
        cmndData[0] = 0x5A
        if cmnd == self.SET_FRAME_RATE:
            cmndData[3:5] = param.to_bytes(2, byteorder='little')
        elif cmnd == self.SET_BAUD_RATE:
            cmndData[3:6] = param.to_bytes(3, byteorder='little')
        cmndData = cmndData[:cmndLen]
        cmndData[-1] = sum(cmndData[:-1]) & 0xFF
        self.pStream.reset_input_buffer()
        self.pStream.reset_output_buffer()
        self.pStream.write(cmndData)
        if replyLen == 0:
            return True
        serialTimeout = time.time() + 1
        self.reply = bytearray(replyLen)
        while self.reply[0] != 0x5A or self.reply[1] != replyLen:
            if self.pStream.inWaiting():
                self.reply.append(self.pStream.read()[0])
                self.reply = self.reply[1:]
            if time.time() > serialTimeout:
                self.status = self.TFMP_HEADER
                return False
        chkSum = sum(self.reply[:-1]) & 0xFF
        if chkSum != self.reply[-1]:
            self.status = self.TFMP_CHECKSUM
            return False
        if cmnd == self.GET_FIRMWARE_VERSION:
            self.version = self.reply[3:6]
        elif cmnd in {self.SOFT_RESET, self.HARD_RESET, self.SAVE_SETTINGS} and self.reply[3] == 1:
            self.status = self.TFMP_FAIL
            return False
        self.status = self.TFMP_READY
        return True

    def printStatus(self):
        status_dict = {
            self.TFMP_READY: "READY",
            self.TFMP_SERIAL: "SERIAL",
            self.TFMP_HEADER: "HEADER",
            self.TFMP_CHECKSUM: "CHECKSUM",
            self.TFMP_TIMEOUT: "TIMEOUT",
            self.TFMP_PASS: "PASS",
            self.TFMP_FAIL: "FAIL",
            self.TFMP_I2CREAD: "I2C-READ",
            self.TFMP_I2CWRITE: "I2C-WRITE",
            self.TFMP_I2CLENGTH: "I2C-LENGTH",
            self.TFMP_WEAK: "Signal weak",
            self.TFMP_STRONG: "Signal saturation",
            self.TFMP_FLOOD: "Ambient light saturation",
        }
        print(f"Status: {status_dict.get(self.status, 'OTHER')}")

    def printFrame(self):
        self.printStatus()
        print("Data:", end='')
        for byte in self.frame:
            print(f" {byte:02X}", end='')
        print()

    def printReply(self):
        self.printStatus()
        for byte in self.reply:
            print(f" {byte:02X}", end='')    
        print()

if __name__ == "__main__":
    print("tfmplus - This Python module supports the Benewake TFMini-Plus Lidar device")
    try:
        tfm = TFMiniPlus()
        tfm.begin("/dev/ttyUSB0", 115200)
        tfm.printStatus()
        while True:
            dataSuccess = tfm.getData()
            if dataSuccess:
                print(tfm.dist, tfm.flux, tfm.temp)
            else:
                tfm.printStatus()
    except KeyboardInterrupt:
        if tfm.pStream:
            tfm.pStream.close()
