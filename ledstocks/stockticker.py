#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""StockTicker.Py : A python script that makes use of ScrollPhat HD on Raspberyr Pi to produce live
near real-tme stock quotes. Makes use of screen scraping (or Stock API) to grab specific stock prices
and displays them in a standard scrolling ticker format. Heavily borrows code for Advanced Scrolling 
Pimoroni library to make the ticker have a more animated look.


Requires: Raspberry Pi + ScrollPhat HD
https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-scroll-phat-hd

Author: Abrandao.com
Date: 2-25-2018


"""
import json
import fcntl
import struct
import socket
import operator
import subprocess
import socket
import os
import time
import urllib2
import re
from datetime import datetime
try:
  import scrollphathd
except ImportError:
  raise ImportError('Error Importing Module: scrollphathd Check hardware')


print("""
StockTicker.py a Scroll pHAT HD python script for Live stock quotes.
Advanced scrolling example which displays a message line-by-line
Press Ctrl+C to exit.
""")

# Uncomment to rotate 180 degrees, useful for flipping rpi0 upside down easier with usb cord
scrollphathd.rotate(180)


#how long to wait secs.  before refreshing data and blanking screen
REFRESH_INTERVAL = 180 #defult every  three  minutes


#Ticker mode: 
# True: a scrolling ticker refrreshing all stocks continuously
# False: on specific alert price/percent change  displays stock price - silent otherwise
continuous_ticker=False # set to False to use Alert style


#Stock symbols Change stock symbols to match your favorites 
# format is {SYMBOL: % change to trigger}
#percent represents trigger % (1.50=1.5%)  PERCENT change value stock to appear when continuous_ticker=False
#if  sotck price exceeds by -% / +%   it will be displayed
stock_tickers = { ".DJI" : 0.60 , ".IXIC" : 0.60 , "F": 1.00, "T": 1.00,"GE": 1.50,"BP": 2.0,"TEVA": 1.50,"ROKU": 2.0,"GRMN": 2.0,"GLD": 1.00 }

#Ticker Title
TICKER_TITLE="ACB Stock Ticker"

# Dial down the brightness
scrollphathd.set_brightness(0.2)

# If rewind is True the scroll effect will rapidly rewind after the last line
rewind = True


# Speed of ticker Delay is the time (in seconds) between each pixel scrolled
delay = 0.03

#display certain items, like title or ip address one time in display
display_once=True

#LCD Lines buffer -Global lines buffer to hold scrolling text
lines = []


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])



def internet_connected(ip='172.217.12.142'):  
  try:
     # connect to the host -- tells us if the host is actually
    # reachable
    s = socket.create_connection((ip, 80), 2)
    return True
  except:
     pass
  return False

def scrollLine(msg):
  scrollphathd.write_string(msg, x=0, y=0)
  scrollphathd.show()
  scrollphathd.scroll()

  return 


def swipe():
	try:
	  print "Swiping the display..."
	  for x in range (3):	
		for z in range(18):
			scrollphathd.fill(0.6,0,0,z,7)
			scrollphathd.show()

		for z in range(18):
			scrollphathd.fill(0.1,0,0,z,7)
			scrollphathd.show()
	
		print "End Swipe the display..."
  	except KeyboardInterrupt:
		
		scrollphathd.fill(0)
		scrollphathd.show()

  	return None


def blink(msg):
  scrollphathd.clear()  # so we can rebuild it
  scrollphathd.show()
  time.sleep(0.5) 
  scrollphathd.write_string( msg, x=0, y=0)
  scrollphathd.show()
  time.sleep(0.5)
  scrollphathd.fill(0)
  scrollphathd.show()
  return    

# Call external shell script to try and reconnect...
# source shell script: https://gist.github.com/mharizanov/5325450 
def wifi_reconnect():
  result=False

  print "Checking connection"
  scrollLine("Trying to reconnect...Reseting Wlan0 ")
  # try to recover the connection by resetting the LAN  
  return result


def stockquote(symbols=None):
	global json_data
	stock_table=''

	symbol_list= symbols.split(",")

	if  internet_connected()==False:
		return  json.loads('{"Stocks":["OffLine"]}')
	
	if not symbols:
		return  json.loads('{"Stocks":["No Symbols"]}')

	# Stock web scraping code,  I know this is not the best way ... its quick and dirty :)
	# this can be revised to use an API-key based stock price tool
	#  Consider rewriting this section using  https://pypi.python.org/pypi/googlefinance  
	# or using pandas-datareader https://github.com/pydata/pandas-datareader 
	# right now we just scrape google page 

	try:
		base_url ="https://finance.google.com/finance?q="+symbols

		print "fetching... "+base_url
		headers = { 'User-Agent' : 'Mozilla/5.0' }
		req = urllib2.Request(base_url, None, headers)
		html = urllib2.urlopen(req).read()

		#first use reg ex to extract the JSON snippet all the stock quotes we need
		stock_table = re.search('"rows":(.*?)]}]', html)

		json_string = stock_table.string[stock_table.start():stock_table.end()]  # extract the json
		json_string= "{"+ json_string + "}"
		json_data = json.loads(json_string)  #convert into a json data object
		#print json_data
	except Exception as e: 
		print(e)
		return  json.loads('{"Stocks":["Data scraoe error: ',e,']}')


	return json_data 



  
def get_stock_quotes():
	global continuous_ticker,stock_tickers
	stock_quote_lines=''	
	symbols=''

	print "Getting Stock prices mode: (Continuous "+str(continuous_ticker)+")"

	# how to sort a dictionary
    # for key in sorted(mydict.iterkeys()):
    #   print "%s: %s" % (key, mydict[key])

	for symbol, pct in stock_tickers.items():
		symbols = symbols+ symbol+","  # comma delimited symbols list
	symbols = symbols.rstrip(',')  #stip off the last comma

	print "Stocks: "+symbols
	if   internet_connected()==True:     #lets make sure we're still onlne
		stock_data =stockquote(symbols)  # lets get ALL the stock quotes
	else:
		stock_quote_lines="Offline :: no quotes avaialble -  check Internet connection"
		return stock_quote_lines


	print stock_data

	for s in stock_data["rows"]:
		stock_symbol=s['values'][0]
		stock_price=s['values'][2]
		stock_change=s['values'][3]
		stock_percent=s['values'][5]

		if continuous_ticker==True :   #continuosly display prices
		  stock_quote_lines+= stock_symbol+" "+ stock_price+ " "+ stock_change + "  ."
		  print "Stocks:  "+stock_symbol+ " $"+stock_price +"  "+ stock_change +" "+stock_percent+"%"

		else:
		  try:
			pct_change =float(stock_percent)  #convert the percentage 
			pct_change =float(stock_percent)  #convert the percentage 
		  except Exception as e:
			print e
			pct_change =0.0

		  print stock_symbol+"::"+stock_price+"  "+ str(pct_change) + "%  threshold: "+str(stock_tickers[stock_symbol]) 
		  if abs(pct_change) >= stock_tickers[stock_symbol]:  #did the stock change +/- more than % trigger?
			stock_quote_lines+= " "+stock_symbol+" "+ stock_price  + " "+stock_change  + " " +stock_percent + "%  "
			print "<<DISPLAY>>:  "+stock_symbol+ " $"+stock_price+"  "+stock_change+" "+stock_percent+"% ("+str(stock_tickers[stock_symbol])+") "+stock_symbol

	return stock_quote_lines

def  load_data():
  global display_once, lines

  # empty lcd buffer
  lines[:] = []

  #one time display
  if display_once==True:
	  print  "Gettig Ticker DATA ..." 
	  lines.append(TICKER_TITLE )
	  ip_address=get_ip_address("wlan0")
	  print "IP: "+ip_address
	  lines.append("IP: "+ip_address )
	  display_once=False  #now no longer display

  #get Stock quotes
  lines.append( get_stock_quotes() )

  #Every hour on the hour   blink time
  onthehour= datetime.now().strftime('%M')
  if  onthehour=="00" :
     #  Blink on the hours
    for y in range(5):
      blink( datetime.now().strftime('%H%p') )
        
  
  now = datetime.now().strftime('%m-%d-%y %H:%M %p')    
  lines.append(now )
 
  print "Time: "+now
 

  return lines


def startled():
	global scrollphathd, lines ,lengths,line_height

	#  Clear buffer
	scrollphathd.clear()  # so we can rebuild it
	scrollphathd.show()


	if  internet_connected()==False:
		print "No Internet connection available. No data to display" #getip addressss
		lines.append("IP: "+get_ip_address("wlan0") )
		lines.append("OFFLINE: NO Internet Connection.")
		scrollLine(lines)
	else:
		print "Initial data load"
		load_data()



	lines.append("")   #append a final blank line to cause a scroll off 
	#code below directly from Pimoroni Advanced-scrolling example
	# Determine how far apart each line should be spaced vertically
  	line_height = scrollphathd.DISPLAY_HEIGHT + 2

	# Store the left offset for each subsequent line (starts at the end of the last line)
	offset_left = 0

	# Draw each line in lines to the Scroll pHAT HD buffer
	# scrollphathd.write_string returns the length of the written string in pixels
	# we can use this length to calculate the offset of the next line
	# and will also use it later for the scrolling effect.
	lengths = [0] * len(lines)

	print "Content of lines buffer: "+str(len(lines))
	print lines


	for line, text in enumerate(lines):
		lengths[line] = scrollphathd.write_string(text, x=offset_left, y=line_height * line)
		offset_left += lengths[line]

		print "Adding to buffer: "+text
		# This adds a little bit of horizontal/vertical padding into the buffer at
		# the very bottom right of the last line to keep things wrapping nicely.
		scrollphathd.set_pixel(offset_left - 1, (len(lines) * line_height) - 1, 0)

	
	return; #end of start_lcd



#Start of the Main Program Logic , setup display and scroll vairables
if __name__ == "__main__":


	#check for hardware and make sure no GPIO / hardware faults

	try:  
		print "Checking Hardware ScrollPhat HD is availble"  
		swipe()
		print " Passed!"  
	except KeyboardInterrupt:  
		# here you put any code you want to run before the program   
		# exits when you press CTRL+C  
		print "\n", counter # print value of counter  
	except:  
		# this catches ALL other exceptions including errors.  
		print "Hardware Error SchrollPhat HD is no responding. Check hardware."  

	### Load the main data and LED display
	startled()



	#loop and scroll content

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
			if current_line == len(lines) - 1:
			   swipe()
			   print "Sleeping for "+str(REFRESH_INTERVAL)+" seconds"
			   time.sleep(REFRESH_INTERVAL)   
			   print "Awake refreshing data..."
			   startled()  #reload new data into LCD 

			# Otherwise, progress to the next line by scrolling upwards
			else:
			    for x in range(line_height):
			        scrollphathd.scroll(0, 1)
			        pos_y += 1
			        scrollphathd.show()
			        time.sleep(delay)