#! python3
# textMyself.py - Defines the textmyself() function that texts a message 
# passed to it as a string. 
# Ref: Automate the Boring Stuff with Python, Sweigart, Al
# Preset values:
accountSID = ''
authToken = ''
myNumber = ""
twilioNumber = ''

from twilio.rest import Client

def textmyself(message):
    twilioCli = Client(accountSID, authToken)
    twilioCli.messages.create(body=message, from_=twilioNumber, to=myNumber)
