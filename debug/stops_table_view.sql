/*For viewing stop_times table data e.g. in QGIS*/

-- set your table names here
\set stops_table       jv_stops
\set stop_times_table  jv_stop_times

DROP VIEW IF EXISTS stop_times_view;

CREATE OR REPLACE VIEW stop_times_view AS 
SELECT 
	DISTINCT ON (st.trip_id, st.stop_id) st.stop_id,
	st.trip_id,
	st.stop_sequence,
	st.etime,
	s.the_geom
FROM :stop_times_table AS st
JOIN :stops_table AS s 
	ON s.stop_id = st.stop_id AND
	s.report_time <= st.etime
ORDER BY st.stop_id, st.trip_id, s.report_time

