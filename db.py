# functions involving BD interaction
import psycopg2, json, math
from conf import conf
from shapely.wkb import loads as loadWKB
from minor_objects import Stop, Vehicle

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

def get_trip_attributes(trip_id):
	"""Return the attributes of a stored trip necessary 
		for the construction of a new trip object.
		This now includes the vehicle report times and positions."""
	c = cursor()
	c.execute(
		"""
			SELECT
				block_id,
				direction_id,
				route_id,
				vehicle_id,
				(ST_DumpPoints(ST_Transform(orig_geom,4326))).geom,
				unnest(times)
			FROM {trips}
			WHERE trip_id = %(trip_id)s
		""".format(**conf['db']['tables']),
		{ 'trip_id':trip_id }
	)
	vehicle_records = []
	for (bid, did, rid, vid, WGS84geom, epoch_time ) in c:
		# only consider the last three variables, as the rest are 
		# the same for every record
		WGS84geom = loadWKB(WGS84geom,hex=True)
		# Vehicle( epoch_time, longitude, latitude)
		vehicle_records.append( Vehicle( epoch_time, WGS84geom.x, WGS84geom.y ) )
	result = {
		'block_id': bid,
		'direction_id': did,
		'route_id': rid,
		'vehicle_id': vid,
		'points': vehicle_records
	}
	return result


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
	"""clear the tables of any processing results
		but NOT of original data from the API"""
	c = cursor()
	c.execute(
		"""
			TRUNCATE {stop_times};
			UPDATE {trips} SET 
				service_id = NULL,
				match_confidence = NULL,
				ignore = TRUE,
				clean_geom = NULL,
				problem = '',
				match_geom = NULL;
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


def add_trip_match(trip_id,confidence,wkb_geometry_match):
	"""update the trip record with it's matched geometry"""
	c = cursor()
	# store the given values
	c.execute(
		"""
			UPDATE {trips}
			SET  
				match_confidence = %(confidence)s,
				match_geom = ST_SetSRID(%(match)s::geometry,%(localEPSG)s)
			WHERE trip_id  = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{
			'localEPSG':conf['localEPSG'],
			'confidence':confidence, 
			'match':wkb_geometry_match, 
			'trip_id':trip_id
		}
	)


def insert_trip(trip_id,block_id,route_id,direction_id,vehicle_id,times,orig_geom):
	"""Store the basics of the trip in the database."""
	c = cursor()
	# store the given values
	c.execute(
		"""
			INSERT INTO {trips} 
				( 
					trip_id, 
					block_id, 
					route_id, 
					direction_id, 
					vehicle_id, 
					times,
					orig_geom
			) 
			VALUES 
				( 
					%(trip_id)s,
					%(block_id)s,
					%(route_id)s,
					%(direction_id)s,
					%(vehicle_id)s, 
					%(times)s,
					ST_SetSRID( %(orig_geom)s::geometry, %(localEPSG)s )
				);
		""".format(**conf['db']['tables']),
		{
			'trip_id':trip_id, 
			'block_id':block_id, 
			'route_id':route_id, 
			'direction_id':direction_id, 
			'vehicle_id':vehicle_id,
			'times':times,
			'orig_geom':orig_geom,
			'localEPSG':conf['localEPSG']
		}
	)


def get_direction_uid(direction_id,trip_time):
	"""Find the correct direction entry based on the direction_id and the time
		of the trip. Trip_time is an epoch value, direction_id is a string."""
	c = cursor()
	c.execute(
		"""
			SELECT uid 
			FROM {directions}
			WHERE 
				direction_id = %(direction_id)s AND 
				report_time <= %(trip_time)s
			ORDER BY report_time DESC
			LIMIT 1
		""".format(**conf['db']['tables']),
		{ 'direction_id':direction_id, 'trip_time':trip_time }
	)
	uid, = c.fetchone()
	return uid


def get_stops(direction_id, trip_time):
	"""Get an ordered list of Stop objects from the schedule data."""
	c = cursor()
	# get the uid of the relevant direction entry
	direction_uid = get_direction_uid(direction_id,trip_time)
	if not direction_uid: return None
	c.execute(	
		"""
			SELECT uid, the_geom FROM (
				SELECT 
					DISTINCT ON (a.stop) a.stop AS stop_id,
					s.uid,
					a.seq,
					s.the_geom
				FROM {directions} AS d, unnest(d.stops) WITH ORDINALITY a(stop, seq)
				JOIN {stops} AS s ON s.stop_id = a.stop
				WHERE d.uid = %(direction_uid)s AND s.report_time <= %(trip_time)s
				-- get uniques stops with the earliest report time and order by sequence
				ORDER BY a.stop, s.report_time
			) AS whatever ORDER BY seq
		""".format(**conf['db']['tables']),
		{ 'direction_uid':direction_uid, 'trip_time':trip_time }
	)
	# return a schedule-ordered list of stop objects
	return [ Stop( stop_uid, geom ) for stop_uid, geom in c.fetchall() ]


def get_route_geom(direction_id, trip_time):
	"""Get the geometry of a direction or return None. This is meant to be a 
		backup in case map-matching is going badly. Direction geometries must be 
		supplied manually. If all goes well this returns a shapely geometry in
		the local projection. Else, None."""
	c = cursor()
	# get the uid of the relevant direction entry
	uid = get_direction_uid(direction_id,trip_time)
	if not uid: return None
	# now find the geometry
	c.execute(
		"""
			SELECT 
				route_geom
			FROM {directions} 
			WHERE uid = %(uid)s;
		""".format(**conf['db']['tables']),
		{ 'uid':uid }
	)
	geom, = c.fetchone()
	if geom: return loadWKB(geom,hex=True)
	else: return None


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

def get_trip_problem(trip_id):
	"""What problem was associated with the processing of this trip?"""
	c = cursor()
	c.execute(
		"""
			SELECT problem FROM {trips} WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{ 'trip_id':trip_id }
	)
	problem, = c.fetchone()
	return problem if problem != '' else None


def store_timepoints(trip_id,timepoints):
	"""store the estimated stop times for a trip"""
	assert len(timepoints) > 1
	c = cursor()
	# be sure the timepoints are in ascending temporal order
	timepoints = sorted(timepoints,key=lambda tp: tp.arrival_time) 
	# insert the stops
	records = []
	seq = 1
	for timepoint in timepoints:
		# list of tuples
		records.append( (trip_id,timepoint.stop_id,timepoint.arrival_time,seq) )
		seq += 1
	args_str = ','.join( [ "({},{},{},{})".format(*x) for x in records ] )
	c.execute("INSERT INTO {stop_times} (trip_id, stop_uid, etime, stop_sequence) VALUES ".format(**conf['db']['tables']) + args_str)


def get_timepoints(trip_id):
	"""Essentially, this should be the inverse of the above function."""
	c = cursor()
	c.execute("""
		SELECT stop_id, etime, stop_sequence
		FROM {stop_times}
		WHERE trip_id = %(trip_id)s
		ORDER BY stop_sequence
	""".format(**conf['db']['tables']),
	{ 'trip_id':trip_id })
	return c.fetchall()


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
			INSERT INTO {stops} ( 
				stop_id, stop_name, stop_code, 
				the_geom, 
				lon, lat, 
				report_time 
			) 
			VALUES ( 
				%(stop_id)s, %(stop_name)s, %(stop_code)s, 
				ST_Transform( ST_SetSRID( ST_MakePoint(%(lon)s, %(lat)s),4326),%(localEPSG)s ),
				%(lon)s, %(lat)s, 
				EXTRACT(EPOCH FROM NOW())
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
					%s, EXTRACT(EPOCH FROM NOW())
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
			UPDATE {trips} SET 
				match_confidence = NULL,
				match_geom = NULL,
				clean_geom = NULL,
				problem = '',
				ignore = FALSE,
				service_id = NULL
			WHERE trip_id = %(trip_id)s;

			DELETE FROM {stop_times} 
			WHERE trip_id = %(trip_id)s;
		""".format(**conf['db']['tables']),
		{ 'trip_id':trip_id }
	)


def get_trip_ids_by_range(min_id,max_id):
	"""return a list of all trip ids in the specified range"""
	c = cursor()
	c.execute(
		"""
			SELECT trip_id 
			FROM {trips}
			WHERE trip_id BETWEEN %(min)s AND %(max)s 
			ORDER BY trip_id ASC;
		""".format(**conf['db']['tables']),
		{
			'min':min_id,
			'max':max_id
		}
	)
	return [ result for (result,) in c.fetchall() ]


def get_trip_ids_by_route(route_id):
	"""return a list of all trip ids operating a given route"""
	c = cursor()
	c.execute(
		"""
			SELECT trip_id 
			FROM {trips}
			WHERE route_id = %(route_id)s 
			ORDER BY trip_id ASC;
		""".format(**conf['db']['tables']),
		{
			'route_id':route_id
		}
	)
	return [ result for (result,) in c.fetchall() ]


def get_trip_ids_unfinished():
	""""""
	c = cursor()
	c.execute(
		"""
			SELECT trip_id 
			FROM {trips} 
			WHERE problem = '' AND ignore
			ORDER BY trip_id ASC;
		""".format(**conf['db']['tables'])
	)
	return [ result for (result,) in c.fetchall() ]


def trip_exists(trip_id):
	"""Check whether a trip exists in the database, 
		returning boolean."""
	c = cursor()
	c.execute(
		"""
			SELECT EXISTS (SELECT * FROM {trips} WHERE trip_id = %(trip_id)s)
		""".format(**conf['db']['tables']),
		{ 'trip_id':trip_id }
	)
	(existence,) = c.fetchone()
	return existence

