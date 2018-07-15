import sys
sys.path.append("..") # Adds higher directory to python modules path.
import conf, db

def export(outdir):
    """ export data from db into GTFS feed """
    c = db.cursor()
    # make calendar_dates.txt
    with open(outdir + '/calendar.txt', 'w') as f:
        c.copy_expert(
                """
                COPY(
                	SELECT DISTINCT 
                		service_id,
                		to_char(TIMESTAMP 'EPOCH' + (service_id * INTERVAL '1 day'),'YYYYMMDD') AS date,
                		1 AS exception_type
                	FROM {trips_table}
                	WHERE NOT ignore
                	ORDER BY service_id ASC
                ) TO STDOUT WITH CSV HEADER;
                """.format(                    
                    trips_table = conf.conf['db']['tables']['trips']
                    )
                , f)
    # make stops.txt
    with open(outdir + '/stops.txt', 'w') as f:
        c.copy_expert(
                """
                COPY (
                	SELECT
                		DISTINCT
                		st.fake_stop_id AS stop_id,
                		s.stop_code::varchar,
                		s.stop_name,
                		s.lat AS stop_lat,
                		s.lon AS stop_lon
                	FROM {stop_times} AS st JOIN {stops} AS s 
                		ON s.uid = st.stop_uid
                ) TO STDOUT WITH CSV HEADER;
                """.format(                    
                    stops = conf.conf['db']['tables']['stops'],
                    stop_times = conf.conf['db']['tables']['stop_times']
                    )
                , f)