"""
Micropython module for Automated Can Crusher using the following hardware:
Raspberry Pi 3 B+
Breakout Board w/ screw terminals
Wolfwhoop PW-D Control Buck Converter
    6-24V to 5V 1.5A Step-Down Regulator Module Power Inverter Volt Stabilizer
    (One needed to power Pico all by itself, due to voltage drop, other to power sensors, relays, and driver)
IR Break Beam Sensor ( 2 sets )
28BYJ-48 ULN2003 5V Stepper Motor + ULN2003 Driver Board
DC 5V Relay Module with Optocoupler Low Level Trigger Expansion Board
Pneumatic Tubing Pipe 3/8" OD Blue Air Compressor PU Line Hose
TAILONZ PNEUMATIC 3/8"NPT Solenoid Valve 4V310-10 12V
TAILONZ PNEUMATIC Air Cylinder
    Bore: 2 1/2 inch (63mm)
    Stroke: 6 inch (150mm)
    Piston type: Screwed Piston Rod
    Dual Action (Air powered exttend and retract)
    (additional fittings will be needed to connect to valve, see next item:)
Male Straight 3/8 Inch Tube OD x 3/8 Inch NPT Thread Push to Connect Fittings

Various wiring and power distribution choices, none of which matter to construction.


Physical loader is a 4 spoke paddle wheel design, with holes for ir
break-beam sensors to detect both positioning and payload.

"""
import sys
import drivers
from time import sleep
from time import time as ti

#from machine import I2C, Pin
#from lcd_api import LcdApi
#from i2c_lcd import I2cLcd
lcd = drivers.Lcd()

sleep(1.5)
home_pin = 14
# old start_pin = 2
start_pin = 4
# reset_pin = 28
# load_pin = 6
# retract_pin = 7
# l1 = 25
# l2 = 0
# old_disp_sda = 4
disp_sda = 2
# old_disp_scl = 5
disp_scl = 3
# crushPin = 20
# compPin = 22
# case_safety = 16
ts = ti()
nts = ''

# Non-Class devices
# led1 = Pin(l1, Pin.OUT)
# led2 = Pin(l2, Pin.OUT)
# home_switch = Pin(home_pin, Pin.IN, Pin.PULL_UP)
# safe_switch = Pin(case_safety, Pin.IN, Pin.PULL_UP)
# start_button = Pin(start_pin, Pin.IN, Pin.PULL_UP)
# reset_button = Pin(reset_pin, Pin.IN, Pin.PULL_UP)
# load = Pin(load_pin, Pin.OUT)
# retract = Pin(retract_pin, Pin.OUT)
# crusher = Pin(crushPin, Pin.OUT)
# crusher.value(1)
# compressor = Pin(compPin, Pin.OUT)
# compressor.value(1)

### LCD Display Creation
# Find and define Display
i2c = I2C(0, sda=Pin(disp_sda), scl=Pin(disp_scl), freq=400000)
I2C_ADDR = i2c.scan()[0]
#I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16

### Instantiate classes
# Create display instance
lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns)

def is_safe():
    if safe_switch.value():
        lcd.clear()
        lcd.putstr('Rotator Jammed')
        print("Rotator is Jammed!")
        sys.exit()
    else:
        lcd.clear()
        lcd.putstr('Safe to Run')
        print("Safe to run")
        return True

# Create Loader
# s1 = Stepper.create(Pin(p1,Pin.OUT),Pin(p2,Pin.OUT),Pin(p3,Pin.OUT),Pin(p4,Pin.OUT),Pin(l1,Pin.OUT),Pin(ir1,Pin.IN,Pin.PULL_UP),delay=2)
def home():
    is_safe()
    global ts
    looptime = ti()
    try:
        led1.value(1)
        if load_can():
            # Add pressure check function here later
            compressor.value(0)
            countdown(need_pressure())
            crush_it()
        else:
            if safe_switch.value() == 0:
                print('Safe Passed')
                lcd.clear()
                lcd.putstr('Loader ready')
                blink()
                return True
            else:
                print('Home function timed out')
                lcd.clear()
                lcd.putstr('Timeout...')
                blink_error()
                return False
    except KeyboardInterrupt:
        print('Program terminated by KBI')
        led1.value(0)
        return False

def load_can():
    if is_safe():
        sleep(1)
        lcd.clear()
        lcd.putstr('Safe passed')

    can_there = False
    can_loaded = False
    lcd.clear()
    while not home_switch.value() == 0:
        load.value(1)
        sleep(0.1)
        load.value(0)
        if can_there and safe_switch.value() == 0:
            can_loaded = True
            print('Can Loaded')
            lcd.clear()
            lcd.putstr('Can Loaded')
        elif safe_switch.value() == 1:
            can_there = True
            print('Can Found')
            lcd.clear()
            lcd.putstr('Can Found')
        else:
            print('Keep Moving')
    unhome()
    sleep(0.25)
    if can_there and safe_switch.value() == 0:
        can_loaded = True
        print('Can Loaded')
        lcd.clear()
        lcd.putstr('Can Loaded')

    if can_there and can_loaded:
        return True
    else:
        return False

def unhome():
    while home_switch.value() == 0:
        f_inch(0.1)

def f_inch(val=0.25):
    load.value(1)
    sleep(val)
    load.value(0)

def b_inch(val=0.25):
    retract.value(1)
    sleep(val)
    retract.value(0)

def crush_it():
    lcd.clear()
    lcd.putstr("Crushing!!")
    sleep(0.5)
    crusher.value(0)
    sleep(1)
    lcd.clear()
    lcd.putstr("Retracting!!")
    crusher.value(1)
    sleep(2)

def blink():
    print("blink")
    blinkVal = 10
    while blinkVal > 0:
        led1.value(0)
        led2.value(0)
        sleep(0.07)
        led1.value(1)
        led2.value(1)
        sleep(0.07)
        blinkVal -= 1
    else:
        led1.value(0)
        led2.value(0)

def blink_error():
    print("Blink_error")
    blinkVal = 3
    while blinkVal > 0:
        led1.value(0)
        led2.value(0)
        sleep(0.5)
        led1.value(1)
        led2.value(1)
        sleep(0.5)
        blinkVal -= 1
    else:
        led1.value(0)
        led2.value(0)

def countdown(n):
    while n>0:
        print(str(n), 'seconds left')
        lcd.clear()
        thisSecond = str(n)
        lcd.putstr( 'Pressurizing....Countdown = ')
        lcd.putstr(thisSecond)
        n = n -1
        sleep(0.8)

def need_pressure():
    nts = ti()
    time_diff = nts - ts
    if time_diff >= 144000:
        print("Time greater than 40 hours")
        return 40
    elif time_diff <= 3600:
        print("Time less than 1 hour")
        return 1
    else:
        print("time_diff = ", str(time_diff))
        print("Calculating required time...")
        pressure_time_ratio = round(time_diff / 3600)
        return pressure_time_ratio

def runCycler():
    global ts
    # Add pressure check function here later
    compressor.value(0)
    countdown(need_pressure())
    sleep(0.5)
    crush_it()
    led1.value(1)
    led2.value(1)
    count = 5
    while load_can():
        if count > 0:
            crush_it()
            sleep(2)
            count -= 1
        else:
            lcd.clear()
            lcd.putstr("Max 5 exceeded!!Reset in 10 sec")
            sleep(10)
            compressor.value(1)
    else:
            lcd.clear()
            lcd.putstr("No more cans!!  Reset in 10 sec")
            sleep(10)
            compressor.value(1)

    home()
    ts = ti()
    print("Timestamp reset to", str(ts))
    led1.value(0)
    led2.value(0)


## Beginning of commands ##
# Safety check
is_safe()
print("Safety Check Done")
# Acknowedge power on
lcd.clear()
lcd.putstr("Power-On-Self-  Test")
blink_error()
compressor.value(0)
countdown(40)
compressor.value(1)
ts = ti()
print("Timestamp reset to", str(ts))

# Ensure crusher is retracted at start
crusher.value(1)

# show dict
lcd.__dict__

# Home the rotor
lcd.clear()
lcd.putstr("Homing loader   for first time")
sleep(2)
lcd.clear()
home()
# Wait for Start Button
try:
    while True:
        first = start_button.value()
        r_first = reset_button.value()
        sleep(0.01)
        second = start_button.value()
        r_second = reset_button.value()
        if first and not second:
            lcd.clear()
            lcd.putstr('Start pressed!')
        elif not first and second:
            lcd.clear()
            lcd.putstr('Start released!')
            runCycler()
        elif r_first and not r_second:
            lcd.clear()
            lcd.putstr('Reset Pressed')
        elif not r_first and r_second:
            lcd.clear()
            lcd.putstr('Reset released')
            compressor.value(0)
            want_pressure = need_pressure()
            if want_pressure < 10:
                want_pressure = 10
            countdown(want_pressure)
            compressor.value(1)
            ts = ti()
            print("Timestamp reset to", str(ts))

except KeyboardInterrupt:
    lcd.clear()
    lcd.putstr('Program terminated by KBI')
    crusher.value(1)
    compressor.value(1)
    led1.value(0)
    led2.value(0)
