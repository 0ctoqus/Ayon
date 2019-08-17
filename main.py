# Libs
import machine

# import esp32
# from math import ceil
import utime
import _thread

# Local libs
# import uasyncio as asyncio

# Local scripts
from screen import Screen_element
from screen import Screen_Handler
from internet import Network
import consts as const
from google import Google


# https://docs.python.org/3.5/library/_thread.html#module-_thread
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/thread_example_1
# _thread.start_new_thread(google.get, (now,))

# https://github.com/peterhinch/micropython-async/blob/master/TUTORIAL.md#01-installing-uasyncio-on-bare-metal
# https://forum.micropython.org/viewtopic.php?f=2&t=2876&start=10
# https://github.com/peterhinch/micropython-mqtt/tree/master/mqtt_as


class Clock(Screen_element):
    def __init__(self, ntw, sc, max_time_check):
        Screen_element.__init__(self, ntw, sc, max_time_check)
        self.url = const.CLOCK_URL
        self.tm = None

    def get(self):
        print("Getting time")
        time_data = self.ntw.request("GET", self.url)
        if time_data is not None:
            unix_timestamp = (
                int(time_data["unixtime"]) - 946684800 + 3600 * const.CLOCK_UTC_OFFSET
            )
            is_set = True
        else:
            unix_timestamp = 0
            is_set = False
        self.tm = utime.localtime(unix_timestamp)
        machine.RTC().datetime(self.tm[0:3] + (0,) + self.tm[3:6] + (0,))
        print("machine time set")
        return is_set

    # async def get_async(self):
    #    next_check = 0
    #    while True:
    #        if self.ntw.connected and utime.time() >= next_check:
    #            if self.set():
    #                next_check = utime.time() + self.max_time_check
    #        self.get()
    #        await asyncio.sleep(const.MAIN_CYCLE_TIME)

    # def get_async(self):
    #    next_check = 0
    #    while True:
    #        if self.ntw.connected and utime.time() >= next_check:
    #            if self.set():
    #                next_check = utime.time() + self.max_time_check
    #        self.get()
    #        utime.sleep(const.MAIN_CYCLE_TIME)


class Weather(Screen_element):
    def __init__(self, ntw, sc, max_time_check):
        Screen_element.__init__(self, ntw, sc, max_time_check)
        self.current_temperature = None
        self.complete_url = (
            const.WEATHER_URL
            + "appid="
            + const.WEATHER_API_KEY
            + "&q="
            + const.WEATHER_CITY
        )
        # https://www.weatherbit.io/api/codes
        self.id_options = {
            2: "thunder",
            3: "rain",
            5: "rain",
            6: "snow",
            7: "mist",
            8: "clouds",
            9: "rain",
        }

    def get(self):
        print("Getting weather")
        WEATHER_data = self.ntw.request("GET", self.complete_url)
        print("Weather response =", WEATHER_data)

        if WEATHER_data is not None and WEATHER_data["cod"] != "404":
            self.WEATHER_description = WEATHER_data["weather"][0]["description"]
            self.WEATHER_id = WEATHER_data["weather"][0]["id"]
            self.current_temperature = round(WEATHER_data["main"]["temp"] - 273.15)
            self.current_pressure = WEATHER_data["main"]["pressure"]
            self.current_humidity = WEATHER_data["main"]["humidity"]

            if self.WEATHER_id == 800:
                self.pixel_art = "clear"
            elif int(self.WEATHER_id / 100) in self.id_options:
                self.pixel_art = self.id_options[int(self.WEATHER_id / 100)]
            else:
                self.pixel_art = "cross"
            result = True
        else:
            print("City Not Found")
            self.WEATHER_description = "None"
            self.WEATHER_id = 0
            self.current_temperature = 0
            self.current_pressure = 0
            self.current_humidity = 0
            self.pixel_art = "cross"
            result = False

        temp_str = str(self.current_temperature)
        y = 7
        self.sc.set_memory(
            name="WEATHER_art",
            elem_type="pixel",
            content=(0, y, self.pixel_art),
            update=True,
        )
        self.sc.set_memory(
            name="WEATHER_temp", elem_type="str", content=(1, y, temp_str), update=True
        )
        self.sc.set_memory(
            name="WEATHER_temp_type",
            elem_type="pixel",
            content=(1 + len(temp_str), y, "celcius"),
            update=True,
        )
        self.sc.set_memory(
            name="WEATHER_humidity",
            elem_type="str",
            content=(2 + len(temp_str), y, str(self.current_humidity) + "%"),
            update=True,
        )
        return result


def scroll_text(sc):
    sc.set_memory(
        name="test", elem_type="str", content=(0, 2, "Hello world"), update=False
    )
    sc.oled.hw_scroll_h(direction=True, start_page=2, end_page=5)
    sc.oled.show(start_page=0x02, end_page=0x05)


def main():
    sc = Screen_Handler()
    ntw = Network(sc, const.NTW_CHECK_TIME)
    clock = Clock(ntw, sc, const.CLOCK_TIME_CHECK)
    weather = Weather(ntw, sc, const.WEATHER_TIME_CHECK)
    # google = Google(ntw, sc, const.GOOGLE_TIME_CHECK)

    # loop = asyncio.get_event_loop()
    # loop.create_task(sc.get_async())
    # loop.create_task(ntw.get_async())
    # loop.create_task(clock.get_async())
    # loop.create_task(weather.get_async())
    # loop.create_task(google.get_async())
    # loop.run_forever()

    # _thread.stack_size(1024 * )
    _thread.start_new_thread(sc.get_async, ())
    _thread.start_new_thread(ntw.get_async, ())
    # _thread.start_new_thread(test, ())

    # while False:
    #    # sc.text("Satic", 0, 0)
    #    # sc.text("-----", 0, 1 * 8)
    #    # sc.text("Hello World", 0, 2 * 8)
    #    sc.set_memory(
    #        name="test", elem_type="str", content=(0, 2, "Hello world"), update=False
    #    )
    #    # sc.text("-----", 0, 6 * 8)
    #    # sc.text("Static", 0, 7 * 8)
    #    sc.oled.show(start_page=0x02, end_page=0x05)
    #    # scroll right
    #    sc.oled.hw_scroll_h(direction=True, start_page=0x02, end_page=0x05)
    #    utime.sleep(3)
    #    # scroll left
    #    sc.oled.hw_scroll_h(direction=False, start_page=0x02, end_page=0x05)
    #    utime.sleep(3)
    #    sc.oled.hw_scroll_off()

    scroll_text(sc)
    while True:
        now = utime.time()
        # ntw.check(now)

        if ntw.wlan.isconnected():
            clock.check(now)
            weather.check(now)
        # google.check(now)
        utime.sleep(const.MAIN_CYCLE_TIME)


if __name__ == "__main__":
    main()
