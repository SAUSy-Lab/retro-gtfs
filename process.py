# call this file to begin processing a set of trips from 
# stored vehicle locations. It will ask which trips from 
# the db to process. For now, I am testing with one at a 
# time. 

import threading
import db
from time import sleep
from trip import trip

trip_id = raw_input('trip_id to process--> ')

# create a trip object
this_trip = trip.fromDB(trip_id)

db.scrub_trip(trip_id)
db.sequence_vehicles(trip_id)

this_trip.process()

#for route_id in routes:
#	t = threading.Thread(target=fetch_route,args=(route_id,))
#	t.start()
#	if threading.active_count() >= 20:
#		sleep(3)
#	sleep(10)

## call the big function. This takes longer to run the first time, 
#get_new_vehicles()

## so wait a bit longer than usual to call the timer function 10secs later
#threading.Timer( 10, time_loop ).start()
## then it calls itself every N secs
