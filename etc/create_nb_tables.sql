/*
create tables necessary for NextBus drivn realtime GTFS project
*/

/*
DROP TABLE IF EXISTS nb_routes;
CREATE TABLE nb_routes (
	route_id varchar PRIMARY KEY,
	route_short_name varchar, -- required
	route_long_name varchar, -- required
	route_type integer, -- required
	title varchar -- not required
);
*/

DROP TABLE IF EXISTS nb_stops;
CREATE TABLE nb_stops (
	uid serial PRIMARY KEY,
	stop_id varchar,
	stop_name varchar, -- required
	stop_code integer, -- public_id
	lon numeric,
	lat numeric,
	the_geom geometry(POINT,26917),
	report_time timestamp with time zone
);
CREATE INDEX ON nb_stops (stop_id);

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
	report_time timestamp with time zone
);
CREATE INDEX ON nb_directions (direction_id);

DROP TABLE IF EXISTS nb_vehicles;
CREATE TABLE nb_vehicles (
	trip_id integer,
	seq integer, -- sequence in the trip reports
	report_time double precision, -- epoch time of report
	lat numeric,
	lon numeric,
	location geometry(Point,26917),
	ignore boolean DEFAULT FALSE -- ignore this vehicle during processing?
);
CREATE INDEX ON nb_vehicles (trip_id);

DROP TABLE IF EXISTS nb_trips;
CREATE TABLE nb_trips (
	trip_id integer PRIMARY KEY,
	route_id integer,
	direction_id varchar(35),
	service_id integer,
	vehicle_id integer,
	block_id integer,
	match_confidence real,
	match_geom geometry(LINESTRING,26917), -- map-matched route geometry
	orig_geom  geometry(LINESTRING,26917),	-- geometry of points used in map matching
	problem varchar DEFAULT NULL,	-- description of any problems that arise
	ignore boolean DEFAULT FALSE	-- ignore this vehicle during processing?
);

DROP TABLE IF EXISTS nb_stop_times;
CREATE TABLE nb_stop_times(
	uid serial PRIMARY KEY,
	trip_id integer,
	stop_id varchar,
	stop_sequence integer,
	etime double precision, -- epoch time at greenwich
	arrival_time interval HOUR TO SECOND,
	departure_time interval HOUR TO SECOND
);

