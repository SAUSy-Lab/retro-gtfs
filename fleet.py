from vehicle import Vehicle
from time import time as now

class Fleet():
	"""Hold references to all active vehicles, manage means of accessing them."""

	def __init__(self):
		# dict of references to vehicle objects
		# keyed by vehicleID
		self.vehicles = {}

	def take_updates(self,updates):
		"""Decide what to do with some new updates. 
			"updates" is a list of status objects"""
		for status in updates:
			# see if we have a record of this vehicle
			if status.id in self.vehicles:
				pass
			else: # we don't have record of this vehicle yet
				# so create one
				self.vehicles[status.id] = Vehicle(
					self,					# passed reference to rest of fleet
					status.id,			# vehicle ID
					status.line,		# line ID
					status.direction,	# direction name
					status.fromStation, # likely not correct yet
					status.estArrival	# likely not correct yet
				)
				print status.estArrival - now()
