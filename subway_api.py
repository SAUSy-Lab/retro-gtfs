# functions involving requests to the nextbus APIs

import requests, time, json


def get_incoming_trains(stationName):
	"""Fetch and return data for one subway station."""
	# time the request was made
	request_time = time.time()
	try: 
		response = requests.get(
			'http://www.ttc.ca/Subway/loadNtas.action',
			params={
				'subwayLine':1,
				'stationId':'',
				'searchCriteria':stationName
				#'_':time.time()
			},
			headers={'Accept-Encoding':'gzip, deflate'},
			timeout=3
		)
		# parse the data
		trains = json.loads(response.text)['ntasData']
	except:
		print 'connection problem'
		return
	# time the response was received
	response_time = time.time()
	# approximate time the response was generated
	server_time = (response_time+request_time)/2
	# go over the trains
	ts = []
	for train in trains:
		ts.append({
			'id': train['trainId'],
			'dir': train['trainDirection'],
			'timeAway': train['timeInt'] * 60,
			'time': server_time + train['timeInt'] * 60,
			# one of ['SHEP','YUS','??']
			'line': train['subwayLine']
		})
	return ts
