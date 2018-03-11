from shapely.wkb import loads as loadWKB
from conf import conf
from shapely.geometry import Point
from shapely.ops import transform as reproject


class Vehicle(object):
	"""A transit vehicle GPS/space-time point record
		geometries provided straight from PostGIS"""

	def __init__( self, epoch_time, longitude, latitude ):
		# set now
		self.time = epoch_time
		self.longitude = longitude
		self.latitude = latitude
		self.local_geom = reproject( conf['projection'], Point(longitude,latitude) )
		# set later
		self.measure = None	# measure in meters along the matched route geometry

	@property
	def lat(self):
		return self.latitude

	@property
	def lon(self):
		return self.longitude
	
	@property
	def geom(self):
		return self.local_geom

	def set_measure(self,measure_in_meters):
		assert measure_in_meters >= 0
		self.measure = measure_in_meters



class Stop(object):
	"""A physical transit stop."""

	def __init__( self, stop_id, projected_geom_hex ):
		# set now
		self.id = stop_id
		self.geom = loadWKB( projected_geom_hex, hex=True )
		# set later
		self.distance_from_route = None

	@property
	def on_route(self):
		"""Is this stop on the route?"""
		if self.distance_from_route is not None:
			return self.distance_from_route <= conf['stop_dist']
		else:
			return False

	def set_measure(self,measure_in_meters):
		assert measure_in_meters >= 0
		self.measure = measure_in_meters

	def set_distance(self,distance_in_meters):
		assert distance_in_meters >= 0
		self.distance_from_route = distance_in_meters	



class TimePoint(object):
	"""A stop in sequence."""
	
	def __init__( self, stop_object_reference, measure, distance_from_route ):
		self.stop = stop_object_reference	# Stop object
		self.measure = measure					# meters alongn route
		self.dist = distance_from_route		# meters distant from route
		# set after initialization
		self.arrival_time = None
		self.departure_time = None
	
	@property
	def stop_id(self):
		return self.stop.id
	@property
	def geom(self):
		return self.stop.geom

	def set_time(self,epoch_time):
		self.arrival_time = epoch_time
		self.departure_time = epoch_time
	









