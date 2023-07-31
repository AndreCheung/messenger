#! python3
# messenger.py - Get image from webpage, overlay local time and weather, and sent it to LookOut
# LookOut Messeger is a free application for LookOut Wildfire Detection SaaS customers
# Last update: 20230731
# Author: Andre Cheung
# Organizaton: RoboticsCats.com
import sys, requests, os, time, datetime, pytz, re
from PIL import Image, ImageDraw, ImageFont

# global constants unique to each LookOut camera endpoints
# this am example of a public webcam image at sunpeaks resort
inputUrl ='https://www.sunpeaksresort.com/sites/default/files/webcams/ele_view_of_morrisey.jpg'
# this is a LookOut camera endpoint. SECRET info.
lookoutUrl = ''
lookoutName = 'CA-BC-SunPeaks'
location = 'Canada/Pacific'
# camera GPS location
latitude = 50.88
longitude = 119.89
# This is the OpenWeather API key. SECRET info.
apikey=''
# detection interval is 60 for standard plan and 30 for premium plan respectively
interval = 60

# Raspberry Pi font to draw text on image
Font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 20)

# Code below this lines work for all LookOut camera endpoints. Please do not modify.


# upload image to LookOut via HTTP Post
def upload_image(url, image_path):
    try:
        # Open the image file in binary mode and read its contents
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            
        image_file.close()

        # Set the headers for the HTTP POST request
        headers = {
            'Content-Type': 'image/jpeg'  # Set the correct content type for JPEG images
        }

        # Make the HTTP POST request with the image data
        response = requests.post(url, headers=headers, data=image_data)
        return response
    
    except Exception as e:
        print(f"Error: {e}")
        return response

# get current weather info (temperature, humidity, wind speed)
def weather(lat,long, key):
    # define the regexes
    temperature = re.compile(r'("temp":)(\d?\d?\d.\d?\d?)')
    humidity = re.compile(r'("humidity":)(\d?\d?\d)')
    wind_speed = re.compile(r'("wind_speed":)(\d?\d?\d.\d?\d?)')
    
    url = 'https://api.openweathermap.org/data/3.0/onecall?lat=' + str(round(lat,4)) + '&lon=' + str(round(long,4)) + '&exclude=minutely,hourly,daily&units=metric&appid=' + str(key)
    
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


# main program
cycle = 0
MaxCycle = 3
detection = 0
failure = 0

# check program arguments
if len(sys.argv) >= 2:
    MaxCycle = int(sys.argv[1])
    
if MaxCycle < 0 or MaxCycle > 86400:
    print('Parameter is out of range.')
    sys.exit()

# if there is no program argumemt, then ask user input
while len(sys.argv) < 2:
    print('How many detection cycles?')
    MaxCycle = input()
    try:
        MaxCycle = int(MaxCycle)
    except:
        print('Please use numeric digits.')
        continue
    if MaxCycle < 1:
        print('Please enter a positive number.')
        continue
    if MaxCycle > 86400:
        print('Please enter a positive number less than 86400.')
        continue
    break

print(f'Your want to run {MaxCycle} detection cycles.\n')

utc_start = pytz.utc.localize(datetime.datetime.utcnow())
location_start = utc_start.astimezone(pytz.timezone(location))

# last time to call OpenWeather API
lastOWtime = utc_start
weather_now = weather(latitude, longitude, apikey)

# create temp.jpg
temp_image = Image.new('YCbCr', (1920, 1080))
temp_image.save('temp.jpg', 'JPEG')

# main loop
while cycle < MaxCycle:
    
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    location_now = utc_now.astimezone(pytz.timezone(location))
    location_now_str = location_now.strftime('%Y-%m-%d-%H:%M:%S')

    # sanity check
    print('Detection cycle #' + str(cycle + 1) + '/' + str(MaxCycle) + ' : ' + location_now_str)
    
    # HTTP Get the image, timestamp is added to the url to retrive the latest image
    try:
        res = requests.get(inputUrl + '?timestamp=' + str(round(time.time())))
        #res.raise_for_status()
    except Exception as exc:
        print('There was a problem: %s' % (exc))
    
    # if HTTP Get successes
    if res.status_code == 200:
        # Header includes local time and weather info. Check weather info every 10 minutes.
        if lastOWtime + datetime.timedelta(seconds=600) < utc_now:
            weather_now = weather(latitude, longitude, apikey)
            lastOWtime = utc_now
        
        header = 'roboticscats.com | ' + location_now_str + ' | ' + weather_now

        # Save the dowbloaded image to temp.jpg
        try:
            inputReady = False
            imageFile = open('temp.jpg', 'wb')
            for chunk in res.iter_content(100000):
                imageFile.write(chunk)
            imageFile.close()
            
        except Exception as e:
            print(f"Error1: {e}")

        # Write timestamp and weahter info on the image top left corner
        try:
            imageText = Image.open('temp.jpg')
            #imageText.LOAD_TRUNCATED_IMAGES = True
            draw = ImageDraw.Draw(imageText)
            draw.text((20,20), header, font=Font)
            imageText.save('temp.jpg')
            imageText.close()
            inputReady = True
        
        except Exception as e:
            print(f"Error2: {e}")
            
        # if downloaded image is ready, then HTTP Post image to LookOut
        if inputReady:
            result = upload_image(lookoutUrl, 'temp.jpg')
            if result.status_code == 200:
                if 'score' in result.text:
                    detection = detection + 1
            else:    
                failure = failure + 1
        else:               
            failure = failure + 1
                
    else:
        failure = failure + 1
    
    dt = pytz.utc.localize(datetime.datetime.utcnow()) - utc_now

    # sanity check
    try:
        if inputReady:
            print('Result from LookOut: ' + result.text)
        else:
            print('Result from LookOut: N/A')
    except Exception as e:
        print(f"Error: {e}")
       
    print('Time used in second: ' + str(round((dt.total_seconds()),2)) + '\n')
    #print('Last Time to OW API: ' + lastOWtime.strftime('%Y-%m-%d-%H:%M:%S'))
    
    if MaxCycle > 1 and dt.total_seconds() < interval:
        time.sleep(interval - dt.total_seconds())
    
    cycle = cycle + 1
    
    utc_last = pytz.utc.localize(datetime.datetime.utcnow())
    location_last = utc_last.astimezone(pytz.timezone(location))
    location_last_str = location_last.strftime('%Y-%m-%d %H:%M:%S')
    time_spent = utc_last - utc_start

    with open('summary.txt', mode='w') as file_object:
        print('LookOut Messenger mission completed.\n', file=file_object)
        print('LookOut camera: ' + lookoutName, file=file_object)
        print('Detection interval: ' + str(interval) + ' seconds\n', file=file_object)
        print('Start time: ' + location_start.strftime('%Y-%m-%d %H:%M:%S') + ', ' + location, file=file_object)
        print('Last time: ' + location_last_str + ', ' + location +'\n', file=file_object)
        print(str(cycle) + ' detection cycles made in the last ' + str(int(time_spent.total_seconds())) + ' seconds.', file=file_object)
        print(str(detection) + ' images with positives.', file=file_object)
        print(str(failure) + ' fail image uploads.', file=file_object)
        file_object.close()
        
print('LookOut Messenger mission completed.')
