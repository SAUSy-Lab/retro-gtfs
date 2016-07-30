-- stops
COPY (
	SELECT
		stop_id,
		stop_code::varchar,
		stop_name,
		lat AS stop_lat,
		lon AS stop_lon
	FROM nb_stops
	UNION
	SELECT *
	FROM gtfs_ttc_stops
) TO '/home/ubuntu/nb/output/stops.txt' CSV HEADER;

-- routes
COPY (
	SELECT 
		DISTINCT
			route_id,
			route_id::varchar AS route_short_name,
			'' AS route_long_name,
			3 AS route_type -- they are all bus for now
	FROM nb_directions
	UNION
	SELECT * FROM gtfs_ttc_routes
) TO '/home/ubuntu/nb/output/routes.txt' CSV HEADER;

-- trips
COPY (
	SELECT
		t.route_id::varchar,
		t.service_id,
		t.trip_id,
		t.direction_id
	FROM nb_trips AS t
	WHERE service_id IS NOT NULL
	UNION 
	SELECT * FROM gtfs_ttc_trips
	ORDER BY trip_id ASC
) TO '/home/ubuntu/nb/output/trips.txt' CSV HEADER;

/*
-- shapes
COPY (
	SELECT 
		shape_id,
		path[1] AS shape_pt_sequence,
		ST_X(ST_Transform(geom,4326))::double precision AS shape_pt_lon,
		ST_Y(ST_Transform(geom,4326))::double precision AS shape_pt_lat
	FROM ( SELECT
		'shp_'||trip_id AS shape_id,
		(ST_DumpPoints(match_geom)).*
	FROM nb_trips
	WHERE service_id IS NOT NULL) AS sub
) TO '/home/ubuntu/nb/output/shapes.txt' CSV HEADER;
*/


-- stop_times
-- TODO there are stop times in the output with their trip_ids not in the trips table
COPY (
	SELECT 
		st.trip_id,
		FLOOR(EXTRACT(EPOCH FROM arrival_time) / 3600)||':'||to_char(arrival_time,'MI:SS') AS arrival_time,
		FLOOR(EXTRACT(EPOCH FROM departure_time) / 3600)||':'||to_char(departure_time,'MI:SS') AS departure_time,
		stop_id,
		stop_sequence
	FROM nb_stop_times AS st JOIN nb_trips AS t ON st.trip_id = t.trip_id
	WHERE 
	    arrival_time IS NOT NULL AND
	    t.service_id IS NOT NULL -- prevents incomplete trips from being used
	UNION 
	SELECT * FROM gtfs_ttc_stop_times
	ORDER BY trip_id,stop_sequence ASC
) TO '/home/ubuntu/nb/output/stop_times.txt' CSV HEADER;
