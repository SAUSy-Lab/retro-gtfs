WITH stops_made AS (
	--For each trip, get an array of stop_id's of stops made. 
	--Can be Null.
	SELECT 
		t.trip_id,
		CASE 
			WHEN array_agg(stop_id) = ARRAY[NULL::varchar] THEN '{}'
			ELSE array_agg(stop_id ORDER BY stop_sequence) 
		END AS stops
	FROM jv_trips AS t 
	LEFT JOIN jv_stop_times AS st ON t.trip_id = st.trip_id
	GROUP BY t.trip_id
), stops_given AS (
	-- Same as above, but this is the list of scheduled stops.
	SELECT 
		DISTINCT ON (t.trip_id) t.trip_id, d.stops
	FROM jv_trips AS t
	JOIN jv_directions AS d 
		ON t.direction_id = d.direction_id AND
		d.report_time <= t.times[array_upper(t.times,1)]
	ORDER BY t.trip_id, d.report_time ASC
)
SELECT 
	route_id,
	COUNT(*) AS num_trips,
	COUNT(*) FILTER ( WHERE array_length(sm.stops,1) = 2 ) AS two,
	round( AVG( 
		array_length(sm.stops,1) / array_length(sg.stops,1)::numeric 
	),4 )AS avg_pct_stops_made,
	round( STDDEV( 
		array_length(sm.stops,1) / array_length(sg.stops,1)::numeric 
	),4 )AS stdev_pct_stops_made
FROM jv_trips AS t 
JOIN stops_made AS sm ON t.trip_id = sm.trip_id
JOIN stops_given AS sg ON t.trip_id = sg.trip_id
WHERE t.problem NOT IN ('too short','too few vehicles')
GROUP by route_id 
ORDER BY num_trips DESC

