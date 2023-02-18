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
from gpiozero import Button, LED, Motor, DigitalOutputDevice

sleep(1.5)
home_pin = 23
start_pin = 20
reset_pin = 16
load_pin = 8
retract_pin = 7
l1 = 17
l2 = 21
disp_sda = 2
disp_scl = 3
crushPin = 19
compPin = 13
case_safety = 24
ts = ti()
nts = ''

# Non-Class devices
led1 = LED(l1)
led2 = LED(l2)
home_switch = Button(home_pin, pull_up=True)
safe_switch = Button(case_safety, pull_up=True)
start_button = Button(start_pin, pull_up=True)
reset_button = Button(reset_pin, pull_up=True)
loader = Motor(load_pin, retract_pin)
crusher = DigitalOutputDevice(crushPin, active_high=False, initial_value=False)
crusher.off()
compressor = DigitalOutputDevice(compPin, active_high=False, initial_value=False)
compressor.off()

### Instantiate classes
# Create display instance
lcd = drivers.Lcd()

def switch_test():
    try:
        while True:
            if start_button.is_pressed:
                lcd.lcd_clear()
                lcd.lcd_display_string('Start Pressed', 1)
            else:
                lcd.lcd_clear()
                lcd.lcd_display_string('Start released', 1)
            sleep(2)
            if reset_button.is_pressed:
                lcd.lcd_clear()
                lcd.lcd_display_string('Reset Pressed', 1)
            else:
                lcd.lcd_clear()
                lcd.lcd_display_string('Reset released', 1)
            sleep(2)
            if safe_switch.is_pressed:
                lcd.lcd_clear()
                lcd.lcd_display_string('Safe Pressed', 1)
            else:
                lcd.lcd_clear()
                lcd.lcd_display_string('Safe released', 1)
            sleep(2)
            if home_switch.is_pressed:
                lcd.lcd_clear()
                lcd.lcd_display_string('Home Pressed', 1)
            else:
                lcd.lcd_clear()
                lcd.lcd_display_string('Home released', 1)
            sleep(2)
    except KeyboardInterrupt:
        # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
        print("Cleaning up!")
        display.lcd_clear()
        lcd.lcd_display_string('Exiting debug', 1)
        sleep(3)
        display.lcd_clear()

def is_safe():
    if safe_switch.is_pressed:
        lcd.lcd_clear()
        lcd.lcd_display_string('Rotator Jammed', 1)
        print("Rotator is Jammed!")
        sys.exit()
    else:
        lcd.lcd_clear()
        lcd.lcd_display_string('Safe to Run', 1)
        print("Safe to run")
        return True

def home():
    is_safe()
    global ts
    looptime = ti()
    try:
        led1.on()
        if load_can():
            # Add pressure check function here later
            compressor.on()
            countdown(need_pressure())
            crush_it()
            compressor.off()
        else:
            if not safe_switch.is_pressed:
                print('Safe Passed')
                lcd.lcd_clear()
                lcd.lcd_display_string('Loader ready', 1)
                lcd.lcd_display_string('Green first!', 2)
                compressor.off()
                blink()
                return True
            else:
                print('Home function timed out')
                lcd.lcd_clear()
                lcd.lcd_display_string('Timeout...', 1)
                blink_error()
                return False
    except KeyboardInterrupt:
        print('Program terminated by KBI')
        led1.off()
        return False

def load_can():
    if is_safe():
        sleep(1)
        lcd.lcd_clear()
        lcd.lcd_display_string('Safe passed', 1)
    can_there = False
    can_loaded = False
    lcd.lcd_clear()
    delay = ti() + 3
    while not home_switch.is_pressed:
        loader.forward()
        sleep(0.25)
        if ti() > delay:
            print('Loader Jammed!')
            lcd.lcd_clear()
            lcd.lcd_display_string('Timeout reached!', 1)
            lcd.lcd_display_string('Loader Jammed!', 2)
            back_off()
            return False
        if can_there and not safe_switch.is_pressed:
            can_loaded = True
            print('Can Loaded')
            lcd.lcd_clear()
            lcd.lcd_display_string('Can Loaded', 1)
        elif safe_switch.is_pressed:
            can_there = True
            print('Can Found')
            lcd.lcd_clear()
            lcd.lcd_display_string('Can Found', 1)
        else:
            print('Keep Moving')
    unhome()
    sleep(0.25)
    if can_there and not safe_switch.is_pressed:
        can_loaded = True
        print('Can Loaded')
        lcd.lcd_clear()
        lcd.lcd_display_string('Can Loaded', 1)
    if can_there and can_loaded:
        return True
    else:
        return False

def back_off():
    loader.backward()
    sleep(0.5)
    loader.stop()

def unhome():
    print("unhoming")
    loader.forward()
    home_switch.wait_for_release()
    loader.stop()

def f_inch(val=0.25):
    loader.forward()
    sleep(val)
    loader.stop()

def b_inch(val=0.25):
    loader.reverse()
    sleep(val)
    loader.stop()

def crush_it():
    print("Crushing")
    lcd.lcd_clear()
    lcd.lcd_display_string("Crushing!!", 1)
    compressor.off()
    sleep(0.5)
    crusher.on()
    sleep(1)
    # lcd.lcd_clear()
    print("Retracting")
    lcd.lcd_display_string("Retracting!!", 2)
    crusher.off()
    sleep(0.5)
    lcd.lcd_clear()
    lcd.lcd_display_string("Crush Complete", 1)
    compressor.on()
    sleep(2)

def blink():
    print("blink")
    led1.blink(on_time=0.07, off_time=0.07, n=10, background=False)
    led2.blink(on_time=0.07, off_time=0.07, n=10, background=False)

def blink_error():
    print("blink_error")
    led1.blink(on_time=0.5, off_time=0.5, n=3, background=False)
    led2.blink(on_time=0.5, off_time=0.5, n=3, background=False)

def countdown(n):
    while n>0:
        print(str(n), 'seconds left')
        lcd.lcd_clear()
        thisSecond = str(n)
        lcd.lcd_display_string( 'Pressurizing....', 1)
        thisMessage = ''
        thisMessage = str('Countdown = ' + str(n))
        lcd.lcd_display_string(thisMessage, 2)
        n = n -1
        sleep(0.8)

def need_pressure():
    nts = ti()
    time_diff = nts - ts
    if time_diff >= 36000:
        print("Time greater than 10 hours")
        return 40
    elif time_diff <= 600:
        print("Time less than 10 min")
        return 5
    else:
        print("time_diff = ", str(time_diff))
        print("Calculating required time...")
        pressure_time_ratio = round(time_diff / 1200)
        return pressure_time_ratio

def runCycler():
    global ts
    # Add pressure check function here later
    compressor.on()
    countdown(need_pressure())
    crush_it()
    led1.on()
    led2.on()
    while load_can():
        crush_it()
        sleep(4)
    else:
        lcd.lcd_clear()
        lcd.lcd_display_string("No more cans!!", 1 )
        lcd.lcd_display_string("Reset in 10 sec", 2)
        sleep(10)
        compressor.off()
    ts = ti()
    print("Timestamp reset to", str(ts))
    lcd.lcd_clear()
    lcd.lcd_display_string('Loader ready', 1)
    lcd.lcd_display_string('Green first!', 2)
    led1.off()
    led2.off()


## Beginning of commands ##
# Safety check
is_safe()
print("Safety Check Done")
# Acknowedge power on
lcd.lcd_clear()
lcd.lcd_display_string("Power-On-", 1)
lcd.lcd_display_string("Self-Test", 2)
sleep(1)
compressor.on()
countdown(30)
compressor.off()
ts = ti()
print("Timestamp reset to", str(ts))

# Ensure crusher is retracted at start
crusher.off()

# Home the rotor
lcd.lcd_clear()
lcd.lcd_display_string("Homing loader", 1)
lcd.lcd_display_string("for first time", 2)
sleep(2)
lcd.lcd_clear()
home()
# Wait for Start Button
try:
    while True:
        first = start_button.value
        r_first = reset_button.value
        sleep(0.01)
        second = start_button.value
        r_second = reset_button.value
        if first and not second:
            lcd.lcd_clear()
            lcd.lcd_display_string('Start pressed!', 1)
        elif not first and second:
            lcd.lcd_clear()
            lcd.lcd_display_string('Start released!', 1)
            runCycler()
        elif r_first and not r_second:
            lcd.lcd_clear()
            lcd.lcd_display_string('Reset Pressed', 1)
        elif not r_first and r_second:
            lcd.lcd_clear()
            lcd.lcd_display_string('Reset released', 1)
            compressor.on()
            want_pressure = need_pressure()
            if want_pressure < 15:
                want_pressure = 15
            countdown(want_pressure)
            runCycler()
            compressor.off()
            ts = ti()
            print("Timestamp reset to", str(ts))
            lcd.lcd_clear()
            lcd.lcd_display_string('Loader ready', 1)
            lcd.lcd_display_string('Red To Start', 2)

except KeyboardInterrupt:
    lcd.lcd_clear()
    lcd.lcd_display_string('Program Stop', 1)
    lcd.lcd_display_string('by KBI',2)
    loader.stop()
    crusher.off()
    compressor.off()
    blink_error()
    led1.off()
    led2.off()
