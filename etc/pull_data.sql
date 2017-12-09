-- calendar dates
COPY(
	SELECT 
		service_id,
		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
		1 AS exception_type
	FROM (SELECT DISTINCT service_id FROM ttc_trips WHERE NOT ignore) AS s
	ORDER BY service_id ASC
) TO '/home/nate/retro-gtfs/output/ttc/calendar_dates.txt' CSV HEADER;

/*
-- stops
COPY (
	SELECT
		stop_id,
		stop_code::varchar,
		stop_name,
		lat AS stop_lat,
		lon AS stop_lon
	FROM ttc_stops 
	WHERE stop_id IN (SELECT DISTINCT stop_id FROM ttc_stop_times WHERE trip_id < 10000)
) TO '/home/nate/retro-gtfs/output/ttc/stops.txt' CSV HEADER;
*/
-- TODO testing fake stop_ids
COPY (
	SELECT
		fake_stop_id AS stop_id,
		stop_code::varchar,
		stop_name,
		lat AS stop_lat,
		lon AS stop_lon
	FROM 
		(SELECT DISTINCT fake_stop_id FROM ttc_stop_times) AS f JOIN
		ttc_stops AS s
		ON btrim(f.fake_stop_id,'_') = s.stop_id
) TO '/home/nate/retro-gtfs/output/ttc/stops.txt' CSV HEADER;

-- routes
COPY (
	SELECT 
		DISTINCT
			route_id,
			1 AS agency_id, -- all the same agency 
			route_id::varchar AS route_short_name,
			'' AS route_long_name,
			3 AS route_type -- they are all bus for now
	FROM ttc_trips
	WHERE NOT ignore
) TO '/home/nate/retro-gtfs/output/ttc/routes.txt' CSV HEADER;

-- trips
COPY (
	SELECT
		t.route_id::varchar,
		t.service_id,
		t.trip_id,
		t.block_id,
		'shp_'||trip_id AS shape_id
	FROM ttc_trips AS t
	WHERE NOT ignore
) TO '/home/nate/retro-gtfs/output/ttc/trips.txt' CSV HEADER;

-- stop_times
COPY (
	SELECT 
		t.trip_id,
		-- time formatting nightmare
		-- TODO note the timezones in the time calculations
		(
			to_char( (etime-4*3600-service_id*86400)::int / 3600, 'fm00' ) ||':'||
			to_char( (etime-4*3600-service_id*86400)::int % 3600 / 60, 'fm00' ) ||':'||
			to_char( (etime-4*3600-service_id*86400)::int % 60, 'fm00' )
		) AS arrival_time,
		(
			to_char( (etime-4*3600-service_id*86400)::int / 3600, 'fm00' ) ||':'||
			to_char( (etime-4*3600-service_id*86400)::int % 3600 / 60, 'fm00' ) ||':'||
			to_char( (etime-4*3600-service_id*86400)::int % 60, 'fm00' )
		) AS departure_time,
		-- TODO testing
		fake_stop_id AS stop_id,
		stop_sequence
	FROM ttc_stop_times AS st JOIN ttc_trips AS t ON st.trip_id = t.trip_id
	WHERE NOT t.ignore -- not actually necessary
	ORDER BY trip_id, stop_sequence ASC
	
) TO '/home/nate/retro-gtfs/output/ttc/stop_times.txt' CSV HEADER;

-- shapes
-- this simply fills in the gaps in multilines
COPY (
	SELECT 
		shape_id,
		-- path is an array of [line number, point number]
		row_number() OVER (PARTITION BY shape_id ORDER BY path ASC) AS shape_pt_sequence,
		ST_X(ST_Transform(geom,4326))::double precision AS shape_pt_lon,
		ST_Y(ST_Transform(geom,4326))::double precision AS shape_pt_lat
	FROM ( SELECT
		'shp_'||trip_id AS shape_id,
		(ST_DumpPoints(ST_Simplify(match_geom,10))).*
	FROM ttc_trips
	WHERE NOT ignore) AS sub
) TO '/home/nate/retro-gtfs/output/ttc/shapes.txt' CSV HEADER;