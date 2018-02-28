# LED StockTicker.PY

![LEd Stock Ticker](www.abrandao.com/wp-content/uploads/2018/02/stockticker_scrollphat.gif)

A simple Stock Ticker python script geared to using the Raspberyr Pi + ScrollPhat HD Led display
to show live (near real-time)stock quotes. The quotes pullled form Google Finance are updated peridically. 

One of two modes available, continuous stock ticker (the traditional look) or just an alerting stock ticker , where only
various percentage changes will trigger displays.

## Getting Started

to get started and how to setup the hardware see my blog post here 
[Blog Post on Stock Ticker ](http://www.abrandao.com/2018/02/raspberry-pi-zero-w-led-stock-ticker-code-and-demo/)



### Prerequisites

  * Raspberry Pi (any model that can use a 40-pin header), for compactnesss a Pi Zero W is best
  * [ScrollPhat HD] (https://shop.pimoroni.com/products/scroll-phat-hd)
  * Raspian installed and configured
  * [Scrollphat HD libraries] (https://github.com/pimoroni/scroll-phat-hd)
  * The code here.

```
Give examples
```

### Installing

Once the hardware and is confirmed running,  simmply clone this directory onto your Pi such as..

and issue the command

``
cd /home/pi
git clone <this git hub>  
```

```./python stockticker.py```

### Configuring the Stocks

Next edit the top of the script to suit your needs:
```
# Uncomment to rotate 180 degrees, useful for flipping rpi0 upside down easier with usb cord
scrollphathd.rotate(180)

#Ticker mode: 
# True: a scrolling ticker refrreshing all stocks continuously
# False: on specific alert price/percent change  displays stock price - silent otherwise
continuous_ticker=True # set to False to use Alert style

#Stock symbols Change stock symbols to match your favorites 
# format is {SYMBOL: % change to trigger}
#percent represents trigger % (1.50=1.5%)  PERCENT change value stock to appear when continuous_ticker=False
#if  stock price exceeds by -% / +%   it will be displayed
stock_tickers = {"DJI": 1.50, "F": 1.00, "T": 1.50,"GE": 1.50,"BP": 2.0,"TEVA": 1.50,"ROKU": 2.0,"GRMN": 3.0,"GLD": 2.0 }

#Ticker Title
TICKER_TITLE="ACB Stock Ticker"

# Dial down the brightness
scrollphathd.set_brightness(0.2)
```

Now save the changes and run the script

```python ledstock.py ```   

## Running at strartup

Once you're satisfied with the setup and confirm that the script works, you can now have it run automatically by adding it to the 
```/etc/rc.local``` file on your pi, here's a sample

```
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

#Run the led stockticker at startup
python /home/pi/raspberry_pi/ledstocks/stockticker.py >> /tmp/stockticker.log &


exit 0

```

## Deployment

Simple run the stockticker.py

## Contributing

If you're interested in updating this script or have some ideas feel free to gt in touch.

## Versioning


## Authors


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
