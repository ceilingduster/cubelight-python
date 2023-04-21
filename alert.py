#!/usr/bin/env python
import time
import requests
from datetime import datetime
from enum import Enum
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw, ImageFont


def center_object(size, y_offset=0):
    W, H = (64, 64)
    w, h = size
    return ((W-w)/2, ((H-h)/2)+y_offset)


# define RGB matrix options
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 5
options.parallel = 1
options.hardware_mapping = 'adafruit-hat-pwm'
options.gpio_slowdown = 2

# initialize RGB matrix
matrix = RGBMatrix(options=options)

api_endpoint = "https://api.open-meteo.com/v1/forecast"
location = "San Francisco, CA"
hours = 24
params = {
    "latitude": 37.6180555556,
    "longitude": -122.3786111111,
    "current_weather": True,
    "temperature_unit": "fahrenheit"
}

# {'latitude': 37.78929, 'longitude': -122.422, 'generationtime_ms': 0.13399124145507812, 'utc_offset_seconds': 0, 'timezone': 'GMT',
# 'timezone_abbreviation': 'GMT', 'elevation': 72.0, 'current_weather': {'temperature': 13.6, 'windspeed': 9.7, 'winddirection': 315.0,
# 'weathercode': 0, 'is_day': 1, 'time': '2023-04-19T19:00'}}

response = requests.get(api_endpoint, params=params)
temperature = round(response.json()['current_weather']['temperature'])

weather_im = Image.new("RGB", (320, 64), color='black')
draw = ImageDraw.Draw(weather_im)
font_25 = ImageFont.truetype('fonts/segment.ttf', 25)
font_40 = ImageFont.truetype('fonts/segment.ttf', 40)
font_16 = ImageFont.truetype('fonts/arial.ttf', 16)
font_14 = ImageFont.truetype('fonts/arial.ttf', 14)
font_10 = ImageFont.truetype('fonts/arial.ttf', 10)
segment_18 = ImageFont.truetype('fonts/segment.ttf', 18)

# DO TIME
now = datetime.now()
date = now
ordinal = {1: 'st', 2: 'nd', 3: 'rd'}.get(
    date.day % 10, 'th') if date.day not in (11, 12, 13) else 'th'

# DO SOC TOUR MSG
soc_time = "CLOSED"
if date.day == 27:
    if date.hour > 0 and date.hour < 10:
        soc_time = "10:10a"
    elif date.hour > 10 and date.hour < 13:
        soc_time = "1p"
else:
    if date.hour > 0 and date.hour < 10:
        soc_time = "10:10a"
    elif date.hour > 10 and date.hour < 15:
        soc_time = "3p"
    elif date.hour > 15 and date.hour < 17:
        soc_time = "4:30p"

# PANEL 1
draw.text((72, 8), "%sF" % str(temperature), font=font_40)
draw.text((71, 45), "@SFO", fill=(150, 150, 150), font=font_16)

# PANEL 2
time_text = '{d:%l}:{d.minute:02}{d:%p}'.format(d=now).replace("M", "")
date_text = "%s%s" % (date.day, ordinal)
month_text = date.strftime("%b")
draw.text((135, 4), time_text, font=segment_18)
draw.text((150, 25), "SOC", font=font_10)
draw.text((150, 35), "Tour", font=font_10)

(x, y) = center_object(font_14.getsize(soc_time), y_offset=22)
draw.text((x+128, y), soc_time, font=font_14)

# PANEL 3
draw.text((200, 8), "%sF" % str(temperature), font=font_40)
draw.text((199, 45), "@SFO", fill=(150, 150, 150), font=font_16)

# PANEL 4
draw.text((263, 4), time_text, font=segment_18)
draw.text((278, 25), "SOC", font=font_10)
draw.text((278, 35), "Tour", font=font_10)

(x, y) = center_object(font_14.getsize(soc_time), y_offset=22)
draw.text((x+256, y), soc_time, font=font_14)

top_logo = Image.open(
    'images/cisco-logo.jpg').resize((64, 64), resample=Image.NEAREST)
weather_im.paste(top_logo, box=(0, 0, 64, 64))

matrix.SetImage(weather_im)

while True:
    pass
