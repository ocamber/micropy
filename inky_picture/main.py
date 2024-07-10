import gc
import jpegdec
from urllib import urequest
from ujson import load
import time
import uos
from machine import Pin, SPI, PWM, ADC
import sdcard
from picographics import PicoGraphics
from picographics import DISPLAY_INKY_FRAME as DISPLAY

print('INITIALIZE...')
graphics = None
WIDTH = 600
HEIGHT = 448

SD_MOUNTPOINT = "/sd"
#FILENAME = "/sd/A_Sunday_on_la_Grande_Jatte.jpg"
FILENAME = "/sd/Bonaventure_Pine.jpg"

def show_error(text):
    graphics.set_pen(4)
    graphics.rectangle(0, 10, WIDTH, 35)
    graphics.set_pen(1)
    graphics.text(text, 5, 16, 400, 2)


print('INTERFACE SETUP...')

### Inky Frame pins
##IF_HOLD_VSYS_EN_PIN = 2
IF_I2C_INT_PSRAM_CS_PIN = 3
IF_MISO = 16
IF_CLK = 18
IF_MOSI = 19
IF_SD_CS = 22
IF_VSYS_DIV3 = 29
IF_VBUS = 'WL_GPIO2'


print('BUTTONS & LEDS...')

import inky_frame
buttons_at_startup = inky_frame.SHIFT_STATE
### Inky Frame bit mask for buttons and wake events
### Pimoroni's ShiftRegister.read returns opposite order and there's
### a lot of confusing discrepancies with ordering in library code
IF_BUTTON_A = 1 << 7
IF_BUTTON_B = 1 << 6
IF_BUTTON_C = 1 << 5
IF_BUTTON_D = 1 << 4
IF_BUTTON_E = 1 << 3
IF_BUTTONS = IF_BUTTON_A | IF_BUTTON_B | IF_BUTTON_C | IF_BUTTON_D | IF_BUTTON_E
IF_RTC_ALARM = 1 << 2
IF_EXTERNAL_TRIGGER = 1 << 1
IF_EINK_BUSY = 1 << 0

### This is dealing with issues related to
### https://github.com/pimoroni/pimoroni-pico/issues/719
def read_buttons():
    """Read value and re-order to match the ordering of wakeup.get_shift_state"""
    sr_buttons_a_lsb = inky_frame.sr.read()
    sr_buttons = 0
    for _ in range(8):
        sr_buttons <<= 1
        sr_buttons += (sr_buttons_a_lsb & 1)
        sr_buttons_a_lsb >>= 1
    return sr_buttons


led_brightness = 0.4
leds_pwm = {inky_frame.LED_BUSY: PWM(Pin(inky_frame.LED_BUSY)),
            inky_frame.LED_WIFI: PWM(Pin(inky_frame.LED_WIFI)),
            inky_frame.LED_A: PWM(Pin(inky_frame.LED_A)),
            inky_frame.LED_B: PWM(Pin(inky_frame.LED_B)),
            inky_frame.LED_C: PWM(Pin(inky_frame.LED_C)),
            inky_frame.LED_D: PWM(Pin(inky_frame.LED_D)),
            inky_frame.LED_E: PWM(Pin(inky_frame.LED_E))}

gc.collect()

def set_led(led, brightness=1, duration=0, flicker=None):
    """Set led brightness with optional pause and flicker frequency."""

    ### led goes off with 65535 for some reason??
    leds_pwm[led].duty_u16(round(brightness * 65534))

    ### min frequency is 8Hz, 1907 is default
    if flicker is not None:
        leds_pwm[led].freq(max(8, flicker if flicker != 0 else 1907))

    if duration:
        time.sleep(duration)
        leds_pwm[led].duty_u16(0)

set_led(inky_frame.LED_B)


print('MOUNT SD...')

sd_spi = SPI(0,
             sck=Pin(IF_CLK, Pin.OUT),
             mosi=Pin(IF_MOSI, Pin.OUT),
             miso=Pin(IF_MISO, Pin.OUT))
sd = sdcard.SDCard(sd_spi, Pin(IF_SD_CS))
uos.mount(sd, SD_MOUNTPOINT)
gc.collect()


print('LOAD JPEG...')

graphics = PicoGraphics(DISPLAY)
gc.collect()

graphics.set_pen(1)
graphics.clear()

try:
    jpeg = jpegdec.JPEG(graphics)
    gc.collect()  # For good measure...
    jpeg.open_file(FILENAME)
    jpeg.decode()
except OSError as osx:
    print('ERROR!')
    print(osx)
    graphics.set_pen(4)
    graphics.rectangle(0, (HEIGHT // 2) - 20, WIDTH, 40)
    graphics.set_pen(1)
    graphics.text("Unable to display image!", 5, (HEIGHT // 2) - 15, WIDTH, 2)

print('UPDATE SCREEN...')

gc.collect()

graphics.update()

