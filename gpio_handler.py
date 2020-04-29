
import pigpio


class GPIOHandler:
    def __init__(self):
        self.gpio = pigpio.pi()

    def pinStatus(self, pin):
        status = self.gpio.read(pin)
        return status

    def setPullUp(self, pin):
        return self.gpio.set_pull_up_down(pin, pigpio.PUD_UP)

    def setPullDown(self, pin):
        return self.gpio.set_pull_up_down(pin, pigpio.PUD_DOWN)

    def __del__(self):
        self.gpio.stop()
        return
