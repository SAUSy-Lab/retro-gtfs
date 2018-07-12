import sys
sys.path.append("..") # Adds higher directory to python modules path.
from db import *
import conf

def TableExists(TableName, create = True):
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
    
def init_DB(reset = True):
    PROJECT_EPSG = conf.PROJECT_EPSG
    if reset:
        for key, TableName in conf.conf['db']['tables'].items():
            if TableExists(TableName): DropTable(TableName)
    # Create Stops table:
    c = cursor()
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
    # Create stop_times table:
    print('Create stop_times table')
    c.execute(
            """
            CREATE TABLE {stop_times} (
            	trip_id integer,
            	stop_uid integer,
            	stop_sequence integer,
            	etime double precision, -- non-localized epoch time in seconds
            	fake_stop_id varchar -- allows for repeated visits of the same stop
            );
            CREATE INDEX ON {stop_times} (trip_id);
            """.format(stop_times = conf.conf['db']['tables']['stop_times'])
            )
            
    