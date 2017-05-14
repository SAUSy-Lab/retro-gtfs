import requests, json
from time import time as now

def get_incoming_trains(stationName):
	"""Fetch and return data for one subway station. Returns a list of 
		vehicle status objects."""
	# time the request was made
	request_time = now()
	try: 
		response = requests.get(
			'http://www.ttc.ca/Subway/loadNtas.action',
			params={
				'subwayLine':1,
				'stationId':'',
				'searchCriteria':stationName
				#'_':time()
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
	response_time = now()
	# approximate time the response was generated
	server_time = (response_time+request_time)/2
	
	# parse the results into a list of status objects 
	results = []
	for train in trains:
		results.append( Status(train,stationName,server_time) )

	return results



class Status(object):
	"""defines a nugget of train status information delivered from the server"""

	def __init__(self, train, fromStation, time):
		"""is initiated with 
				train: direct-from-JSON results object
				fromStation: station the time was estimated for
				time: (estimated) time the server generated the estimate"""
		self.id = train['trainId']
		self.line = train['subwayLine']
		self.direction = train['trainDirection']
		self.fromStation = fromStation
		self.estArrival = time + train['timeInt'] * 60
		


