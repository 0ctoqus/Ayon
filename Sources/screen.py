# Libs
import machine
import utime

# Local libs
import ssd1306
import uasyncio as asyncio

# Local scripts
import consts as const


class Screen_Handler:
    def __init__(self):
        # Constants
        self.screen_columns = 16
        self.screen_spacing = 8
        self.screen_width = 128
        self.screen_height = 64
        self.char_width = int(self.screen_width / self.screen_columns)
        self.char_height = int(self.screen_height / self.screen_spacing)

        # For small board uncomment this
        # pin16 = machine.Pin(16, machine.Pin.OUT)
        # pin16.value(1) # set reset Pin hight
        # machine.Pin(16, machine.Pin.OUT).value(1)
        # self.i2c = machine.I2C(scl=machine.Pin(15), sda=machine.Pin(4))

        self.i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))

        self.oled = ssd1306.SSD1306_I2C(self.screen_width, self.screen_height, self.i2c)
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

    def width_to_pixel(self, x):
        return int(self.screen_width / self.screen_columns * x)

    def height_to_pixel(self, y):
        return int(self.screen_height / self.screen_spacing * y)

    def reset_zone(self, x1, y1, x2, y2):
        self.oled.rect(x1, y1, x2 - x1, y2 - y1, True, 0)

    def display_str(self, elem):
        x1, y1, string = elem
        x1 = self.width_to_pixel(x1)
        y1 = self.height_to_pixel(y1)
        x2 = (len(string) + 1) * self.char_width
        y2 = self.char_height
        self.reset_zone(x1, y1, x2, y2)
        self.oled.text(string, x1, y1)
        return (x1, y1, x2, y2)

    def display_pixel(self, elem):
        x1, y1, content_name = elem
        x1 = self.width_to_pixel(x1)
        y1 = self.height_to_pixel(y1)
        art = self.pixel_art[content_name]
        self.reset_zone(x1, y1, len(art[0]), len(art))
        y2 = y1
        for pixel_str in self.pixel_art[content_name]:
            x2 = x1
            for pixel in pixel_str:
                if pixel == "1":
                    self.oled.pixel(x2, y2, 1)
                x2 += 1
            y2 += 1
        return (x1, y1, x2, y2)

    def display_line(self, elem):
        x1, y1, x2, y2 = elem
        self.reset_zone(x1, y1, x2, y2)
        self.oled.line(x1, y1, x2, y2)
        return (x1, y1, x2, y2)

    def display_rect(self, elem):
        x1, y1, x2, y2, fill, col = elem
        self.reset_zone(x1, y1, x2, y2)
        self.oled.rect(x1, y1, x2 - x1, y2 - y1, fill, col)
        return (x1, y1, x2, y2)

    def set_memory(self, name, elem_type=None, content=None, delete=False):
        # Delete element
        if delete and name in self.memory_index:
            x1, y1, x2, y2 = self.memory_index[name]
            self.reset_zone(x1, y1, x2, y2)
            del self.memory_index[name]
        if elem_type is not None and content is not None:
            elems = tuple(list(content))
            self.memory_index[name] = self.displayables[elem_type](content)

    def update_display(self):
        self.oled.show()

    async def get_async(self):
        while True:
            self.update_display()
            await asyncio.sleep_ms(int(const.MAIN_CYCLE_TIME * 1000))


class Screen_element:
    def __init__(self, ntw, sc, max_time_check):
        self.ntw = ntw
        self.sc = sc
        self.last_time_check = 0
        self.time_diff = 0
        self.max_time_check = max_time_check

    async def get_async(self):
        while True:
            if self.ntw.connected:
                self.get()
                wait_time = self.max_time_check
            else:
                wait_time = const.MAIN_CYCLE_TIME
            await asyncio.sleep(wait_time)
