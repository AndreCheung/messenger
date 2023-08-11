#! python3
# messenger.py - Get images from camera, overlay local time and weather, and sent to LookOut
# LookOut Messeger (beta) is a free application for LookOut Wildfire Detection SaaS customers
# Last update: 20230810
# Developer: @roboticscats, @jiansuo
import sys, requests, os, time, datetime, pytz, re, threading
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from requests.auth import HTTPDigestAuth
import weather, uploadimage

# BELOW this line is customer-specific information
# Global constants unique to each LookOut camera endpoints
lookoutName = 'your_camera_name'
# your location for timezone info
location = 'Asia/Hong_Kong'
# camera GPS location
latitude = 22.00
longitude = 114.00
# detection interval is 60 for standard plan and 30 for premium plan respectively
interval = 60
# font to draw text on image
Font = ImageFont.truetype('/Users/andre/Library/Group Containers/UBF8T346G9.Office/FontCache/4/CloudFonts/Segoe UI/38386564244.ttf', 23)
# Font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 20)
# camera admin URL
cameraUrl = 'http://your_camera_hostname_or_IP_address'
# guard tour is a list of presets.
# Each preset is list of preset name, LookOut camera endpoint, PTZ movement time, heading direction, FOV.
guardtour = [
    {'preset':'preset_name_1', 'lookout':'your_lookout_endpoint_url_of_preset_name_1', 'ptz':5, 'heading':0, 'FOV':60},
    {'preset':'preset_name_2', 'lookout':'your_lookout_endpoint_url_of_preset_name_2', 'ptz':5, 'heading':60, 'FOV':60},
    {'preset':'preset_name_3', 'lookout':'your_lookout_endpoint_url_of_preset_name_3', 'ptz':5, 'heading':120, 'FOV':60},
    {'preset':'preset_name_4', 'lookout':'your_lookout_endpoint_url_of_preset_name_4', 'ptz':5, 'heading':180, 'FOV':60},
    {'preset':'preset_name_5', 'lookout':'your_lookout_endpoint_url_of_preset_name_5', 'ptz':5, 'heading':240, 'FOV':60}
    ]
# ABOVE this line is customer-specific information

# BELOW this line is program code. Please DO NOT modify if you are not sure what you do.

# move the AXIS camera to a specific position in the guardtour
def movetopreset(position, time):
    url = cameraUrl + '/axis-cgi/com/ptz.cgi?gotoserverpresetname=' + guardtour[position]['preset']
    try:
        response = requests.get(url, auth=HTTPDigestAuth('username', 'password'))
        return response.status_code
    except Exception as exc:
        print('There was a problem: %s' % (exc))
        return response.status_code

# main program
cycle = 0
MaxCycle = 3
detection = 0
failure = 0
status = False

# check program arguments
if len(sys.argv) >= 2:
    MaxCycle = int(sys.argv[1])
    
if MaxCycle < 0 or MaxCycle > 86400:
    print('Parameter is out of range.')
    sys.exit()

# if there is no program argumemt, then ask user input
while len(sys.argv) < 2:
    status = True
    print('How many guard tour cycles?')
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

print(f'Your want to run {MaxCycle} guard tour cycles.\n')

# start time of the main loop
utc_start = pytz.utc.localize(datetime.datetime.utcnow())
location_start = utc_start.astimezone(pytz.timezone(location))

# first time weather info check. Need to import weather
# use weather_now = '' if don't use weather
weather_now = weather.weather(latitude, longitude)

# last time to call OpenWeather API
lastOWtime = utc_start

# change current working directory to ~/Documents/python
os.chdir(Path.home()/Path('Documents/python'))

# Save the downloaded image to temp.jpg
file_path = Path('temp.jpg')

# create temp.jpg
temp_image = Image.new('YCbCr', (1920, 1080))
temp_image.save(file_path, 'JPEG')

# measure the fastest cycle time in seconds
min_cycle_time = 180.0

# main loop
while cycle < MaxCycle:
    
    uploadThreads = []
    
    #print('Cycle ' + str(cycle) + ' : ' + pytz.utc.localize(datetime.datetime.utcnow()).astimezone(pytz.timezone(location)).strftime('%Y-%m-%d %H:%M:%S'))

    # start time of cycle
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    location_now = utc_now.astimezone(pytz.timezone(location))
    location_now_str = location_now.strftime('%Y-%m-%d %H:%M:%S')
    
    # guard tour: move the camera among presets in guardtour, get and post images
    for position in range(len(guardtour)):
        # start time of each preset
        position_utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        position_loc_now = position_utc_now.astimezone(pytz.timezone(location))
        position_loc_now_str = position_loc_now.strftime('%Y-%m-%d %H:%M:%S')
        
        if (len(guardtour)) > 1:
            movetopreset(position, position_loc_now_str)
        
        # wait for camera to move the preset properly
        time.sleep(guardtour[position]['ptz'])
        
        # HTTP Get image from an AXIS visual camera
        try:
            res = requests.get(cameraUrl + '/axis-cgi/jpg/image.cgi?resolution=1920X1080', auth=HTTPDigestAuth('username', 'password'))
        except Exception as exc:
            print('There was a problem: %s' % (exc))
            
        # if HTTP Get successes
        if res.status_code == 200:
        
            # Check weather info at 10 minutes interval. Need to import weather
            if lastOWtime + datetime.timedelta(seconds=600) < position_utc_now:
                weather_now = weather.weather(latitude, longitude)
                lastOWtime = position_utc_now
                #print('Last time to call OpenWeather API: ' + position_loc_now_str)
            
            # Header includes local time and weather info
            header = 'roboticscats.com | ' + position_loc_now_str + ' | ' + weather_now
            
            # write respone image to file_path
            try:
                inputReady = False
                with file_path.open(mode='wb') as imageFile:
                    for chunk in res.iter_content(100000):
                        imageFile.write(chunk)                      
            except Exception as e:
                print(f"Error1: {e}")
                
            # write timestamp and weather info on the image top left corner
            try:
               with Image.open(file_path) as imageText:
                    draw = ImageDraw.Draw(imageText)
                    draw.text((20,30), header, font=Font)
                    imageText.save(file_path)
                    inputReady = True
            except Exception as e:
                print(f"Error2: {e}")
            
            # HTTP Post image to LookOut
            if inputReady:
                lookoutUrl = guardtour[position]['lookout']
                message = lookoutName + '-' + str(guardtour[position]['preset']) + ' at ' + location_now_str + '. Weather: ' + weather_now
                try:
                    # thread to achieve concurrent network uploads
                    #uploadThread = threading.Thread(target=uploadimage.upload_image, args=(lookoutUrl, file_path))
                    uploadThread = threading.Thread(target=uploadimage.upload_image_alert, args=(lookoutUrl, file_path, message))                    
                    uploadThreads.append(uploadThread)
                    uploadThread.start()
                except Exception as e:
                    print(f"Error3: {e}")
                    failure = failure + 1

            else:               
                failure = failure + 1
                
        else:
            failure = failure + 1

    for uploadThread in uploadThreads:
        uploadThread.join()
        
    # dt is the total time used in this cycle           
    dt = pytz.utc.localize(datetime.datetime.utcnow()) - utc_now
    
    #print('\t  Busy time for PTZ, HTTP Get, overlay, & Post: ' + str(round(dt.total_seconds(),2)))
    if min_cycle_time > round(dt.total_seconds(),2):
        min_cycle_time = round(dt.total_seconds(),2)
        
    # wait till next interval
    if MaxCycle > 1 and (dt.total_seconds() < interval):
        time.sleep(interval - dt.total_seconds())

    # save detection information at the end of each guard tour cycles
    utc_last = pytz.utc.localize(datetime.datetime.utcnow())
    location_last = utc_last.astimezone(pytz.timezone(location))
    location_last_str = location_last.strftime('%Y-%m-%d %H:%M:%S')
    time_spent = utc_last - utc_start

    # go to next guard tour cycle
    cycle = cycle + 1   

    with open('summary-wwf.txt', mode='w') as file_object:
        print('LookOut Messenger mission completed.\n', file=file_object)
        
        print('LookOut camera: ' + lookoutName, file=file_object)
        print('Detection interval: ' + str(interval) + ' seconds', file=file_object)
        print('Guard tour cycle: ' + str(MaxCycle) + '\n', file=file_object)
        
        print('Start time: ' + location_start.strftime('%Y-%m-%d %H:%M:%S') + ', ' + location, file=file_object)
        print('Last time: ' + location_last_str + ', ' + location +'\n', file=file_object)
        
        print(str(cycle) + ' guard tour cycles made in the last ' + str(int(time_spent.total_seconds())) + ' seconds.', file=file_object)
        print('Fastest cycle is ' + str(min_cycle_time) + ' seconds.', file=file_object)
        print(str(cycle * len(guardtour)) + ' image uploads and ' + str(failure) + ' upload failure.', file=file_object)
        #print(str(failure) + ' image upload failure.', file=file_object)
       
    
# the main program ends
print(f'LookOut Messenger mission completed at {location_last_str}.')
