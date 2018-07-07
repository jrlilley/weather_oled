# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import urllib3
import json
import time
import datetime
from math import cos, sin, radians


class OpenWeather:

    def __init__(self):
        self.weatherdata = []
        self.weather = {'temp': 0, 'wind': {'direction': 0, 'speed': 0}}

    @property
    def temp(self):
        return self.weather['temp']

    @property
    def winddir(self):
        return self.weather['wind']['direction']

    @property
    def windspd(self):
        return self.weather['wind']['speed']

    def fetch(self):
        http = urllib3.PoolManager()

        try:
            r = http.request('GET',
                             'http://api.openweathermap.org/data/2.5/weather',
                             fields={'id': '2634552', 'units': 'metric', 'APPID': '19ae2f09393a8f2d9b624ffa5ebb9dee'})
        except:
            print("request failed")
            return False

        data = json.loads(r.data.decode('utf-8'))

        with open("lastpoll.json", "w") as fout:
            json.dump(data, fout)

        try:
            self.weather['temp'] = int(round(data['main']['temp']))
        except NameError:
            print("temp not defined")

        try:
            self.weather['wind']['direction'] = int(round(data['wind']['deg']))
        except NameError:
            print("wind direction not defined")

        try:
            self.weather['wind']['speed'] = int(round(data['wind']['speed']))
        except NameError:
            print("wind speed not defined")

        return True


RST = None  # on the PiOLED this pin isnt used

DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# Input pins:
L_pin = 27
R_pin = 23
C_pin = 4
U_pin = 17
D_pin = 22

A_pin = 5
B_pin = 6


def setup_buttons():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(A_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
    GPIO.setup(B_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
    GPIO.setup(L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
    GPIO.setup(R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
    GPIO.setup(U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
    GPIO.setup(D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
    GPIO.setup(C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up


def drawwind(di, fnt, direction, speed):
    coords = [(0, 10, 0, 18), (0, 18, -4, 14), (0, 18, 4, 14)]
    di.ink = 1
    ox = 100
    oy = 20
    m = 1

    wind_blowing_to = (direction + 180) % 360

    for n in coords:
        (x1, y1, x2, y2) = n
        (x1, y1) = rot(wind_blowing_to, x1, y1)
        (x2, y2) = rot(wind_blowing_to, x2, y2)
        di.line((ox + x1 * m, oy + y1 * m, ox + x2 * m, oy + y2 * m))

    di.ellipse((ox - 10, oy - 10, ox + 10, oy + 10))
    di.text((ox, oy - 5), str(speed), font=fnt)


def histo(di, xy, pc):
    di.ink = 1
    di.rectangle(xy, fill=0, outline=1)
    (x1, y1, x2, y2) = xy
    x2 = int((x2 - x1) * pc / 100)
    xy = (x1, y1, x2, y2)
    di.rectangle(xy, fill=1, outline=1)


def rot(d, x, y):
    r = radians(d)
    c = cos(r)
    s = sin(r)
    x1 = x * c + y * s
    y1 = x * s - y * c
    return [int(round(x1)), int(round(y1))]


# ------- MAIN --------

setup_buttons()

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.

width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

smallfont = ImageFont.load_default()
# smallfont = ImageFont.truetype('vcr.ttf', 21)
font = ImageFont.truetype('vcr.ttf', 42)

failcount = 0
refreshtimer = updatetimer = failtimer = time.monotonic()
# timer is one hour
TIMERCONST = 3600
TIMERCONSTSHORT = 300
wheel = "|/-\\"
wheeloffset = 0
# inital values will be read when we initialise the weather class
timer = 0
a_pressed = a_clicked = a_up = False
b_pressed = b_clicked = b_up = False
message = "boot"

weather = OpenWeather()

while True:

    if time.monotonic() > (updatetimer + timer):
        if weather.fetch():
            timer = TIMERCONST
            updatetimer = time.monotonic()
            message = "OK"
            failcount = 0
        else:
            timer = TIMERCONSTSHORT
            message = "fail"
            failcount += 1
            updatetimer = time.monotonic()

    if time.monotonic() > (refreshtimer + 1):
        disp.clear()
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        date = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M %d-%b-%y")
        draw.text((x, top), str(weather.temp), font=font, fill=255)
        draw.text((x, top + 40), str(date), font=smallfont, fill=255)
        draw.text((x + 96, top + 40), str(message), font=smallfont, fill=255)
        draw.text((x, top + 50), str(failcount), font=smallfont, fill=255)
        draw.text((x + 50, top + 50), str(wheel[wheeloffset]), font=smallfont, fill=255)
        wheeloffset += 1
        wheeloffset = (wheeloffset % 4)
        # Display image.
        drawwind(draw, smallfont, weather.winddir, weather.windspd)
        histo(draw, (1, 60, 127, 63), ((updatetimer + timer - time.monotonic()) / TIMERCONST * 100))
        disp.image(image.transpose(Image.ROTATE_180))
        disp.display()
        refreshtimer = time.monotonic()

    if not GPIO.input(A_pin):
        a_pressed = True
        a_up = False
    else:
        a_up = True

    if a_up and a_pressed:
        a_clicked = True
        a_pressed = False

    if a_clicked:
        print("button A was pressed and released")
        timer = 0
        a_clicked = False

    if not GPIO.input(B_pin):
        b_pressed = True
        b_up = False
    else:
        b_up = True

    if b_up and b_pressed:
        b_clicked = True
        b_pressed = False

    if b_clicked:
        print("button B was pressed and released")
        timer -= 500
        b_clicked = False

    time.sleep(.01)