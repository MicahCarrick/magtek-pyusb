#!/usr/bin/python
"""
Read a MagTek USB HID Swipe Reader in Linux. A description of this
code can be found at: http://www.micahcarrick.com/credit-card-reader-pyusb.html

You must be using the new PyUSB 1.0 branch and not the 0.x branch.

Copyright (c) 2010 - Micah Carrick
"""
import sys
import usb.core
import usb.util

VENDOR_ID = 0x0801
PRODUCT_ID = 0x0002
DATA_SIZE = 337

# find the MagTek reader

device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if device is None:
    sys.exit("Could not find MagTek USB HID Swipe Reader.")

# make sure the hiddev kernel driver is not active

if device.is_kernel_driver_active(0):
    try:
        device.detach_kernel_driver(0)
    except usb.core.USBError as e:
        sys.exit("Could not detatch kernel driver: %s" % str(e))

# set configuration

try:
    device.reset()
    device.set_configuration()
except usb.core.USBError as e:
    sys.exit("Could not set configuration: %s" % str(e))
    
endpoint = device[0][(0,0)][0]

# wait for swipe

data = []
swiped = False
print "Please swipe your card..."

while 1:
    try:
        data += device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
        if not swiped: 
            print "Reading..."
        swiped = True

    except usb.core.USBError as e:
        if e.args == ('Operation timed out',) and swiped:
            if len(data) < DATA_SIZE:
                print "Bad swipe, try again. (%d bytes)" % len(data)
                print "Data: %s" % ''.join(map(chr, data))
                data = []
                swiped = False
                continue
            else:
                break   # we got it!

# now we have the binary data from the MagReader! 

enc_formats = ('ISO/ABA', 'AAMVA', 'CADL', 'Blank', 'Other', 'Undetermined', 'None')

print "Card Encoding Type: %s" % enc_formats[data[6]]

print "Track 1 Decode Status: %r" % bool(not data[0])
print "Track 1 Data Length: %d bytes" % data[3]
print "Track 1 Data: %s" % ''.join(map(chr, data[7:116]))

print "Track 2 Decode Status: %r" % bool(not data[1])
print "Track 2 Data Length: %d bytes" % data[4]
print "Track 2 Data: %s" % ''.join(map(chr, data[117:226]))

print "Track 3 Decode Status: %r" % bool(not data[2])
print "Track 3 Data Length: %d bytes" % data[5]
print "Track 3 Data: %s" % ''.join(map(chr, data[227:336]))

# since this is a bank card we can parse out the cardholder data

track = ''.join(map(chr, data[7:116]))

info = {}

i = track.find('^', 1)
info['account_number'] = track[2:i].strip()
j = track.find('/', i)
info['last_name'] = track[i+1:j].strip()
k = track.find('^', j)
info['first_name'] = track[j+1:k].strip()
info['exp_year'] = track[k+1:k+3]
info['exp_month'] = track[k+3:k+5]

print "Bank card info: ", info

    
