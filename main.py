# import urequests
from urequests import request
import network
import framebuf
from math import ceil
import esp32
import utime
import ujson
import _thread
import machine
import ssd1306
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

        # set reset Pin hight
        # try:
        # pin16 = machine.Pin(16, machine.Pin.OUT)
        # pin16.value(1)
        # machine.Pin(16, machine.Pin.OUT).value(1)
        # self.i2c = machine.I2C(scl=machine.Pin(15), sda=machine.Pin(4))

        self.i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))

        # self.i2c = machine.I2C(scl=machine.Pin(15), sda=machine.Pin(4))
        # print(self.i2c.scan())
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
        x2 = len(string) * self.char_width
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


class Screen_element:
    def __init__(self, ntw, sc, max_time_check):
        self.ntw = ntw
        self.sc = sc
        self.last_time_check = 0
        self.time_diff = 0
        self.max_time_check = max_time_check  # * 1000

    def get_time_diff(self, now):
        self.time_diff = now - self.last_time_check
        if self.time_diff < 0:
            self.last_time_check = 0
            self.time_diff = now
        if self.time_diff > self.max_time_check:
            self.last_time_check = now
            return True
        return False


class Clock(Screen_element):
    def __init__(self, ntw, sc, max_time_check):
        Screen_element.__init__(self, ntw, sc, max_time_check)
        self.url = const.CLOCK_URL
        self.tm = None

    def set(self):
        print("Getting time")
        time_data = self.ntw.request("GET", self.url)
        if time_data is not None:
            unix_timestamp = (
                int(time_data["unixtime"]) - 946684800 + 3600 * const.CLOCK_UTC_OFFSET
            )
        else:
            unix_timestamp = 0
        self.tm = utime.localtime(unix_timestamp)
        machine.RTC().datetime(self.tm[0:3] + (0,) + self.tm[3:6] + (0,))

    def get(self, now):
        if self.get_time_diff(now) or self.tm is None:
            self.set()

        localtime = utime.localtime()
        date = " " + "%02d" % localtime[2] + "/" + "%02d" % localtime[1]
        time = (
            "%02d" % localtime[3]
            + ":"
            + "%02d" % localtime[4]
            + ":"
            + "%02d" % localtime[5]
        )
        self.sc.set_memory(
            name="date", elem_type="str", content=(1, 0, time + " " + date)
        )


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

    def get(self, now):
        if self.get_time_diff(now) or self.current_temperature is None:
            print("Getting weather")
            WEATHER_data = self.ntw.request("GET", self.complete_url)

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
            else:
                print("City Not Found")
                self.WEATHER_description = "None"
                self.WEATHER_id = 0
                self.current_temperature = 0
                self.current_pressure = 0
                self.current_humidity = 0
                self.pixel_art = "cross"

            temp_str = str(self.current_temperature)
            y = 7
            self.sc.set_memory(
                name="WEATHER_art", elem_type="pixel", content=(0, y, self.pixel_art)
            )
            self.sc.set_memory(
                name="WEATHER_temp", elem_type="str", content=(1, y, temp_str)
            )
            self.sc.set_memory(
                name="WEATHER_temp_type",
                elem_type="pixel",
                content=(1 + len(temp_str), y, "celcius"),
            )
            self.sc.set_memory(
                name="WEATHER_humidity",
                elem_type="str",
                content=(2 + len(temp_str), y, str(self.current_humidity) + "%"),
            )


class Network(Screen_element):
    def __init__(self, sc, max_time_check):
        Screen_element.__init__(self, None, sc, max_time_check)
        self.ip = None
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.trying_to_connect = False
        self.ssid = None
        self.pswd = None

    def request(self, request_type, url, data=None, headers={}):
        if self.wlan.isconnected():
            json = None
            if data is not None:
                data = ujson.dumps(data)
            response = request(request_type, url, data=data, headers=headers)
            if response is not None:
                json = response.json()
            response.close()
            return json
        print("request error")
        return None

    def connect(self):
        self.sc.set_memory(
            name="connection_status", elem_type="pixel", content=(0, 0, "cross")
        )
        self.sc.update_display()
        print("connecting to:", self.ssid, " with password ", self.pswd)
        self.wlan.connect(self.ssid, self.pswd)

    def get_best_wifi(self):
        available_wifi = []

        # Scan for available networks and only keep known ones
        for wifi in self.wlan.scan():
            ssid = wifi[0].decode("utf-8")
            signal_strenght = wifi[3]
            if ssid in const.NTW_LIST:
                available_wifi.append((ssid, signal_strenght))

        # Only keep the one with the best signal
        if len(available_wifi) > 0:
            print("Available wifi ", available_wifi)
            self.ssid = max(available_wifi, key=lambda wifi: wifi[1])[0]
            self.pswd = const.NTW_LIST[self.ssid]
            print("Select wifi ", self.ssid)
        else:
            print("No wifi available")
            self.ssid = None
            self.pswd = None

        return self.ssid

    def check_connection(self, now):
        # Check if we have to check for connection
        if (
            self.get_time_diff(now)
            or not self.wlan.isconnected()
            or self.trying_to_connect
        ):
            # print("checking connection")
            self.last_time_check = now

            # If not connected try connecting
            if not self.wlan.isconnected() and not self.trying_to_connect:
                print("connecting")
                if self.get_best_wifi() is not None:
                    self.connect()
                    self.trying_to_connect = True

            # If we have reconnected last iteration then update
            if self.wlan.isconnected():
                self.ip = self.wlan.ifconfig()
                print("network config:", self.ip)
                self.sc.set_memory(
                    name="connection_status", elem_type="pixel", content=(0, 0, "check")
                )
                self.trying_to_connect = False

        return self.wlan.isconnected()


class Google(Screen_element):
    class Oauth(Screen_element):
        # https://developers.google.com/identity/protocols/OAuth2ForDevices
        # https://console.developers.google.com/apis/credentials?project=esp32-watch&authuser=1
        def __init__(self, ntw, sc):
            Screen_element.__init__(self, ntw, sc, 5)
            self.ntw = ntw
            self.client_id = const.GOOGLE_CLIENT_ID
            self.client_secret = const.GOOGLE_CLIENT_SECRET
            self.scope = const.GOOGLE_SCOPE
            self.device_code = None
            self.authorization_data = None
            self.expires_at = 0
            self.interval = None
            self.access_token = None
            self.token_type = None
            self.displayed = None
            try:
                with open(const.GOOGLE_REFRESH_TOKEN_FILE, "r") as refresh_token_file:
                    self.refresh_token = refresh_token_file.read()
                    print("Found refresh_token ", self.refresh_token)
            except OSError:
                print("Not dound refresh_token")
                self.refresh_token = None

        # Request device and user codes
        def request_oauth_code(self, now):
            data = {"client_id": self.client_id, "scope": self.scope}
            response = self.ntw.request("POST", const.GOOGLE_OAUTH_CODE_URL, data)
            if response is None:
                print("Google oauth request ko")
            elif "error_code" in response or "error" in response:
                print("Google oauth request ko: error ", response)
            else:
                print("Google oauth authorization ok: ", response)
                self.device_code = response["device_code"]
                user_code = response["user_code"]
                verification_url = response["verification_url"].split("google.com", 1)[
                    1
                ]
                # Might crash if now + expires_in int overflow
                self.expires_at = now + response["expires_in"]
                self.max_time_check = response["interval"]
                self.authorization_data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": self.device_code,
                    "grant_type": "http://oauth.net/grant_type/device/1.0",
                }
                print(
                    self.device_code,
                    user_code,
                    verification_url,
                    self.expires_at,
                    self.max_time_check,
                )
                self.sc.set_memory(
                    name="google_text",
                    elem_type="str",
                    content=(0, 2, "Go to google.com"),
                )
                self.sc.set_memory(
                    name="google_url", elem_type="str", content=(0, 3, verification_url)
                )
                self.sc.set_memory(
                    name="google_code", elem_type="str", content=(0, 4, user_code)
                )
                self.displayed = ["google_text", "google_url", "google_code"]
                return False

        # Check user authorization
        def request_oauth_authorization(self, now):
            response = self.ntw.request(
                "POST", const.GOOGLE_OAUTH_TOKEN_URL, self.authorization_data
            )
            if response is None:
                print("Google oauth request ko")
            elif "error_code" in response or "error" in response:
                print("Google oauth request ko: error ", response)
            else:
                self.access_token = response["access_token"]
                self.refresh_token = response["refresh_token"]
                self.token_type = response["token_type"]
                self.expires_at = now + response["expires_in"]
                for elem in self.displayed:
                    self.sc.set_memory(name=elem, delete=True)
                print("Google oauth authorized")
                print(
                    self.access_token,
                    self.refresh_token,
                    self.token_type,
                    self.expires_at,
                )

                # Save refresh token to file for later use
                with open(const.GOOGLE_REFRESH_TOKEN_FILE, "w") as refresh_token_file:
                    print("refresh_token saved to file")
                    refresh_token_file.write(self.refresh_token)
                return True
            return False

        # Refresh user authorization
        def request_oauth_refresh(self, now):
            data = {
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            }
            response = self.ntw.request("POST", const.GOOGLE_OAUTH_TOKEN_URL, data)
            if response is None:
                print("Google oauth request ko")
            elif "error_code" in response or "error" in response:
                self.refresh_token = None
                self.expires_at = 0
                print("Google oauth request ko: error ", response)
            else:
                self.access_token = response["access_token"]
                # self.expires_in = response["expires_in"]
                self.expires_at = now + response["expires_in"]
                self.token_type = response["token_type"]
                print("Google oauth refreshed")
                print(self.access_token, self.token_type, self.expires_at)
                return True
            return False

        def check_connected(self, now):
            time_before_expired = self.expires_at - now
            if self.refresh_token is None:
                if time_before_expired > 0:
                    print("Requesting auth")
                    return self.request_oauth_authorization(now)
                else:  # elif self.device_code is None:
                    print("Requesting code")
                    return self.request_oauth_code(now)
            elif time_before_expired - 60 <= 0:
                print("Requesting refresh")
                return self.request_oauth_refresh(now)
            elif self.access_token is not None:
                return True
            print("Error")
            return False

    class Drive:
        def __init__(self, ntw):
            self.ntw = ntw
            self.file_url = const.GOOGLE_DRIVE_URL
            self.file_id = None

        def create_file(self, access_token):
            print("Creating drive file")
            data = {
                "title": "automated_unread_mail.json",
                "mimeType": "application/json",
                "labels": {"trashed": True},
            }
            headers = {
                "Authorization": "Bearer " + access_token,
                "Content-Type": "application/json; charset=UTF-8",
            }
            response = self.ntw.request(
                "POST",
                self.file_url + "?uploadType=resumable",
                data=data,
                headers=headers,
            )
            if "alternateLink" in response:
                print("Success creating file")
                self.file_id = response["id"]
            else:
                print("Error creating file")
                self.file_id = None

        def check_file(self, access_token):
            headers = {"Authorization": "Bearer " + access_token}
            response = self.ntw.request(
                "GET", self.file_url + "?maxResults=1", headers=headers
            )
            if "items" in response:
                if len(response["items"]) == 0:
                    self.create_file(access_token)
                else:
                    print("No need to create drive file")
                    self.file_id = response["items"][0]["id"]
            else:
                self.file_id = None

        def get_file(self, access_token):
            headers = {"Authorization": "Bearer " + access_token}
            return self.ntw.request(
                "GET",
                self.file_url + "/" + self.file_id + "?alt=media",
                headers=headers,
            )

    def __init__(self, ntw, sc):
        Screen_element.__init__(self, ntw, sc, 0)
        self.oauth = self.Oauth(ntw, sc)
        self.drive = self.Drive(ntw)
        self.messages = []

    def get(self, now):
        if self.oauth.get_time_diff(now) and self.oauth.check_connected(now):
            if self.drive.file_id is None:
                self.drive.check_file(self.oauth.access_token)
            elif len(self.messages) == 0:
                print("Drive ready", self.drive.file_id)
                self.messages = self.drive.get_file(self.oauth.access_token)
                for pos in range(len(self.messages)):
                    print(self.messages[pos])
                    self.sc.set_memory(
                        name="email_" + str(pos),
                        elem_type="str",
                        content=(0, 2 + pos, self.messages[pos][2]),
                    )


def main():
    sc = Screen_Handler()
    ntw = Network(sc, const.NTW_CHECK_TIME)
    weather = Weather(ntw, sc, const.WEATHER_TIME_CHECK)
    clock = Clock(ntw, sc, const.CLOCK_TIME_CHECK)
    google = Google(ntw, sc)
    sc.set_memory(
        name="line_top",
        elem_type="rect",
        content=(
            0,
            sc.height_to_pixel(2) - 7,
            sc.width_to_pixel(17),
            sc.height_to_pixel(2) - 5,
            True,
            1,
        ),
    )
    sc.set_memory(
        name="line_bottom",
        elem_type="rect",
        content=(
            0,
            sc.height_to_pixel(6) + 5,
            sc.width_to_pixel(17),
            sc.height_to_pixel(6) + 7,
            True,
            1,
        ),
    )

    # https://docs.python.org/3.5/library/_thread.html#module-_thread
    # https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/thread_example_1
    # _thread.start_new_thread(ok, ("in thread",))\

    # https://github.com/peterhinch/micropython-async/blob/master/TUTORIAL.md#01-installing-uasyncio-on-bare-metal
    import uasyncio as asyncio

    async def bar():
        count = 0
        while True:
            count += 1
            print(count)
            await asyncio.sleep(1)  # Pause 1s

    loop = asyncio.get_event_loop()
    loop.create_task(bar())  # Schedule ASAP
    loop.run_forever()
    print("here")

    while True:
        now = utime.time()
        is_connected = ntw.check_connection(now)
        if is_connected:
            weather.get(now)
            clock.get(now)
            google.get(now)
            # _thread.start_new_thread(google.get, (now,))
            # else:
            #     print("No internet connection")
        sc.update_display()
        utime.sleep(const.MAIN_CYCLE_TIME)


if __name__ == "__main__":
    main()
