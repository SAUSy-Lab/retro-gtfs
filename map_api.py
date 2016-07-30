# do the map matching. This is separated to 
# avoid circular dependencies

import requests, json, db

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
		'http://206.167.182.17:5000/match/v1/transit/'+coords,
		params=options,
		timeout=10
	)
	# parse the result
	j = json.loads(response.text)
	# see if there is more than one match. If there is, try again 
	# without times. Avoid infinite recursion
	if include_times: # was first try
		if j['code']=='Ok' and len(j['matchings']) > 1: # and now more than one match
			print 'trying',trip_id,'again without times'
			# try without times
			j = map_match(trip_id,False)
	multi_match_test(j,trip_id)
	return j

def multi_match_test(match_result,trip_id):
	"""test a map match response object for multiple matches.
		If found, write these into a geojson file in the temp
		folder for individual analysis."""
	if match_result['code'] != 'Ok':
		return
	if len(match_result['matchings']) == 1:
		return
	# has matches (more than one)
	# start the output geojson object
	output = {
		'type':'FeatureCollection',
		'features':[]
	}
	# iterate over matches
	for i in range(0,len(match_result['matchings'])):
		match = match_result['matchings'][i]
		# append match geometry with match number
		output['features'].append(
			{
				'type':'feature',
				'geometry':match['geometry'],
				'properties': {
					'input':False,
					'match_num':i,
					'confidence':match['confidence']
				}
			}
		)
	# add input geometry
	(lons,lats,times) = db.get_vehicles(trip_id)
	output['features'].append(
		{
			'type':'feature',
			'geometry':{
				'type':'LineString',
				'coordinates':[ [float(lon),float(lat)] for (lon,lat) in zip(lons,lats)],
			},
			'properties':{
				'input':True,
				'match_num':None,
				'confidence':None
			}
		}
	)
	# write the file
	filename = '/home/ubuntu/nb/match_pairs/'+str(trip_id)+'.geojson'
	f = open(filename,'w+')
	f.write(json.dumps(output))
	f.close()
	return









