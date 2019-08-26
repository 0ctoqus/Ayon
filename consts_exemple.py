# Main
MAIN_CYCLE_TIME = 0.05

# Wifi
NTW_LIST = {"SSID1": "password1", "SSID2": "password2"}
NTW_CHECK_TIME = 30

# Clock
CLOCK_URL = "http://worldtimeapi.org/api/timezone/Europe/Paris.json"
CLOCK_UTC_OFFSET = 2
CLOCK_TIME_CHECK = 600

# Weather
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?"
WEATHER_API_KEY = "API_KEY"
WEATHER_CITY = "paris"
WEATHER_TIME_CHECK = 300

# Google api
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_SCOPE = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/drive.file"
GOOGLE_OAUTH_CODE_URL = "https://accounts.google.com/o/oauth2/device/code"
GOOGLE_OAUTH_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
GOOGLE_REFRESH_TOKEN_FILE = "refresh_token.txt"
GOOGLE_DRIVE_URL = "https://www.googleapis.com/drive/v2/files"
GOOGLE_TIME_CHECK = 5
