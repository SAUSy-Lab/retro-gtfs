# documentation on the nextbus feed:
# http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf

import re, db, math, random 
import map_api
from geom import cut
from numpy import mean
from conf import conf
from shapely.wkb import loads as loadWKB, dumps as dumpWKB
from shapely.ops import transform as reproject
from shapely.geometry import Point, asShape, LineString, MultiLineString
from minor_objects import Vehicle

class Trip(object):
	"""The trip class provides all the methods needed for dealing
		with one observed trip/track. Classmethods provide two 
		different ways of instantiating."""

	def __init__(self):
		"""Initialization method, ONLY accessed by the two @classmethods below"""
		# set initial attributes
		self.trip_id = -1				# int
		self.block_id = -1			# int
		self.direction_id = ''		# str
		self.route_id = ''			# str
		self.vehicle_id = -1			# int
		self.last_seen = -1			# last vehicle report (epoch time)
		# initialize sequence
		self.seq = 1					# sequence which increments at each vehicle report
		# declare several vars for later in the matching process
		self.speed_string = ""		# str for error cleaning
		self.segment_speeds = []	# reported speeds of all segments (error cleaning)
		self.length = 0				# length in meters of current GPS trace
		self.vehicles = []			# ordered vehicle records
		self.ignored_vehicles = []	# discarded vehicle records
		self.stops = []				# Stop objects for this route
		self.timepoints = []			# Timepoint objects for this trip
		self.waypoints = []			# points on the finallized trip only
		self.match = None				# match object created during processing


	@classmethod
	def new(clss,trip_id,block_id,direction_id,route_id,vehicle_id,last_seen):
		"""create wholly new trip object, providing all parameters"""
		# create an empty trip object
		Trip = clss()
		# set the inital attributes
		Trip.trip_id = trip_id
		Trip.block_id = block_id
		Trip.direction_id = direction_id
		Trip.route_id = route_id
		Trip.vehicle_id = vehicle_id
		Trip.last_seen = last_seen
		# return the new object
		return Trip


	@classmethod
	def fromDB(clss,trip_id):
		"""Construct a trip object from an existing record in the database."""
		# construct the trip object from info in the DB
		dbta = db.get_trip_attributes(trip_id)
		# create the object
		Trip = clss()
		# set the inital attributes
		Trip.trip_id = trip_id
		Trip.block_id = dbta['block_id']
		Trip.direction_id = dbta['direction_id']
		Trip.route_id = dbta['route_id']
		Trip.vehicle_id = dbta['vehicle_id']
		Trip.vehicles = dbta['points']
		Trip.last_seen = Trip.vehicles[-1].time
		return Trip


	def add_point(self,lon,lat,etime):
		"""Add a vehicle location (which has just been observed) to the end 
			of this trip."""
		self.vehicles.append( Vehicle( etime, lon, lat ) )


	def save(self):
		"""Store a record of this trip in the DB. This allows us to 
			reprocess as from the beginning with different parameters, 
			data, etc. GPS points are stored as an array of times and 
			a linestring. This function is to be called just before 
			process() as data is being collected."""
		db.insert_trip(
			self.trip_id,
			self.block_id,
			self.route_id, 
			self.direction_id,
			self.vehicle_id,
			[ v.time for v in self.vehicles ],
			dumpWKB( self.get_geom(), hex=True )
		)


	def process(self):
		"""A trip has just ended. What do we do with it?"""
		# As this may be being REprocessed we need to clean up any traces of the 
		# result of earlier processing so that we have a fresh start
		db.scrub_trip(self.trip_id)
		# see if we have enough stuff to bother with
		if len(self.vehicles) < 5: # km
			return db.ignore_trip(self.trip_id,'too few vehicles')
		# calculate vector of segment speeds
		self.segment_speeds = self.get_segment_speeds()
		# check for very short trips
		if self.length < 0.8: # km
			return db.ignore_trip(self.trip_id,'too short')
		# check for errors and attempt to correct them
		while self.has_errors():
			# make sure it's still long enough to bother with
			if len(self.vehicles) < 5:
				return db.ignore_trip(self.trip_id,'processing made too short')
			# still long enough to try fixing
			self.fix_error()
			# update the segment speeds for the next iteration
			self.segment_speeds = self.get_segment_speeds()
		# trip is clean, so store the cleaned line 
		db.set_trip_clean_geom(
			self.trip_id,
			dumpWKB( self.get_geom(), hex=True )
		)
		# and begin matching
		self.map_match_trip()
		if len(self.vehicles) < 3:
			return db.ignore_trip(self.trip_id,'too many vehicles removed during measurement')
		self.interpolate_stop_times()


	def get_geom(self):
		"""Return a clean shapely geometry LineString in the local projection 
			using all currently active vehicles."""
		return LineString( [ v.geom for v in self.vehicles ] )


	def get_segment_speeds(self):
		"""Return speeds (kmph) on the segments between non-ignored vehicles."""
		# iterate over segments (i-1)
		dists = []	# km
		times = []	# hours
		for i in range(1,len(self.vehicles)):
			v1 = self.vehicles[i-1]
			v2 = self.vehicles[i]
			# distance in kilometers
			dists.append( v1.geom.distance(v2.geom)/1000 )
			# time in hours
			times.append( (v2.time-v1.time)/3600 )
		# set the total distance
		self.length = sum(dists)
		# calculate speeds
		return [ d/t for d,t in zip(dists,times) ]


	def map_match_trip(self):
		"""1) Match the trip GPS points to the road network, id est, improve
			the spatial accuracy of the trip.
			2) Get the location/measure of stops and vehicles along the path.
			4) Interpolate sequence of stop_times from vehicle times."""
		# create a match object, passing it this trip to get it started
		self.match = map_api.match(self)
		if not self.match.is_useable:
			return db.ignore_trip(self.trip_id,'match problem')
		# store the match info and geom in the DB
		db.add_trip_match(
			self.trip_id,
			self.match.confidence,
			dumpWKB(self.match.geometry,hex=True)
		)
		# find the measure of the vehicles for time interpolation
		self.match.locate_vehicles_on_route()


	def interpolate_stop_times(self):
		"""Interpolates stop times after map matching."""
		if not self.match.is_useable:
			return
		# get the stops (as a list of Stop objects)
		self.stops = db.get_stops(self.direction_id,self.last_seen)
		# locate the stops on the route. This generates a list of timepoints
		# with measures but without times. These are sorted already by measure
		self.timepoints = self.match.locate_stops_on_route()
		# interpolate/extrapolate times for each timepoint
		for timepoint in self.timepoints:
			timepoint.set_time( self.interpolate_time(timepoint.measure) )
		# there is more than one stop, right?
		if len(self.timepoints) > 1:
			# store the stop times
			db.store_timepoints(self.trip_id,self.timepoints)
		else:
			db.ignore_trip(self.trip_id,'one or fewer timepoints')
		return


	def ignore_vehicle(self,var):
		"""Ignore a vehicle specified by either the index in the current list
			or by giving the vehicle object itself."""
		if isinstance(var,int): # then using index
			index = var
			v = self.vehicles.pop(index)
			self.ignored_vehicles.append(v)
		elif isinstance(var,Vehicle):
			vehicle = var
			for index, v in enumerate(self.vehicles):
				if v == vehicle:
					self.vehicles.pop(index)
					self.ignored_vehicles.append(v)
		else:
			print( 'ERROR' )


	def has_errors(self):
		"""Each segment between GPS points is classified based on it's speed. 
			See if the speed segments indicate that there are any fixable errors 
			by making the speed string and checking for fixeable patterns."""
		# convert the segment speeds into a string with three possible characters
		# 'x' indicates very high speed
		# 'o' indicates very low speed (essentially no motion)
		# '-' indicates moderate speed
		# e.g. 'oo---o----xx----------' and so pn
		self.speed_string = ''.join([ 
			'x' if seg > 120 else 'o' if seg < 0.1 else '-'
			for seg in self.segment_speeds ])
		# check for slow segments that can be fixed
		match_oo = re.search('oo|^o|o$',self.speed_string)
		# check for any very fast segments (all will be fixed)
		match_x = re.search('x',self.speed_string)
		if match_oo or match_x:
			return True
		else:
			return False


	def fix_error(self):
		"""remove redundant points and fix obvious positional 
			errors using RegEx. Fixes one error each time it's 
			called: the first it finds"""
		# check for leading o's (stationary start)
		m = re.search('^oo*',self.speed_string)
		if m: # remove the first vehicle
			self.ignore_vehicle(0)
			return
		# check for trailing o's (stationary end)
		m = re.search('oo*$',self.speed_string)
		if m: # remove the last vehicle
			self.ignore_vehicle( len(self.speed_string) )
			return
		# check for x near beginning, in first four segs
		m = re.search('^.{0,3}x',self.speed_string)
		if m: # remove the first vehicle
			self.ignore_vehicle(0)
			return
		# check for x near the end, in last four segs
		m = re.search('x.{0,3}$',self.speed_string)
		if m: # remove the last vehicle
			self.ignore_vehicle(len(self.speed_string))
			return
		# check for two or more o's in the middle and take from after the first o
		m = re.search('.ooo*.',self.speed_string)
		if m:
			# remove the vehicle after the first o. This matches like '-oo-'
			# so we need to add 2 to the start position to remove the vehicle 
			# report from between the o's ('-o|o-')
			self.ignore_vehicle(m.span()[0]+1)
			return
		# 'xx' in the middle, delete the point after the first x
		m = re.search('.xxx*',self.speed_string)
		if m:
			# same strategy as above
			self.ignore_vehicle(m.span()[0]+1)
			return
		# lone middle x
		m = re.search('.x.',self.speed_string)
		if m:
			# delete a point either before or after a lone x
			i = m.span()[0]+1+random.randint(0,1)
			self.ignore_vehicle(i-1)
			return


	def interpolate_time(self,distance_along_trip):
		"""Get the time for a stop by doing an interpolation on the trip times
			and locations. We already know the m of the stop and of the points on 
			the trip/track."""
		vfirst = self.vehicles[0]
		vlast = self.vehicles[-1]
		# if the stop is before the vehicle records
		if distance_along_trip < vfirst.measure:
			trip_speed = (vlast.time-vfirst.time)/(vlast.measure-vfirst.measure)
			gap = distance_along_trip - vfirst.measure
			# negative gap projects time forward
			return vfirst.time + gap * trip_speed
		# trip is off the back
		elif distance_along_trip > vlast.measure:
			trip_speed = (vlast.time-vfirst.time)/(vlast.measure-vfirst.measure)
			gap = distance_along_trip - vlast.measure
			# positive gap projects time backwards
			return vlast.time + gap * trip_speed
		# the stop is among vehicle records
		else:
			# iterate over the segments of the trip, looking for the segment
			# which holds the stop of interest
			first = True
			for point in self.vehicles:
				if first:
					first = False
					m1 = point.measure
					t1 = point.time
					continue
				m2 = point.measure
				t2 = point.time
				if m1 <= distance_along_trip <= m2:	# intersection is at or between these points
					# interpolate the time
					if distance_along_trip == m1:
						return t1
					percent_of_segment = (distance_along_trip - m1) / (m2 - m1)
					additional_time = percent_of_segment * (t2 - t1) 
					return t1 + additional_time
				# create the segment for the next iteration
				m1,t1 = m2,t2

