
Concept
#######
A simple MicroPython script to turn an ESP32 with oled into smart watch.

Currently it can connect to internet, get the weather and time.
Next, Il be adding access to Gmail using OAuth2ForDevices from Google and a script to save unread mail to Google Drive.

Setup
=====

0 - Install MicroPython on your board.
1 - In the consts_exemple.py file, replace the NTW_LIST, WEATHER_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET values with yours.
2 - Rename the consts_exemple.py into consts.py.
3 - Upload the consts.py and the python files in the Libs folder at the root directory of your ESP32. You can use Ampy program to do so.
4 - Run the main.py, you can use Ampy. For testing is like to use Esplorer.

Working boards
==============

Large one
---------
https://www.banggood.com/Geekcreit-ESP32-OLED-Module-For-Arduino-ESP32-OLED-WiFi-bluetooth-Dual-ESP-32-ESP-32S-ESP8266-p-1148119.html?rmmds=myorder

Small one
---------
https://eu.banggood.com/LILYGO-TTGO-16M-bytes-128M-Bit-Pro-ESP32-OLED-V2_0-Display-WiFi-bluetooth-ESP-32-Module-For-Arduino-p-1205876.html?rmmds=myorder

The oled is not connected to the standard I2C pins, its SDA pin is 4 and SCL pin is 15.
You can set this up by adding Wire.begin(4, 15) to your setup code. The display's I2C address is 0x3C. You will also need to use the OLED_RST pin to enable the display: pinMode(16,OUTPUT); digitalWrite(16, LOW); delay(50); digitalWrite(16, HIGH);
After applying these settings I2CScan can find the display and most SSD1306 Arduino libraries work (for example the Adafruit SSD1306 works after changing Wire.begin() to Wire.begin(4, 15) and setting the reset pin and the I2C address).

Dimensions
25.5mm height
50mm width
5.75mm thickness
