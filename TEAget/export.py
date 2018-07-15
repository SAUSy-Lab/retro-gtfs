import sys
sys.path.append("..") # Adds higher directory to python modules path.
import conf, db

def export(outdir):
    """ export data from db into GTFS feed """
    print('----- Exporting to {dir} ----------'.format(dir = outdir))
    c = db.cursor()
    
#    print('Updating service_id in trips table')
#    c.execute(
#            """
#            WITH sub AS (
#            	SELECT 
#            		t.trip_id, 
#            		( to_timestamp(st.etime) AT TIME ZONE :'tz' )::date - 'epoch'::date AS service_id
#            	FROM {trips_table} AS t 
#            	LEFT JOIN {stop_times_table} AS st
#            		ON t.trip_id = st.trip_id AND st.stop_sequence = 1
#            )
#            UPDATE {trips_table} AS t SET service_id = sub.service_id
#            FROM sub 
#            WHERE 
#            	t.trip_id = sub.trip_id AND 
#            	-- only changed values
#            	(t.service_id != sub.service_id OR t.service_id IS NULL);            
#            """.format(
#                trips_table = conf.conf['db']['tables']['trips'],
#                stop_times_table = conf.conf['db']['tables']['stop_times']
#                )
#            )
    
#    # make calendar_dates.txt
#    with open(outdir + '/calendar.txt', 'w') as f:
#        c.copy_expert(
#                """
#                COPY(
#                	SELECT DISTINCT 
#                		service_id,
#                		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
#                		1 AS exception_type
#                	FROM {trips_table}
#                	WHERE NOT ignore
#                	ORDER BY service_id ASC
#                ) TO STDOUT WITH CSV HEADER;
#                """.format(                    
#                    trips_table = conf.conf['db']['tables']['trips']
#                    )
#                , f)
    
    #
    
    # copy stop_id to stop_times table
    
    print('Updating stop_id in stop_times table ...')
    c.execute(
            """
            UPDATE {stop_times} as st SET fake_stop_id = stops.stop_id
            FROM {stops} as stops
            WHERE st.stop_uid =  stops.uid
            """.format(
                stop_times = conf.conf['db']['tables']['stop_times'],
                stops = conf.conf['db']['tables']['stops']
                )
            )
    # make stops.txt
    print('writing stops.txt ... ')
    with open(outdir + '/stops.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (
                	SELECT
                		stop_id,
                		stop_code::varchar,
                		stop_name,
                		lat AS stop_lat,
                		lon AS stop_lon
                	FROM {stops} 
                ) TO STDOUT WITH CSV HEADER;
                """.format(                    
                    stops = conf.conf['db']['tables']['stops']
                    )
                , f)
    # make routes table                
    print('writing routes.txt ... ')
    with open(outdir + '/routes.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (
                	SELECT 
                		DISTINCT
                			route_id,
                			1 AS agency_id, -- all the same agency 
                			route_id::varchar AS route_short_name,
                			'' AS route_long_name,
                			3 AS route_type -- LET THEM RIDE BUSES
                	FROM {trips}
                	WHERE NOT ignore
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    trips = conf.conf['db']['tables']['trips']
                    )
                , f)                
                
    # make trips table                
    print('writing trips.txt ... ')
    with open(outdir + '/trips.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (
                	SELECT
                		t.route_id::varchar,
                		t.service_id,
                		t.trip_id,
                		t.block_id,
                		'shp_'||trip_id AS shape_id
                	FROM {trips} AS t
                	WHERE NOT ignore
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    trips = conf.conf['db']['tables']['trips']
                    )
                , f)                                
                
    # make stop_times table                
    print('writing stop_times.txt ... ')
    with open(outdir + '/stop_times.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (
                	SELECT 
                		t.trip_id,		
                		EXTRACT( EPOCH FROM 
                			-- local time of stop minus local service date
                			to_timestamp(round(st.etime)) AT TIME ZONE {timezone} -
                			('1970-01-01'::date + t.service_id * INTERVAL '1 day')::date
                		) * INTERVAL '1 second' AS arrival_time,
                		EXTRACT( EPOCH FROM 
                			-- local time of stop minus local service date
                			to_timestamp(round(st.etime)) AT TIME ZONE {timezone} -
                			('1970-01-01'::date + t.service_id * INTERVAL '1 day')::date
                		) * INTERVAL '1 second' AS departure_time,
                		stop_sequence,
                		fake_stop_id AS stop_id
                	FROM {stop_times} AS st JOIN {trips} AS t ON st.trip_id = t.trip_id
                	WHERE NOT t.ignore -- not actually necessary
                	ORDER BY trip_id, stop_sequence ASC
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    trips = conf.conf['db']['tables']['trips'],
                    stop_times = conf.conf['db']['tables']['stop_times'],
					timezone = conf.conf['timezone']
                    )
                , f)  
                                              
    print('writing true_stop_times.txt ... ')
    with open(outdir + '/true_stop_times.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (                
                    SELECT {true_stop_times}.*
                    FROM {true_stop_times} INNER JOIN 
                        (SELECT DISTINCT trip_id from {stop_times}) as filter
                    ON {true_stop_times}.trip_id = filter.trip_id                    
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    true_stop_times = conf.conf['db']['tables']['true_stop_times']
                    )
                , f)                         