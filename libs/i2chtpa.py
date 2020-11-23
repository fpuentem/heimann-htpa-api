from periphery import I2C
# import numpy as np
# import sys
import time

class I2Cdriver():

	def __init__(self):
		self.i2c = I2C("/dev/i2c-1")

	def generate_command(self, register, value):
		return [I2C.Message([register, value])]

	def generate_expose_block_command(self, block, blockshift, blind=False, vdd_means=False):
		""" 

		"""
		if blind:
			# print("Read blind --> offset")
			# blind mode is to get electrical offset, bit 1
			# print((block << self.blockshift))
			# print(0x09 + (block << self.blockshift) + 0x02)
			return self.generate_command(0x01, 0x09 + (block << blockshift) + 0x02)

		elif vdd_means:
			# Configuration register(bit 2)
			return self.generate_command(0x01, 0x09 + (block << blockshift) + 0x04)

		else:
			# print("Config register: {}".format(0x09 + (block << blockshift)))
			# print(0x09 + (block << self.blockshift))
			return self.generate_command(0x01, 0x09 + (block << blockshift))

	def send_command(self, address, cmd, wait=True):
		self.i2c.transfer(address, cmd)
		if wait:
			time.sleep(0.005) # sleep for 5 ms

	#def close(self):
	#	sleep = self.generate_command(0x01, 0x00)
	#	self.send_command(sleep)

