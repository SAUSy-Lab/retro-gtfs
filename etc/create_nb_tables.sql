/*
create tables necessary for NextBus driven realtime GTFS project
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
CREATE INDEX nbs_idx ON nb_stops (stop_id);
CLUSTER nb_stops USING nbs_idx;

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
CREATE INDEX nbd_idx ON nb_directions (direction_id);
CLUSTER nb_directions USING nbd_idx;

DROP TABLE IF EXISTS nb_vehicles;
CREATE TABLE nb_vehicles (
	uid serial PRIMARY KEY, -- bigserial if more than ~2B records needed
	trip_id integer,
	report_time double precision, -- epoch time of report
	lat numeric,
	lon numeric,
	ignore boolean DEFAULT FALSE -- ignore this vehicle during processing?
);
CREATE INDEX nbv_idx ON nb_vehicles (trip_id);
CLUSTER nb_vehicles USING nbv_idx;

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
	orig_geom  geometry(LINESTRING,26917),	-- geometry of all points TODO kill
	clean_geom geometry(LINESTRING,26917), -- geometry of points used in map matching TODO kill
	problem varchar DEFAULT '',	-- description of any problems that arise
	ignore boolean DEFAULT FALSE	-- ignore this vehicle during processing?
);
CREATE INDEX nbt_idx ON nb_trips (trip_id);
CLUSTER nb_trips USING nbt_idx;

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
CREATE INDEX nbst_idx ON nb_stop_times (trip_id);
CLUSTER nb_stop_times USING nbst_idx;

