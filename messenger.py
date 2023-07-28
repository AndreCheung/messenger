#! python3
# LookOutMessenger.py - Get image from webpage and sent it to LookOut
# Last update: 20230728
# Author: RoboticsCats.com
import sys, requests, os, time, datetime, pytz
from PIL import Image, ImageDraw

# global constants
inputUrl ='https://www.sunpeaksresort.com/sites/default/files/webcams/ele_view_of_morrisey.jpg'
lookoutUrl = 'https://lax.pop.roboticscats.com/api/detects?apiKey=bb8f59aeb27255f1201e12edf7ccfd79'
lookoutName = 'CA-BC-SunPeaks'
location = 'America/Los_Angeles'

# detection interval is 60 for standard plan and 30 for premium plan respectively
interval = 30

# working image file
#temp_image = 'temp.jpg'

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
    
        # Check the response status
#        if response.status_code == 200:
#            print("Image uploaded successfully!")
#        else:
#            print(f"Failed to upload image. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

# main program
cycle = 0
MaxCycle = 3
detection = 0
failure = 0

temp_image = Image.new('RGB', (1920, 1080))
temp_image.save('temp.jpg')

if len(sys.argv) >= 2:
    MaxCycle = int(sys.argv[1])
    
if MaxCycle < 0 or MaxCycle > 86400:
    print('Parameter is out of range.')
    sys.exit()

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

start_time = pytz.utc.localize(datetime.datetime.utcnow())

while cycle < MaxCycle:
    
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    location_now = utc_now.astimezone(pytz.timezone(location))
    location_now_str = location_now.strftime('%Y-%m-%d-%H:%M:%S')

    # sanity check
    print('Detection cycle #' + str(cycle + 1) + '/' + str(MaxCycle) + ' : ' + location_now_str)

    header = 'roboticscats.com | ' + location_now_str
    
    res = requests.get(inputUrl + '?timestamp=' + str(round(time.time())))
    try:
        res.raise_for_status()
    except Exception as exc:
        print('There was a problem: %s' % (exc))

    # Save the image to temp.jpg
    imageFile = open('temp.jpg', 'wb')
    for chunk in res.iter_content(100000):
        imageFile.write(chunk)
    imageFile.close()

    # write timestamp on the image top left corner
#    try:
    imageText = Image.open('temp.jpg')
    draw = ImageDraw.Draw(imageText)
    draw.text((10,10), header)
    imageText.save('temp.jpg')
        
#    except Exception as e:
#        print(f"Error: {e}")

    result = upload_image(lookoutUrl, 'temp.jpg')
    
    if result.status_code != 200:
        failure = failure + 1
        
    if 'score' in result.text:
        detection = detection + 1
    
    dt = pytz.utc.localize(datetime.datetime.utcnow()) - utc_now

    # sanity check
    print('Result from LookOut: ' + result.text)
    print('Time used in second: ' + str(round((dt.total_seconds()),2)))
    print()
    
    if MaxCycle > 1 and dt.total_seconds() < interval:
        time.sleep(interval - dt.total_seconds())
    
    cycle = cycle + 1
    
end_time = pytz.utc.localize(datetime.datetime.utcnow())
time_spent = end_time - start_time

print()
print("Mission completed.")
print(str(cycle) + ' images are send to LookOut camera ' + lookoutName
      + ' in the last ' + str(int(time_spent.total_seconds())) + ' seconds.')
print(str(detection) + ' images with positives.')
print(str(failure) + ' fail image uploads.')
