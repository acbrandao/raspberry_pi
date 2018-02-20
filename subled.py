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
import json
import socket
import re
import urllib2 

# MQTT Specific
mqtt_broker_ip = "localhost"		# Local MQTT broker
mqtt_port = 1883			# Local MQTT port
mqtt_user = ""			# Local MQTT user
mqtt_pass = ""			# Local MQTT password
mqtt_topic = "sensor/door"		# Local MQTT topic to monitor
localTimeOut = 120			# Local MQTT session timeout
mqtt_timer = int(round(time.time() ))  #times mqtt between reuqsts

#Uncomment to rotate the text
scrollphathd.rotate(180)

#cache HTML scrape to be nice on network
htmlText_cached=None
htmlText_cached_time=None
html_cache_expire_time =180   #number of seconds to hold cache
html_last_url=None

#Quiet Hours time periods in which alerts will not show



def scrape_url(url, start_tag,end_tag):
	global htmlText_cached,htmlText_cached_time,html_cache_expire_time,html_last_url
	result = ""
	base_url = url

	n2=int(round(time.time() ))
	if  ( htmlText_cached_time  is  None )  or  ( n2 - htmlText_cached_time >  html_cache_expire_time ) or  (html_last_url <> base_url):
		print " HTML from WEB"
		htmlText =  urllib2.urlopen(base_url).read()
		htmlText_cached =htmlText
		htmlText_cached_time=int(round(time.time() ))
		html_last_url=base_url
	else:  
		print " HTML from CACHE Text"
		htmlText=htmlText_cached

	try:
		result =re.findall(start_tag+'(.*?)'+end_tag, htmlText)[0]
	except:
		print "Invalid No Match found"
		result ="Invalid No Match found"
	#print 'Searching between '+start_tag+' and '+end_tag+' on urL: ' + url 
	return result



def getWeather():
	temp = scrape_url("http://forecast.weather.gov/MapClick.php?lat=40.732&lon=-74.1742#.Won5xainE2w",'<p class="myforecast-current-lrg">','</p>')
	temp=temp.replace('&deg;',' ')
	print 'Newark Weather: [ ' + temp + " ]"	
	scroll(" Newark: "+temp)

	return None


def getExchangeRate():

	usdeur = scrape_url("https://www.bloomberg.com/quote/USDEUR:CUR",'<div class="price">','</div>')
	print 'EURO->USD: [ ' + usdeur + " ]"	
	scroll(" 1 USD= "+ ("%0.2f" % float(usdeur) ) + " EUR ")
	return None


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
	

def scroll(textmsg="???",bright=0.3,speed=0.04):
	global scrollphathd
	#  Clear buffer
	# Reset the animation
	scrollphathd.scroll_to(0, 0)
   	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	
	# Keep track of the X and Y position for the rewind effect
	pos_x = 0

	textmsg=" "+textmsg+"         ."  # append 3 spaces tp message  to prevent wrapping of start
	print "Scrolling  %s. size: %d" % (textmsg , len(textmsg  ) )
	scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7, brightness=bright)
	
	# Scroll to the end of the current line
	msgpixels=len(textmsg)*4
        for y in range(msgpixels):
            scrollphathd.scroll(1, 0)
            pos_x += 1
            time.sleep(speed)
            scrollphathd.show()

	#time.sleep(0.05)
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	return

def show(textmsg="???",bright=0.5):
	global scrollphathd
	 #  Clear buffer
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7,brightness=bright)
	scrollphathd.show()

	return None

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
	global mqtt_topic,mqtt_timer
	now=int(round(time.time() ))
	elapsed= (now-mqtt_timer)
	print "onConnect with result code ..."+str(elapsed)+"s"
	print("rc: " + str(rc))
	if  (rc==0):
	  client.connected_flag=True #set flag
	  show("RDY",0.2)
	else:
	  show(str(rc),0.1 )
	
	mqtt_timer=int(round(time.time() ))
	client.subscribe(mqtt_topic)

def on_message(client, obj, msg):
	global message,mqtt_timer

	print("on_message Rcvd: "+ msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	message = msg.payload

	#lts handle the diffferent payloads

	if msg.topic=="sensor/door":
			if (message=="0"):
				fade("CLOSE")
			else:
				show("OPN",0.5)

	elif msg.topic=="sensor/running_time":
			scroll(message,0.5)
	else:
		print("No Topic/Message hanlder available")
		fade("OK")

	mqtt_timer=int(round(time.time() ))
	return
	
def on_publish(client, obj, mid):
    print("on_publish mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
	print("on_subscribe: " + str(mid) + " QoS:" + str(granted_qos))

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
	scroll(" IP:"+ip_address,0.2,0.02)

   #connect(host, port=1883, keepalive=60, bind_address="")
	client.connect(mqtt_broker_ip, mqtt_port, 0)

	#subscribe
	print "Subscribing to :"+mqtt_topic
	client.subscribe(mqtt_topic)
	
	#start the MQTT lient loop
	client.loop_start()	
     
	# see schedule for examples https://pypi.python.org/pypi/schedule
	schedule.every().hour.do(hournow)
	schedule.every(30).minutes.do(getWeather)
	schedule.every().hour.do(getExchangeRate)

	hournow()
	

	while True:
		schedule.run_pending()
		client.loop(.1)  #blocks for 100ms

	#client.disconnect()

	quit()
