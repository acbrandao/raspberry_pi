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
from pexpect import spawn
import time
import datetime

KEY_UP = '\x1b[A'
KEY_DOWN = '\x1b[B'
KEY_RIGHT = '\x1b[C'
KEY_LEFT = '\x1b[D'
KEY_ESCAPE = '\x1b'
KEY_BACKSPACE = '\x7f'

URL="http://start.att.net"
PortalResponse="Welcome to AT&T Wi-Fi"


print "Spawning:  ", 'elinks ',URL
child = spawn('elinks '+URL)
print 'waiting for ',URL,' to load'
# child.interact()
# child.expect(PortalResponse)
print("Response: ", child.before)
time.sleep(0.1)
print 'Accepting Terms Now Logging in Via keystrokes'
child.sendline(KEY_DOWN * 5)
time.sleep(0.1)
child.sendline('')
time.sleep(0.1)
child.sendline('')  #press ENTER key 2x

#print 'waiting for search results'
print("Response: ", child.before)
#child.expect('(*?)')   #expect anything
#time.sleep(0.1)
#child.interact() #uncomment to interact with elinks, good for debugging
print 'quiting'
child.sendline('q')
child.wait()
