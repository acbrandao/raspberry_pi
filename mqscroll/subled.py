#!/usr/bin/env python

import os
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
import requests
import socket
import re
import urllib2 
import sqlite3 #for logging and storing the data


# MQTT Specific
mqtt_broker_ip = "localhost"		# Local MQTT broker
mqtt_port = 1883			# Local MQTT port
mqtt_user = ""			# Local MQTT user
mqtt_pass = ""			# Local MQTT password

localTimeOut = 120			# Local MQTT session timeout
mqtt_timer = int(round(time.time() ))  #times mqtt between reuqsts

#Uncomment to rotate the text
scrollphathd.rotate(180)

#cache HTML scrape to be nice on network
htmlText_cached=None
htmlText_cached_time=None
html_cache_expire_time =180   #number of seconds to hold cache
html_last_url=None

#Quiet Hours time periods in which alerts will not Scroll oh ScrollPHAT
quiet_start=datetime.time(22,00,00)
quiet_end =datetime.time(06,30,00)

#database
db=None

def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else: # over midnight e.g., 23:30-04:15
        return start <= now or now < end


def scrape_url(url, start_tag,end_tag):
	global htmlText_cached,htmlText_cached_time,html_cache_expire_time,html_last_url
	result = ""
	base_url = url

	n2=int(round(time.time() ))
	if  ( htmlText_cached_time  is  None )  or  ( n2 - htmlText_cached_time >  html_cache_expire_time ) or  (html_last_url <> base_url):
		print " HTML from WEB url: "+url
		htmlText =  urllib2.urlopen(base_url).read()
		htmlText_cached =htmlText
		htmlText_cached_time=int(round(time.time() ))
		html_last_url=base_url
	else:  
		print " HTML from CACHED url: "+url
		htmlText=htmlText_cached

	try:
		result =re.findall(start_tag+'(.*?)'+end_tag, htmlText)[0]
	except:
		print "No Matches"
		result ="No Matches	"
	#print 'Searching between '+start_tag+' and '+end_tag+' on urL: ' + url 
	return result



def getWeather():
	#scrape site to get weather
	try:
		lines=[]
		lines.append("Tempo: ")
		temp = scrape_url("http://forecast.weather.gov/MapClick.php?lat=40.732&lon=-74.1742",'<p class="myforecast-current-lrg">','</p>')
		temp=temp.replace('&deg;',' ')
		lines.append('Newark ' + temp  )

		#Read this JSON Feed below and parse

		url1="http://services.sapo.pt/WeatherJSON/GetWeatherForecast/?cityCode=PO0002"
		print "JSON from web: "+url1

		weather = json.loads(requests.get(url1).text)
		temp= float(weather["GetWeatherForecastResponse"]["GetWeatherForecastResult"]["CurrentWeather"]["AirTemperature"]);
		cidade= weather["GetWeatherForecastResponse"]["GetWeatherForecastResult"]["CurrentWeather"]["City"];
		desc=weather["GetWeatherForecastResponse"]["GetWeatherForecastResult"]["CurrentWeather"]["Description"];
		lines.append(cidade+" "+  str(round(9.0/5.0*temp+32) )  +"F  "+desc)
		scrollup(lines )

	except Exception as e:
		print("Exception getWeather "+str(e) )
		writedb_log("ERROR",str(e),"PYTHON")


	return None


def getExchangeRate():
	#scrape site to get exchange rate
	usdeur = scrape_url("https://www.bloomberg.com/quote/USDEUR:CUR",'<div class="price">','</div>')
	print 'EURO->USD: [ ' + str(round( float(usdeur),2)) + " ]"	
	scroll(" 1 Dollar = "+ str(round( float(usdeur),2)) + " Euros ")
	return None

def getCDRate():
	#scrape site to get exchange rate
	result = scrape_url("http://cdrates.bankaholic.com/",'<div class="apr">','</div>')
	print '1 Ano CD : [ ' + result + " ]"	
	scroll(" 1 ano CD  "+ result + "%")
	return None
	
##############################################
#SQLite database functions for logging events and data
###########################################
def setup_db(dbname='/home/pi/log.db'):
	db=None
	if os.path.isfile(dbname)==True: #file exists open it
		db = sqlite3.connect(dbname)
		db.commit()
		#open the database
	else:
		# Get a cursor object
		db = sqlite3.connect(dbname)
		cursor = db.cursor()
		cursor.execute('''
		CREATE TABLE [event] (
			[id] INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
			[time] DATETIME   NULL,
			[topic] VARCHAR(64)  NULL,
			[payload] VARCHAR(128)  NULL,
			[source] VARCHAR(32)  NULL
			)
		''')
		db.commit()
		#create a new database
		
	return db
	
def writedb_log(topic,payload,source):
	try:
		# Open the database
		db = setup_db()  #create or OPEN Existing database
		cursor = db.cursor()

		# Insert record
		ts = time.gmtime()
		cursor.execute('''INSERT INTO event (time,topic,payload,source)
					  VALUES(?,?,?,?)''', (time.strftime("%Y-%m-%d %H:%M:%S"),topic,payload,source))
		id = cursor.lastrowid
		print('Inserted Record: row id: %d' % id)

		db.commit()
	# Catch the exception
	except Exception as e:
		  print 'DATABASE ERROR :', e
		
	finally:
		# Close the db connection
		db.close()
	return

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
	print time.strftime("Time:%I%p \n")
	glow( time.strftime("%I%p"),0.3)
	return None

def hournowcity():
	lines=[]
	lines.append("Horas")
	lines.append("Newark "+time.strftime("%I:%M %p") )
	lines.append("Portugal: "+datetime.datetime.utcnow().strftime("%I:%M %p") )

	scrollup(lines)


def calendardate():
	print time.strftime("Date: %a - %B %e \n")
	scroll( time.strftime("%a - %B %e"),0.3)
	return None
	
##############################################
# ScrollPhat HD effects and Message routines
###########################################
#taken from advanced Acrolling example to scrollup by one line
def scrollup(lines, ignore_quiet_time=False):  

	#if quiet hours do not display
	if is_quiet_time() and ignore_quiet_time==False:
		return None

	# Delay is the time (in seconds) between each pixel scrolled
	delay = 0.03
	scrollphathd.set_brightness(0.2)

	# Determine how far apart each line should be spaced vertically
	line_height = scrollphathd.DISPLAY_HEIGHT + 2

	# Store the left offset for each subsequent line (starts at the end of the last line)
	offset_left = 0

	# Draw each line in lines to the Scroll pHAT HD buffer
	# scrollphathd.write_string returns the length of the written string in pixels
	# we can use this length to calculate the offset of the next line
	# and will also use it later for the scrolling effect.
	lengths = [0] * len(lines)

	for line, text in enumerate(lines):
	    lengths[line] = scrollphathd.write_string(text, x=offset_left, y=line_height * line)
	    offset_left += lengths[line]
	    print text

	# This adds a little bit of horizontal/vertical padding into the buffer at
	# the very bottom right of the last line to keep things wrapping nicely.
	scrollphathd.set_pixel(offset_left - 1, (len(lines) * line_height) - 1, 0)

    # Reset the animation
	scrollphathd.scroll_to(0, 0)
	scrollphathd.show()

	# Keep track of the X and Y position for the rewind effect
	pos_x = 0
	pos_y = 0

	for current_line, line_length in enumerate(lengths):
		# Delay a slightly longer time at the start of each line
		time.sleep(delay*10)

		# Scroll to the end of the current line
		for y in range(line_length):
			scrollphathd.scroll(1, 0)
			pos_x += 1
			time.sleep(delay)
			scrollphathd.show()
	
		for x in range(line_height):
			scrollphathd.scroll(0, 1)
			pos_y += 1
			scrollphathd.show()
			time.sleep(delay)

	scrollphathd.fill(0)
	scrollphathd.show()	
	print "Ending scrollup() "


def clocktick():
# Display the hour as two digits
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	print time.strftime("Time:  %H:%M:%S \n")
	scrollphathd.write_string( time.strftime("%M:%S") ,x=0,y=0,font=font5x5,brightness=0.4)
	scrollphathd.show()
	return None
	

def scroll(textmsg="???",bright=0.3,speed=0.04, ignore_quiet_time=False):
	global scrollphathd
	
	#if quiet hours do not display
	if is_quiet_time() and ignore_quiet_time==False:
		return None
	
	#  Clear buffer
	# Reset the animation
	scrollphathd.scroll_to(0, 0)
   	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	
	# Keep track of the X and Y position for the rewind effect
	pos_x = 0

	textmsg=" "+textmsg+"   ."  # append 3 spaces tp message  to prevent wrapping of start
	print "Scrolling  %s. size: %d" % (textmsg , len(textmsg  ) )
	scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7, brightness=bright)
	
	# Scroll to the end of the current line
	msgpixels=len(textmsg)*7
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
	
	#if quiet hours do not display
	if is_quiet_time():
		return None
	
	 #  Clear buffer
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()
	scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7,brightness=bright)
	scrollphathd.show()

	return None
	
def glow(textmsg="???",bright=0.5, time_secs=3):
	global scrollphathd
	
	#if quiet hours do not display
	if is_quiet_time():
		return None
	
	 #  Clear buffer
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()

	endTime = datetime.datetime.now() + datetime.timedelta(seconds=time_secs)
	while True:
		if datetime.datetime.now() >= endTime:
			break
		for x in range(5,0,-1):
			brite=0.1*x
			scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7,brightness=brite)
			scrollphathd.show()
			time.sleep(0.03)
		for x in range(1,5,1):
			brite=0.1*x
			scrollphathd.write_string(textmsg, x=0, y=0, font=font5x7,brightness=brite)
			scrollphathd.show()
			time.sleep(0.03)
			
			
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()	
		

	return None	
	
def swipe():
		for x in range(18):
			scrollphathd.fill(0.1,0,0,x,7)
			scrollphathd.show()
		for x in range(18):
			scrollphathd.fill(0,0,0,x,7)
			scrollphathd.show()	
		return;

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
		time.sleep(0.1)
		#scrollphathd.scroll()
		#time.sleep(0.05)
        return
		
		
##############################################
#Paho MQTT Event Handlers
###########################################

def on_connect(client, userdata, flags, rc):
	global mqtt_timer
	now=int(round(time.time() ))
	elapsed= (now-mqtt_timer)
	print "onConnect with result code ..."+str(elapsed)+"s"
	print("rc: " + str(rc))
	if  (rc==0):
	  client.connected_flag=True #set flag
	  glow("OK",0.2,2)
	else:
	  show(str(rc),0.1 )
	  
	# Now lets subscrbe to messages from the broker
	# Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
	mqtt_topics = ["sensor/door/state", "sensor/door/runtime", "sensor/door/rssi", "sensor/door/bootcount","sensor/door/name"]
	for mqtt_topic in mqtt_topics:
		client.subscribe(mqtt_topic)
		print("Subscribing to: "+mqtt_topic)   

	mqtt_timer=int(round(time.time() ))
	
	
	return None


def on_message(client, obj, msg):
	global message,mqtt_timer
	
	source="unknown"  #client source is not known

	print("on_message Rcvd: "+ msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	
	if msg.retain==1:
		print("This is a retained message:")
		
	message = msg.payload

	#lts handle the diffferent payloads
	if msg.topic=="sensor/door/state":
		if (message=="1"):
			show("OPN",0.4)  # Open is =1 
		else:
			swipe()

	elif msg.topic=="sensor/door/bootcount":
		print(msg.topic+"  "+message)
		
	elif msg.topic=="sensor/door/name":
		source=message	

	else:
		print("No Topic/Message handler available")
		#show("???"+msg.topic,0.2)

	writedb_log(msg.topic,message,source)
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
	
##############################################
#Utility functions
###########################################
#determing if hourse are quiet time
def  is_quiet_time():
	global quiet_start, quiet_end
	
	now=datetime.datetime.now()
	this_time=now.time()
	
	# print("Now  :"+this_time.strftime("%H:%M:%S") )
	# print("Start:"+quiet_start.strftime("%H:%M:%S") )
	# print("End  :"+quiet_end.strftime("%H:%M:%S") )
	
	if in_between( this_time, quiet_start,quiet_end ):
		print "<<<< SHhhh QUIET HOURS - DISPLAY TURNED OFF >>>"
		return True
	else:
		return False



########################
# Main
########################
 
if "__main__" == __name__:

	
	now=datetime.datetime.now()
	this_time=now.time()

	# Testing methods go here...	
	#getExchangeRate()	
	#hournow()
	#calendardate()
	#getWeather()
	#hournowcity()
	#print "EndTesting"
	#quit()

	ip_address= get_ip_address('wlan0')
	writedb_log("STARTUP",ip_address,"SYSTEM")
	


	print("Now  :"+this_time.strftime("%H:%M:%S") )
	print("Start:"+quiet_start.strftime("%H:%M:%S") )
	print("End  :"+quiet_end.strftime("%H:%M:%S") )
	
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
	
	ip_address= get_ip_address('wlan0')
	print "Localhost IP adress:"+ip_address
	# Once we have told the client to connect, let the client object run itself
	# client.loop_forever()   this funciton is blocking
	scroll(" IP:"+ip_address,0.2,0.02,True)  #Display always regardless of quiet time
	

	calendardate()
	hournow()


	print "Connecting to MQTT broker at ", mqtt_broker_ip + "\nPort: " + str(mqtt_port)
	
   #connect(host, port=1883, keepalive=60, bind_address="")
	client.connect(mqtt_broker_ip, mqtt_port, 0)

	
#subscribe
	client.loop_start()	
	
	# see schedule for examples https://pypi.python.org/pypi/schedule
	

	schedule.every().day.at("9:00").do(calendardate)
	schedule.every().day.at("9:00").do(hournow)
	schedule.every().day.at("10:00").do(hournow)
	schedule.every().day.at("11:00").do(hournow)
	schedule.every().day.at("12:00").do(hournowcity)
	schedule.every().day.at("12:01").do(calendardate)
 	schedule.every().day.at("13:00").do(hournow)
 	schedule.every().day.at("14:00").do(hournow)
	schedule.every().day.at("15:00").do(hournow)
 	schedule.every().day.at("16:00").do(hournow)
	schedule.every().day.at("17:00").do(hournowcity)
	schedule.every().day.at("19:00").do(hournow)
	

	schedule.every(180).minutes.do(getWeather)  #every 3 hours show weather
	schedule.every(240).minutes.do(getExchangeRate)  #every 4 hours dispplay

	
	try:
		while True:
			schedule.run_pending()
			client.loop(.1)  #blocks for 100ms

	except KeyboardInterrupt:
		print "User Ended SubLed"
		scrollphathd.fill(0)
		scrollphathd.show()
		client.disconnect()

		quit()
