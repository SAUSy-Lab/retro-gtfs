# Map match the GPS track to the street/rail network using OSRM. 
# Try altering some parameters if the match is poor. 

import requests, json
from conf import conf
from numpy import mean
from shapely.geometry import MultiLineString, asShape


class match(object):
	"""map match result object"""

	def __init__(self,vehicles):
		# initialize some variables
		self.vehicles = vehicles
		self.confidence = None					# average match confidence
		self.geom = MultiLineString()			# multiline shapely geom
		self.error_radius = conf['error_radius']
		self.use_times = True					# whether times are sent to OSRM
		self.response = {}						# python-parsed formerly-JSON object
		self.is_useable = True					# good enough to be used elsewhere?
		self.num_attempts = 0
		# send the query right away
		self.send()
		# validate the results - can we likely improve on them?
		self.validate()
		# print 
		print '\tconf. is',self.confidence,'on',len(self.response['matchings']),'match(es) after',self.num_attempts,'tries' 


	def send(self):
		"""construct the query and send it to OSRM"""
		# structure it as API requires
		lons, lats, times, radii = [], [], [], []
		for v in self.vehicles:
			lons.append(v['lon'])
			lats.append(v['lat'])
			times.append( int( round( v['time'] ) ) )
		coords = ';'.join( [str(lon)+','+str(lat) for (lon,lat) in zip(lons,lats)] )
		times = ';'.join( [str(time) for time in times] )
		radii = ';'.join( [str(round(self.error_radius))]*len(lons) )
		# construct and send the request
		options = {
			'radiuses':radii,
			'steps':'false',
			'geometries':'geojson',
			'annotations':'false',
			'overview':'full',
			'gaps':'split', # split the track based on big time gaps?
			'tidy':'true',
			'generate_hints':'false'
		}
		# optionally include timestamps
		if self.use_times:
			options['timestamps'] = times 
		# make the request 
		raw_response = requests.get(
			conf['OSRMserver']['url']+'/match/v1/transit/'+coords,
			params=options,
			timeout=conf['OSRMserver']['timeout']
		)
		# parse the result to a python object
		self.response = json.loads(raw_response.text)
		# note the attempt
		self.num_attempts += 1


	def validate(self):
		"""if improved matches are possible, try to make them"""
		while self.may_be_improved():
			self.error_radius *= 1.5
			self.send()


	def may_be_improved(self):
		"""can this match likely be improved by anything we can control here?"""
		if self.response['code'] != 'Ok':
			print '\tcode not Ok'
			self.is_useable = False
			return False
		# estimate the match confidence
		confidences = [ m['confidence'] for m in self.response['matchings'] ]
		self.confidence = mean(confidences)
		if (
			self.confidence / len(self.response['matchings']) < 0.2
			and self.error_radius < 2*conf['error_radius']
		):
			return True
		else:
			return False


	def geometry(self):
		"""return the multi-line geometry from one or more matches"""
		# get a list of lists of coords
		lines = [asShape(matching['geometry']) for matching in self.response['matchings']]
		return MultiLineString(lines)


	def vehicles_used(self):
		"""for each vehicle, return a boolean list in the same order telling that 
			vehicle was used to construct the match result"""
		# these are the matched points of the input cordinates
		# null (None) entries indicate an omitted (outlier) point
		tracepoints = self.response['tracepoints']
		# true where not none
		return [ point is not None for point in tracepoints ]


	def cum_distances(self):
		"""return the cumulative distances for each vehicle point along the
			track, which is based on the leg distances provided by OSRM. Each 
			leg is just the trip between matched points. Each match has one more 
			vehicle record associated with it than legs"""
		cum_dist = 0
		dist_list = []
		for matching in self.response['matchings']:
			# the first point is at 0 per match
			dist_list.append(cum_dist)
			for leg in matching['legs']:
				cum_dist += leg['distance']
				dist_list.append(cum_dist)
		return dist_list






