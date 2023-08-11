# LookOut Messenger
last update: 20230811
author: Andre Cheung
organization: roboticscats.com

LookOut Messenger is a simple application to retrieve a jpeg image, from a surveillance camera or a webpage, and then upload the image to LookOut Wildfire Detection SaaS, https://roboticscats.com/lookout/

LookOut Messenger uses HTTP Get in image retrival.
LookOutMessenger uses HTTP Post in image upload.

File list:
messenger.py: main program
messenger-ptz.py: main program support PTZ guard tour
weather.py: function to get current weather info from OpenWeather
imageupload.py: function to HTTP Post image to LookOut Wildfire Detection SaaS, and send SMS notification using textMyself
textMyself.py: function send SMS message via Twilio
