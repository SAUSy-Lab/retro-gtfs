from time import time as now


class Vehicle(object):
	"""describes a subway train with latest known properties"""

	def __init__( self, fleet, vid, line, direction, next_stop_name, est_arrival ):
		# reference to the parent object
		self.fleet = fleet
		# unique vehicle id
		self.id = vid
		# identifier of the subway line
		self.line = line
		# Cardinal direction being operated. 
		# Corresponds with ordering of stops
		self.direction = direction
		# name of the next stop that the train will arrive at
		self.next_stop = next_stop_name
		# estimated arrival time at next stop
		# seconds from epoch
		self.est_arrival = est_arrival
		
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
