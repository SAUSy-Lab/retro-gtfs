# functions involving requests to the nextbus APIs

import requests, time, db
import xml.etree.ElementTree as ET
from trip import trip
import threading
from os import remove, path
from conf import conf # configuration
import sys

# should we process trips (or simply store the vehicles)? default False
doMatching = True if 'doMatching' in sys.argv else False

# GLOBALS
fleet = {} 			# operating vehicles in the ( fleet vid -> trip_obj )
next_trip_id = db.new_trip_id()	# next trip_id to be assigned 
next_bid = db.new_block_id()		# next block_id to be assigned
last_update = 0	# last update from server, removed results already reported

fleet_lock = threading.Lock()
print_lock = threading.Lock()
record_check_lock = threading.Lock()

def get_new_vehicles():
	"""hit the vehicleLocations API and get all vehicles that have updated 
		since the last check. Associate each vehicle with a trip_id (tid)
		and send the trips for processing when it is determined that they 
		have ended"""
	global fleet
	global next_trip_id
	global next_bid
	global last_update
	# time the request was sent
	request_time = time.time()
	try: 
		response = requests.get(
			'http://webservices.nextbus.com/service/publicXMLFeed',
			params={'command':'vehicleLocations','a':conf['agency'],'t':last_update},
			headers={'Accept-Encoding':'gzip, deflate'},
			timeout=3
		)
	except:
		print 'connection problem'
		return
	# time the response was received
	response_time = time.time()
	# estimated time the server generated it's report
	# halfway between send and reply
	server_time = (request_time + response_time) / 2
	# list of trips to send for processing
	ending_trips = []
#	vehicles_to_store = []
	# this is the whole big ol' parsed XML document
	XML = ET.fromstring(response.text)
	# get values from the XML
	last_update = int(XML.find('./lastTime').attrib['time'])
	vehicles = XML.findall('.//vehicle')
	# prevent simulataneous editing
	with fleet_lock:
		# check to see if there's anything we just haven't heard from at all lately
		for vid in fleet.keys():
			# if it's been more than 3 minutes
			if server_time - fleet[vid].last_seen > 180:
				# it has ended
				ending_trips.append(fleet[vid])
				del fleet[vid]
		# Now, for each reported vehicle
		for v in vehicles:
			# if it's not predictable, it's not operating a route
			if v.attrib['predictable'] == 'false': 
				continue
			try: # if it has no direction, it's invalid
				v.attrib['dirTag']
			except: 
				continue
			# get values from XML
			vid, rid, did = int(v.attrib['id']),v.attrib['routeTag'],v.attrib['dirTag']
			lon, lat = float(v.attrib['lon']), float(v.attrib['lat'])
			report_time = server_time - int(v.attrib['secsSinceReport'])
			try: # have we seen this vehicle recently?
				fleet[vid]
			except: # haven't seen it! create a new trip
				fleet[vid] = trip.new(next_trip_id,next_bid,did,rid,vid,report_time)
				# add this vehicle to the trip
				fleet[vid].add_point(lon,lat,report_time)
				# increment the trip and block counters
				next_trip_id += 1
				next_bid += 1
#				# store the vehicle record
#				vehicles_to_store.append((fleet[vid].trip_id,1,lon,lat,report_time))
				# done with this vehicle
				continue
			# we have a record for this vehicle, and it's been heard from recently
			# see if anything else has changed that makes this a new trip
			if ( fleet[vid].route_id != rid or fleet[vid].direction_id != did ):
				# get the block_id from the previous trip
				last_bid = fleet[vid].block_id
				# this trip is ending
				ending_trips.append( fleet[vid] )
				# create the new trip in it's place
				fleet[vid] = trip.new(next_trip_id,last_bid,did,rid,vid,report_time)
				# add this vehicle to it
				fleet[vid].add_point(lon,lat,report_time)
				# increment the trip counter
				next_trip_id += 1
#				# store the vehicle record
#				vehicles_to_store.append((fleet[vid].trip_id,1,lon,lat,report_time))
			else: # not a new trip, just add the vehicle
				fleet[vid].add_point(lon,lat,report_time)
				# then update the time and sequence
				fleet[vid].last_seen = report_time
				fleet[vid].seq += 1
#				# and store the vehicle of course
#				vehicles_to_store.append((
#					fleet[vid].trip_id, 
#					fleet[vid].seq,
#					lon,lat,report_time
#				))
	# release the fleet lock
	print len(fleet),'in fleet,',len(ending_trips),'ending trips'
#	# create/open a temporary file to write the results to
#	filename = path.abspath('temp')+'/'+threading.currentThread().getName()+'.csv'
#	f = open(filename,'w+')
#	# for each vehicle record
#	for (tid,seq,lon,lat,etime) in vehicles_to_store:
#		# write line to file
#		f.write( str(tid)+','+str(seq)+','+str(lon)+','+str(lat)+','+str(etime)+'\n' )
#	# close the file, copy it to the DB and delete it
#	f.close()
#	db.copy_vehicles(filename)
#	remove(filename)
	# process the trips that are ending?
	if doMatching:
		for some_trip in ending_trips:
			# start each in it's own thread
			thread = threading.Thread(target=some_trip.process)
			thread.setDaemon(True)
			thread.start()

def fetch_route(route_id):
	"""function for requesting and storing all relevant information 
		about a given route. Hits the routeConfig command, parses the
		results, and checks them against available information."""
	# request routeConfig for this route
	try: 
		response = requests.get(
			'http://webservices.nextbus.com/service/publicXMLFeed', 
			params={'command':'routeConfig','a':conf['agency'],'r':route_id,'verbose':''}, 
			headers={'Accept-Encoding':'gzip, deflate'}, 
			timeout=3
		)
	except:
		print 'connection error'
		return
	# this is the whole big ol' parsed XML document
	XML = ET.fromstring(response.text)
	# get a list of all stops with locations and iterate over them
	stops = XML.find('.//route').findall('./stop')
	for stop in stops:
		try:	# some stops don't have a stop_Id / stop_code
			stop_code = int(stop.attrib['stopId'])
		except:
			stop_code = -1
		# store the stop, (or ignore it if there is nothing new)
		with record_check_lock:
			db.try_storing_stop(
				stop.attrib['tag'],		# stop_id
				stop.attrib['title'],	# stop_name
				stop_code,					# stop_code # sometimes is missing!
				stop.attrib['lon'], 
				stop.attrib['lat']
			)
	# get a list of "direction"s and iterate over them
	directions = XML.find('.//route').findall('./direction')
	for d in directions:
		# get the ordered stops from this direction and store them
		stops = d.findall('./stop')
		ordered_stop_tags = []
		for stop in stops:
			 ordered_stop_tags.append( stop.attrib['tag'] )
		# attempt to store the direction data
		try: # may have missing tag
			branch = d.attrib['branch']
		except:
			branch = ''
		with record_check_lock:
			db.try_storing_direction(
				route_id,					# route_id
				d.attrib['tag'],			# direction_id
				d.attrib['title'],		# title
				d.attrib['name'],			# name
				branch,						# branch
				d.attrib['useForUI'],	# useforui
				ordered_stop_tags			# stops
			)
	with print_lock:
		print 'fetched route',route_id

def all_routes():
	"""return a list of all available route tags"""
	try:
		response = requests.get(
			'http://webservices.nextbus.com/service/publicXMLFeed', 
			params={'command':'routeList','a':conf['agency']}, 
			headers={'Accept-Encoding':'gzip, deflate'}, 
			timeout=5
		)
	except:
		print 'connection error'
		return []
	# this is the whole big ol' parsed XML document
	XML = ET.fromstring(response.text)
	routes = XML.findall('.//route')
	# initialize list
	routelist = []
	# populate list
	for route in routes:
		routelist.append(route.attrib['tag'])
	# returns a list of strings
	return routelist



