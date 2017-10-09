﻿/*
	This defines the schema necessary for NextBus driven realtime GTFS project, 
	in the devlopment case, for the Toronto Transit Commission. 
	Table names may be changed, but this must be indicated in conf.py.
*/


/*
	equivalent to GTFS stops table
*/
DROP TABLE IF EXISTS nb_stops;
CREATE TABLE nb_stops (
	uid serial PRIMARY KEY,
	stop_id varchar,
	stop_name varchar, -- required
	stop_code integer, -- public_id
	lon numeric,
	lat numeric,
	the_geom geometry(POINT,32610),
	report_time double precision, -- epoch time
	active boolean DEFAULT TRUE -- debugging flag
);
CREATE INDEX ON nb_stops (stop_id);

/*
	Similar to GTFS trips table, in that it stores sequences of 
	stops to be served by a trip and these can be matched to a 
	direction_id on a particular vehicle
*/
DROP TABLE IF EXISTS nb_directions;
CREATE TABLE nb_directions (
	uid serial PRIMARY KEY,
	route_id varchar,
	direction_id varchar,
	title varchar,
	name varchar,
	branch varchar,
	useforui boolean,
	stops text[],
	report_time double precision -- epoch time
);
CREATE INDEX ON nb_directions (direction_id);

/*
	Data on vehilce locations fetched from the API gets stored here along 
	with map-matched geometries. When extracted into GTFS, most feilds here 
	are ignored. "Trips" are the primary object of the data processing sequence.  
*/
DROP TABLE IF EXISTS nb_trips;
CREATE TABLE nb_trips (
	trip_id integer PRIMARY KEY,
	orig_geom geometry(LINESTRING,32610),	-- geometry of all points
	times double precision[], -- sequential report_times, corresponding to points on orig_geom
	route_id varchar,
	direction_id varchar,
	service_id smallint,
	vehicle_id varchar,
	block_id integer,
	match_confidence real,
	ignore boolean DEFAULT FALSE,	-- ignore this trip during processing?
	-- debugging fields
	match_geom geometry(LINESTRING,32610), -- map-matched route geometry
	clean_geom geometry(LINESTRING,32610), -- geometry of points used in map matching
	problem varchar DEFAULT '', -- description of any problems that arise
	active boolean DEFAULT TRUE -- debugging flag
);
CREATE INDEX ON nb_trips (trip_id);

/*
	Where interpolated stop times are stored for each trip. 
*/
DROP TABLE IF EXISTS nb_stop_times;
CREATE TABLE nb_stop_times(
	trip_id integer,
	stop_id varchar,
	stop_sequence integer,
	etime double precision, -- epoch time at greenwich
	arrival_time interval HOUR TO SECOND
);
CREATE INDEX ON nb_stop_times (trip_id);