# Libs
import machine
import esp32
from math import ceil
import utime
import _thread

# Local libs
# import uasyncio as asyncio

# Local scripts
from screen import Screen_element
from screen import Screen_Handler
from internet import Network
import consts as const


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
        return result


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

    def __init__(self, ntw, sc, max_time_check):
        Screen_element.__init__(self, ntw, sc, max_time_check)
        self.oauth = self.Oauth(ntw, sc)
        self.drive = self.Drive(ntw)
        self.messages = None
        self.accu = 0

    def get(self):
        if self.oauth.check_connected(utime.time()):
            if self.drive.file_id is None:
                self.drive.check_file(self.oauth.access_token)
            else:
                print("Drive ready", self.drive.file_id)
                self.messages = self.drive.get_file(self.oauth.access_token)
                if self.messages != None:
                    for pos in range(len(self.messages)):
                        print(self.messages[pos])
                        self.sc.set_memory(
                            name="email_" + str(pos),
                            elem_type="str",
                            content=(
                                0,
                                2 + pos,
                                str(self.accu) + self.messages[pos][2],
                            ),
                            delete=True,
                        )
                self.accu += 1


def main():
    sc = Screen_Handler()
    ntw = Network(sc, const.NTW_CHECK_TIME)
    clock = Clock(ntw, sc, const.CLOCK_TIME_CHECK)
    weather = Weather(ntw, sc, const.WEATHER_TIME_CHECK)
    google = Google(ntw, sc, const.GOOGLE_TIME_CHECK)
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

    def test():
        while True:
            print("Alive")
            utime.sleep(1)

    # loop = asyncio.get_event_loop()
    # loop.create_task(sc.get_async())
    # loop.create_task(ntw.get_async())
    # loop.create_task(clock.get_async())
    # loop.create_task(weather.get_async())
    # loop.create_task(google.get_async())
    # loop.run_forever()

    # _thread.stack_size(1024 * )
    _thread.start_new_thread(sc.get_async, ())
    # _thread.start_new_thread(ntw.get_async, ())
    # _thread.start_new_thread(test, ())

    while True:
        now = utime.time()
        ntw.check(now)
        clock.check(now)
        weather.check(now)
        google.check(now)
        utime.sleep(const.MAIN_CYCLE_TIME)


if __name__ == "__main__":
    main()
