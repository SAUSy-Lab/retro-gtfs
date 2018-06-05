/* DB views for viewing and debugging trip-level data e.g. in QGIS */

-- set your table names here
\set prefix						'ttc_'

\set stops_table				:prefix'stops'
\set stop_times_table		:prefix'stop_times'
\set directions_table		:prefix'directions'

\set stop_times_view			:prefix'stop_times_view'
\set trip_sched_stops_view	:prefix'trip_sched_stops'


-- Adds geometry to stop_times table

DROP VIEW IF EXISTS :stop_times_view;
CREATE OR REPLACE VIEW :stop_times_view AS 
SELECT 
	st.stop_uid,
	st.trip_id,
	st.stop_sequence,
	st.etime,
	s.stop_name,
	s.stop_code,
	s.report_time,
	s.the_geom
FROM :stop_times_table AS st
JOIN :stops_table AS s 
	ON s.uid = st.stop_uid;


-- Gives sets of stops with geometry from the schedule data

DROP VIEW IF EXISTS :trip_sched_stops_view;
CREATE OR REPLACE VIEW :trip_sched_stops_view AS 
SELECT DISTINCT ON (t.trip_id, s.stop_id) 
	t.trip_id,
	s.stop_id,
	d.direction_id,
	s.the_geom,
	s.uid AS stop_uid,
	s.stop_code,
	s.stop_name,
	d.report_time AS direction_report_time,
	s.report_time AS stop_report_time
FROM ttc_trips AS t
JOIN ttc_directions AS d ON 
	t.direction_id = d.direction_id AND
	d.report_time <= t.times[array_upper(t.times,1)]
JOIN ttc_stops AS s ON 
	s.stop_id = ANY(d.stops) AND
	s.report_time <= t.times[array_upper(t.times,1)]
ORDER BY t.trip_id, s.stop_id, d.report_time, s.report_time ASC
