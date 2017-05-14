from vehicle import Vehicle

class Fleet():
	"""Hold references to all active vehicles, manage means of accessing them."""
	def __init__(self):
		# dict of references to vehicle objects
		# keyed by vehicleID
		self.vehicles = {}

	def take_update(self,status):
		"""decide what if anything to do with a new Status"""
		# see if we have a record of this vehicle
		vid = status.id
		if vid not in self.vehicles:
			# we don't have a record, so create one
			self.vehicles[vid] = Vehicle(
				vid,
				status.line,
				status.direction,
				status.fromStation, # likely not correct
				status.estArrival # likely not correct
			)
		else:
			pass
