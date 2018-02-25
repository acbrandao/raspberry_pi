#!/usr/bin/env python
import subprocess
import os
import time
import feedparser
import signal
import json
import socket
from urllib2 import urlopen
import urllib
import re
from datetime import datetime
try:
  import scrollphathd
except ImportError:
  raise ImportError('Error Importing Module: scrollphathd Check hardware')


print("""
Scroll pHAT HD: Advanced Scrolling
Advanced scrolling example which displays a message line-by-line
and then skips back to the beginning.
Press Ctrl+C to exit.
""")

# Uncomment to rotate 180 degrees
#scrollphathd.rotate(180)
#Ticker Title
TICKER_TITLE="Tony Ticker"

# Dial down the brightness
scrollphathd.set_brightness(0.2)

# If rewind is True the scroll effect will rapidly rewind after the last line
rewind = True

#how long to wait secs.  before refreshing data and blanking screen
REFRESH_INTERVAL = 10

# Delay is the time (in seconds) between each pixel scrolled
delay = 0.02

#maximum number of lines to  display - prevent buffer overflow
max_lines  =  4
 
#max chars news headlines
max_headline_length=40

#Stock symbols
stock_tickers =["DJI","F","T","GE","BP","TEVA","ROKU","GRMN","GLD"]

#LCD Lines buffer -Global 
lines = []

def is_connected(ip='172.217.12.142'):  
  try:
     # connect to the host -- tells us if the host is actually
    # reachable
    s = socket.create_connection((ip, 80), 2)
    return True
  except:
     pass
  return False

def scrollLine(msg):
	scrollphathd.write_string(msg, x=0, y=0, font=font5x7, brightness=0.1)
	scrollphathd.show()
	scrollphathd.scroll()

	return   

# Call external shell script to try and reconnect...
# source shell script: https://gist.github.com/mharizanov/5325450	
def wifi_reconnect():
	global lines
	result=False

	print "Trying to reconnect:"
	scrollLine("Trying to reconnect...Reseting Wlan0 ")
	# try to recover the connection by resetting the LAN
	subprocess.call(['logger "WLAN is down, Pi is resetting WLAN connection"'], shell=True)
	result = True # try to recover
	subprocess.call(['sudo /sbin/ifdown wlan0 && sleep 10 && sudo /sbin/ifup --force wlan0'], shell=True)
	scrollLine("Finished Resetting Wlan0 ")
	
	return result


def stockquote(symbol):
    quote=[]
    base_url = 'http://finance.google.com/finance?q='
    content = urllib.urlopen(base_url + symbol).read()
    m = re.search('id="ref_(.*?)">(.*?)<', content)
    q = re.search('id="ref_(.*?)_c">(.*?)<', content)
    if m:
		quote.append( m.group(2) )
		quote.append( q.group(2) )
    else:
        quote = 'no quote available for: ' + symbol
    return quote

	
def get_stock_quotes():

	stock_quote_lines=''
	
	for symbol in stock_tickers:
		stock_val =stockquote(symbol)
		print "Stocks:  "+symbol+ " $"+stock_val[0]+"  "+stock_val[1]
		stock_quote_lines+= symbol+" "+ stock_val[0] + " "+ stock_val[1] + " | "


	return stock_quote_lines
	

def filltest():
  try:
    while True:
        for x in range(18):
            scrollphathd.fill(0.1,0,0,x,7)
            scrollphathd.show()
        for x in range(18):
            scrollphathd.fill(0,0,0,x,7)
            scrollphathd.show()
  except KeyboardInterrupt:
    scrollphathd.fill(0)
    scrollphathd.show()

  return

def getweather():
	#get weather forcast.io  --- requires a api key
	apikey="cecade584092bac0e862aad1f9615018" # get a key from https://developer.forecast.io/register
	# Latitude & longitude - change values to match your location.
	lati="40.8021296"
	longi="-74.167454"

	# Add units=si to get it in sensible ISO units not stupid Fahreneheit.
	url="https://api.forecast.io/forecast/"+apikey+"/"+lati+","+longi+"?units=us"

	meteo=urlopen(url).read()
	meteo = meteo.decode('utf-8')
	weather = json.loads(meteo)

	print "weather: {} {} F".format( weather['currently']['summary'] ,  weather['currently']['temperature'] )

	return weather
	
def getip_address():
	ip_address=[l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

	print  "Getting IP "+ip_address 
	return ip_address

def getnews():
	articles=0
	headlines=[]
	print  "Getting news feeds..." 

	#get the news 
	feed = feedparser.parse("http://feeds.reuters.com/reuters/topNews")
	feed_title = feed['feed']['title']
	feed_entries = feed.entries

	for entry in feed.entries:
		headline = entry.title[0:max_headline_length]
		
		headlines.append(headline)
		print headline
		articles=articles+1
		if articles >= max_lines:
			break

	return  headlines
	



def  load_data():
	# empty lcd buffer
	lines[:] = []

	print  "Gettig Ticker DATA ..."	
	lines.append(TICKER_TITLE )

	#getip addressss
	lines.append("IP: "+getip_address() )

	#get the weather
	weather=getweather()
	lines.append( weather['currently']['summary'] +" "+  str(round( weather['currently']['temperature'],0) ) + "F" )

	#get Stock quotes
	lines.append( get_stock_quotes() )

	#get news headlines
	stories=getnews()
	for story in stories:
		lines.append(""+story)

	now = datetime.now().strftime('%m-%d-%y %H:%M %p')
	lines.append(now )
	print "Time: "+now
	return


def startlcd():
	global scrollphathd, lines , lengths, line_height,offset_left
	
#  Clear buffer
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()


	if is_connected() == False:
		print "No Internet connection available. No data to display" #getip addressss
	        lines.append("IP: "+getip_address() )
		lines.append("NO Internet Conneciton");

		scrollLine(lines);
		# status = wifi_reconnect()
		# if status == True :
	   	#	scrollLine("IP: "+getip_address() )
		# else:
	   	#scrollLine("Not connected to WIFI..")
		# os.system("iwlist wlan0 scan | grep SSID ")
		#wifi_spots=os.popen('iwlist wlan0 scan | grep ESSID').read()
		#wifi_spots= wifi_spots.replace(" ", "")	
		#lines.append(wifi_spots.replace("ESSID:", ""))	
		#lines.append("Available Wifi:"+wifi_spots)
		# Disabled because it causes loss of network wifi_reconnect()

	else:
		print "Initial data load"
		load_data()




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

	# This adds a little bit of horizontal/vertical padding into the buffer at
	# the very bottom right of the last line to keep things wrapping nicely.
	scrollphathd.set_pixel(offset_left - 1, (len(lines) * line_height) - 1, 0)
	return




#check for hardware and make sure no GPIO / hardware faults
  
try:  
   print "Checking Hardware ScrollPhat HD is availble"  
   scrollphathd.scroll_to(0, 0)
   print " Passed!"  

   print "Rotatng display - for placing upside down with Pi zero"
   scrollphathd.rotate(180)
    
except KeyboardInterrupt:  
    # here you put any code you want to run before the program   
    # exits when you press CTRL+C  
    print "\n", counter # print value of counter  
  
except:  
    # this catches ALL other exceptions including errors.  
    # You won't get any error messages for debugging  
    # so only use it once your code is working  
    print "Hardware Error SchrollPhat HD is no responding. Check hardware."  
  
#finally:  
#    GPIO.cleanup() # this ensures a clean exit  

### Start main loading 
startlcd()


	
while True:
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

        # If we're currently on the very last line and rewind is True
        # We should rapidly scroll back to the first line.
        if current_line == len(lines) - 1 and rewind:
           # for y in range(pos_y):
           #     scrollphathd.scroll(-int(pos_x/pos_y), -1)
           #     scrollphathd.show()
           #     time.sleep(delay)
           print "Sleeping for "+str(REFRESH_INTERVAL)+" seconds"
           time.sleep(REFRESH_INTERVAL)   
           print "Awake refreshing data..."
           startlcd()  #reload new data into LCD display
         

        # Otherwise, progress to the next line by scrolling upwards
        else:
            for x in range(line_height):
                scrollphathd.scroll(0, 1)
                pos_y += 1
                scrollphathd.show()
                time.sleep(delay)
