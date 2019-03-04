import sys
sys.path.append("..") # Adds higher directory to python modules path.
from db import *
import conf

def TableExists(TableName):
    """Check if table exists"""
    c = cursor()
    c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %(TableName)s;
            """,
            {'TableName': TableName}
            )
    if c.rowcount == 1: return True
    else: return False

def DropTable(TableName):
    """drop a table from database"""
    c = cursor()
    c.execute(
            """
            DROP TABLE {TableName};
            """.format(TableName = TableName)
    )
    
def init_DB(reset_all = True):
    c = cursor()
    # Always reset trips:
    DropTable(conf.conf['db']['tables']['trips'])
    # Create trips table:
    print('Create trips table')
    c.execute(
            """
            CREATE TABLE {trips} (
            	trip_id varchar PRIMARY KEY,
            	orig_geom geometry( LINESTRING, {EPSG}),	
            	times double precision[],
            	route_id varchar,
            	direction_id varchar,
            	service_id smallint,
            	vehicle_id varchar,
            	block_id integer,
            	match_confidence real,
            	ignore boolean DEFAULT TRUE,
            	match_geom geometry( MULTILINESTRING, {EPSG} ),
            	clean_geom geometry( LINESTRING, {EPSG} ),
            	problem varchar DEFAULT ''
            );
            CREATE INDEX ON {trips} (trip_id);
            """.format(trips = conf.conf['db']['tables']['trips'], EPSG = conf.PROJECT_EPSG)
            )    
    if reset_all:
        # reset tables
        for key, TableName in conf.conf['db']['tables'].items():
            if TableExists(TableName) and TableName != conf.conf['db']['tables']['trips']:                 
                DropTable(TableName)
        # Then create new tables
        # Create Stops table:
        print('Create stops table')
        c.execute(
                """
                CREATE TABLE {stops} (
                	uid serial PRIMARY KEY,
                	stop_id varchar,
                	stop_name varchar, -- required
                	stop_code integer, -- public_id
                	lon numeric,
                	lat numeric,
                	the_geom geometry( POINT, {EPSG} ),
                	report_time double precision -- epoch time
                    );
                CREATE INDEX ON {stops} (stop_id);
                """.format(stops = conf.conf['db']['tables']['stops'], EPSG = conf.PROJECT_EPSG)
                )
        # Create directions table:
        print('Create directions table')
        c.execute(
                """
                CREATE TABLE {directions} (
                	uid serial PRIMARY KEY,
                trip_id varchar,
                	route_id varchar,
                	direction_id varchar,
                	title varchar,
                	name varchar,
                	branch varchar,
                	useforui boolean,
                	stops text[],
                	report_time double precision, -- epoch time
                	route_geom geometry( LINESTRING, {EPSG}) -- optional default route geometry
                );
                CREATE INDEX ON {directions} (direction_id);
                """.format(directions = conf.conf['db']['tables']['directions'], EPSG = conf.PROJECT_EPSG)
                )

        # Create stop_times table:
        print('Create stop_times table')
        c.execute(
                """
                CREATE TABLE {stop_times} (
                	trip_id varchar,
                	stop_uid integer,
                	stop_sequence integer,
                	etime double precision, -- non-localized epoch time in seconds
                	stop_id varchar
                );
                CREATE INDEX ON {stop_times} (trip_id);
                """.format(stop_times = conf.conf['db']['tables']['stop_times'])
                )
        print('Create true_stop_times table')
        c.execute(
                """
                CREATE TABLE {true_stop_times} (
                	trip_id varchar,
                	stop_id varchar,
                	stop_sequence integer,
                    arrival_time varchar,
                    departure_time varchar
                	
                );
                """.format(true_stop_times = conf.conf['db']['tables']['true_stop_times'])
                )
            
def Update_stop_id():
    """
    update all stop_id from stop_times table by looking up stops table
    """
    c = cursor()
    c.execute("""
              UPDATE {stop_times}
              SET stop_id = {stops}.stop_id
              FROM {stops}
              WHERE {stop_times}.stop_uid = {stops}.uid
              """.format(stop_times = conf.conf['db']['tables']['stop_times'],
                         stops = conf.conf['db']['tables']['stops'])              
              )