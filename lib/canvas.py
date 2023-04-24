import io
import base64
import requests
from datetime import datetime
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from timeit import default_timer


class SignCanvas:
    def __init__(self):
        # Hardcoded matrix config; commandline args ignored
        self.options = RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 5
        self.options.parallel = 1
        self.options.brightness = 100
        self.options.hardware_mapping = "adafruit-hat-pwm"
        self.options.pixel_mapper_config = ""
        self.options.gpio_slowdown = 4
        #self.options.show_refresh_rate = 1
        self.abort = False
        self.e = None
        self.mqtt_client = None

        self._width = (self.options.rows*5)
        self._height = self.options.cols
        self._sides_image = Image.new(
            "RGBA", (self._width - self.options.cols, self._height), color='black')
        self._top_image = Image.new(
            "RGBA", (self.options.cols, self.options.rows), color='black')
        self._buffer = Image.new(
            "RGB", (self.options.cols * self.options.chain_length, self.options.rows), color='black')

        # setup the matrix
        self.matrix = RGBMatrix(options=self.options)
        self.offset_canvas = self.matrix.CreateFrameCanvas()

    def decode_img(self, msg, width=64, height=64):
        try:
            msg = base64.b64decode(msg)
            buf = io.BytesIO(msg)
            im = Image.open(buf)
            return im
        except:
            im = Image.new("RGB", size=(width, height))
            draw = ImageDraw.Draw(im)
            draw.text((0, 0), text="Invalid", fill=(255, 0, 0))
            draw.text((0, 10), text="image.", fill=(255, 0, 0))
            return im

    def _center_object(self, canvas, size, y_offset=0):
        W, H = canvas.size
        w, h = size
        return ((W-w)/2, ((H-h)/2)+y_offset)

    def _center_panel(self, size, y_offset=0):
        W, H = (64, 64)
        w, h = size
        return ((W-w)/2, ((H-h)/2)+y_offset)

    def sleep(self, seconds):
        start = default_timer()
        while True:
            if default_timer() - start >= seconds:
                break
            if self.abort:
                self.abort = False
                return None

    def set_top_time(self):
        time_im = Image.new("RGBA", self._top_image.size, color='black')
        draw = ImageDraw.Draw(time_im)
        font = ImageFont.truetype('fonts/pretend.otf', 13)
        now = datetime.now()
        text = '{d:%l}:{d.minute:02}{d:%p}'.format(d=now)
        draw.text(self._center_object(self._top_image,
                  font.getsize(text)), text, font=font)
        self._top_image = time_im

    def _get_ordinal_suffix(self, day):
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') if day not in (11, 12, 13) else 'th'

    def set_top_date(self):
        time_im = Image.new("RGBA", self._top_image.size, color='black')
        draw = ImageDraw.Draw(time_im)
        font = ImageFont.truetype('fonts/pretend.otf', 13)
        font_big = ImageFont.truetype('fonts/pretend.otf', 18)
        date = datetime.now()
        date_text = "%s%s" % (date.day, self._get_ordinal_suffix(date.day))
        month_text = date.strftime("%b")
        draw.text(self._center_object(self._top_image, font.getsize(
            date_text), y_offset=10), date_text, font=font, fill='white')
        draw.text(self._center_object(self._top_image, font.getsize(
            month_text), y_offset=-10), month_text, font=font_big, fill='red')
        self._top_image = time_im

    def set_top_image(self, image):
        self._top_image = image.resize(self._top_image.size)

    def set_top_image_from_file(self, file_name):
        self.set_top_image(Image.open(file_name))

    def image_open(self, file_name):
        img = Image.open(file_name)
        return img

    def show(self):
        self._buffer.paste(self._top_image, (0, 0))
        self._buffer.paste(self._sides_image, (64, 0))

        self.offset_canvas.SetImage(self._buffer)
        self.offset_canvas = self.matrix.SwapOnVSync(self.offset_canvas)

    def clear_display(self):
        self._sides_image = Image.new(
            "RGBA", (self._width - self.options.cols, self._height), color='black')
        self._top_image = Image.new(
            "RGBA", (self.options.cols, self.options.rows), color='black')
        self._buffer = Image.new(
            "RGB", (self.options.cols * self.options.chain_length, self.options.rows), color='black')
        self.show()

    def get_noc_tours(self, duration):
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

        (x, y) = self._center_panel(font_14.getsize(soc_time), y_offset=22)
        draw.text((x+128, y), soc_time, font=font_14)

        # PANEL 3
        draw.text((200, 8), "%sF" % str(temperature), font=font_40)
        draw.text((199, 45), "@SFO", fill=(150, 150, 150), font=font_16)

        # PANEL 4
        draw.text((263, 4), time_text, font=segment_18)
        draw.text((278, 25), "SOC", font=font_10)
        draw.text((278, 35), "Tour", font=font_10)

        (x, y) = self._center_panel(font_14.getsize(soc_time), y_offset=22)
        draw.text((x+256, y), soc_time, font=font_14)

        top_logo = Image.open(
            'images/cisco-logo.jpg').resize((64, 64), resample=Image.NEAREST)
        weather_im.paste(top_logo, box=(0, 0, 64, 64))

        self.offset_canvas.SetImage(weather_im)
        self._image = weather_im
        self._sides_image = weather_im

        new_image = Image.new(
            "RGBA", (self._width - self.options.cols, self._height), color='black')
        self._image = new_image
        self._top_image = new_image.resize((64, 64), resample=Image.NEAREST)
        self._sides_image = new_image

        self.offset_canvas = self.matrix.SwapOnVSync(self.offset_canvas)

        start = default_timer()
        while True:
            if default_timer() - start >= duration:
                break
            
            if self.abort:
                self.abort = False
                return None

    def get_sides(self):
        return self._image.crop((self.options.cols, 0, self._width, self._height))

    def side_image(self, image, duration=5):
        self._sides_image = image.resize(self._sides_image.size)

    def side_image_from_file(self, file_name, duration=5):
        self.side_image(Image.open(file_name))

    def _circle_centered_coord(self, canvas, size):
        return (int(canvas.width / 2) - size,
                int(canvas.height / 2) - size,
                int(canvas.width / 2) + size,
                int(canvas.height / 2) + size)

    def transition(self, image, sleep_seconds=0.01):
        # has to be same size as _sides_image
        new_image = image.resize(self._sides_image.size)
        for size in range(0, 200, 2):
            # create the mask
            mask_im = Image.new("L", self._sides_image.size, color='white')

            draw = ImageDraw.Draw(mask_im)
            draw.ellipse(self._circle_centered_coord(
                mask_im, size), fill='black')

            im = Image.composite(self._sides_image, new_image, mask_im)
            draw = ImageDraw.Draw(im)
            draw.ellipse(self._circle_centered_coord(
                mask_im, size), width=10, outline=(128, 128, 255))

            self._sides_image = im  # flush back to _sides_image
            self.show()
            self.sleep(sleep_seconds)

    def transition_from_file(self, file_name):
        # has to be same size as _sides_image
        new_image = Image.open(file_name)
        self.transition(new_image)

    def infinite_scroll(self, image, number_loops=1, sleep_seconds=0.05, duration=1, speed=1):
        start = default_timer()

        self._sides_image = image.resize(self._sides_image.size)
        while True:
            for c in range(0, number_loops):
                for i in range(0, self._sides_image.width, speed):
                    if default_timer() - start >= duration:
                        return None

                    if self.abort:
                        self.abort = False
                        return None

                    front_crop = self._sides_image.crop(
                        (0, 0, speed, self._sides_image.height))
                    back_crop = self._sides_image.crop(
                        (speed, 0, self._sides_image.width, self._sides_image.height))
                    self._sides_image.paste(back_crop, (0, 0))
                    self._sides_image.paste(front_crop, (back_crop.width, 0))
                    self.show()
                    self.sleep(sleep_seconds)

    def infinite_scroll_from_file(self, file_name, number_loops=1, sleep_seconds=0.05):
        self.infinite_scroll(Image.open(file_name),
                             number_loops, sleep_seconds)
