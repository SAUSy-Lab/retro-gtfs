import sys
sys.path.append("..") # Adds higher directory to python modules path.
import conf, db

def export(outdir):
    """ export data from db into GTFS feed """
    print('----- Exporting to {dir} ----------'.format(dir = outdir))
    c = db.cursor()
    
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
                	SELECT * from {routes_table}
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    routes_table = conf.conf['agency'] + "_routes_orig"
                    )
                , f)                
                
    # make trips table                
    print('writing trips.txt ... ')
    with open(outdir + '/trips.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (
                	SELECT * from {trips_table}
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    trips_table = conf.conf['agency'] + "_trips_orig"
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
                		(to_timestamp(round(st.etime)) AT TIME ZONE '{timezone}')::time AS arrival_time,
                		(to_timestamp(round(st.etime)) AT TIME ZONE '{timezone}')::time AS departure_time,
                		stop_sequence,
                		stop_id AS stop_id
                	FROM {stop_times} AS st JOIN {trips} AS t ON st.trip_id = t.trip_id
                	WHERE NOT t.ignore
                	ORDER BY trip_id, stop_sequence ASC
                ) TO STDOUT CSV HEADER;                
                """.format(                    
                    trips = conf.conf['db']['tables']['trips'],
                    stop_times = conf.conf['db']['tables']['stop_times'],
					timezone = conf.conf['timezone']
                    )
                , f)  
                  