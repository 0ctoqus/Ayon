Connect other screen
--------------------

This board works great, I was able to get both the WiFi and the OLED up and running. The OLED is a bit tricky, it's not connected to the standard I2C pins, its SDA pin is 4 and SCL pin is 15. You can set this up by adding Wire.begin(4, 15) to your setup code. The display's I2C address is 0x3C. You will also need to use the OLED_RST pin to enable the display: pinMode(16,OUTPUT); digitalWrite(16, LOW); delay(50); digitalWrite(16, HIGH); After applying these settings I2CScan can find the display and most SSD1306 Arduino libraries work (for example the Adafruit SSD1306 works after changing Wire.begin() to Wire.begin(4, 15) and setting the reset pin and the I2C address).

Dimensions
----------

+-------------------+
| 					|
| 					| 25.5mm
|					|
+-------------------+
		50mm		 \
					  \
					  	5.75mm