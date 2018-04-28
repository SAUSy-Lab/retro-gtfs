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
\set stops_table       ttc_stops
\set directions_table  ttc_directions
\set trips_table       ttc_trips
\set stop_times_table  ttc_stop_times
-- timezone
\set tz                'America/Toronto'
-- where to save the output
\set outdir            '/home/nate/retro-gtfs/output/scarbs/'
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


-- set the service_id of trips based on the time of their first stop
-- service_id is the number of days since the local epoch to ensure
-- unique values per day. Reset first. 
\echo 'UPDATING service_ids'
UPDATE :trips_table SET service_id = NULL WHERE service_id IS NOT NULL;

UPDATE :trips_table  AS t SET service_id = 
	( to_timestamp(st.etime) AT TIME ZONE :'tz' )::date - '1970-01-01'::date
FROM :stop_times_table AS st 
WHERE t.trip_id = st.trip_id AND st.stop_sequence = 1;


-- we may need to fudge some stop ID's in case any happen to be repeated 
-- for a trip
\echo 'Fudging some stop_ids'
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


-- make calendar_dates.txt
\echo 'Exporting calendar.txt'
COPY(
	SELECT DISTINCT 
		service_id,
		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
		1 AS exception_type
	FROM :trips_table 
	WHERE NOT ignore
	ORDER BY service_id ASC
) TO :'calendar_dates' CSV HEADER;


-- make stops.txt
\echo 'Exporting stops.txt'
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


\echo 'Exporting routes.txt'
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


\echo 'Exporting trips.txt'
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


\echo 'Exporting stop_times.txt'
COPY (
	SELECT 
		t.trip_id,		
		-- this elaborate formatting is necessary to allow times to be based on 
		-- the service day, meaning that they can extend beyond midnight
		-- the service_id is essentially the local Nth day since the epoch		
		EXTRACT( EPOCH FROM 
			-- local time of stop minus local service date
			to_timestamp(round(st.etime)) AT TIME ZONE :'tz' -
			('1970-01-01'::date + t.service_id * INTERVAL '1 day')::date
		) * INTERVAL '1 second' AS arrival_time,
		EXTRACT( EPOCH FROM 
			-- local time of stop minus local service date
			to_timestamp(round(st.etime)) AT TIME ZONE :'tz' -
			('1970-01-01'::date + t.service_id * INTERVAL '1 day')::date
		) * INTERVAL '1 second' AS departure_time,
		stop_sequence,
		fake_stop_id AS stop_id
	FROM :stop_times_table AS st JOIN :trips_table AS t ON st.trip_id = t.trip_id
	WHERE NOT t.ignore -- not actually necessary
	ORDER BY trip_id, stop_sequence ASC
) TO :'stop_times' CSV HEADER;


\echo 'Exporting shapes.txt'
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

