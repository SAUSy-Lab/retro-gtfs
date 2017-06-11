# do the map matching. This is separated to 
# avoid circular dependencies

import requests, json, db
from conf import conf

def map_match(vehicles,include_times=True):
	"""Map Match the GPS track to the street/rail network
		return the python-parsed JSON object"""
	# structure it like fussy API needs
	lons = []
	lats = []
	times = []
	radii = []
	for v in vehicles:
		lons.append(v['lon'])
		lats.append(v['lat'])
		times.append( int( round( v['time'] ) ) )
	coords = ';'.join( [str(lon)+','+str(lat) for (lon,lat) in zip(lons,lats)] )
	times = ';'.join( [str(time) for time in times] )
	radii = ';'.join( ['20']*len(lons) )
	# construct and send the request
	options = {
		'geometries':'geojson',
		'overview':'full',
		'radiuses':radii,
		'gaps':'split',	# split the track based on big time gaps?
		'tidy':True
	}
	if include_times:
		options['timestamps'] = times
	response = requests.get(
		conf['OSRMserver']['url']+'/match/v1/transit/'+coords,
		params=options,
		timeout=conf['OSRMserver']['timeout']
	)
	# parse the result
	j = json.loads(response.text)
	# see if there is more than one match. If there is, try again 
	# without times. Avoid infinite recursion
	if include_times: # was first try
		if j['code']=='Ok' and len(j['matchings']) > 1: # and now more than one match
			# try without times
			j = map_match(vehicles,False)
	return j
