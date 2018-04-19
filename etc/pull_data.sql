/*
	This script pulls the data out of the database into CSV text files that 
	should conform to the requirements of the GTFS specification:
	https://developers.google.com/transit/gtfs/reference/
	It uses psql variables to minimize the necessary editing, and so it 
	shuld be run with psql. Be sure to change the variables just below to 
	match your own configuration.

	Just as a note, this was tested on psql version 9.5
*/

-- set your table names
\set stops_table       jv_stops
\set directions_table  jv_directions
\set trips_table       jv_trips
\set stop_times_table  jv_stop_times
-- timezone offset
\set local_tz          'America/Toronto'
\set tzoffset          -4
-- where to save the output
\set outdir            '/home/nate/retro-gtfs/output/jv/'
-- stop configuration past here... just setting output locations from 
-- the above because concatenation is complicated
\set filename          'calendar_dates.txt'
\set calendar_dates    :outdir:filename
\set filename          'stops.txt'
\set stops             :outdir:filename
\set filename          'routes.txt'
\set routes            :outdir:filename
\set filename          'trips.txt'
\set trips             :outdir:filename
\set filename          'stop_times.txt'
\set stop_times        :outdir:filename
\set filename          'shapes.txt'
\set shapes            :outdir:filename

-- make calendar_dates.txt
COPY(
	SELECT
		service_id,
		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
		1 AS exception_type
	FROM (SELECT DISTINCT service_id FROM :trips_table WHERE NOT ignore) AS s
	ORDER BY service_id ASC
) TO :'calendar_dates' CSV HEADER;


-- we may need to fudge some stop ID's in case any happen to be repeated 
-- for a trip
WITH sub AS (
	SELECT 
		trip_id,
		stop_sequence,
		stop_uid  || repeat(
			'_'::text,
			(row_number() OVER (PARTITION BY trip_id, stop_uid ORDER BY etime ASC))::int - 1
		) AS fake_id
	FROM :stop_times_table
	ORDER BY trip_id,stop_sequence ASC
)
UPDATE :stop_times_table AS st SET fake_stop_id = fake_id
FROM sub 
WHERE st.trip_id = sub.trip_id AND st.stop_sequence = sub.stop_sequence;


-- make stops.txt
COPY (
	SELECT
		DISTINCT
		st.fake_stop_id AS stop_id,
		s.stop_code::varchar,
		s.stop_name,
		s.lat AS stop_lat,
		s.lon AS stop_lon
	FROM :stop_times_table AS st JOIN :stops_table AS s 
		ON s.uid = st.stop_uid
) TO :'stops' CSV HEADER;


-- make routes.txt
COPY (
	SELECT 
		DISTINCT
			route_id,
			1 AS agency_id, -- all the same agency 
			route_id::varchar AS route_short_name,
			'' AS route_long_name,
			3 AS route_type -- LET THEM RIDE BUSES
	FROM :trips_table
	WHERE NOT ignore
) TO :'routes' CSV HEADER;


-- make trips.txt
COPY (
	SELECT
		t.route_id::varchar,
		t.service_id,
		t.trip_id,
		t.block_id,
		'shp_'||trip_id AS shape_id
	FROM :trips_table AS t
	WHERE NOT ignore
) TO :'trips' CSV HEADER;


-- stop_times
COPY (
	SELECT 
		t.trip_id,
		-- TODO note the timezones in the time calculations
		(to_timestamp(round(etime)) at time zone :'local_tz')::time AS arrival_time,
		(to_timestamp(round(etime)) at time zone :'local_tz')::time AS departure_time,
		stop_sequence,
		fake_stop_id AS stop_id
	FROM :stop_times_table AS st JOIN :trips_table AS t ON st.trip_id = t.trip_id
	WHERE NOT t.ignore -- not actually necessary
	ORDER BY trip_id, stop_sequence ASC
) TO :'stop_times' CSV HEADER;


-- make shapes.txt
-- this simply fills in the gaps in multilines
COPY (
	SELECT 
		shape_id,
		-- path is an array of [line number, point number]
		row_number() OVER (PARTITION BY shape_id ORDER BY path ASC) AS shape_pt_sequence,
		ST_X(ST_Transform(geom,4326))::real AS shape_pt_lon,
		ST_Y(ST_Transform(geom,4326))::real AS shape_pt_lat
	FROM ( SELECT
		'shp_'||trip_id AS shape_id,
		(ST_DumpPoints(ST_Simplify(match_geom,10))).*
	FROM :trips_table
	WHERE NOT ignore) AS sub
) TO :'shapes' CSV HEADER;
