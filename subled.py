#!/usr/bin/env python

import math
import time, datetime
import signal
import paho.mqtt.client as mqtt  # MQTT install using: pip install paho-mqtt
import scrollphathd  # Python library for ScrollPhat HD https://github.com/pimoroni/scroll-phat-hd
from scrollphathd.fonts import font5x7
from scrollphathd.fonts import font5x5
import socket
import fcntl
import struct
import random
from threading import Timer,Thread,Event
import schedule   # install with:   pip install schedule

# MQTT Specific
mqtt_broker_ip = "localhost"		# Local MQTT broker
mqtt_port = 1883			# Local MQTT port
mqtt_user = ""			# Local MQTT user
mqtt_pass = ""			# Local MQTT password
mqtt_topic = "sensor/door"		# Local MQTT topic to monitor
localTimeOut = 120			# Local MQTT session timeout


#Uncomment to rotate the text
scrollphathd.rotate(180)

##############################################
#timer class to handle timer events in a perate thread
###########################################
def print_time(): 
	print "From print_time", time.time() 
	

def timenow():
	print time.strftime("%Y-%m-%d %H:%M \n")
	#scroll(now)
	return None
	
	
def hournow():
	print time.strftime("Time:  %H:%M:%S \n")
	scroll( time.strftime("%H:%M:%S") )
	return None
	
def clocktick():
# Display the hour as two digits
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	print time.strftime("Time:  %H:%M:%S \n")
	scrollphathd.write_string( time.strftime("%M:%S") ,x=0,y=0,font=font5x5,brightness=0.4)
	scrollphathd.show()
	return None
	
def plasma():
	i=0
	i += 2
	s = math.sin(i / 50.0) * 2.0 + 6.0

	for x in range(0, 17):
	  for y in range(0, 7):
		v = 0.3 + (0.3 * math.sin((x * s) + i / 4.0) * math.cos((y * s) + i / 4.0))

		scrollphathd.pixel(x, y, v)

	time.sleep(0.01)
	scrollphathd.show()
	return None

def scroll(textmsg="???",bright=0.3):
	global scrollphathd
	#  Clear buffer
	# Reset the animation
	scrollphathd.scroll_to(0, 0)
   	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	
	# Keep track of the X and Y position for the rewind effect
	pos_x = 0

	textmsg=textmsg+"..."  # append 3 spaces tp message  to prevent wrapping of start
	print "Scrolling  %s. size: %d" % (textmsg , len(textmsg  ) )
	scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7, brightness=bright)
	
	# Scroll to the end of the current line
	msgpixels=len(textmsg)*4
        for y in range(msgpixels):
            scrollphathd.scroll(1, 0)
            pos_x += 1
            time.sleep(.05)
            scrollphathd.show()

	#time.sleep(0.05)
	scrollphathd.clear()  # so we can rebuild it
	return


def fade(textmsg="???"):
        global scrollphathd
	x=0
	br=1
        #  Clear buffer
        scrollphathd.clear()  # so we can rebuild it
        scrollphathd.show()

	for x in range(5,0,-1):
		brite=0.05*x
        	scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7,brightness=brite)
        	scrollphathd.show()
		time.sleep(0.01)
        #scrollphathd.scroll()
        #time.sleep(0.05)
        return


def on_connect(client, userdata, flags, rc):
	global mqtt_topic
	print "onConnect with result code ..."
	print("rc: " + str(rc))
	if  (rc==0):
	  scroll("RDY",0.2)
	else:
	  scroll(str(rc),0.1 )
	
	client.subscribe(mqtt_topic)

def on_message(client, obj, msg):
	global message
	print("Rcvd: "+ msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	message = msg.payload
	if (message=="0"):
		fade("CLOSE")
	else:
		scroll("OPEN DOOR",0.5)
	return
	
def on_publish(client, obj, mid):
    print("mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
	print("Subscribed: " + str(mid) + " QoS:" + str(granted_qos))

def on_log(client, obj, level, string):
    print(string)


def timenow():
     now=datetime.datetime.now()
     return now.isoformat()+" : "

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])     

########################
# Main
########################
 
if "__main__" == __name__:
# Set timer
 
	print timenow()+"Starting MQTT Subscriber main... "
	client = mqtt.Client("piZeroLCD")  #Client MQTT object
	
	# Here, we are telling the client which functions are to be run
	# on connecting, and on receiving a message
# Assign event callbacks
	client.on_message = on_message
	client.on_connect = on_connect
	client.on_publish = on_publish
	client.on_subscribe = on_subscribe
	
	# Once everything has been set up, we can (finally) connect to the broker
	# 1883 is the listener port that the MQTT broker is using
	
	print "Connecting to MQTT broker at ", mqtt_broker_ip + "\nPort: " + str(mqtt_port)
	ip_address= get_ip_address('wlan0')
	print "Localhost IP adress:"+ip_address
	# Once we have told the client to connect, let the client object run itself
	# client.loop_forever()   this funciton is blocking
	scroll("IP:"+ip_address)

	client.connect(mqtt_broker_ip, mqtt_port)

	#subscribe
	print "Subscribing to :"+mqtt_topic
	client.subscribe(mqtt_topic)
	
	#start the MQTT lient loop
	client.loop_start()	
     
	# see schedule for examples https://pypi.python.org/pypi/schedule
	schedule.every(60).seconds.do(hournow)
	
    
	while True:
		schedule.run_pending()
		client.loop(.1)  #blocks for 100ms

	#client.disconnect()

	quit()
