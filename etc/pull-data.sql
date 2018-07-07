/*
	This script pulls the data out of the database into CSV text files that 
	should conform to the requirements of the GTFS specification:
	https://developers.google.com/transit/gtfs/reference/
	It uses psql variables to minimize the necessary editing, and so it 
	should be run with psql. Be sure to change the variables just below to 
	match your own configuration.

	Just as a note, this was tested on psql version 9.5
*/

-- set your table name prefix
\set prefix            'ttc_'
-- set your service_id as a row_record, i.e. '(1,2,3)'
\set service_ids       '(17476)'

-- set the table names
\set stops_table       :prefix'stops'
\set directions_table  :prefix'directions'
\set trips_table       :prefix'trips'
\set stop_times_table  :prefix'stop_times'
-- timezone
\set tz                'America/Toronto'
-- where to save the output
\set outdir            '/home/nate/retro-gtfs/output/ttc/'
-- stop configuration past here... just setting output locations from 
-- the above because concatenation is complicated
\set calendar_dates    :outdir'calendar_dates.txt'
\set stops             :outdir'stops.txt'
\set routes            :outdir'routes.txt'
\set trips             :outdir'trips.txt'
\set stop_times        :outdir'stop_times.txt'
\set shapes            :outdir'shapes.txt'


-- set the service_id of trips based on the time of their first stop
-- service_id is the number of days since the local epoch to ensure
-- unique values per day. This query is a bit complicated to speed up the 
-- update by only modifying values that will change.
\echo 'UPDATING service_ids as necessary'
WITH sub AS (
	SELECT 
		t.trip_id, 
		( to_timestamp(st.etime) AT TIME ZONE :'tz' )::date - 'epoch'::date AS service_id
	FROM :trips_table AS t 
	LEFT JOIN :stop_times_table AS st
		ON t.trip_id = st.trip_id AND st.stop_sequence = 1
)
UPDATE :trips_table AS t SET service_id = sub.service_id
FROM sub 
WHERE 
	t.trip_id = sub.trip_id AND 
	-- only changed values
	(t.service_id != sub.service_id OR t.service_id IS NULL);


-- we may need to fudge some stop ID's in case any happen to be repeated 
-- for a trip
\echo 'Fudging some stop_ids as necessary'
WITH sub AS (
	SELECT 
		trip_id,
		stop_sequence,
		stop_uid  || repeat(
			'_'::text,
			(row_number() OVER (PARTITION BY trip_id, stop_uid ORDER BY etime ASC))::int - 1
		) AS fake_id
	FROM :stop_times_table
)
UPDATE :stop_times_table AS st SET fake_stop_id = sub.fake_id
FROM sub 
WHERE 
	st.trip_id = sub.trip_id AND 
	st.stop_sequence = sub.stop_sequence AND
	-- only changed or null values
	( st.fake_stop_id != sub.fake_id OR st.fake_stop_id IS NULL );

-- make calendar_dates.txt
\echo 'Exporting calendar.txt'
COPY(
	SELECT DISTINCT 
		service_id,
		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
		1 AS exception_type
	FROM :trips_table 
	WHERE NOT ignore AND 
	service_id IN :service_ids
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
	FROM :trips_table AS t 
	JOIN :stop_times_table AS st ON
		t.trip_id = st.trip_id
	JOIN :stops_table AS s ON 
		s.uid = st.stop_uid
	WHERE t.service_id IN :service_ids
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
	WHERE service_id IN :service_ids AND NOT ignore
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
	WHERE service_id IN :service_ids AND NOT ignore
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
	WHERE service_id IN :service_ids AND NOT t.ignore 
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
	WHERE service_id IN :service_ids AND NOT ignore ) AS sub
) TO :'shapes' CSV HEADER;

