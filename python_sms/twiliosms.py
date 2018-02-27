#!/usr/bin/env python

# Download the twilio-python library from twilio.com/docs/libraries/python
from twilio.rest import Client

#to_number phone number  of  recipient of SMS  must statrt with +1<9 digits>
to_number ="+19731234567"   #Put SMSrecient number here
from_number="+19042990359"  #Twilio assifned number

# Find these values at https://twilio.com/user/account
# TEST keys below :: will not send out SMS - just simulate
account_sid= "AC159642d501306ab4790c27f3ec2a1884"
auth_token= "7597d85aed73258a70371b48cff807c3"

# LIVE SMS account values

print "Sending SMS  via TWILIO service to number "+to_number
client=Client(account_sid, auth_token)
message = client.messages.create(
        body="All in the game, yo",
        to=to_number,
        from_=from_number)

print "Message SENT!  ID:"+ message.sid
