-- calendar dates
COPY(
	SELECT 
		service_id,
		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
		1 AS exception_type
	FROM (SELECT DISTINCT service_id FROM muni_trips WHERE service_id IS NOT NULL AND NOT ignore) AS s
	ORDER BY service_id ASC
) TO '/home/nate/retro-gtfs/output/muni/calendar_dates.txt' CSV HEADER;

-- stops
COPY (
	SELECT
		stop_id,
		stop_code::varchar,
		stop_name,
		lat AS stop_lat,
		lon AS stop_lon
	FROM muni_stops 
	WHERE stop_id IN (SELECT DISTINCT stop_id FROM muni_stop_times)
) TO '/home/nate/retro-gtfs/output/muni/stops.txt' CSV HEADER;

-- routes
COPY (
	SELECT 
		DISTINCT
			route_id,
			1 AS agency_id, -- all the same agency 
			route_id::varchar AS route_short_name,
			'' AS route_long_name,
			3 AS route_type -- they are all bus for now
	FROM muni_trips
) TO '/home/nate/retro-gtfs/output/muni/routes.txt' CSV HEADER;

-- trips
COPY (
	SELECT
		t.route_id::varchar,
		t.service_id,
		t.trip_id,
		t.block_id,
		'shp_'||trip_id AS shape_id
	FROM muni_trips AS t
	WHERE NOT ignore AND service_id IS NOT NULL
) TO '/home/nate/retro-gtfs/output/muni/trips.txt' CSV HEADER;

-- stop_times
COPY (
	SELECT 
		t.trip_id,
		arrival_time,
		-- time formatting nightmare
		-- TODO note the timezones in the time calculations
		(
			to_char( (etime-7*3600-service_id*86400)::int / 3600, 'fm00' ) ||':'||
			to_char( (etime-7*3600-service_id*86400)::int % 3600 / 60, 'fm00' ) ||':'||
			to_char( (etime-7*3600-service_id*86400)::int % 60, 'fm00' )
		) AS arrival_time,
		(
			to_char( (etime-7*3600-service_id*86400)::int / 3600, 'fm00' ) ||':'||
			to_char( (etime-7*3600-service_id*86400)::int % 3600 / 60, 'fm00' ) ||':'||
			to_char( (etime-7*3600-service_id*86400)::int % 60, 'fm00' )
		) AS departure_time,
		stop_id,
		stop_sequence
	FROM muni_stop_times AS st JOIN muni_trips AS t ON st.trip_id = t.trip_id
	WHERE arrival_time IS NOT NULL AND t.trip_id = 130769
	ORDER BY trip_id, stop_sequence ASC
	
) TO '/home/nate/retro-gtfs/output/muni/stop_times.txt' CSV HEADER;

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
	FROM muni_trips
	WHERE NOT ignore AND service_id IS NOT NULL) AS sub
) TO '/home/nate/retro-gtfs/output/muni/shapes.txt' CSV HEADER;