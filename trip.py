# documentation on the nextbus feed:
# http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf

import re, db, json
import map_api
from numpy import mean
import threading
import sys

print_lock = threading.Lock()

# should we process trips (or simply store the vehicles)? default False
doMatching = True if 'doMatching' in sys.argv else False

class trip(object):
	"""The trip class provides all the methods needed for dealing
		with one observed trip/track. Classmethods provide two 
		different ways of instantiating."""

	def __init__(self,trip_id,block_id,direction_id,route_id,vehicle_id,last_seen):
		# set initial attributes
		self.trip_id = trip_id				# int
		self.block_id = block_id			# int
		self.direction_id = direction_id	# str
		self.route_id = route_id			# int
		self.vehicle_id = vehicle_id		# int
		self.last_seen = last_seen			# last vehicle report (epoch time)
		# initialize sequence
		self.seq = 1							# sequence which increments at each report
		# declare several vars for later in the matching process
		self.speed_string = ""				# str
		self.match_confidence = -1			# 0 - 1 real
		self.match_geometry = {}			# parsed geojson object
		self.stops = {}						# not set until process()
		self.segment_speeds = []			# reported speeds of all segments
		self.waypoints = []					# points on the finallized trip only

	@classmethod
	def new(clss,trip_id,block_id,direction_id,route_id,vehicle_id,last_seen):
		"""create wholly new trip object, providing all paremeters"""
		# store instance in the DB
		db.insert_trip( trip_id, block_id, route_id, direction_id, vehicle_id )
		return clss(trip_id,block_id,direction_id,route_id,vehicle_id,last_seen)

	@classmethod
	def fromDB(clss,trip_id):
		"""construct a trip object from an existing record in the database"""
		(bid,did,rid,vid,last_seen) = db.get_trip(trip_id)
		return clss(trip_id,bid,did,rid,vid,last_seen)

	def process(self):
		"""A trip has just ended. What do we do with it?"""
		# populate the geometry field
		db.update_vehicle_geoms(self.trip_id)
		if db.trip_length(self.trip_id) < 0.8: # 0.8km
			return db.delete_trip(self.trip_id)
		# check for errors and attempt to correct them
		self.segment_speeds = db.trip_segment_speeds(self.trip_id)
		while self.has_errors():
			# make sure it's still long enough to bother with
			if len(self.speed_string) < 3:
				return db.delete_trip(self.trip_id)
			# still long enough to try fixing
			self.fix_error()
			# update the segment speeds for the next iteration
			self.segment_speeds = db.trip_segment_speeds(self.trip_id)
		if doMatching:
			self.match()
		

	def match(self):
		"""Match the trip to the road network, and do all the
			things that follow therefrom."""
		match = map_api.map_match(self.trip_id)
		# flag results with multiple matches for now until you can 
		# figure out exactly what is going wrong
		if match['code'] != 'Ok':
			return db.flag_trip(self.trip_id,'match problem, code not "Ok"')
		if len(match['matchings']) > 1:
			return db.flag_trip(self.trip_id,'more than one match segment')
		# get the matched points
		tracepoints = match['tracepoints']
		match = match['matchings'][0]
		# store the trip geometry
		db.add_trip_match(
			self.trip_id,
			match['confidence'],
			json.dumps(match['geometry'])
		)
		# is the match good enough to proceed with?
		if match['confidence'] < 0.5:
			print '\t',match['confidence'],', is too low'
		else:
			print '\t',match['confidence']
		# get the times for the waypoints from the vehicle locations
		times = db.get_waypoint_times(self.trip_id)
		# compare to the corresponding points on the matched line 
		for point,time in zip(tracepoints,times):
			# these are the matched points of the input cordinates
			try:
				self.waypoints.append({
					't':time,
					'm':db.locate_trip_point(
						self.trip_id,
						point['location'][0],	# lon
						point['location'][1]		# lat
					)
				})
			except:
				print '\t\t\twaypoint fail'
		# get the stops ( as a dict keyed by stop_id
		# with keys {'s':sequence,'m':measure,'d':distance}
		self.stops = db.get_stops(self.trip_id,self.direction_id)
		# we now have all the waypoints and all the stops and
		# can begin interpolating times, to be stored alongside the stops.
		num_times = True
		for stop_id in self.stops.keys():
			if self.stops[stop_id]['d'] < 20: # if close enough to be interpolated
				stop_time = self.interpolate_time(stop_id)
				if not stop_time: 
					continue
				# get the stop time and store it
				db.store_stop_time(
					self.trip_id,	# trip_id
					stop_id,			# stop_id
					stop_time		# epoch time
				)
				num_times += 1
		if num_times > 1:
			db.finish_trip(self.trip_id)
		else:
			db.delete_trip(self.trip_id)
		return


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
		"""remove redundant points and fix obvious positional errors using RegEx
			fixes one error each time it's called, the first it finds"""
		# check for leading o's (stationary start)
		m = re.search('^oo*',self.speed_string)
		if m: # remove the first vehicle
			db.delete_vehicle( self.trip_id, 1 )
			return
		# check for trailing o's (stationary end)
		m = re.search('oo*$',self.speed_string)
		if m: # remove the last vehicle
			db.delete_vehicle( self.trip_id, len(self.speed_string)+1 )
			return
		# check for x near beginning, in first four segs
		m = re.search('^.{0,3}x',self.speed_string)
		if m: # remove the first vehicle
			db.delete_vehicle( self.trip_id, 1 )
			return
		# check for x near the end, in last four segs
		m = re.search('x.{0,3}$',self.speed_string)
		if m: # remove the last vehicle
			db.delete_vehicle( self.trip_id, len(self.speed_string)+1 )
			return
		# check for two or more o's in the middle and take from after the first o
		m = re.search('.ooo*.',self.speed_string)
		if m:
			# remove the vehicle after the first o. This matches like '-oo-'
			# so we need to add 2 to the start position to remove the vehicle 
			# report from between the o's ('-o|o-')
			db.delete_vehicle( self.trip_id, m.span()[0]+2 )
			return
		# TODO this is a hack that deletes problems
		# see if you can't do a better job of handling xx's near the middle
		m = re.search('xx',self.speed_string)
		if m:
			print self.trip_id,'has a problem with Xs'
			db.delete_trip(self.trip_id)


	def interpolate_time(self,stop_id):
		"""get the time for a stop which is ordered by doing an interpolation
			on the trip times and locations. We already know the m of the stop
			and of the points on the trip/track"""
		stop_m = self.stops[stop_id]['m']
		# iterate over the segments of the trip, looking for the segment
		# which holds the stop of interest
		first = True
		for point in self.waypoints:
			if first:
				first = False
				m1 = point['m'] # zero
				t1 = point['t'] # time
				continue
			m2 = point['m']
			t2 = point['t']
			if m1 <= stop_m <= m2:	# intersection is at or between these points
				# interpolate the time
				if stop_m == m1:
					return t1
				percent_of_segment = (stop_m - m1) / (m2 - m1)
				additional_time = percent_of_segment * (t2 - t1) 
				return t1 + additional_time
			# create the segment for the next iteration
			m1,t1 = m2,t2
		print '\t\t\tstop thing failed??'
		return None


