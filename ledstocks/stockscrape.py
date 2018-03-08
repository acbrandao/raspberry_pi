#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2
import re

#Stock symbols Change stock symbols to match your favorites 
# format is {SYMBOL: % change to trigger}
#percent represents trigger % (1.50=1.5%)  PERCENT change value stock to appear when continuous_ticker=False
#if  sotck price exceeds by -% / +%   it will be displayed
stock_tickers = {"AAPL": 1.50, "NFLX": 1.00, "T": 1.50,"GE": 1.50,"BP": 2.0}
json_data= None

def stockquote(symbols=None):
	global json_data
	stock_table=''

	symbol_list= symbols.split(",")
	
	if not symbols:
		return  json.loads('{"Stocks":["none"]}')

	# Stock web scraping code,  I know this is not the best way ... its quick and dirty :)
	# this can be revised to use an API-key based stock price tool
	#  Consider rewriting this section using  https://pypi.python.org/pypi/googlefinance  
	# or using pandas-datareader https://github.com/pydata/pandas-datareader 

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
	except Exception as e: print(e)


	return json_data 

	
symbols=''

for symbol, pct in stock_tickers.items():
	symbols = symbols+ symbol+","  # comma delimited symbols list
	
symbols = symbols.rstrip(',')  #stip off the last comma
	
print "Stocks: "+symbols
stock_data =stockquote(symbols)

#print stock_data

for s in stock_data["rows"]:
	print s['values'][0]+' '+s['values'][2]+' '+s['values'][3]+' '+s['values'][5]


  
