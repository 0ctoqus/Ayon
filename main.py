from sys import path

path.append("Sources")

# Local libs
# import esp32
# import _thread
# import uasyncio as asyncio
# from google import Google

from internet import Network
import elements
from screen import Screen_Handler
import utime
import consts as const


def update_clock(sc):
    localtime = utime.localtime()
    date = " " + "%02d" % localtime[2] + "/" + "%02d" % localtime[1]
    time = (
        "%02d" % localtime[3]
        + ":"
        + "%02d" % localtime[4]
        + ":"
        + "%02d" % localtime[5]
    )
    sc.set_memory(
        name="date", elem_type="str", content=(1, 0, time + " " + date), delete=True
    )


def main():
    print("Running Ayon")
    sc = Screen_Handler()
    ntw = Network(sc, const.NTW_CHECK_TIME)
    clock = elements.Clock(ntw, sc, const.CLOCK_TIME_CHECK)
    weather = elements.Weather(ntw, sc, const.WEATHER_TIME_CHECK)
    # google = Google(ntw, sc, const.GOOGLE_TIME_CHECK)

    grid = []
    gate = True
    for x in range(40):
        for y in range(128):
            grid.append(int(gate))
            gate != gate
    sc.pixel_art["grid"] = grid
    sc.set_memory(name="grid", elem_type="pixel", content=(0, 2, "grid"))

    while True:
        now = utime.time()
        # if ntw.check_connection(now):
        #    clock.check(now)
        #    weather.check(now)
        # google.check(now)
        # update_clock(sc)
        # sc.set_memory(
        #    name="scroll_text",
        #    elem_type="str",
        #    content=(8, 2, "Hello world"),
        #    scroll=True,
        # )
        update_clock(sc)
        utime.sleep(const.MAIN_CYCLE_TIME)


if __name__ == "__main__":
    main()
