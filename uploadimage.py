#! python3
# uploadimage.py - upload image via HTTP Post
# Last update: 20230810: function call by thread
# Developer: @roboticscats
import requests, textMyself

# upload image to LookOut via HTTP Post
def upload_image(url, image_path):
    try:
        # Open the image file in binary mode and read its contents
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        # Set the headers for the HTTP POST request
        headers = {
            'Content-Type': 'image/jpeg'  # Set the correct content type for JPEG images
        }

        # Make the HTTP POST request with the image data
        response = requests.post(url, headers=headers, data=image_data)
        
        #if 'score' in response.text:
            #detection = detection + 1

        return response

    except Exception as e:
        print(f"Error: {e}")
        return response
        

# upload image to LookOut via HTTP Post and send SMS alert of result
def upload_image_alert(url, image_path, alert):
    try:
        # Open the image file in binary mode and read its contents
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        # Set the headers for the HTTP POST request
        headers = {
            'Content-Type': 'image/jpeg'  # Set the correct content type for JPEG images
        }

        # Make the HTTP POST request with the image data
        response = requests.post(url, headers=headers, data=image_data)
        
        if 'score' in response.text:
            # send SMS via Twilio. Need to import textMyself
            textMyself.textmyself('LookOut detects wildfire from the camera ' + alert)

        return response

    except Exception as e:
        print(f"Error: {e}")
        return response

