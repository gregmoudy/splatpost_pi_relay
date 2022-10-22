import time
import timeit

import PIL.Image

import signal

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

class relay:
    relay_pins = {"R1":31,"R2":33,"R3":35,"R4":37}

    def __init__(self, pins):
        self.pin = self.relay_pins[pins]
        self.pins = pins
        GPIO.setup(self.pin,GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        GPIO.output(self.pin,GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin,GPIO.LOW)

#SPLATOON SETTINGS
#IMAGE_PATH = 'me.gif'
#IMAGE_PATH = '32_square.gif'
IMAGE_PATH = 'cb2.gif'

#SPLATOON_WIDTH = 320
#SPLATOON_HEIGHT = 120

# Sometimes these values are read in flipped from the bitmap.
WHITE = 1 # 0
BLACK = 0 # 1


# RELAY SETTINGS
DELAY_SEC = 0.025
# 0.020 is too fast. 0.025 works. 
# 0.025 Had some errors, trying 0.03. 
# 0.03 had errors as well but spaced differently.
# When I watched it it dropped left and right inputs at some point and came up short, not sure why.
# Either a failure of relay, the pico, or dropped input on part of Splatoon.
# Currently I don't know how to fix it, and the only recovery I can think is to force a bunch of right/left and the end of a line to to make sure we are lined up for the next line.

BTN_A = relay("R1") # A
BTN_RIGHT = relay("R2") # RIGHT
BTN_DOWN = relay("R3") # DOWN
BTN_LEFT = relay("R4") # LEFT


# HANDLER
def handler(signum, frame):
	# If we hit ctrl-c to break out of the code early, turn all the relays off.
	BTN_A.off()
	BTN_RIGHT.off()
	BTN_DOWN.off()
	BTN_LEFT.off()
	exit(1)


# FUNCTIONS
def press_button(relay):
	relay.on()
	time.sleep(DELAY_SEC)
	relay.off()
	time.sleep(DELAY_SEC)



def button_on(relay):
	relay.on()
	time.sleep(DELAY_SEC)



def button_off(relay):
	relay.off()
	time.sleep(DELAY_SEC)



# Create the handler for an early out.
signal.signal(signal.SIGINT, handler)
#signal.signal(signal.SIGTERM, handler)


# Reset all the relays just in case. This might be something to put in to the relay class init.
BTN_A.off()
BTN_RIGHT.off()
BTN_DOWN.off()
BTN_LEFT.off()


# Load the image file.
image = PIL.Image.open( IMAGE_PATH )

start_time = timeit.default_timer()

BUTTON_A_STATE = False

# Print the image file to Splatoon.
for y in range( image.height ):
	x_pixel_range = list( range( image.width ) )

	# Need to read in reverse since we got right to left on odd lines.
	if ( y % 2 ) != 0:
		x_pixel_range.reverse( )

	# Skips rows that have no black in them.
	vals = [ image.getpixel( ( x_pixel, y ) ) for x_pixel in x_pixel_range ]
	if len(set(vals)) == 1 and vals[0] == WHITE:
		press_button(BTN_DOWN)
		continue

	for index, x in enumerate( x_pixel_range ):
		STATUS_FREQ = 10
		if index % STATUS_FREQ == 0:
			print( 'Printing ROW: {0}/{1} COL: {2}-{3}/{4}'.format(y, image.height, index, index+STATUS_FREQ, image.width))

		pixel_value = image.getpixel( ( x, y ) )

		if pixel_value == BLACK:
			if BUTTON_A_STATE == False:
				button_on(BTN_A)
				BUTTON_A_STATE = True

			try:
				next_pixel_x = x_pixel_range[ index + 1 ]
				next_pixel_value = image.getpixel( ( next_pixel_x, y ) )

			except IndexError:
				next_pixel_value = WHITE

			if next_pixel_value == WHITE:
				button_off(BTN_A)
				BUTTON_A_STATE = False

		else:
			button_off(BTN_A)
			BUTTON_A_STATE = False

		# Move left or right but not if it is the last item in the list.
		if x_pixel_range.index(x) + 1 != len(x_pixel_range):
			if ( y % 2 ) == 0:
				press_button(BTN_RIGHT)

			else:
				press_button(BTN_LEFT)

	press_button(BTN_DOWN)

elapsed_time = timeit.default_timer() - start_time

print('Runtime: {} seconds.'.format(elapsed_time))
