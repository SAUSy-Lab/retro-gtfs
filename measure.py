# working toward a comprehensive set of quality metrics for retro-gtfs data

import db
from trip import Trip
from numpy import percentile, median 

mode = raw_input('Mode (single, all, or route) --> ')


def assess_trips(trip_ids):
	"""Given a list of trips, come up with basic quality measures for each, 
		then aggregate and print the results."""
	# define variables to store metrics
	stop_ratios = []
	trips_wo_stops = []
	# iterate over trips
	for trip_id in trip_ids:
		# pull in the necessary data for a trip
		trip = Trip.fromDB(trip_id)
		stops = db.get_stops(trip.direction_id,trip.last_seen)
		timepoints = db.get_timepoints(trip.trip_id)
		# start calculating metrics and appending them to lists
		# 
		# ratio of timepoints / stops 
		stop_ratios.append( len(timepoints) / float(len(stops)) )
		# trips with no stops
		if len(timepoints) == 0:
			trips_wo_stops.append(trip.trip_id)
		
	# stdout
	print 'stop ratios:', percentile(stop_ratios,[0,25,50,75,100])
	print 'trips without stops:',len(trips_wo_stops),'/',len(trip_ids),'or',(len(trips_wo_stops)/float(len(trip_ids)))*100,'%'

# single mode enters one trip at a time and stops when 
# a non-integer is entered
if mode in ['single','s']:
	trip_id = raw_input('trip_id to process--> ')
	while trip_id.isdigit():
		if db.trip_exists(trip_id):
			assess_trips( [trip_id] )
		else:
			print 'no such trip'
		# ask for another trip and continue
		trip_id = raw_input('trip_id to process --> ')

# 'range' mode does all valid ids in the given range
elif mode in ['all','a']:
	# get a list of all trip id's
	trip_ids = db.get_trip_ids_by_range(-float('inf') ,float('inf'))
	print len(trip_ids),'trips in that range'
	assess_trips(trip_ids)

# process only a certain route, then a subset of that route's trips
elif mode in ['route','r']:
	route_id = raw_input('route_id --> ')
	trip_ids = db.get_trip_ids_by_route(route_id)
	print len(trip_ids),'trips on that route'
	assess_trips(trip_ids)

else:
	print 'invalid mode entered' 
