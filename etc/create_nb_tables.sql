/*
create tables necessary for NextBus driven realtime GTFS project
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

/*
DROP TABLE IF EXISTS nb_vehicles;
CREATE TABLE nb_vehicles (
	uid serial PRIMARY KEY, -- bigserial if more than ~2B records needed
	seq smallint,
	trip_id integer,
	report_time double precision, -- epoch time of report
	lat numeric,
	lon numeric,
	ignore boolean DEFAULT FALSE -- ignore this vehicle during processing?
);
CREATE INDEX nbv_idx ON nb_vehicles (trip_id);
CLUSTER nb_vehicles USING nbv_idx;
*/

DROP TABLE IF EXISTS nb_trips;
CREATE TABLE nb_trips (
	trip_id integer PRIMARY KEY,
	orig_geom geometry(LINESTRING,26917),	-- geometry of all points
	times double precision[], -- sequential report_times, corresponding to points on orig_geom
	route_id integer,
	direction_id varchar,
	service_id smallint,
	vehicle_id varchar,
	block_id integer,
	match_confidence real,
	ignore boolean DEFAULT FALSE,	-- ignore this trip during processing?
	-- debugging fields
	match_geom geometry(LINESTRING,26917), -- map-matched route geometry
	clean_geom geometry(LINESTRING,26917), -- geometry of points used in map matching
	problem varchar DEFAULT ''	-- description of any problems that arise
);
CREATE INDEX nbt_idx ON nb_trips (trip_id);
CLUSTER nb_trips USING nbt_idx;

DROP TABLE IF EXISTS nb_stop_times;
CREATE TABLE nb_stop_times(
	trip_id integer,
	stop_id varchar,
	stop_sequence integer,
	etime double precision, -- epoch time at greenwich
	arrival_time interval HOUR TO SECOND
);
CREATE INDEX nbst_idx ON nb_stop_times (trip_id);
CLUSTER nb_stop_times USING nbst_idx;

