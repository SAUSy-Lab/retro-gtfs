/*
	This script measures the quality of trip matches. It uses psql 
	variables and should be run with psql on a PostgreSQL 9.5+ database. 
	You'll need to provide a table name prefix or otherwise change the 
	table names to distinguish among agencies within a database.
*/

-- set your table names here
\set directions_table  prefix_directions
\set trips_table       prefix_trips
\set stop_times_table  prefix_stop_times


WITH stops_made AS (
	--For each trip, get an array of stop_id's of stops made. 
	--Can be Null.
	SELECT 
		t.trip_id,
		CASE 
			WHEN array_agg(stop_id) = ARRAY[NULL::varchar] THEN '{}'
			ELSE array_agg(stop_id ORDER BY stop_sequence) 
		END AS stops,
		COUNT(stop_id) AS num_stops 
	FROM :trips_table AS t 
	LEFT JOIN :stop_times_table AS st ON t.trip_id = st.trip_id
	GROUP BY t.trip_id
), stops_given AS (
	-- Same as above, but this is the list of scheduled stops.
	SELECT 
		DISTINCT ON (t.trip_id) t.trip_id, 
		d.stops,
		array_length(d.stops,1) AS num_stops 
	FROM :trips_table AS t
	JOIN :directions_table AS d 
		ON t.direction_id = d.direction_id AND
		d.report_time <= t.times[array_upper(t.times,1)]
	ORDER BY t.trip_id, d.report_time ASC
)
SELECT 
	route_id,
	COUNT(*) AS num_trips,
	percentile_disc( array[0.25,0.5,0.75] ) WITHIN GROUP ( ORDER BY ROUND(sm.num_stops::numeric/sg.num_stops,2) ) AS stop_quartiles,
	-- average percentage of stops made by trips
	round( AVG( sm.num_stops / sg.num_stops::numeric )*100, 3 )AS avg_pct_stops,
	-- average confidence of matched trips (including default = 1)
	round( AVG(match_confidence)::numeric, 4 ) AS avg_confidence,
	-- trip_id's of trips making less than half of stops
	( array_agg(t.trip_id ORDER BY random()) FILTER (WHERE sm.num_stops < sg.num_stops/2) )[1:4] AS potentially_bad_trips
FROM :trips_table AS t 
JOIN stops_made AS sm ON t.trip_id = sm.trip_id
JOIN stops_given AS sg ON t.trip_id = sg.trip_id
WHERE t.problem NOT IN ('too short','too few vehicles')
GROUP by route_id 
ORDER BY num_trips DESC

