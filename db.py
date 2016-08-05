# functions involving BD interaction
import psycopg2		# DB interaction
import json
from conf import conf

# connect and establish a cursor, based on parameters in conf.py
conn_string = (
	"host='"+conf['db']['host']
	+"' dbname='"+conf['db']['name']
	+"' user='"+conf['db']['user']
	+"' password='"+conf['db']['password']+"'"
)
conn = psycopg2.connect(conn_string)
conn.autocommit = True

def new_trip_id():
	"""get a next trip_id to start from, defaulting to 1"""
	c = conn.cursor()
	c.execute("SELECT MAX(trip_id) FROM nb_vehicles;")
	try:
		(trip_id,) = c.fetchone()
		trip_id += 1
	except:
		trip_id = 1
	return trip_id

def new_block_id():
	"""get a next block_id to start from, defaulting to 1"""
	c = conn.cursor()
	c.execute("SELECT MAX(block_id) FROM nb_trips;")
	try:
		(block_id,) = c.fetchone()
		block_id += 1
	except:
		block_id = 1
	return block_id

def empty_tables():
	"""clear the tables"""
	c = conn.cursor()
	c.execute("""
		TRUNCATE nb_trips;
		TRUNCATE nb_vehicles;
		TRUNCATE nb_stop_times;
	""")

def copy_vehicles(filename):
	"""copy a CSV of vehicle records into the nb_vehicles table"""
	c = conn.cursor()
	c.execute("""
		COPY nb_vehicles (trip_id,seq,lon,lat,report_time) FROM %s CSV;
	""",(filename,))

def update_vehicle_geoms(trip_id):
	"""make the location geometries from the lat/lon"""
	c = conn.cursor()
	c.execute("""
		UPDATE nb_vehicles SET 
			location = ST_Transform(ST_SetSRID(ST_MakePoint(lon,lat),4326),26917)
		WHERE trip_id = %s; 
	""",(trip_id,))

def trip_length(trip_id):
	"""return the length of the trip in KM"""
	c = conn.cursor()
	c.execute("""
		SELECT 
			ST_Length(ST_MakeLine(location ORDER BY seq)) / 1000
		FROM nb_vehicles 
		WHERE trip_id = %s
		GROUP BY trip_id;
	""",(trip_id,))
	(km,) = c.fetchone()
	return km

def delete_trip(trip_id):
	"""delete a trip completely from the db"""
	c = conn.cursor()
	c.execute("""
		DELETE FROM nb_vehicles WHERE trip_id = %s;
		DELETE FROM nb_trips WHERE trip_id = %s;
		DELETE FROM nb_stop_times WHERE trip_id = %s;
	""",(trip_id,trip_id,trip_id) )
	return

def delete_trip_times(trip_id):
	"""delete stop times for a given trip. Used to delete the trip 
		from the output while keeping the geometry in nb_trips for 
		error checking"""
	c = conn.cursor()
	c.execute("DELETE FROM nb_stop_times WHERE trip_id = %s;",(trip_id,))

def trip_segment_speeds(trip_id):
	"get a list of the speeds (KMpH) on each inter-vehicle trip segment"
	c = conn.cursor()
	# calculate segment-level speeds, in order of appearance
	c.execute("""
		SELECT
			(v1.location <-> v2.location) / 1000 AS km,
			(v2.report_time - v1.report_time) / 3600 AS hrs
		FROM nb_vehicles AS v1
		JOIN nb_vehicles AS v2
			ON v1.seq = v2.seq-1
		WHERE v1.trip_id = %s AND v2.trip_id = %s
		ORDER BY v1.seq;
	""",(trip_id,trip_id) )
	# divides km/h, returning a list
	try:
		return [ kilometers/hours for (kilometers,hours) in c.fetchall() ]
	except:
		print 'trip '+str(trip_id)+'produced an error in trip_segment_speeds()'
		return []

def delete_vehicle( trip_id, position ):
	"""Remove a vehicle location record and shift the trip_sequence 
		numbers accordingly"""
	c = conn.cursor()
	# delete the record of a single specified vehicle
	# shift the sequence number down one for all vehicles past the deleted one
	c.execute("""
		DELETE FROM nb_vehicles
		WHERE trip_id = %s AND seq = %s;
		UPDATE nb_vehicles SET seq = seq - 1
		WHERE trip_id = %s AND seq > %s;
	""",( trip_id ,position, trip_id, position ))

def get_vehicles(trip_id):
	"""gets data on the ordered vehicles for a trip.
		This is for input into map matching"""
	c = conn.cursor()
	# get the trip geometry and timestamps
	c.execute("""
		SELECT
			lon, lat,
			ROUND(report_time)::int AS t
		FROM nb_vehicles 
		WHERE trip_id = %s
		ORDER BY report_time ASC;
	""",(trip_id,))
	# turn that data into correctly formatted lists
	lons = []
	lats = []
	times = []
	for (lon,lat,time) in c.fetchall():
		lons.append(lon)
		lats.append(lat)
		times.append(time)
	return (lons,lats,times)

def store_trip(tid,bid,rid,did,vid,confidence,geometry):
	"""store the trip in the database"""
	c = conn.cursor()
	# store the given values
	c.execute("""
		INSERT INTO nb_trips ( 
			trip_id, block_id, route_id, direction_id, vehicle_id, 
			match_confidence,
			match_geom ) 
		VALUES ( 
			%s,%s,%s,%s,%s,
			%s,
			ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),26917)
		);
	""",(
		tid, bid, rid, did, vid, 
		confidence,
		geometry
	))

def get_waypoint_times(trip_id):
	"""get the times for the ordered vehicle locations"""
	c = conn.cursor()
	c.execute("""
		SELECT
			report_time
		FROM nb_vehicles
		WHERE trip_id = %s
		ORDER BY report_time ASC;
	""",(trip_id,))
	# assign the times to a dict keyed by sequence
	result = []
	for (time,) in c.fetchall():
		result.append(time)
	return result

def get_stops(trip_id,direction_id):
	"""given the direction id, get the ordered list of stops
		and their attributes for the direction, returning 
		as a dictionary"""
	c = conn.cursor()
	c.execute("""
		WITH sub AS (
			SELECT
				unnest(stops) AS stop_id
			FROM nb_directions 
			WHERE
				direction_id = %s AND
				report_time = (
					SELECT MAX(report_time) -- most recent 
					FROM nb_directions 
					WHERE direction_id = %s
				)
		)
		SELECT 
			sub.stop_id,
			ST_LineLocatePoint(nb_trips.match_geom,nb_stops.the_geom) AS m,
			nb_trips.match_geom <-> nb_stops.the_geom AS dist
		FROM nb_trips
		JOIN sub ON TRUE
		JOIN nb_stops
			ON sub.stop_id = nb_stops.stop_id
		WHERE nb_trips.trip_id = %s;
	""",(direction_id,direction_id,trip_id))
	result = {}
	for (stop_id,measure,distance) in c.fetchall():
		result[stop_id] = {
			'm':measure,
			'd':distance
		}
	return result

def locate_trip_point(trip_id,lon,lat):
	"""use ST_LineLocatePoint to locate a point on a trip geometry.
		This is always a point matched to the trip, so should be
		right on the line. No need to measure distance."""
	c = conn.cursor()
	c.execute("""
		SELECT 
			ST_LineLocatePoint(
				match_geom,	-- line
				ST_Transform(ST_SetSRID(ST_MakePoint(%s,%s),4326),26917)	-- point
			)
		FROM nb_trips 
		WHERE trip_id = %s;
	""",(lon,lat,trip_id))
	(result,) = c.fetchone()
	return result

def store_stop_time(trip_id,stop_id,time):
	"""store the time and trip of a stop. sequence and service-day-relative 
		arrival/departure times will be set later."""
	c = conn.cursor()
	c.execute("""
		INSERT INTO nb_stop_times (trip_id,stop_id,etime) 
		VALUES (%s,%s,%s);
	""",(trip_id,stop_id,time))

def finish_trip(trip_id):
	"""stop times are stored, do the rest and be done:
		1. set the stop_sequence field of nb_stop_times
		2. determine and set the service_id in nb_trips.
		3. set the arrival and departure times based on the day start"""
	c = conn.cursor()
	# set the stop sequences
	c.execute("""
		WITH sub AS (
			SELECT uid, row_number() OVER (ORDER BY etime ASC)
			FROM nb_stop_times
			WHERE trip_id = %s
		)
		UPDATE nb_stop_times SET stop_sequence = row_number 
		FROM sub WHERE sub.uid = nb_stop_times.uid
	""",(trip_id,))
	# get the first start time
	c.execute("""
		SELECT etime
		FROM nb_stop_times 
		WHERE trip_id = %s AND stop_sequence = 1;
	""",(trip_id,))
	(t,) = c.fetchone()
	t = t
	# find the etime of the first moment of the day
	# first center the day on local time
	tlocal = t - 4*3600
	from_dawn = tlocal % (24*3600)
	# service_id is distinct to local day
	service_id = (tlocal-from_dawn)/(24*3600)
	day_start = t - from_dawn
	c.execute("""
		UPDATE nb_trips SET service_id = %s WHERE trip_id = %s;
	""",(service_id,trip_id))
	# set the arrival and departure times
	c.execute("""
		UPDATE nb_stop_times SET 
			arrival_time = ROUND(etime - %s) * INTERVAL '1 second',
			departure_time = ROUND(etime - %s) * INTERVAL '1 second'
		WHERE trip_id = %s;
	""",(day_start,day_start,trip_id))

def try_storing_stop(stop_id,stop_name,stop_code,lon,lat):
	"""we have received a report of a stop from the routeConfig
		data. Is this a new stop? Have we already heard of it?
		Decide whether to store it or ignore it. If absolutely
		nothing has changed about the record, ignore it. If not,
		store it with the current time."""
	c = conn.cursor()
	# see if precisely this record already exists
	c.execute("""
		SELECT * FROM nb_stops
		WHERE 
			stop_id = %s AND
			stop_name = %s AND
			stop_code = %s AND
			ABS(lon - %s::numeric) <= 0.0001 AND
			ABS(lat - %s::numeric) <= 0.0001;
	""",( stop_id,stop_name,stop_code,lon,lat ) )
	# if any result, we already have this stop
	if c.rowcount > 0:
		return
	# store the stop
	c.execute("""
		INSERT INTO nb_stops ( 
			stop_id, stop_name, stop_code, 
			the_geom, 
			lon, lat, report_time 
		) 
		VALUES ( 
			%s, %s, %s, 
			ST_Transform( ST_SetSRID( ST_MakePoint(%s, %s),4326),26917 ),
			%s, %s, NOW()
		)""",( 
			stop_id,stop_name,stop_code,
			lon,lat,
			lon,lat #,time
		) )

def try_storing_direction(route_id,did,title,name,branch,useforui,stops):
	"""we have recieved a report of a route direction from the 
		routeConfig data. Is this a new direction? Have we already 
		heard of it? Decide whether to store it or ignore it. If 
		absolutely nothing has changed about the record, ignore it. 
		If not, store it with the current time."""
	c = conn.cursor()
	# see if exactly this record already exists
	c.execute("""
		SELECT * FROM nb_directions
		WHERE
			route_id = %s AND
			direction_id = %s AND
			title = %s AND
			name = %s AND
			branch = %s AND
			useforui = %s AND
			stops = %s;
	""",(route_id,did,title,name,branch,useforui,stops))
	if c.rowcount > 0:
		return # already have the record
	# store the data
	c.execute("""
		INSERT INTO nb_directions 
			( 
				route_id, direction_id, title, 
				name, branch, useforui, 
				stops, report_time
			) 
		VALUES 
			( 
				%s, %s, %s,
				%s, %s, %s, 
				%s, NOW()
			)""",(
				route_id,did,title,
				name,branch,useforui,
				stops
			)
		)

#
# functions for separate processing of trips
#

#def clear_stop_times_and_trips():
#	"""clear the trips and stop times tables"""
#	c = conn.cursor("""
#		TRUNCATE nb_stop_times;
#		TRUNCATE nb_trips;
#	""")

#def sample_trips(num_trips,offset=0):
#	"""return N trip_ids in a list"""
#	c = conn.cursor()
#	c.execute("""
#		SELECT 
#			trip_id
#		FROM nb_vehicles
#		ORDER BY trip_id ASC
#		LIMIT %s
#		OFFSET %s;
#	""",(num_trips,offset))
#	trips = []
#	for (tid,) in c.fetchall():
#		trips.append(tid)
#	return trips





