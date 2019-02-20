#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""portalLogin.Py : A python script that makes use of  elinks + pexpect Library  to send keystrokes to a  Captive Portal login
Most captive Portals imply have an "I AGREE" (or equivelant ) button or image this scrpt makes use of teh Pepect Python library
to send keystrokes to the  shell, monitors those keystrokes and  performs certain actions. 

Each captive Portal is  unqiue in its own way and will likely require you cusotmize the command sequence below.

Requires: 
pexpect  Python Keystroke  library ( pip install pexpect )
elinks  Linux terminal text-based web browser (sudo at-get install elinks)


Author: Abrandao.com
Date: 3-14-2018
"""
import sys
from pexpect import spawn
import time
import datetime

KEY_UP = '\x1b[A'
KEY_DOWN = '\x1b[B'
KEY_RIGHT = '\x1b[C'
KEY_LEFT = '\x1b[D'
KEY_ESCAPE = '\x1b'
KEY_BACKSPACE = '\x7f'

URL="www.yahoo.com"
PortalResponse="Welcome to AT&T Wi-Fi"

launch_url='elinks '+URL 
print "Spawning:  ", launch_url
child = spawn(launch_url, encoding='utf-8')
time.sleep(0.1)
sys.stdout = open('pexpect_stdout.txt', 'w')
child.logfile=sys.stdout

# child.interact() #uncomment to interact with elinks, good for debugging
# child.expect(PortalResponse)
# print("Response: ", child.before)
time.sleep(0.3)
#print 'Accepting Terms Now Logging in Via keystrokes'
for  x in range(5): #send 5 DOWNN press with slight delay in between
	child.sendline(KEY_DOWN)
	time.sleep(0.1)   

child.sendline('')
time.sleep(0.1)
child.sendline('Y')  #press ENTER key 2x
child.sendline('')
#print("Response: ", child.before)
child.sendline('')
child.sendline('q')
child.sendline('Y')
child.close()
print "Finished:"
