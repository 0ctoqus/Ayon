# MicroPython SSD1306 OLED driver, I2C and SPI interfaces

import time
import framebuf

from math import ceil


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


class Segment:
    def __init__(self, x, y, width, height):
        # crash without is it height if == 2
        width = int(ceil(width / 8.0)) * 8
        height = int(ceil(height / 8.0)) * 8

        self.buffer = bytearray(height * width // 8)
        # print("bytes", len(memoryview(self.buffer)))
        self.framebuf = framebuf.FrameBuffer1(
            memoryview(self.buffer), width, height, framebuf.MONO_HMSB
        )
        self.framebuf.fill(0)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        """
        print(
            "creating segment",
            "x",
            self.x,
            "y",
            self.y,
            "w",
            self.width,
            "h",
            self.height,
        )
        """


class SSD1306:
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        # Note the subclass must initialize self.framebuf to a framebuffer.
        # This is necessary because the underlying data buffer is different
        # between I2C and SPI implementations (I2C needs an extra byte).
        self.poweron()
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR,
            0x00,  # horizontal
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

    def merge_framebuff(self, segment):
        # print("blit at pos", segment.x, segment.y)
        self.framebuf.blit(segment.framebuf, segment.x, segment.y)

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, segment, x, y, col):
        segment.framebuf.pixel(x, y, col)

    def text(self, segment, string, col=1):
        segment.framebuf.text(string, 0, 0, col)

    def line(self, segment, x2, y2, col=1):
        segment.framebuf.line(0, 0, x2, y2, col)

    def scroll(self, segment, dx, dy):
        segment.framebuf.scroll(dx, dy)

    def rect(self, segment, w, h, fill=True, col=1):
        # print("rect:", w, h)
        if fill:
            segment.framebuf.fill_rect(0, 0, w, h, col)
        else:
            segment.framebuf.rect(0, 0, w, h, col)

        """
    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def line(self, x1, y1, x2, y2, col=1):
        self.framebuf.line(x1, y1, x2, y2, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def rect(self, x, y, w, h, fill=True, col=1):
        if fill:
            self.framebuf.fill_rect(x, y, w, h, col)
        else:
            self.framebuf.rect(x, y, w, h, col)

    # Does not work, srolling create weird glitchs for non scrolling part of the screen.
    # Also, you can't have more characters than the lenght of the screen moving making this useless.

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

    # This is for the diagonal scroll, it shows wierd actifacts on the lcd!!
    def hw_scroll_diag(self, direction=True):   # default to scroll verticle and right
        self.write_cmd(SET_HWSCROLL_OFF)  # turn off hardware scroll per SSD1306 datasheet
        if not direction:
            self.write_cmd(SET_HWSCROLL_VL)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x07) # start page = page 7
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x00) # end page = page 0
            self.write_cmd(self.height)
        else:
            self.write_cmd(SET_HWSCROLL_VR)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x00) # start page = page 0
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x07) # end page = page 7
            self.write_cmd(self.height)

        self.write_cmd(0x00)
        self.write_cmd(0xff)
        self.write_cmd(SET_HWSCROLL_ON) # activate scroll

    def scroll_text(sc):
        sc.set_memory(
            name="testtest",
            elem_type="str",
            content=(0, 2, "123456789ABCDEFGHIJKLM"),
            update=False,
        )
        sc.oled.hw_scroll_h(direction=False, start_page=2, end_page=2)
        sc.oled.show(start_page=0x02, end_page=0x02)
    """


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        # Add an extra byte to the data buffer to hold an I2C data/command byte
        # to use hardware-compatible I2C transactions.  A memoryview of the
        # buffer is used to mask this byte from the framebuffer operations
        # (without a major memory hit as memoryview doesn't copy to a separate
        # buffer).
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

    def write_framebuf(self):
        # Blast out the frame buffer using a single I2C transaction to support
        # hardware I2C interfaces.
        self.i2c.writeto(self.addr, self.buffer)

    def poweron(self):
        pass
