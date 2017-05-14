from time import time

class Vehicle(object):
	"""describes a subway train with latest known properties"""

def __init__(self, vid, line, direction, next_stop_name, mins_from_now ):
		# unique vehicle id
		self.id = vid
		# identifier of the subway line
		self.line = line
		# Cardinal direction being operated. 
		# Corresponds with ordering of stops
		self.direction = direction
		# 
		self.next_stop = next_stop_name
		# estimated arrival time at next stop
		# seconds from epoch
		self.est_arrival = time() + mins_from_now * 60
		
	# check values 
	@property
	def line(self):
		return self._line
	@line.setter
	def line(self,value):
		if value not in ['SHEP','YUS']:
			raise ValueError('unknown line ID given')
		self._line = value

	@property
	def direction(self):
		return self._line
	@direction.setter
	def direction(self,value):
		if value not in ['North','South','East','West']:
			raise ValueError('unknown direction given')
		self._line = value
