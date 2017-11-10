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

class trip(object):
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
		self.seq = 1					# sequence which increments at each report
		# declare several vars for later in the matching process
		self.speed_string = ""		# str
		self.match_confidence = -1	# 0 - 1 real
		self.stops = []				# stop objects for this route
		self.timepoints = []			# copies of stops with arrival times added
		self.segment_speeds = []	# reported speeds of all segments
		self.waypoints = []			# points on the finallized trip only
		self.length = 0				# length in meters of current string
		self.vehicles = []			# ordered vehicle records
		self.ignored_vehicles = []	# discarded records
		self.match_geom = None		# map-matched linestring 


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
		Trip.last_seen = Trip.vehicles[-1]['time']
		# this is being REprocessed so clean up any traces of the 
		# result of earlier processing so that we have a fresh start
		db.scrub_trip(trip_id)
		return Trip


	def add_point(self,lon,lat,etime):
		"""add a vehicle location (which has just been observed) to the end 
			of this trip"""
		point = {
			# time past the epoch in seconds
			'time':etime, 
			# shapely geom in local meter-based projection
			'geom': reproject( conf['projection'], Point(lon,lat) ),
			# these are for input into OSRM without reprojection
			'lon':lon,
			'lat':lat
		}
		self.vehicles.append(point)


	def save(self):
		"""Store a record of this trip in the DB. This allows us to 
			reprocess as from the beginning with different parameters, 
			data, etc. GPS points are stored as an array of times and 
			a linestring. This function is to be called just before 
			process() as data is being collected."""
		times = []
		for v in self.vehicles:
			times.append(v['time'])
		db.insert_trip(
			self.trip_id,
			self.block_id,
			self.route_id, 
			self.direction_id,
			self.vehicle_id,
			times,
			self.get_geom()
		)


	def process(self):
		"""A trip has just ended. What do we do with it?"""
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
		db.set_trip_clean_geom(self.trip_id,self.get_geom())
		# and begin matching
		self.match()


	def get_geom(self):
		"""return a clean WKB geometry string using all vehicles
			in the local projection"""
		line = []
		for v in self.vehicles:
			line.append(v['geom'])
		return dumpWKB(LineString(line),hex=True)


	def get_segment_speeds(self):
		"""return speeds (kmph) on the segments between vehicles
			non-ignored only and using shapely"""
		# iterate over segments (i-1)
		dists = []	# km
		times = []	# hours
		for i in range(1,len(self.vehicles)):
			v1 = self.vehicles[i-1]
			v2 = self.vehicles[i]
			# distance in kilometers
			dists.append( v1['geom'].distance(v2['geom'])/1000 )
			# time in hours
			times.append( (v2['time']-v1['time'])/3600 )
		# set the total distance
		self.length = sum(dists)
		# calculate speeds
		return [ d/t for d,t in zip(dists,times) ]


	def match(self):
		"""Match the trip to the road network, and do all the
			things that follow therefrom."""
		match = map_api.match(self.vehicles)				
		if not match.is_useable:
			return db.ignore_trip(self.trip_id,'match problem')
		self.match_confidence = match.confidence
		# store the trip geometry
		self.match_geom = match.geometry()
		# and reproject it
		self.match_geom = reproject( conf['projection'], self.match_geom )
		# simplify slightly for speed (2 meter simplification)
		self.match_geom = self.match_geom.simplify(2)
		# if the multi actually just had one line, this simplifies to a 
		# linestring, which can cause problems down the road
		if self.match_geom.geom_type == 'LineString':
			self.match_geom = MultiLineString([self.match_geom])
		# store the match info and geom in the DB
		db.add_trip_match(
			self.trip_id,
			self.match_confidence,
			dumpWKB(self.match_geom,hex=True)
		)
		# drop vehicles that did not contribute to the match 
		vehicles_used = match.vehicles_used()
		for i in reversed( range( 0, len(self.vehicles) ) ):
			if not vehicles_used[i]: del self.vehicles[i]
		# get distances of each vehicle along the match geom
		for vehicle,cum_dist in zip( self.vehicles, match.cum_distances() ):
			vehicle['cum_dist'] = cum_dist
		# However, because we've simplified the line, the distances will be slightly off
		# and need correcting 
		adjust_factor = self.match_geom.length / self.vehicles[-1]['cum_dist']
		for v in self.vehicles:
			v['cum_dist'] = v['cum_dist'] * adjust_factor
		# get the stops as a list of objects
		# with keys {'id':stop_id,'g':geom}
		self.stops = db.get_stops(self.direction_id,self.last_seen)
		# process the geoms
		for stop in self.stops:
			stop['geom'] = loadWKB(stop['geom'],hex=True)
		# now match stops to the trip geometry, 750m at a time
		path = self.match_geom
		traversed = 0
		# while there is more than 750m of path remaining
		while path.length > 0:
			subpath, path = cut(path,750)
			# check for nearby stops
			for stop in self.stops:
				# if the stop is close enough
				stop_dist = subpath.distance(stop['geom'])
				if stop_dist <= conf['stop_dist']:
					# measure how far it is along the trip
					measure = traversed + subpath.project(stop['geom'])
					# add it to a list of possible stop times
					self.add_arrival(stop['id'],measure,stop_dist)
			# note what we have already traversed
			traversed += 750
		# sort stops by arrival time
		self.timepoints = sorted(self.timepoints,key=lambda k: k['time'])
		# there is more than one stop, right?
		if len(self.timepoints) > 1:
			# store the stop times
			db.store_timepoints(self.trip_id,self.timepoints)
			# Now set the service_id, which is the (local) DAY equivalent of 
			# the unix epoch, which is centered on Greenwich.
			# (The service_id is distinct to a day in the local timezone)
			# First, shift the second_based epoch to local time
			tlocal = self.timepoints[0]['time'] + conf['timezone']*3600
			# then find the "epoch day"
			service_id = math.floor( tlocal / (24*3600) )
			# and store it in the DB
			db.set_service_id(self.trip_id,service_id)
		else:
			db.ignore_trip(self.trip_id,'only one timepoint estimated')
		return


	def add_arrival(self,stop_id,measure,distance):
		"""take an observed stop on a trip and decide if 
			A) this is a legit stop
			B) this is an artifact of the trip splitting procedure
			store the information necessary for the stop_times table"""
		# check for B
		for timepoint in self.timepoints:
			# same stop id and close to the same position?
			if timepoint['stop_id']==stop_id and abs(timepoint['measure']-measure) < 2*conf['stop_dist']:
				# keep the one that is closer
				if timepoint['distance'] <= distance:
					# the stop we already have is closer
					return
				else:	
					# the new stop is closer					
					timepoint['measure'] = measure
					timepoint['dist'] = distance
					timepoint['time'] = self.interpolate_time(measure)
					return
		# we don't have anything like this stop yet, so add it
		# though we may actually have seen this stop already
		self.timepoints.append({
			'stop_id':stop_id,
			'measure':measure,
			'distance':distance,
			'time':self.interpolate_time(measure)
		})


	def ignore_vehicle(self,index):
		"""ignore a vehicle specified by the index"""
		v = self.vehicles.pop(index)
		self.ignored_vehicles.append(v)


	def has_errors(self):
		"""see if the speed segments indicate that there are any 
			fixable errors by making the speed string and checking
			for fixeable patterns."""
		# convert the speeds into a string
		self.speed_string = ''.join([ 
			'x' if seg > 120 else 'o' if seg < 0.1 else '-'
			for seg in self.segment_speeds ])
		# do RegEx search for 'x' or 'oo'
		match_oo = re.search('oo',self.speed_string)
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
		"""get the time for a stop by doing an interpolation on the trip times
			and locations. We already know the m of the stop and of the points on 
			the trip/track"""
		# iterate over the segments of the trip, looking for the segment
		# which holds the stop of interest
		first = True
		for point in self.vehicles:
			if first:
				first = False
				m1 = point['cum_dist']
				t1 = point['time'] # time
				continue
			m2 = point['cum_dist']
			t2 = point['time']
			if m1 <= distance_along_trip <= m2:	# intersection is at or between these points
				# interpolate the time
				if distance_along_trip == m1:
					return t1
				percent_of_segment = (distance_along_trip - m1) / (m2 - m1)
				additional_time = percent_of_segment * (t2 - t1) 
				return t1 + additional_time
			# create the segment for the next iteration
			m1,t1 = m2,t2
		# if we've made it this far, the stop was not technically on or 
		# between any waypoints. This is probably a precision issue and the 
		# stop should be right off one of the ends.
		if distance_along_trip == 0:
			return self.vehicles[0]['time'] - 20
		# vv stop is off the end
		else:
			print '\t\tstop off by',round(distance_along_trip - self.vehicles[-1]['cum_dist'],5),'meters for trip',self.trip_id
			return self.vehicles[-1]['time'] + 20


