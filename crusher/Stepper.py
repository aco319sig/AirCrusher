"""
Modified Stepper class made to run 28BYJ-48 Stepper Motor with a ULN2003 motor controller.
Full rotation variable determined from http://www.jangeox.be/2013/10/stepper-motor-28byj-48_25.html
"""
import time


class Stepper:
    FULL_ROTATION = 509

    ROTATE = [
        [0, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 1],
    ]
    
    def __init__(self, mode, pin1, pin2, pin3, pin4, led, ir1, delay):
        self.mode = self.ROTATE
        self.pin1 = pin1
        self.pin2 = pin2
        self.pin3 = pin3
        self.pin4 = pin4
        self.led = led
        self.ir1 = ir1
        self.delay = delay  # Recommend 10+ for FULL_STEP, 1 is OK for ROTATE
        
        # Initialize all to 0
        self.reset()
        
    def step(self, count, direction=1):
        """Rotate count steps. direction = -1 means backwards"""
        if count<0:
            direction = -1
            count = -count
        for x in range(count):
            for bit in self.mode[::direction]:
                self.pin1(bit[0])
                self.pin2(bit[1])
                self.pin3(bit[2])
                self.pin4(bit[3])
                time.sleep_ms(self.delay)
        self.reset()
        
    def angle(self, r, direction=1):
        self.step(int(self.FULL_ROTATION * r / 360), direction)
    
    def reset(self):
        # Reset to 0, no holding, these are geared, you can't move them
        self.pin1(0) 
        self.pin2(0) 
        self.pin3(0) 
        self.pin4(0)
        
    def home(self):
        looptime = time.time()
        try:
            self.led.value(1)
            # self.angle(5)
            while not self.ir1.value() and time.time() < looptime + 30:
                self.step(-2)
            else:
                if self.ir1.value():
                    self.led.value(0)
                    self.reset()
                    return True
                else:
                    print('Home function timed out')
                    self.led.value(0)
                    self.reset()
                    return False
        except KeyboardInterrupt:
            print('Program terminated by KBI')
            self.led.value(0)
            self.reset()
            return False

def create(pin1, pin2, pin3, pin4, led, ir1, delay=2, mode='ROTATE'):
    return Stepper(mode, pin1, pin2, pin3, pin4, led, ir1, delay)


