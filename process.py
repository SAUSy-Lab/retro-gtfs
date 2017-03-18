# call this file to begin processing a set of trips from 
# stored vehicle locations. It will ask which trips from 
# the db to process. For now, I am testing with one at a 
# time. 

import threading
import db
from time import sleep
from trip import trip

# let mode be one of ('single','range?')
mode = raw_input('Processing mode (single or range) --> ')

# single mode enters one trip at a time and stops when 
# a non-integer is entered
if mode == 'single':
	trip_id = raw_input('trip_id to process--> ')
	while trip_id.isdigit():
		if db.trip_exists(trip_id):
			# create a trip object
			this_trip = trip.fromDB(trip_id)
			# get the DB (back) to a fresh state
			db.scrub_trip(trip_id)
			db.sequence_vehicles(trip_id)
			# process
			this_trip.process()
		else:
			print 'no such trip'
		# ask for another trip and continue
		trip_id = raw_input('trip_id to process--> ')

# 'range' mode does all valid ids in the given range
elif mode == 'range':
	id_range = raw_input('trip_id range as start:end --> ')
	id_range = id_range.split(':')
	# get a list of trip id's in the range
	trip_ids = db.get_trip_ids(id_range[0],id_range[1])
	print len(trip_ids),'trips in that range'
	# how many threads to use?
	max_threads = int(raw_input('max simultaneous threads--> '))
	# start looping over trips
	while len(trip_ids) > 0:
		if threading.active_count() < max_threads + 1:
			tid = trip_ids.pop()
			print tid
			some_trip = trip.fromDB(tid)
			thread = threading.Thread(target=some_trip.process)
			thread.start()
		else:
			print 'sleeping..'
			sleep(0.3)	

else:
	print 'invalid entry mode given' 







