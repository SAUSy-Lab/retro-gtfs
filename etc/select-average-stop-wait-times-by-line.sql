/* 
	Select average wait times at all stops on a line
	for one service day, in minutes
	TODO 
	-- bring in from cloud: nb_stops, nb_stop_times, nb_trips
*/
WITH trips AS (
	SELECT trip_id 
	FROM nb_trips
	WHERE route_id = 94 AND service_id IN (17248)
), ordered_arrivals AS (
	SELECT 
		uid,
		stop_id,
		EXTRACT( EPOCH FROM departure_time) AS dt,
		ROW_NUMBER() OVER (PARTITION BY stop_id ORDER BY departure_time ASC) AS seq
	FROM nb_stop_times 
	WHERE trip_id IN (SELECT trip_id FROM trips)
), headways AS (
	SELECT 
		oa1.stop_id,
		(oa2.dt - oa1.dt) / 60 AS headway
	FROM ordered_arrivals AS oa1 JOIN ordered_arrivals AS oa2 
		ON oa1.seq = oa2.seq-1 AND oa1.stop_id = oa2.stop_id
)
SELECT 
	stop_id,
	AVG(headway) AS avg_headway,
	(AVG(headway)/2)*(1+VARIANCE(headway)/AVG(headway)^2) AS average_wait
FROM headways
GROUP BY stop_id