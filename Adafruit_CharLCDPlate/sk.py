#!/usr/bin/python

import os
import socket
import psutil
import urllib2
from time import sleep
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from datetime import datetime

def service_run(process_name="apache2", checkport=80):
	running = False
	for proc in psutil.process_iter():
		if proc.name != process_name:
			# Not target
			continue
		for con in proc.get_connections():
			# Tuple ip, port
			port = con.local_address[1]
			if port == int(checkport):
				running = True
	return running

if os.name != "nt":
    import fcntl
    import struct
    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
            )[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = ["eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break;
            except IOError:
                pass
    return ip
    
def internet_on(ip='88.198.158.155'):
    try:
        response=urllib2.urlopen('http://' + ip,timeout=1)
        return True
    except:
    	pass
    return False

# Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
global lcd
lcd = Adafruit_CharLCDPlate()
lcd.backlight(lcd.GREEN)

ip = get_lan_ip()

def error_check():
	error = 0
	warning = 0
	if service_run('nginx', '80') == False and service_run('apache2', '80') == False:
		error += 1
	if service_run('mysqld', '3306') == False:
		error += 1
	if internet_on(ip) == False and service_run('apache2', '80'):
		error += 1
	if internet_on() == False:
		warning += 1
	
	return [error, warning]

time = datetime.now().strftime('%H:%M')
global min
min = datetime.now().strftime('%M')

global warnmsg
warnmsg = ''
checkres = error_check()
if checkres[0] > 0 or checkres[1] > 0:
	warnmsg = ' !'

def init_screen(msg1 = 'dieSPEISEKARTE', msg2 = 'v1.0.1     ', time = datetime.now().strftime('%H:%M'), check = True, warnmsg = warnmsg):
	if check == True:
		checkres = error_check()
		if checkres[0] > 0 or checkres[1] > 0:
			warnmsg = ' !'
		else:
			warnmsg = ''

	if warnmsg == '':
		lcd.backlight(lcd.GREEN)
	else:
		lcd.backlight(lcd.YELLOW)
	lcd.clear()
	lcd.message(msg1 + warnmsg + '\n' + msg2 + time)
	return msg1 + warnmsg + '\n' + msg2 + time
	
initmsg = init_screen()

# Clear display and show greeting, pause 1 sec
sleep(1)

# Cycle through backlight colors
col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL,
       lcd.BLUE, lcd.VIOLET, lcd.ON   , lcd.OFF)

# Poll buttons, display message & set backlight accordingly
btn = ((lcd.LEFT    , 'dieSPEISEKARTE\nRest. Stufenbau'     , lcd.GREEN),
       (lcd.UP    , 'dieSPEISEKARTE\nRest. Stufenbau'     , lcd.GREEN),
       (lcd.DOWN  , 'dieSPEISEKARTE\nOrders: 314'    , lcd.GREEN),
       (lcd.RIGHT , 'dieSPEISEKARTE\nIP: ' + ip, lcd.GREEN)	)

state = 'normal'
while True:
	sleep(0.1)
	for b in btn:
		if lcd.buttonPressed(lcd.LEFT):
			lcd.clear()
			lcd.message('dSK Status:\nChecking...')
			lcd.backlight(lcd.YELLOW)
			sleep(1)
			check = error_check()
			error = check[0]
			warning = check[1]
			if error == 0 and warning == 0:
				lcd.clear()
				lcd.message('dSK Status:\nAll is good!')
				lcd.backlight(lcd.GREEN)
			else:
				if error > 0 and warning > 0:
					msg = '%s Err / %s Warn >' % (error, warning)
					state = 'error'
				elif error > 0:
					msg = '%s Error(s)     >' % (error)
					state = 'error'
				elif warning > 0:
					msg = '%s Warning(s)   >' % (warning)
					state = 'warning'
				lcd.clear()
				lcd.message('dSK Status:\n%s' % (msg))
				if state == 'error':
					lcd.backlight(lcd.RED)
				elif state == 'warning':
					lcd.backlight(lcd.YELLOW)
		elif lcd.buttonPressed(lcd.SELECT):
			init_screen(time = datetime.now().strftime('%H:%M'), check = False)
		elif lcd.buttonPressed(b[0]):
			if state == 'error' or state == 'warning':
				if lcd.buttonPressed(lcd.RIGHT):
					message = []
					if service_run('nginx', '80') == False and service_run('apache2', '80') == False:
						message.append('HTTP')
					if service_run('mysqld', '3306') == False:
						message.append('SQL')
					if internet_on(ip) == False and service_run('apache2', '80'):
						message.append('Link')
					if internet_on() == False:
						message.append('Web')
					lcd.clear()
					lcd.message('dSK Error:\n' + ','.join(message))
					lcd.backlight(lcd.YELLOW)
				elif lcd.buttonPressed(lcd.SELECT):
					state = 'normal'
					break
			else:
				lcd.clear()
				lcd.message(b[1])
				lcd.backlight(b[2])
			break
		else:
			newmin = datetime.now().strftime('%M')
			if newmin != min:
				min = newmin
				initmsg = init_screen(time = datetime.now().strftime('%H:%M'))