#! python3
# weather.py - Get the current weather info - temperature, humidity, wind speed - via OpenWeather API
# Last update: 20230801
# Developer: @roboticscats @jiansuo
import re, requests

# This is the OpenWeather API key. SECRET info.
apikey = ''

# get current weather info (temperature, humidity, wind speed)
def weather(lat,long):
    # define the regexes
    temperature = re.compile(r'("temp":)(\d?\d?\d.\d?\d?)')
    humidity = re.compile(r'("humidity":)(\d?\d?\d)')
    wind_speed = re.compile(r'("wind_speed":)(\d?\d?\d.\d?\d?)')
    
    url = 'https://api.openweathermap.org/data/3.0/onecall?lat=' + str(round(lat,4)) + '&lon=' + str(round(long,4)) + '&exclude=minutely,hourly,daily&units=metric&appid=' + str(apikey)
    
    try:
        # call the OpenWeather API to get current weather
        current = requests.get(url)

        if current.status_code == 200:
            t = temperature.search(current.text)
            h = humidity.search(current.text)
            w = wind_speed.search(current.text)
                      
            info = str(round(float(t.group(2)),1)) + chr(176) + 'C | ' + h.group(2) +' % | ' + w.group(2) + ' km/h'
            return info

    except Exception as e:
        print(f"Error: {e}")
        return('')
    
