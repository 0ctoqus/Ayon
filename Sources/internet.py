# Libs
import network
from urequests import request
import ujson
import utime

# Local libs
# import uasyncio as asyncio

# Local scripts
# from screen import Screen_element
import consts as const


class Network:
    def __init__(self, sc, max_time_check):
        # Screen_element.__init__(self, None, sc, max_time_check)
        self.sc = sc
        self.max_time_check = max_time_check
        self.ip = None
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.trying_to_connect = False
        self.ssid = None
        self.pswd = None
        # self.connected = False

    def request(self, request_type, url, data=None, headers={}):
        if self.wlan.isconnected():
            json = None
            if data is not None:
                data = ujson.dumps(data)
            try:
                response = request(request_type, url, data=data, headers=headers)
            except Exception as e:
                print(e)
                response = None
            if response is not None:
                try:
                    json = response.json()
                except:
                    print("error in json")
                    json = None
                response.close()
                return json
        print("request error")
        return None

    def connect(self):
        self.sc.set_memory(
            name="connection_status",
            elem_type="pixel",
            content=(0, 0, "cross"),
            update=True,
        )
        # self.sc.update_display()
        # self.sc.oled.show(start_page=0x00, end_page=0x01)
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
            print("Select wifi", self.ssid)
        else:
            print("No wifi available")
            self.ssid = None
            self.pswd = None

        return self.ssid

    def check_connection(self):
        # Check if we have to check for connection
        if not self.wlan.isconnected() or self.trying_to_connect:

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
                    name="connection_status",
                    elem_type="pixel",
                    content=(0, 0, "check"),
                    update=True,
                )
                self.trying_to_connect = False

        return self.wlan.isconnected()

    def get_async(self):
        while True:
            if self.check_connection():
                wait_time = self.max_time_check
            else:
                wait_time = const.MAIN_CYCLE_TIME
            utime.sleep(wait_time)

    def check(self):
        connected = self.check_connection()
        if not connected:
            print("getting ntw")
        return connected
