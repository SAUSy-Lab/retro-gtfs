/* DB views for viewing and debugging trip-level data e.g. in QGIS */

-- set your table names here
\set stops_table       jv_stops
\set stop_times_table  jv_stop_times
\set directions_table  jv_directions


-- Adds geometry to stop_times table

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
ORDER BY st.stop_id, st.trip_id, s.report_time;


-- Gives sets of stops with geometry from the directions table

DROP VIEW IF EXISTS direction_stops_view;
﻿CREATE OR REPLACE VIEW direction_stops_view AS 
SELECT 
	d.direction_id,
	a.stop, 
	a.seq,
	s.the_geom,
	row_number() OVER () AS uid
FROM :directions_table AS d, unnest(d.stops) WITH ORDINALITY a(stop, seq)
JOIN :stops_table AS s ON s.stop_id = a.stop;
