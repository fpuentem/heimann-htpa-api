# import sys
import time
import copy
import struct

import numpy as np
# import cv2 as cv

import libs.Table as Table
from libs.i2chtpa import *


i2cdriver = I2Cdriver()

class HTPA:
	def __init__(self, address, revision="2018"):
		self.address = address
		# self.PCSCALEVALUE = 100000000.0
		
		if revision == "2018":
			self.blockshift = 4
		else:
			self.blockshift = 2


		# print("Wake Up")
		wakeup_and_blind = i2cdriver.generate_command(0x01, 0x01) # wake up the device
		i2cdriver.send_command(self.address, wakeup_and_blind)
		time.sleep(10 / 1000) #10ms delay (minimum must be 5ms)

		# print ("Grabbing EEPROM data")

		eeprom = self.get_eeprom()
		self.extract_eeprom_parameters(eeprom)
		self.eeprom = eeprom


		# print("ADC Resolution - MBIT TRIM")
		self.set_mbit_trim(self.MBIT_calib)

		# print("BIAS")
		self.set_bias_current(self.BIAS_calib)
		
		# print("Clock")
		self.set_clock_speed(self.CLK_calib)
		
		# print("BPA")
		self.set_cm_current(self.BPA_calib)

		# print("Pull ups - PU-TRIM")
		self.set_pu_trim(self.PU_calib)


		# electrical offset
		self.measure_electrical_offset()

		# initialize offset to zero
		self.offset = np.zeros((32, 32))

		self.TABLENUMBER = 114
		self.PCSCALEVAL = 100000000 #327000000000		//PixelConst scale value for table... lower 'L' for (long)
		self.NROFTAELEMENTS = 7
		self.NROFADELEMENTS = 1595	#130 possible due to Program memory, higher values possible if NROFTAELEMENTS is decreased
		self.TAEQUIDISTANCE = 100		#dK
		self.ADEQUIDISTANCE = 64		#dig
		self.ADEXPBITS = 6		#2^ADEXPBITS=ADEQUIDISTANCE
		self.TABLEOFFSET = 1024*np.ones((32,32))

	def set_mbit_trim(self, mbit):
		mbit_msg = i2cdriver.generate_command(0x03, mbit)
		mbit = int(mbit)
		i2cdriver.send_command(self.address, mbit_msg)
		time.sleep(5 / 1000)

	def set_bias_current(self, bias):
		if bias > 31:
			bias = 31
		if bias < 0:
			bias = 0

		bias = int(bias)

		bias_top = i2cdriver.generate_command(0x04, bias)
		bias_bottom = i2cdriver.generate_command(0x05, bias)

		i2cdriver.send_command(self.address, bias_top)
		time.sleep(5 / 1000)
		i2cdriver.send_command(self.address, bias_bottom)
		time.sleep(5 / 1000)

	def set_clock_speed(self, clk):
		if clk > 63:
			clk = 63
		if clk < 0:
			clk = 0

		clk = int(clk)
		clk_speed = i2cdriver.generate_command(0x06, clk)
		i2cdriver.send_command(self.address, clk_speed)
		time.sleep(5 / 1000)

	def set_cm_current(self, cm):
		if cm > 31:
			cm = 31
		if cm < 0:
			cm = 0
		cm = int(cm)

		cm_top = i2cdriver.generate_command(0x07, cm)
		cm_bottom = i2cdriver.generate_command(0x08, cm)

		i2cdriver.send_command(self.address, cm_top)
		time.sleep(5 / 1000)
		
		i2cdriver.send_command(self.address, cm_bottom)
		time.sleep(5 / 1000)

	def set_pu_trim(self, pu):
		pu = int(pu)
		pu_msg = i2cdriver.generate_command(0x09, pu)
		i2cdriver.send_command(self.address, pu_msg)
		time.sleep(5 / 1000)
		
	def get_eeprom(self, eeprom_address=0x50):
		# Two separate I2C transfers in case the buffer size is small
		q1 = [I2C.Message([0x00, 0x00]), I2C.Message([0x00]*4000, read=True)]
		q2 = [I2C.Message([0x0f, 0xa0]), I2C.Message([0x00]*4000, read=True)]
		i2cdriver.i2c.transfer(eeprom_address, q1)
		i2cdriver.i2c.transfer(eeprom_address, q2)
		return np.array(q1[1].data + q2[1].data)

	def extract_eeprom_parameters(self, eeprom):
		self.VddComp = eeprom[0x0540:0x0740:2] + (eeprom[0x0541:0x0740:2] << 8)

		ThGrad =   eeprom[0x0740:0x0F40:2] + (eeprom[0x0741:0x0F40:2] << 8)
		ThGrad = [tg - 65536 if tg >= 32768 else tg for tg in ThGrad]
		ThGrad = np.reshape(ThGrad, (32, 32))
		ThGrad[16:,:] = np.flipud(ThGrad[16:,:])
		self.ThGrad = ThGrad.astype(int)

		ThOffset = eeprom[0x0F40:0x1740:2] + (eeprom[0x0F41:0x1740:2] << 8)
		ThOffset = [to - 65536 if to >= 32768 else to for to in ThOffset]
		ThOffset = np.reshape(ThOffset, (32, 32))
		ThOffset[16:,:] = np.flipud(ThOffset[16:,:])
		self.ThOffset = ThOffset.astype(int)

		P = eeprom[0x1740::2] + (eeprom[0x1741::2] << 8)
		P = np.reshape(P, (32, 32))
		P[16:, :] = np.flipud(P[16:,:])
		self.P = P.astype(int)

		self.epsilon = 98 #float(eeprom[0x000D])
		# print("<DEBUD> epsilon: {}".format(epsilon))
		GlobalGain = eeprom[0x0055] + (eeprom[0x0056] << 8)
		self.globalGain = GlobalGain

		Pmin = eeprom[0x0000:0x0004]
		Pmax = eeprom[0x0004:0x0008]
		
		Pmin = Pmin.astype('uint8')
		Pmin = Pmin.tobytes()
		self.Pmin = struct.unpack('f', Pmin)[0]
#		Pmin = struct.unpack('f', functools.reduce(lambda a,b: a+b, [chr(p) for p in Pmin]))[0]

		Pmax = Pmax.astype('uint8')
		Pmax = Pmax.tobytes()
		self.Pmax = struct.unpack('f', Pmax)[0]
#		Pmax = struct.unpack('f', functools.reduce(lambda a,b: a+b, [chr(p) for p in Pmax]))[0]
		# print("<DEBUG>GlobalGain:{}".format(float(GlobalGain)))
		# Check again in case of error
		self.PixC = (self.P * (self.Pmax - self.Pmin) / 65535. + self.Pmin) * (self.epsilon / 100) * (float(self.globalGain) / 10000)

		self.PixC = np.ceil(self.PixC)
		# be careful excel operation
		# self.PixC[16:, :] = np.flipud(self.PixC[16:,:])
		# print("<DEBUG> self.PixC:{}".format(self.PixC))
		self.gradScale = eeprom[0x0008]
		# self.VddCalib = eeprom[0x0046] + (eeprom[0x0047] << 8)
		self.Vdd = 3280.0
		self.VddScaling = eeprom[0x004E]

		PTATgradient = eeprom[0x0034:0x0038]
		PTATgradient = PTATgradient.astype('uint8')
		PTATgradient = PTATgradient.tobytes()
		self.PTATgradient = struct.unpack('f', PTATgradient)[0]
		# print('<DEBUG>self.PTATgradient: {}'.format(self.PTATgradient))

		# print(type(self.PTATgradient))
#		self.PTATgradient = struct.unpack('f', functools.reduce(lambda a,b: a+b, [chr(p) for p in PTATgradient]))[0]


		PTAToffset = eeprom[0x0038:0x003c]
		PTAToffset = PTAToffset.astype('uint8')
		PTAToffset = PTAToffset.tobytes()
		self.PTAToffset = struct.unpack('f', PTAToffset)[0]
#		self.PTAToffset = struct.unpack('f', functools.reduce(lambda a,b: a+b, [chr(p) for p in PTAToffset]))[0]

		# TN unsigned number
		self.TABLENUMBER = eeprom[0x000b] + (eeprom[0x000c] << 8)
		# print(self.TABLENUMBER)

		## Constants for dead values (under test June 19)
		self.NrOfDeadPix = eeprom[0x007F]
		self.DeadPixAdr = eeprom[0x0080:0x00B0:2] + (eeprom[0x0081:0x00B0:2] << 8)
		self.DeadPixMask = eeprom[0x00B0:0x00C8:2] + (eeprom[0x00B1:0x00C8:2] << 8)
		
		## VDD compensation constants
		# VDDTH1
		self.VDDTH1 = eeprom[0x0026] + (eeprom[0x0027] << 8)

		# VDDTH2
		self.VDDTH2 = eeprom[0x0028] + (eeprom[0x0029] << 8)

		# PTATTH1
		self.PTATTH1 = eeprom[0x003C] + (eeprom[0x003D] << 8)

		# PTATTH2
		self.PTATTH2 = eeprom[0x003E] + (eeprom[0x003F] << 8)

		# VddScGrad
		self.VddScGrad = eeprom[0x004E]
		
		# VddScOff
		self.VddScOff = eeprom[0x004F]

		# Global offset
		self.globalOff = eeprom[0x0054]

		#VddCompGradij
		VddCompGradij = eeprom[0x0340:0x0540:2] + (eeprom[0x0341:0x0540:2] << 8)
		VddCompGradij = [tg - 65536 if tg >= 32768 else tg for tg in VddCompGradij]
		
		self.VddCompGradij_8x32 = np.reshape(VddCompGradij, (8, 32))
		self.VddCompGradij_32x32 = np.zeros((32,32))

		for i in range(4):
			self.VddCompGradij_32x32[4*i:4*i+4, :] = self.VddCompGradij_8x32[:4, :]				# top half
			self.VddCompGradij_32x32[(4*i+16) : (4*i+16)+4] = np.flipud(self.VddCompGradij_8x32[4:, :])	# botton half

		self.VddCompGradij_32x32 = self.VddCompGradij_32x32.astype(int)

		# VddCompOffij
		VddCompOffij = eeprom[0x0540:0x0740:2] + (eeprom[0x0541:0x0740:2] << 8)
		VddCompOffij = [tg - 65536 if tg >= 32768 else tg for tg in VddCompOffij]
		
		self.VddCompOffij_8x32 = np.reshape(VddCompOffij, (8, 32))
		self.VddCompOffij_32x32 = np.zeros((32,32))

		for i in range(4):
			self.VddCompOffij_32x32[4*i:4*i+4, :] = self.VddCompOffij_8x32[:4, :]				# top half
			self.VddCompOffij_32x32[(4*i+16) : (4*i+16)+4] = np.flipud(self.VddCompOffij_8x32[4:, :])	# botton half
			
		self.VddCompOffij_32x32 = self.VddCompOffij_32x32.astype(int)
		
		# # Calibration values
		# print("MBIT: {}".format(eeprom[0x001a]))
		self.MBIT_calib = eeprom[0x001a]
		
		# print("BIAS: {}".format(eeprom[0x001b]))
		self.BIAS_calib = eeprom[0x001b]
		
		# print("CLK: {}".format(eeprom[0x001c]))
		self.CLK_calib = eeprom[0x001c]

		# print("BPA: {}".format(eeprom[0x001d]))
		self.BPA_calib = eeprom[0x001d]

		# print("PU: {}".format(eeprom[0x001e]))
		self.PU_calib = eeprom[0x001e]

	#fbrc
	# From Latex to human readable
	# https://www.codecogs.com/latex/eqneditor.php?lang=pt-br
	
	def ambient_temperature(self, ptat):
		# Section 11.1: Ambient Temperature
		# T_a = PTAT_{avg} \cdot PTAT_{gradient} + PTAT_{offset} (dK)
		# PTAT_gradient	: stored in EEPROM as float(0x0034 - 0x0038)
		# PTAT_offset	: stored in EEPROM as float(0x0038 - 0x000C)
		# PTAT_{avg} =  \frac{\sum_{i=0}^{7} PTAT_i}{8} (one per block, obtained when get image-measured)
		Ta = np.mean(ptat) * self.PTATgradient + self.PTAToffset
		return Ta

	#fbrc
	def thermal_offset(self, im, ptat):
		# Section 11.2: Thermal Offset
		# V_{ijComp} = V_{ij} - ( \frac{ThGrad_{ij} \cdot PTAT_{av}}{2^{gradScale}} + ThOffset_{ij})
		# V_{ijComp}	: thermal offset compensated data
		# V_{ij}		: is the raw pixel data(digital) fro m RAM
		
		# print("<DEBUG> self.ThGrad: {}".format(self.ThGrad))
		# print("<DEBUG> self.gradScale: {}".format(self.gradScale))
		# print("<DEBUG> self.ThOffset: {}".format(self.ThOffset))
		comp = np.zeros((32,32))
		comp = ((self.ThGrad * np.mean(ptat)) / pow(2, self.gradScale)) + self.ThOffset	
		thermal_comp = im - comp
		return thermal_comp
	#fbrc
	def electrical_compensation(self, im_thermal_comp):
		# Section 11.3: Electrical Offset
		# top half
		# V_{ijComp}* = V_{ijComp} - elOffset[(j + i \cdot 32)\%128]

		# botton half
		# V_{ijComp}* = V_{ijComp} - elOffset[(j + i \cdot 32)\%128 + 128]
		
		# V_{ijComp}*		: Thermal and electrical compensated voltage
		# V_{ijComp}		: Thermal offset compensated voltage.
		# elOffset[k(ij)]	: Electrical offset belonging to pixel ij
		elec_therm_comp =  im_thermal_comp - self.el_offset_32x32
		return elec_therm_comp
	
	# fbrc
	def vdd_compensation(self, im_elec_therm_comp, ptat):
		VDDav = self.measure_vdd_average()
		PTATav = np.mean(ptat)
		
		A_ = ((self.VddCompGradij_32x32*PTATav)/np.power(2, self.VddScGrad) + self.VddCompOffij_32x32)/np.power(2, self.VddScOff)
		B_ = (VDDav - self.VDDTH1 - ((self.VDDTH2 - self.VDDTH1)/(self.PTATTH2 -self.PTATTH1))*(PTATav - self.PTATTH1))
		vdd_elec_therm_comp = im_elec_therm_comp - A_*B_
		return vdd_elec_therm_comp

	# fbrc
	def sensitivity_compensation(self, im_vdd_elec_therm_comp):
		#
		#
		sens_vdd_elec_therm_comp = (im_vdd_elec_therm_comp*self.PCSCALEVAL)/self.PixC

		return sens_vdd_elec_therm_comp.astype(int)

	
	def capture_image(self, blind=False, vdd_means=False):
		pixel_values = np.zeros(1024)
		ptats = np.zeros(8)

		for block in range(4):
			# print("Exposing block " + str(block))
			
			#Comando to wake-up and start to read
			cmdread = i2cdriver.generate_expose_block_command(block, self.blockshift, blind=blind, vdd_means=vdd_means)
			i2cdriver.send_command(self.address, cmdread, wait=False)
			time.sleep(10 / 1000) #10ms delay (minimum must be 5ms)

			#????
			#query = [I2C.Message([0x02]), I2C.Message([0x00], read=True)]
			query = [I2C.Message([0x02]), I2C.Message([0x00], read=True)]

			# if not blind:
			# 	expected = 1 + (block << self.blockshift)
			# else:
			# 	expected = 1 + (block << self.blockshift) + 0x02

			if blind:
				expected = 1 + (block << self.blockshift) + 0x02
			elif vdd_means:
				expected = 1 + (block << self.blockshift) + 0x04
			else:
				expected = 1 + (block << self.blockshift)

			done = False

			while not done:
				i2cdriver.i2c.transfer(self.address, query)

				if not (query[1].data[0] == expected):
					# print("Not ready, received " + str(query[1].data[0]) + ", expected " + str(expected))
					time.sleep(30 / 1000)
				else:
					done = True

			read_block = [I2C.Message([0x0A]), I2C.Message([0x00]*258, read=True)]
			i2cdriver.i2c.transfer(self.address, read_block)
			top_data = np.array(copy.copy(read_block[1].data))
			#print(read_block[1].data)

			read_block = [I2C.Message([0x0B]), I2C.Message([0x00]*258, read=True)]
			i2cdriver.i2c.transfer(self.address, read_block)
			bottom_data = np.array(copy.copy(read_block[1].data))
			#print(read_block[1].data)

			# fbrc little endian
			top_data = (top_data[0::2] << 8) + top_data[1::2]
			bottom_data = (bottom_data[0::2] << 8) + bottom_data[1::2]
			# print(top_data)


			if ((not blind) and (not vdd_means)):
				pixel_values[(0+block*128):(128+block*128)] = top_data[1:]
				# bottom data is in a weird shape
				pixel_values[(992-block*128):(1024-block*128)] = bottom_data[1:33]
				pixel_values[(960-block*128):(992-block*128)] = bottom_data[33:65]
				pixel_values[(928-block*128):(960-block*128)] = bottom_data[65:97]
				pixel_values[(896-block*128):(928-block*128)] = bottom_data[97:]
			else:
				# blind mode electrical offset, Table 18 of datasheet is confusing about index of array
				# We assume old datasheet as correct
				pixel_values[0:128] = top_data[1:]
				pixel_values[128:256] = bottom_data[1:]

			ptats[block] = top_data[0]
			ptats[7-block] = bottom_data[0]
		if not blind:
			pixel_values = np.reshape(pixel_values, (32, 32))

		return (pixel_values, ptats)

	# fbrc
	def measure_electrical_offset(self):
		self.el_offset_32x32 = np.zeros((32,32))

		(offsets, ptats) = self.capture_image(blind=True)
		self.el_offset_8x32 = np.reshape(offsets[:256], (8, 32))
		
		for i in range(4):
			self.el_offset_32x32[4*i:4*i+4, :] = self.el_offset_8x32[:4, :]				# top half
			self.el_offset_32x32[(4*i+16) : (4*i+16)+4] = np.flipud(self.el_offset_8x32[4:, :])	# botton half

	def measure_vdd_average(self):
		#It is the average meaasured supply voltage of the sensor in digits.
		(digits, ptats) = self.capture_image(vdd_means=True)
		return np.mean(ptats) 


	# Methods to correct dead pixels
	def check_dead_pixels(self):
		if self.NrOfDeadPix > 0:
			return True
		else:
			return False

	def get_addr_of_dead_pixels(self, DeadPixAdr):
		actual_DeadPixAdr = np.array([], dtype=np.uint16)
		for px_adr in DeadPixAdr:
			if px_adr < 512:
				actual_DeadPixAdr = np.append(actual_DeadPixAdr, px_adr)
			else:
				actual_DeadPixAdr = np.append(actual_DeadPixAdr, 1024 + 512 - px_adr + (px_adr%32)*2 - 32)
	
	def get_array_mask(self, DeadPixMask):
		bool_mask = np.zeros(8, dtype=np.uint16)
		i = 0
		while DeadPixMask:
			digit = DeadPixMask % 2
			DeadPixMask //= 2
			bool_mask[i] =  digit
			i = i + 1
		return bool_mask

	def mask_pixels_addr(self, DeadPixAdr, DeadPixMask):
		b_msk = self.get_array_mask(DeadPixMask)

		if DeadPixAdr < 512:
			mask_addr = np.array([DeadPixAdr - 32,
								  DeadPixAdr - 32 + 1,
								  DeadPixAdr + 1,
								  DeadPixAdr + 32 +1,
								  DeadPixAdr + 32,
								  DeadPixAdr -1 + 32,
								  DeadPixAdr -1,
								  DeadPixAdr -32 -1])
		else:
			mask_addr = np.array([DeadPixAdr + 32,
								  DeadPixAdr + 32 + 1,
								  DeadPixAdr + 1,
								  DeadPixAdr - 32 +1,
								  DeadPixAdr - 32,
								  DeadPixAdr - 32 - 1,
								  DeadPixAdr -1,
								  DeadPixAdr + 32 -1])
		return b_msk * mask_addr

	# Here we are assuming that background is the same
	def get_frame(self):
		(px, ptat) = self.capture_image()
		im = self.thermal_offset(px, ptat)
		im = self.electrical_compensation(im)
		im = self.vdd_compensation(im, ptat)
		im = self.sensitivity_compensation(im)
		im = im + 1024*np.ones((32,32))

		# im = np.flip(im, 0)
		# Rotate
		# im = cv.rotate(im, cv.ROTATE_90_CLOCKWISE)
		return im
		
	def get_frame_temperature(self):
		(px, ptat) = self.capture_image()
		im = self.thermal_offset(px, ptat)
		im = self.electrical_compensation(im)
		im = self.vdd_compensation(im, ptat)
		im = self.sensitivity_compensation(im)
		im = im + 1024*np.ones((32,32))
		# im = np.flip(im, 0)
		temp_env = self.ambient_temperature(ptat)
		
		# Temperature
		temp_obj_array = np.zeros((32,32))

		# Bilinear interpolation
		for i in range(32):
			for j in range(32):
				temp_obj_array[i][j] = self.calculate_temperature_object(temp_env, im[i][j])

		# Transform to celcius
		temp_obj_array_celcius = self.convert_to_celcius(temp_obj_array)
		return temp_env, temp_obj_array_celcius

	def calculate_temperature_object(self, TAmb, val):
		# first check the position in x-axis of table
		val = int(val)
		if TAmb < Table.XTATemps[0]:
			CurTACol = 0
		else:
			for i in range(0, self.NROFTAELEMENTS):
				if ( Table.XTATemps[i] <= TAmb and Table.XTATemps[i + 1] > TAmb ):
					break

		CurTACol = i
		# print("CurTACol: {}".format(CurTACol))    

		dTA = TAmb - Table.XTATemps[CurTACol]
	
		# now determine row
		y = val >> self.ADEXPBITS
		# print("y: {}".format(y))
		ydist = self.ADEQUIDISTANCE
		if y < (self.NROFADELEMENTS - 1):
			if Table.TempTable[y][CurTACol]:
				vx = (((Table.TempTable[y][CurTACol+1] - Table.TempTable[y][CurTACol]) * dTA)/ self.TAEQUIDISTANCE) + Table.TempTable[y][CurTACol]
				vy = (((Table.TempTable[y+1][CurTACol+1] - Table.TempTable[y+1][CurTACol])* dTA)/ self.TAEQUIDISTANCE) + Table.TempTable[y+1][CurTACol]
				Tobject = ((vy - vx) * ( val - Table.YADValues[y]) / ydist + vx)
				return Tobject
			else:
				return 0
		else:
			return 0
	
	def convert_to_celcius(self, temp_im):
		temp_celcius = (temp_im - 2731.5)/10
		temp_celcius = np.round(temp_celcius, 2)
		return temp_celcius
