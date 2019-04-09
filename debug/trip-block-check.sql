WITH sub AS (
	SELECT 
		trip_id,
		block_id,
		direction_id,
		times[1]::int AS first_time,
		times[array_upper(times,1)]::int AS last_time,
		timestamp 'epoch' + times[1]::int * INTERVAL '1s' AS day,
		row_number() OVER (ORDER BY times[1]) AS seq
	FROM ttc_trips
	WHERE vehicle_id = '4202' 
	ORDER BY times[1]
)
SELECT 
	s1.trip_id,
	s1.direction_id,
	s1.block_id = s2.block_id,
	timestamp 'epoch' + s1.last_time * interval '1s' AS this_end,
	timestamp 'epoch' + s2.first_time * interval '1s' AS next_start,
	(s2.first_time-s1.last_time) * INTERVAL '1s'
FROM sub AS s1 JOIN sub AS s2 ON s1.seq = s2.seq-1