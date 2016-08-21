# do the map matching. This is separated to 
# avoid circular dependencies

import requests, json, db
from conf import conf

def map_match(trip_id,include_times=True):
	"""Map Match the GPS track to the street/rail network
		return the python-parsed JSON object"""
	# get the data for this trip
	(lons,lats,times) = db.get_vehicles(trip_id)
	# structure it like fussy API needs
	coords = ';'.join( [str(lon)+','+str(lat) for (lon,lat) in zip(lons,lats)] )
	times = ';'.join( [str(time) for time in times] )
	radii = ';'.join( ['20']*len(lons) )
	# construct and send the request
	options = {
		'geometries':'geojson',
		'radiuses':radii,
		'overview':'full'
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
			print '\t',trip_id,'again without times'
			# try without times
			j = map_match(trip_id,False)
	return j
