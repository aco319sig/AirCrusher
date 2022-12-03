"""
Micropython module for Automated Can Crusher using the following hardware:
Raspbery Pi Pico 
PICO Breakout Board w/ screw terminals
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
sys.path.append('/crusher')
sys.path.append('/lcd')
import Stepper
import time
from machine import I2C, Pin
from lcd_api import LcdApi
from i2c_lcd import I2cLcd


time.sleep(1.5)
ir1 = 14
ir2 = 15
sbtn = 2
rbtn = 0
p1 = 6
p2 = 7
p3 = 8
p4 = 9
l1 = 25
l2 = 12
disp_sda = 4
disp_scl = 5
crushPin = 20
compPin = 22
case_safety = 13
ts = time.time()
nts = ''

# Non-Class devices
led1 = Pin(l1, Pin.OUT)
led2 = Pin(l2, Pin.OUT)
safe_switch = Pin(case_safety, Pin.IN, Pin.PULL_UP)
button = Pin(sbtn, Pin.IN, Pin.PULL_UP)
payload = Pin(ir2, Pin.IN, Pin.PULL_UP)
resetButton = Pin(rbtn, Pin.IN, Pin.PULL_UP)
crusher = Pin(crushPin, Pin.OUT)
crusher.value(1)
compressor = Pin(compPin, Pin.OUT)
compressor.value(1)

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

if safe_switch.value():
    lcd.clear()
    lcd.putstr('CASE IS OPEN!!')
    print("CASE IS OPEN!!")
    s1.step(5)
    sys.exit()
# Create Loader
s1 = Stepper.create(Pin(p1,Pin.OUT),Pin(p2,Pin.OUT),Pin(p3,Pin.OUT),Pin(p4,Pin.OUT),Pin(l1,Pin.OUT),Pin(ir1,Pin.IN,Pin.PULL_UP),delay=2)

def blink():
    print("blink")
    blinkVal = 10
    while blinkVal > 0:
        led1.value(0)
        led2.value(0)
        time.sleep(0.07)
        led1.value(1)
        led2.value(1)
        time.sleep(0.07)
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
        time.sleep(0.5)
        led1.value(1)
        led2.value(1)
        time.sleep(0.5)
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
        time.sleep(0.8)

def need_pressure():
    nts = time.time()
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

def reset_it():
    big_time = time.time()
    lcd.clear()
    lcd.putstr("Homing Loader...")
    print("Homing Loader...")
    if s1.home():
        lcd.clear()
        lcd.putstr('System is ready')
        print('System is ready')
        blink()
    else:
        lcd.putstr('Failed to home!')
        print('Failed to home!')
        blink_error()

def runCycler():
    global ts
    if safe_switch.value():
        lcd.clear()
        lcd.putstr('CASE IS OPEN!!')
        print("CASE IS OPEN!!")
        s1.step(5)
    else:
        print("Safety Check Complete")
        print("Running Cycler")
        # Add pressure check function here later
        compressor.value(0)
        countdown(need_pressure())
        canThere = False
        extra_crush = False
        led1.value(1)
        led2.value(1)
        s1.step(5)
        s1.home()
        canVal = can_glance()
        if canVal < 1:
            canThere2 = True
        else:
            canThere2 = False

        if canThere2:
            extra_crush = True
            lcd.clear()
            lcd.putstr("XtraCrush=TRUE")
            print("XtraCrush=TRUE")
        
        s1.angle(15,-1)
        s1.home()
        
        if extra_crush:
            crush_it()
        
        count = 5
        canVal = can_glance()
        if canVal < 1:
            canThere = True
        else:
            canThere = False
        
        while canThere and count > 0:
            lcd.clear()
            lcd.putstr("Payload Detected!")
            print("Payload Detected!")
            runit()
            count -= 1
            canVal = can_glance()
            if canVal < 1:
                canThere = True
            else:
                canThere = False
        else:
            if canThere:
                lcd.clear()
                lcd.putstr("Max 5 exceeded!!Reset in 10 sec")
                time.sleep(10)
                compressor.value(1)
                ts = time.time()
                reset_it()
                print("Timestamp reset to", str(ts))
                led1.value(0)
                led2.value(0)
                
            else:
                canStr = ("No Payload - L" + str(canVal))
                lcd.clear()
                lcd.putstr(canStr)
                lcd.putstr(" Reset in 10 sec")
                time.sleep(10)
                reset_it()
                compressor.value(1)
                ts = time.time()
                print("Timestamp reset to", str(ts))
                led1.value(0)
                led2.value(0)
                print(canStr)
                

def can_glance():
    if payload.value():
        return 1
    else:
        s1.step(-5)
        if payload.value():
            return 2
        else:
            s1.step(10)
            if payload.value():
                s1.step(-5)
                return 3
            else:
                s1.step(-5)
                return 0

def crush_it():
    lcd.clear()
    lcd.putstr("Crushing!!")
    time.sleep(0.5)
    crusher.value(0)
    time.sleep(1)
    lcd.clear()
    lcd.putstr("Retracting!!")
    crusher.value(1)
    time.sleep(2)

def runit():
    lcd.clear()
    lcd.putstr("Drop Payload to Crusher!")
    led1.value(1)
    led2.value(1)
    s1.angle(20,-1)
    s1.home()
    time.sleep(0.5)
    crush_it()
    led1.value(0)
    led2.value(0)
    lcd.clear()

## Beginning of commands ##


# Safety check
if safe_switch.value():
    lcd.clear()
    lcd.putstr('CASE IS OPEN!!  Close and restart...')
    print("CASE IS OPEN!!")
    s1.step(5)
else:
    print("Safety Check Done")
    # Acknowedge power on
    lcd.clear()
    lcd.putstr("Power-On-Self-  Test")
    blink_error()
    compressor.value(0)
    countdown(40)
    compressor.value(1)
    ts = time.time()
    print("Timestamp reset to", str(ts))
    
    # Ensure crusher is retracted at start
    crusher.value(1)
 
    # show dict
    lcd.__dict__
    s1.__dict__

    # Home the rotor
    lcd.clear()
    lcd.putstr("Homing loader   for first time")
    time.sleep(2)
    lcd.clear()
    reset_it()
    # Wait for Start Button
    try:
        while True:
            first = button.value()
            r_first = resetButton.value()
            time.sleep(0.01)
            second = button.value()
            r_second = resetButton.value()
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
                ts = time.time()
                print("Timestamp reset to", str(ts))
                reset_it()
    except KeyboardInterrupt:
        lcd.clear()
        lcd.putstr('Program terminated by KBI')
        crusher.value(1)
        compressor.value(1)
        led1.value(0)
        led2.value(0)