
import numpy as np
# import sys
import time
import cv2

class Utils():

	def __init__(self):
		self.ok = 'OK'

	# fbrc
	def bilinear_interpolation(self, x, y, points):
		'''Interpolate (x,y) from values associated with four points.

		The four points are a list of four triplets:  (x, y, value).
		The four points can be in any order.  They should form a rectangle.

			>>> bilinear_interpolation(12, 5.5,
			...                        [(10, 4, 100),
			...                         (20, 4, 200),
			...                         (10, 6, 150),
			...                         (20, 6, 300)])
			165.0

		'''
		# See formula at:  http://en.wikipedia.org/wiki/Bilinear_interpolation

		points = sorted(points)               # order points by x, then by y
		(x1, y1, q11), (_x1, y2, q12), (x2, _y1, q21), (_x2, _y2, q22) = points

		if x1 != _x1 or x2 != _x2 or y1 != _y1 or y2 != _y2:
			raise ValueError('points do not form a rectangle')
		if not x1 <= x <= x2 or not y1 <= y <= y2:
			raise ValueError('(x, y) not within the rectangle')

		return (q11 * (x2 - x) * (y2 - y) +
				q21 * (x - x1) * (y2 - y) +
				q12 * (x2 - x) * (y - y1) +
				q22 * (x - x1) * (y - y1)
			) / ((x2 - x1) * (y2 - y1) + 0.0)

	

	def save_as_image(self, temp_obj_array, filename):
		# Resize factor
		factor = 10
		
		# Save raw data as image
		max_val = np.max(temp_obj_array) 
		min_val = np.min(temp_obj_array)
		range_val = max_val - min_val
		
		# print("min: {}".format(min_val))
		# print("max: {}".format(max_val))
		# print("range_val: {}".format(range_val))
		image_to_save = np.uint8(((temp_obj_array - min_val)/range_val)*255)

		#Image proccessing
		img = cv2.applyColorMap(image_to_save, cv2.COLORMAP_JET)
		# img = cv2.resize(img, (32*factor, 32*factor), interpolation = cv2.INTER_CUBIC)

		cv2.imwrite(filename, img)
		
	def save_as_image_with_flip_and_rotate(self, temp_obj_array, filename):
		# Resize factor
		factor = 10
		
		# Save raw data as image
		max_val = np.max(temp_obj_array) 
		min_val = np.min(temp_obj_array)
		range_val = max_val - min_val
		
		# print("min: {}".format(min_val))
		# print("max: {}".format(max_val))
		# print("range_val: {}".format(range_val))
		image_to_save = np.uint8(((temp_obj_array - min_val)/range_val)*255)

		# Flip
		image_to_save = np.flip(image_to_save, 0)

		# Rotate
		image_to_save = cv2.rotate(image_to_save, cv2.ROTATE_90_CLOCKWISE)

		#Image proccessing
		img = cv2.applyColorMap(image_to_save, cv2.COLORMAP_JET)
		img = cv2.resize(img, (32*factor, 32*factor), interpolation = cv2.INTER_CUBIC)

		cv2.imwrite(filename, img)
