# functions involving BD interaction
import psycopg2, json, math
from conf import conf

# connect and establish a cursor, based on parameters in conf.py
conn_string = (
	"host='"+conf['db']['host']
	+"' dbname='"+conf['db']['name']
	+"' user='"+conf['db']['user']
	+"' password='"+conf['db']['password']+"'"
)
connection = psycopg2.connect(conn_string)
connection.autocommit = True

def reconnect():
	"""renew connections inside a process"""
	global connection
	connection = psycopg2.connect(conn_string)
	connection.autocommit = True

def cursor():
	"""provide a cursor"""
	return connection.cursor()

def new_trip_id():
	"""get a next trip_id to start from, defaulting to 1"""
	c = cursor()
	c.execute(
		"""
			SELECT MAX(trip_id) FROM {trips};
		""".format(**conf['db']['tables'])
	)
	try:
		(trip_id,) = c.fetchone()
		return trip_id + 1
	except:
		return 1

def new_block_id():
	"""get a next block_id to start from, defaulting to 1"""
	c = cursor()
	c.execute(
		"""
			SELECT MAX(block_id) FROM {trips};
		""".format(**conf['db']['tables'])
	)
	try:
		(block_id,) = c.fetchone()
		return block_id + 1
	except:
		return 1

def empty_tables():
	"""clear the tables"""
	c = cursor()
	c.execute(
		"""
			TRUNCATE {trips}, {stop_times}, {directions}, {stops};
		""".format(**conf['db']['tables'])
	)


def ignore_trip(trip_id,reason=None):
	"""mark a trip to be ignored"""
	c = cursor()
	c.execute(
		"""
			UPDATE {trips} SET ignore = TRUE WHERE trip_id = %(trip_id)s;
			DELETE FROM {stop_times} WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{ 'trip_id': trip_id } 
	)
	if reason:
		flag_trip(trip_id,reason)
	return


def flag_trip(trip_id,problem_description_string):
	"""Populate the 'problem' field of trip table: something must 
		have gone wrong and this tells us what."""
	c = cursor()
	c.execute(
		"""
			UPDATE {trips} SET problem = problem || %(description)s 
			WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{
			'description':problem_description_string,
			'trip_id':trip_id
		}
	)



def add_trip_match(trip_id,confidence,geometry_match):
	"""update the trip record with it's matched geometry"""
	c = cursor()
	# store the given values
	c.execute(
		"""
			UPDATE {trips}
			SET  
				match_confidence = %(confidence)s,
				match_geom = ST_Transform(
					ST_SetSRID(ST_GeomFromGeoJSON( %(match)s ),4326),
					%(localEPSG)s
				)
			WHERE trip_id  = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{
			'localEPSG':conf['localEPSG'],
			'confidence':confidence, 
			'match':geometry_match, 
			'trip_id':trip_id
		}
	)


def insert_trip(trip_id,block_id,route_id,direction_id,vehicle_id):
	"""Store the basics of the trip in the database."""
	c = cursor()
	# store the given values
	c.execute(
		"""
			INSERT INTO {trips} 
				( trip_id, block_id, route_id, direction_id, vehicle_id ) 
			VALUES 
				( %(trip_id)s,%(block_id)s,%(route_id)s,%(direction_id)s,%(vehicle_id)s );
		""".format(**conf['db']['tables']),
		{
			'trip_id':trip_id, 
			'block_id':block_id, 
			'route_id':route_id, 
			'direction_id':direction_id, 
			'vehicle_id':vehicle_id
		}
	)



def get_stops(direction_id):
	"""given the direction id, get the ordered list of stops
		and their attributes for the direction, returning 
		as a dictionary"""
	c = cursor()
	c.execute(
		"""
			WITH sub AS (
				SELECT
					unnest(stops) AS stop_id
				FROM {directions} 
				WHERE
					direction_id = %(direction_id)s AND
					report_time = (
						SELECT MAX(report_time) -- most recent 
						FROM {directions} 
						WHERE direction_id = %(direction_id)s
					)
			)
			SELECT 
				stop_id,
				the_geom
			FROM {stops}
			WHERE stop_id IN (SELECT stop_id FROM sub);
		""".format(**conf['db']['tables']),
		{
			'direction_id':direction_id
		}
	)
	stops = []
	for (stop_id,geom) in c.fetchall():
		stops.append({
			'id':stop_id,
			'geom':geom
		})
	return stops


def store_points(trip_id,localWKBgeom,etimes_list):
	"""this should be run on the inital, live collected trip instance.
		It stores the time and location of every given report for this trip."""
	c = cursor()
	c.execute(
		"""
			UPDATE {trips} SET 
				orig_geom = ST_SetSRID( %(geom)s::geometry, %(localEPSG)s ),
				times = %(times)s
			WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{
			'trip_id':trip_id,
			'geom':localWKBgeom,
			'localEPSG':conf['localEPSG'],
			'times':etimes_list
		}
	)


def set_trip_clean_geom(trip_id,localWKBgeom):
	"""Store a geometry of the input to the matching process"""
	c = cursor()
	c.execute(
		"""
			UPDATE {trips} 
			SET clean_geom = ST_SetSRID( %(geom)s::geometry, %(EPSG)s )
			WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{
			'trip_id':trip_id,
			'geom':localWKBgeom,
			'EPSG':conf['localEPSG']
		}
	)


def store_stop_times(trip_id,stops):
	"""store the stop times for a trip"""
	c = cursor()
	# insert the stops
	records = []
	seq = 1
	for stop in stops:
		# list of tuples
		records.append( (trip_id,stop['id'],stop['arrival'],seq) )
		seq += 1
	args_str = ','.join(c.mogrify("(%s,%s,%s,%s)", x) for x in records)
	c.execute("INSERT INTO nb_stop_times (trip_id, stop_id, etime, stop_sequence) VALUES " + args_str)


def set_service_id(trip_id,service_id):
	"""set the service_id of a trip"""
	c = cursor()
	c.execute(
		"""
			UPDATE {trips} 
			SET service_id = %(service_id)s 
			WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{
			'service_id':service_id,
			'trip_id':trip_id
		}
	)


def try_storing_stop(stop_id,stop_name,stop_code,lon,lat):
	"""we have received a report of a stop from the routeConfig
		data. Is this a new stop? Have we already heard of it?
		Decide whether to store it or ignore it. If absolutely
		nothing has changed about the record, ignore it. If not,
		store it with the current time."""
	c = cursor()
	# see if precisely this record already exists
	c.execute(
		"""
			SELECT * 
			FROM {stops}
			WHERE 
				stop_id = %(stop_id)s AND
				stop_name = %(stop_name)s AND
				stop_code = %(stop_code)s AND
				ABS(lon - %(lon)s::numeric) <= 0.0001 AND
				ABS(lat - %(lat)s::numeric) <= 0.0001;
		""".format(**conf['db']['tables']),
		{
			'stop_id':stop_id,
			'stop_name':stop_name,
			'stop_code':stop_code,
			'lon':lon,
			'lat':lat
		}
	)
	# if any result, we already have this stop
	if c.rowcount > 0:
		return
	# store the stop
	c.execute(
		"""
			INSERT INTO nb_stops ( 
				stop_id, stop_name, stop_code, 
				the_geom, 
				lon, lat, report_time 
			) 
			VALUES ( 
				%(stop_id)s, %(stop_name)s, %(stop_code)s, 
				ST_Transform( ST_SetSRID( ST_MakePoint(%(lon)s, %(lat)s),4326),%(localEPSG)s ),
				%(lon)s, %(lat)s, NOW()
			)""".format(**conf['db']['tables']),
			{ 
				'stop_id':stop_id,
				'stop_name':stop_name,
				'stop_code':stop_code,
				'lon':lon,
				'lat':lat,
				'localEPSG':conf['localEPSG']
			} )


def try_storing_direction(route_id,did,title,name,branch,useforui,stops):
	"""we have recieved a report of a route direction from the 
		routeConfig data. Is this a new direction? Have we already 
		heard of it? Decide whether to store it or ignore it. If 
		absolutely nothing has changed about the record, ignore it. 
		If not, store it with the current time."""
	c = cursor()
	# see if exactly this record already exists
	c.execute(
		"""
			SELECT * FROM {directions}
			WHERE
				route_id = %s AND
				direction_id = %s AND
				title = %s AND
				name = %s AND
				branch = %s AND
				useforui = %s AND
				stops = %s;
		""".format(**conf['db']['tables']),
		(
			route_id,
			did,
			title,
			name,
			branch,
			useforui,
			stops
		)
	)
	if c.rowcount > 0:
		return # already have the record
	# store the data
	c.execute(
		"""
			INSERT INTO {directions} 
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
				)""".format(**conf['db']['tables']),
			(
				route_id,did,title,
				name,branch,useforui,
				stops
			)
		)


def scrub_trip(trip_id):
	"""Un-mark any flag fields and leave the DB record 
		as though newly collected and unprocessed"""
	c = cursor()
	c.execute(
		"""
			-- Trips table
			UPDATE nb_trips SET 
				match_confidence = NULL,
				match_geom = NULL,
				orig_geom = NULL,
				clean_geom = NULL,
				problem = '',
				ignore = FALSE 
			WHERE trip_id = %(trip_id)s;
			-- Stop-Times table
			DELETE FROM nb_stop_times 
			WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{'trip_id':trip_id}
	)



def get_trip(trip_id):
	# TODO eliminate dependence on nb_vehicles
	"""return the attributes of a stored trip necessary 
		for the construction of a new trip object"""
	c = cursor()
	c.execute("""
		SELECT 
			block_id, direction_id, route_id, vehicle_id 
		FROM nb_trips
		WHERE trip_id = %s
		""",(trip_id,)
	)
	(bid,did,rid,vid,) = c.fetchone()
	c.execute("""
		SELECT MAX(report_time) 
		FROM nb_vehicles 
		WHERE trip_id = %s AND NOT ignore
		""",(trip_id,)
	)
	(last_seen,) = c.fetchone()
	return (bid,did,rid,vid,last_seen)


def get_trip_ids(min_id,max_id):
	"""return a list of all trip ids in the specified range"""
	c = cursor()
	c.execute(
		"""
			SELECT trip_id 
			FROM {trips}
			WHERE trip_id BETWEEN %(min)s AND %(max)s 
			ORDER BY trip_id ASC
		""".format(**conf['db']['tables']),
		{
			'min':min_id,
			'max':max_id
		}
	)
	return [ result for (result,) in c.fetchall() ]


def trip_exists(trip_id):
	"""Check whether a trip exists in the database, 
		returning boolean."""
	c = cursor()
	c.execute(
		"""
			SELECT EXISTS (SELECT * FROM {trips} WHERE trip_id = %s)
		""".format(**conf['db']['tables']),
		{ 'trip_id':trip_id}
	)
	(existence,) = c.fetchone()
	return existence


#def get_vehicles(trip_id):
#	"""returns full projected vehicle linestring and times"""
#	c = cursor()
#	# get the trip geometry and timestamps
#	c.execute("""
#		SELECT
#			uid, lat, lon, report_time,
#			ST_Transform(ST_SetSRID(ST_MakePoint(lon,lat),4326),26917) AS geom
#		FROM nb_vehicles 
#		WHERE trip_id = %s
#		ORDER BY report_time ASC;
#	""",(trip_id,))
#	vehicles = []
#	for (uid,lat,lon,time,geom) in c.fetchall():
#		vehicles.append({
#			'uid':	uid,
#			'geom':	geom,
#			'time':	time,
#			'lat':	lat,
#			'lon':	lon
#		})
#	return vehicles


