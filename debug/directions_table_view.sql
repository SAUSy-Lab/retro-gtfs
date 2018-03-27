/*For viewing directions table data e.g. in QGIS*/

﻿CREATE OR REPLACE VIEW direction_stops_view AS 
SELECT 
	d.direction_id,
	a.stop, 
	a.seq,
	s.the_geom,
	row_number() OVER () AS uid
FROM jv_directions AS d, unnest(d.stops) WITH ORDINALITY a(stop, seq)
JOIN jv_stops AS s ON s.stop_id = a.stop;
