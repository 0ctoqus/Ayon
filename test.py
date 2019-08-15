from machine import Pin, I2C
import time
import framebuf

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)
SET_HWSCROLL_OFF = const(0x2E)
SET_HWSCROLL_ON = const(0x2F)
SET_HWSCROLL_RIGHT = const(0x26)
SET_HWSCROLL_LEFT = const(0x27)
# SET_HWSCROLL_VR     = const(0x29)
# SET_HWSCROLL_VL     = const(0x2a)


class SSD1306:
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.poweron()
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR | 0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.height == 32 else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_framebuf()
        # self.write_data(self.buffer)

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def line(self, x1, y1, x2, y2, col=1):
        self.framebuf.line(x1, y1, x2, y2, col)

    def rect(self, x, y, w, h, fill=True, col=1):
        if fill:
            self.framebuf.fill_rect(x, y, w, h, col)
        else:
            self.framebuf.rect(x, y, w, h, col)

    def clear(self):
        self.fill(0)
        self.show()

    def hw_scroll_off(self):
        self.write_cmd(SET_HWSCROLL_OFF)  # turn off scroll

    def hw_scroll_h(self, direction=True, start_page=0x00, end_page=0x07):
        # default to scroll right
        self.write_cmd(SET_HWSCROLL_OFF)
        # turn off hardware scroll per SSD1306 datasheet
        if not direction:
            self.write_cmd(SET_HWSCROLL_LEFT)
            self.write_cmd(0x00)  # dummy byte
            self.write_cmd(start_page)  # start page = page 7
            self.write_cmd(0x00)  # frequency = 5 frames
            self.write_cmd(end_page)  # end page = page 0
        else:
            self.write_cmd(SET_HWSCROLL_RIGHT)
            self.write_cmd(0x00)  # dummy byte
            self.write_cmd(start_page)  # start page = page 0
            self.write_cmd(0x00)  # frequency = 5 frames
            self.write_cmd(end_page)  # end page = page 7

        self.write_cmd(0x00)
        self.write_cmd(0xFF)
        self.write_cmd(SET_HWSCROLL_ON)  # activate scroll


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.buffer = bytearray(((height // 8) * width) + 1)
        self.buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
        self.framebuf = framebuf.FrameBuffer1(
            memoryview(self.buffer)[1:], width, height
        )
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    # def write_data(self, buf):
    #    self.temp[0] = self.addr << 1
    #    self.temp[1] = 0x40  # Co=0, D/C#=1
    #    self.i2c.start()
    #    self.i2c.write(self.temp)
    #    self.i2c.write(buf)
    #    self.i2c.stop()

    def write_framebuf(self):
        # Blast out the frame buffer using a single I2C transaction to support
        # hardware I2C interfaces.
        self.i2c.writeto(self.addr, self.buffer)

    def poweron(self):
        pass


def lcdInit():
    # I2C pins
    # I have 4k7 pull ups on scl and sda
    # set up I2C on gpio 14 and 16
    i2c = I2C(scl=Pin(4), sda=Pin(5))
    lcd = SSD1306_I2C(128, 64, i2c)  # lcd is 128x32
    return lcd


def main():

    display = lcdInit()
    display.clear()
    print("in main")
    display.clear()
    while True:
        display.text("Satic", 0, 0)
        display.text("-----", 0, 1 * 8)
        display.text("Hello World", 0, 2 * 8)
        display.text("-----", 0, 6 * 8)
        display.text("Static", 0, 7 * 8)
        display.show()
        # scroll right
        display.hw_scroll_h(direction=True, start_page=0x02, end_page=0x05)
        time.sleep(3)

        # scroll left
        display.hw_scroll_h(direction=False, start_page=0x02, end_page=0x05)

        time.sleep(3)

        display.hw_scroll_off()
        # time.sleep(3)
        # display.clear()
        # time.sleep(1)


main()
