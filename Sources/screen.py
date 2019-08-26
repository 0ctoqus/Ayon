# Libs
import machine
import utime

# Local libs
from ssd1306 import Segment
from ssd1306 import SSD1306_I2C
import consts as const

# import uasyncio as asyncio


class Screen_Handler:
    def __init__(self):
        # Constants
        print("Init screen Screen_Handler")
        self.screen_columns = 16
        self.screen_spacing = 8
        self.screen_width = 128
        self.screen_height = 64
        self.char_width = int(self.screen_width / self.screen_columns)
        self.char_height = int(self.screen_height / self.screen_spacing) - 1

        print("I2C setup")
        # For small board uncomment this
        pin16 = machine.Pin(16, machine.Pin.OUT)
        # set reset Pin hight
        pin16.value(1)
        machine.Pin(16, machine.Pin.OUT).value(1)
        self.i2c = machine.I2C(scl=machine.Pin(15), sda=machine.Pin(4))

        # self.i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))

        print("OLED setup")
        self.oled = SSD1306_I2C(self.screen_width, self.screen_height, self.i2c)
        self.oled.fill(0)
        self.memory_index = {}

        # Array of functions for displayable elements
        self.displayables = {
            "str": self.display_str,
            "pixel": self.display_pixel,
            "line": self.display_line,
            "rect": self.display_rect,
        }

        # Pixel arts
        self.pixel_art = {
            "up_arrow": [
                "001100",
                "011110",
                "111111",
                "001100",
                "001100",
                "001100",
                "001100",
            ],
            "cross": [
                "100001",
                "110011",
                "011110",
                "001100",
                "011110",
                "110011",
                "100001",
            ],
            "check": [
                "000001",
                "000001",
                "000011",
                "000010",
                "110110",
                "011100",
                "001100",
            ],
            "thunder": [
                "011110",
                "111111",
                "111111",
                "011110",
                "000100",
                "001100",
                "001000",
            ],
            "rain": [
                "011110",
                "111111",
                "111111",
                "011110",
                "010010",
                "001001",
                "010010",
            ],
            "snow": [
                "011110",
                "111111",
                "111111",
                "011110",
                "101010",
                "010101",
                "101010",
            ],
            "mist": [
                "011110",
                "111111",
                "111111",
                "011110",
                "000111",
                "111000",
                "000111",
            ],
            "clear": [
                "011110",
                "111111",
                "111111",
                "111111",
                "111111",
                "011110",
                "000000",
            ],
            "clouds": [
                "001110",
                "011111",
                "011111",
                "110001",
                "100001",
                "100001",
                "011110",
            ],
            "celcius": [
                "011000",
                "100000",
                "100000",
                "011000",
                "000000",
                "000000",
                "000000",
            ],
        }

        # Top line
        self.set_memory(
            name="line_top",
            elem_type="rect",
            content=(0, self.height_to_pixel(2) - 7, self.screen_width, 2, True, 1),
        )

        # Bottom line
        self.set_memory(
            name="line_bottom",
            elem_type="rect",
            content=(0, self.height_to_pixel(6) + 5, self.screen_width, 2, True, 1),
        )

    def width_to_pixel(self, x):
        return int(self.screen_width / self.screen_columns * x)

    def height_to_pixel(self, y):
        return int(self.screen_height / self.screen_spacing * y)

    def pixel_to_width(self, x):
        return int(x / (self.screen_width / self.screen_columns))

    def pixel_to_height(self, y):
        return int(y / (self.screen_height / self.screen_spacing))

    # x, y, string
    def display_str(self, elem):
        x, y, string = elem
        x1 = self.width_to_pixel(x)
        y1 = self.height_to_pixel(y)
        x2 = (len(string) + 1) * self.char_width
        y2 = y1 + self.char_height

        segment = Segment(x1, y1, x2 - x1, y2 - y1)
        self.oled.text(segment, string)
        return segment

    # x, y, content_name
    def display_pixel(self, elem):
        x, y, content_name = elem
        x1 = self.width_to_pixel(x)
        y1 = self.height_to_pixel(y)
        art = self.pixel_art[content_name]

        y2 = 0
        segment = Segment(x1, y1, len(art[0]), len(art))
        for pixel_str in self.pixel_art[content_name]:
            x2 = 0
            for pixel in pixel_str:
                if pixel == "1":
                    self.oled.pixel(segment, x2, y2, 1)
                x2 += 1
            y2 += 1
        return segment

    # x1, y1, x2, y2
    def display_line(self, elem):
        x1, y1, x2, y2 = elem
        segment = Segment(x1, y1, x2 - x1, y2 - y1)
        self.oled.line(segment, x2, y2)
        return segment

    # x, y, width, height, fill, col
    def display_rect(self, elem):
        x, y, width, height, fill, col = elem
        segment = Segment(x, y, width, height)
        self.oled.rect(segment, width, height, fill, col)
        return segment

    def set_memory(
        self, name, elem_type=None, content=None, scroll=False, delete=False
    ):
        # Reset zone and delete element if needed
        if (delete or scroll) and name in self.memory_index:
            self.oled.reset_zone(self.memory_index[name])
            if delete or self.memory_index[name].needs_reset:
                del self.memory_index[name]

        # Create element if needed and display
        if elem_type is not None and content is not None:
            if name not in self.memory_index:
                segment = self.displayables[elem_type](content)
            else:
                segment = self.memory_index[name]
            self.oled.merge_framebuff(segment)
            if scroll:
                self.oled.scroll(segment)
            self.memory_index[name] = segment

        # def get_async(self):
        #     while True:
        #         # print("screen update")
        #         # Set time
        #         localtime = utime.localtime()
        #         date = " " + "%02d" % localtime[2] + "/" + "%02d" % localtime[1]
        #         time = (
        #             "%02d" % localtime[3]
        #             + ":"
        #             + "%02d" % localtime[4]
        #             + ":"
        #             + "%02d" % localtime[5]
        #         )
        #         self.set_memory(
        #             name="date",
        #             elem_type="str",
        #             content=(1, 0, time + " " + date),
        #             update=True,
        #             delete=True,
        #         )
        #         # self.oled.show()
        #         utime.sleep(const.MAIN_CYCLE_TIME)


class Screen_element:
    def __init__(self, ntw, sc, max_time_check):
        self.ntw = ntw
        self.sc = sc
        self.next_time_check = 0
        self.time_diff = 0
        self.max_time_check = max_time_check

    # async def get_async(self):
    #    while True:
    #        if self.ntw.connected:
    #            self.get()
    #            wait_time = self.max_time_check
    #        else:
    #            wait_time = const.MAIN_CYCLE_TIME
    #        await asyncio.sleep(wait_time)

    # def get_async(self):
    #     while True:
    #         if self.ntw.connected:
    #             self.get()
    #             wait_time = self.max_time_check
    #         else:
    #             wait_time = const.MAIN_CYCLE_TIME
    #         utime.sleep(wait_time)

    def check(self, now):
        if self.next_time_check - now < 0:  # and self.ntw.connected:
            if self.get():
                self.next_time_check = utime.time() + self.max_time_check
            else:
                self.next_time_check = utime.time() + const.MAIN_CYCLE_TIME * 10
