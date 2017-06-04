"""
hp_display.py

Video playback and headphone selection monitoring commisioned by Rob Larsen

By Marcus Cook <tech@theshogunlodge>
Shogun Lodge Services
2017

Thanks to the authors of all libraries/wrappers used.

Shogun Lodge Services acknowledges the traditional owners and custodians of the 
land on which it works, the Wurundjeri people of the Kulin Nation. It pays 
respects to their Elders both past and present and acknowledges that 
sovereignty has never been ceded.
   
"""

#!/usr/bin/python

import sys
import subprocess
import time
import RPi.GPIO as GPIO

from omxplayer import OMXPlayer
from time import sleep

GPIO.setmode(GPIO.BCM)

# \/\/-Variables-\/\/

# --GPIO--
SWITCH1 = 13			# Headphone switch 1
SWITCH2 = 12			# Headphone switch 2
exitButt = 26			# Exit button

# --Switch State--
skip = 0			# Skip flag - Stops main video reloading itself when 'fade down' aborted

# --Video Locations--
vidA = '/home/pi/video/handbreak_mp4/Layer_1_handbreak.mp4'
vidB = '/home/pi/video/handbreak_mp4/GandjalalaTV_handbreak.mp4'

#vidA = '/home/pi/video/video_a.mp4'		# 'Title Card' video
#vidB = '/home/pi/video/GandjalalaTV_ffmpeg.mp4' # Main video
 
# --Log Files--
logFile = "/home/pi/log/hp_log.txt"				# Log file  - Count of headphone use

# \/\/-Set Ups-\/\/

GPIO.setup(SWITCH1, GPIO.IN, pull_up_down=GPIO.PUD_UP)		# Switch pulled up
GPIO.setup(SWITCH2, GPIO.IN, pull_up_down=GPIO.PUD_UP)		# Switch pulled up
GPIO.setup(exitButt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

player = OMXPlayer(vidA, args=['--no-osd', '-b', '--loop', '--alpha', '0']) # First on 'Title Card'
player.set_aspect_mode("fill")

rtc_time=subprocess.check_output("sudo hwclock -r",  shell=True)	# Read real time clock

# Open log file and write in time and date of boot up
with open(logFile, "a") as file:
	file.write('\n')
	file.write('\n')
	file.write(rtc_time)
	file.write('\n')

# \/\/-Functions-\/\/

# Read states of heaphone switches
def switch_state():
	ip1 = GPIO.input(SWITCH1)
	ip2 = GPIO.input(SWITCH2)

	if (ip1 == 1) or (ip2 == 1):		# Is either heaphone 'up'?
		time.sleep(0.010)		# Debounce
		if (ip1 == 1) or (ip2 == 1):
			x = int(1)		# Value to return

	if (ip1 == 0) and (ip2 == 0):		# Are both headphones down?
		time.sleep(0.010)
		if (ip1 == 0) and (ip2 == 0):
			x = int(0)
	return x

# Fades currnet video down. 'dwn' is the range jump amount and controls speed of fade
# 'flag' is so possiable fade back up only happens in main video
def vidDwn(dwn, flag):
	print "Fading Down..."			# Testing
	start = time.time()			# Testing - Start timer
	for alpha in range(254, -1, dwn):       # Fade loop
		x = switch_state()		# Has headphone been picked up?
		if(x == 1) and (flag == 1):	# If hp up and in main video start fading back up
			print "Hold On!"	# Testing
			vidUp(alpha, 2)
			skip = 1		# Set skip flag
			log()			# Log event
			return skip
		player.set_alpha(alpha)		# Set video alpha
		vol = float(alpha)		
		vol = ((vol/0.0425)-6000.0) 	# Make volume value relative to alpha value
		player.set_volume(vol)		# Set audio volume
	player.quit()				# Stop video
	print "Video Stop"			# Testing
	elapsed = (time.time() - start)		# Testing - Stop timer
	print (alpha)				# Testing
	print (vol / 100)			# Testing
	print (elapsed)				# Testing
	skip = 0				# Set skip flag
	return skip				

# Fades just started video up. 's' is start of fade alpha value
# 'up is the range jump amount and controls speed of fade
def vidUp(s, up):
	print "Fading Up..."			# Testing
	start = time.time()			# Testing - Start timer
        for alpha in range(s, 256, up):		# Fade loop
		player.set_alpha(alpha)		# Set video alpha
                vol = float(alpha)		
                vol = ((vol/0.0425)-6000.0)	# Make volume value relative to alpha value
                player.set_volume(vol)		# Set audio volume
	print "Video Up"			# Testing
        elapsed = (time.time() - start)		# Testing - Stop timer
        print (alpha)				# Testing
	print (vol / 100)			# Testing
	print (elapsed)				# Testing

# Logs headphone 'up' events
def log():
	with open(logFile, "a") as file:
		file.write(" X ")

# Exits script with button press
def interrupt(channel):
	player.quit()
        GPIO.cleanup()
        print ' '
        print "See Ya Later Button Pressed (>'.')>"
        exit("Interrupt Exit")

# \/\/-Main Code-\/\/

# Play 'Title Card'
player.set_alpha(255)
time.sleep(0.5)
player.play()
time.sleep(0.5)
player.pause()

GPIO.add_event_detect(exitButt, GPIO.FALLING, callback=interrupt, bouncetime=200) 

print "State A Video Displayed"			# Testing

print "Here we go... HP Switches Active"		# Testing

try:
	while(1):
		while(1):			
			a = switch_state()	# Test headphone switch state
			if(a != 0):		# If a headphone 'up'
				log()		# Log event
				break
                
		if(skip == 0):										# If 'Title Card' is up
			print 'State B Video Selected'							# Testing
        		vidDwn(-6,0)									# Fade 'Title Card' ~ 2 sec.
			player = OMXPlayer(vidB, args=['--no-osd', '-b', '--loop', '--alpha', '0'])	# Main video
			player.set_volume(-6000.0)							# Volume = -60dB
        		player.set_aspect_mode("fill")							# Set aspect
			vidUp(1,12)									# Fade up ~ 1 sec
		
		skip = 0										# Clear skip flag

        	while(1):
        		b = switch_state()	# Test headphone switch state
			if(b != 1):		# If both headphones down
				break

		print 'State A Video Selected'	# Testing	
		skip = vidDwn(-2,1)		# Fade main video ~ 6 Sec
		if(skip == 0):			# If main video has completely faded
			print "Skip = 0"								# Testing
			player = OMXPlayer(vidA, args=['--no-osd', '-b', '--loop', '--alpha', '0'])	# 'Title Card'
			player.set_aspect_mode("fill")							# Set aspect
			player.set_volume(-6000.0)							# Volume = -60dB
			player.play()									# Play 'Title Card'
			time.sleep(0.5)								
			player.pause()									# Pause 'Title Card'
			vidUp(1,6)									# Fade up ~ 2 Sec

except KeyboardInterrupt:
	player.quit()
	GPIO.cleanup()
	print ' '
	print " CTRL+C = Ciao (o^-^o)"
	sys.exit()


except:
        player.quit()
	GPIO.cleanup()
        print ' '
        print "Dbus Sad :'("
        sys.exit()

