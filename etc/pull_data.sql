-- calendar dates
COPY(
	SELECT 
		service_id,
		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
		1 AS exception_type
	FROM (SELECT DISTINCT service_id FROM ttc_trips WHERE service_id IS NOT NULL) AS s
) TO '/home/nate/retro-gtfs/output/ttc/calendar_dates.txt' CSV HEADER;

-- stops
COPY (
	SELECT
		stop_id,
		stop_code::varchar,
		stop_name,
		lat AS stop_lat,
		lon AS stop_lon
	FROM ttc_stops
) TO '/home/nate/retro-gtfs/output/ttc/stops.txt' CSV HEADER;

-- routes
COPY (
	SELECT 
		DISTINCT
			route_id,
			route_id::varchar AS route_short_name,
			'' AS route_long_name,
			3 AS route_type -- they are all bus for now
	FROM ttc_directions
) TO '/home/nate/retro-gtfs/output/ttc/routes.txt' CSV HEADER;

-- trips
COPY (
	SELECT
		t.route_id::varchar,
		t.service_id,
		t.trip_id,
		t.direction_id,
		t.block_id
	FROM ttc_trips AS t
	WHERE service_id IS NOT NULL
) TO '/home/nate/retro-gtfs/output/ttc/trips.txt' CSV HEADER;

-- stop_times
-- TODO are there stop times in the output with their trip_ids not in the trips table
COPY (
	SELECT 
		st.trip_id,
		arrival_time,
		arrival_time AS departure_time,
		stop_id,
		stop_sequence
	FROM ttc_stop_times AS st JOIN ttc_trips AS t ON st.trip_id = t.trip_id
	WHERE 
	    arrival_time IS NOT NULL AND
	    t.service_id IS NOT NULL -- prevents incomplete trips from being used
	ORDER BY trip_id,stop_sequence ASC
) TO '/home/nate/retro-gtfs/output/ttc/stop_times.txt' CSV HEADER;

-- shapes
COPY (
	SELECT 
		shape_id,
		path[1] AS shape_pt_sequence,
		ST_X(ST_Transform(geom,4326))::double precision AS shape_pt_lon,
		ST_Y(ST_Transform(geom,4326))::double precision AS shape_pt_lat
	FROM ( SELECT
		'shp_'||trip_id AS shape_id,
		(ST_DumpPoints(ST_Simplify(match_geom,10))).*
	FROM ttc_trips
	WHERE service_id IS NOT NULL) AS sub
) TO '/home/nate/retro-gtfs/output/ttc/shapes.txt' CSV HEADER;