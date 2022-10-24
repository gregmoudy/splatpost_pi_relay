import signal
import time
import timeit

import PIL.Image

import RPi.GPIO
RPi.GPIO.setmode(RPi.GPIO.BOARD)
RPi.GPIO.setwarnings(False)



class PiRelay:
	def __init__(self, pin_number):
		self._pin_number = pin_number
		RPi.GPIO.setup(self.pin_number, RPi.GPIO.OUT)
		self.off()


	@property
	def pin_number(self):
		return self._pin_number


	def on(self):
		RPi.GPIO.output(self.pin_number, RPi.GPIO.HIGH)


	def off(self):
		RPi.GPIO.output(self.pin_number, RPi.GPIO.LOW)



class Splatposter:
	# GPIO RELAY PIN NUMBERS
	# TODO: Might move stuff like this out into a user defined json file.
	GPIO_PIN_A 		= 31
	GPIO_PIN_RIGHT 	= 33
	GPIO_PIN_DOWN 	= 35
	GPIO_PIN_LEFT 	= 37

	RELAY_A 	= PiRelay(GPIO_PIN_A)
	RELAY_RIGHT = PiRelay(GPIO_PIN_RIGHT)
	RELAY_DOWN 	= PiRelay(GPIO_PIN_DOWN)
	RELAY_LEFT 	= PiRelay(GPIO_PIN_LEFT)

	#SPLATOON_WIDTH = 320
	#SPLATOON_HEIGHT = 120

	# RELAY SETTINGS
	DELAY_SEC = 0.025
	# 0.020 is too fast. 0.025 works. 
	# 0.025 Had some errors, trying 0.03. 
	# 0.03 had errors as well but spaced differently.
	# When I watched it it dropped left and right inputs at some point and came up short, not sure why.
	# Either a failure of relay, the pico, or dropped input on part of Splatoon.
	# Currently I don't know how to fix it, and the only recovery I can think is to force a bunch of right/left and the end of a line to to make sure we are lined up for the next line.

	# Sometimes the bitmap is read in and values return seem to be inverted. Need to double check this.
	# This class variable will allow you to invert how the read value is treated.
	INVERT_IMAGE = False


	@property
	def PIXEL_BLACK(cls):
		if cls.INVERT_IMAGE:
			return 1

		return 0


	@property
	def PIXEL_WHITE(cls):
		if cls.INVERT_IMAGE:
			return 0

		return 1


	@classmethod
	def reset_relays(cls):
		cls.RELAY_A.off()
		cls.RELAY_RIGHT.off()
		cls.RELAY_DOWN.off()
		cls.RELAY_LEFT.off()


	@classmethod
	def press_button(cls, relay):
		cls.button_on(relay)
		cls.button_off(relay)


	@classmethod
	def button_on(cls, relay):
		relay.on()
		time.sleep(cls.DELAY_SEC)


	@classmethod
	def button_off(cls, relay):
		relay.off()
		time.sleep(cls.DELAY_SEC)


	@classmethod
	def print_image(cls, image_filename):
		# TODO: Overhaul this function, a lot stuff in here was to try to solve problems that I think are more on the side of Switch than this code.
		cls.reset_relays()

		# Load the image file.
		image = PIL.Image.open('./images/' + image_filename)

		start_time = timeit.default_timer()

		button_a_state = False

		# Print the image file to Splatoon.
		for y in range( image.height ):
			x_pixel_range = list(range(image.width))

			# Need to read in reverse since we got right to left on odd lines.
			if ( y % 2 ) != 0:
				x_pixel_range.reverse()

			# Skips rows that have no black in them.
			vals = [image.getpixel((x_pixel, y)) for x_pixel in x_pixel_range]
			if len(set(vals)) == 1 and vals[0] == cls.PIXEL_WHITE:
				cls.press_button(cls.RELAY_DOWN)
				continue

			for index, x in enumerate(x_pixel_range):
				STATUS_FREQ = 10
				if index % STATUS_FREQ == 0:
					print('Printing ROW: {0}/{1} COL: {2}-{3}/{4}'.format(y, image.height, index, index + STATUS_FREQ, image.width))

				pixel_value = image.getpixel((x, y))

				if pixel_value == cls.PIXEL_BLACK:
					if button_a_state == False:
						cls.button_on(cls.RELAY_A)
						button_a_state = True

					try:
						next_pixel_x = x_pixel_range[index + 1]
						next_pixel_value = image.getpixel((next_pixel_x, y))

					except IndexError:
						next_pixel_value = cls.PIXEL_WHITE

					if next_pixel_value == cls.PIXEL_WHITE:
						cls.button_off(cls.RELAY_A)
						button_a_state = False

				else:
					cls.button_off(cls.RELAY_A)
					button_a_state = False

				# Move left or right but not if it is the last item in the list.
				if x_pixel_range.index(x) + 1 != len(x_pixel_range):
					if ( y % 2 ) == 0:
						cls.press_button(cls.RELAY_RIGHT)

					else:
						cls.press_button(cls.RELAY_LEFT)

			cls.press_button(cls.RELAY_DOWN)

		elapsed_time = timeit.default_timer() - start_time
		print('Runtime: {} seconds.'.format(elapsed_time))



def interrupt_handler(_signum, _frame):
	# If we hit ctrl-c to break out of the code early, turn all the relays off.
	Splatposter.reset_relays()
	exit(1)



if __name__ == '__main__':
	# TODO: Might want to add commandline arguments for supply the image file to print.

	# Create a handler for an early out so via ctrl-c so the relays get turned off.
	signal.signal(signal.SIGINT, interrupt_handler)

	# Print the image to Splatoon.
	Splatposter.print_image('cb2.gif') # [ 'me.gif', '32_square.gif', 'cb2.gif' ]
