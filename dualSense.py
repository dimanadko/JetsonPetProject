import time
from evdev import InputDevice, categorize, ecodes
from threading import Thread
from select import select

class DualShockController:
    CENTER = 127
    BLIND = 0
    MAX_EMERGENCY_DELAY = 1000

    button_presses = {
        304: 'square',
        305: 'x',
        306: 'circle',
        307: 'triangle',
        308: 'L1',
        309: 'R1',
        310: 'L2',
        311: 'R2',
        312: 'share',
        313: 'pause',
        314: 'L3',
        315: 'R3',
        316: 'playstation',
        317: 'touchpad'
    }

    button_values = {
        0: 'up',
        1: 'down'
    }

    absolutes = {
        0: 'left joystick left/right',
        1: 'left joystick up/down',
        2: 'right joystick left/right',
        3: 'L2 analog',
        4: 'R2 analog',
        5: 'right joystick up/down',
        16: 'leftpad left/right',
        17: 'leftpad up/down',
    }

    leftpad_left_right_values = {
        -1: 'left',
        0: 'left-right stop',
        1: 'right'
    }

    leftpad_up_down_values = {
        -1: 'up',
        0: 'up-down stop',
        1: 'down'
    }

    def __init__(self, device_path):
        self.device = InputDevice(device_path)
        self.callbacks = []
        self.running = False
        self.emergency_tap_time = 0
        self.left_joystick = [self.CENTER, self.CENTER]
        self.right_joystick = [self.CENTER, self.CENTER]

    def start(self):
        self.running = True
        self.thread = Thread(target=self._run)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

    def _run(self):
        while self.running:
            r, w, x = select([self.device], [], [])
            for event in self.device.read():
                if event.type == ecodes.EV_KEY:
                    self._handle_key_event(event)
                elif event.type == ecodes.EV_ABS:
                    self._handle_abs_event(event)

    def _handle_key_event(self, event):
        if event.code in self.button_presses:
            button = self.button_presses[event.code]
            direction = self.button_values[event.value]
            self._emit_event('button', button, direction)
            if self._is_emergency(event, direction):
                self._emit_event('emergency', button, direction)

    def _handle_abs_event(self, event):
        if event.code in self.absolutes:
            action = self.absolutes[event.code]
            value = event.value
            if event.code in [0, 1, 2, 5]:
                self._update_joystick_position(event)
                if value > (self.CENTER - self.BLIND) and value < (self.CENTER + self.BLIND):
                    return
                self._emit_event('joystick', self.left_joystick, self.right_joystick)
            elif event.code in [3, 4]:
                self._emit_event('trigger', action, value)
            elif event.code in [16, 17]:
                action = self._decode_leftpad(event)
                self._emit_event('leftpad', action)

    def _is_emergency(self, event, direction):
        if event.code == 317 and direction == 'down':
            previous_tap = self.emergency_tap_time
            self.emergency_tap_time = int(round(time.time() * 1000))
            if self.emergency_tap_time < (previous_tap + self.MAX_EMERGENCY_DELAY):
                return True
        return False

    def _update_joystick_position(self, event):
        if event.code == 0:
            self.left_joystick[0] = event.value
        elif event.code == 1:
            self.left_joystick[1] = event.value
        elif event.code == 2:
            self.right_joystick[0] = event.value
        elif event.code == 5:
            self.right_joystick[1] = event.value

    def _decode_leftpad(self, event):
        action = ''
        if event.code == 16:
            action = self.leftpad_left_right_values[event.value]
        elif event.code == 17:
            action = self.leftpad_up_down_values[event.value]
        return f'leftpad: {action}'

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _emit_event(self, event_type, *args):
        for callback in self.callbacks:
            callback(event_type, *args)

if __name__ == '__main__':
    def print_event(event_type, *args):
        # if(event_type == 'joystick'):
        print(f'Event: {event_type}, Args: {args}')

    controller = DualShockController('/dev/input/event9')
    controller.register_callback(print_event)
    controller.start()

    try:
        while True:
            time.sleep(0)
    except KeyboardInterrupt:
        controller.stop()
        print("Controller stopped.")
