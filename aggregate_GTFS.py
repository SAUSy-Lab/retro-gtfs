import sys
sys.path.append("..") # Adds higher directory to python modules path.
import os, shutil, db, conf, pandas, math , WriteDB, sqlalchemy, datetime
pandas.options.mode.chained_assignment = None

indiv_dir = "./output/individuals"
outdir = "./output/aggregated"

def aggregate(indiv_dir, outdir, method):
    if method == 'average':
        return(average_GTFS_SQL(indiv_dir, outdir))
    elif method == 'combine':
        return(combine_GTFS(indiv_dir, outdir))
    else:
        raise Exception('Method ' + method + ' not recognized')

def average_GTFS_SQL(indiv_dir, outdir):
    """
    function to aggregate individual GTFS files from each date into one GTFS file
    by aggregating stop_times.
    indiv_dir: directory that contains individual GTFS files.
    outdir: output directory
    """
    # set up postgres engine
    c = db.cursor()
    postgres_engine = sqlalchemy.create_engine('postgresql+psycopg2://' + 
                                      conf.conf['db']['user'] + 
                                      ':' + conf.conf['db']['password'] + 
                                      '@' + conf.conf['db']['host'] +
                                      '/' + conf.conf['db']['name'] 
                                      )
    
    # reset output directory
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)
    
    # get tables from DB
    trips = db.fetch(conf.conf['agency'] + '_trips_orig')
    routes = db.fetch(conf.conf['agency'] + '_routes_orig')
    stops = db.fetch(conf.conf['db']['tables']['stops'])
    calendar = db.fetch(conf.conf['agency'] + '_calendar')
    

    # loop through indiv_dir to get stop_times
    for day in os.listdir(indiv_dir):
        # check if GTFS files exist
        if os.path.exists(indiv_dir + "/" + day + "/routes.txt"):
            print(day)
            # get stop_times table for that day
            stop_times_day = pandas.read_csv(indiv_dir + "/" + day + "/stop_times.txt", dtype = "str")
            stop_times_day['count'] = 1
            stop_times_day['stop_sequence'] = [int(sq) for sq in stop_times_day['stop_sequence']]
            if not 'stop_times_out' in locals(): # initiate from first day
                stop_times_out = stop_times_day
                stop_times_out['count'] = 1
                stop_times_out['arrival_seconds'] = [time_to_seconds(t) for t in stop_times_out['arrival_time']]
                stop_times_out['departure_seconds'] = [time_to_seconds(t) for t in stop_times_out['departure_time']]

            
            else:            
                # convert time string to seconds:
                stop_times_day['arrival_seconds'] = [time_to_seconds(t) for t in stop_times_day['arrival_time']]
                stop_times_day['departure_seconds'] = [time_to_seconds(t) for t in stop_times_day['departure_time']]
                
                # store to temporary tables in postgresql
                if WriteDB.TableExists('temp_stop_times_out'): WriteDB.DropTable('temp_stop_times_out')
                if WriteDB.TableExists('temp_stop_times_day'): WriteDB.DropTable('temp_stop_times_day')
                stop_times_out.to_sql('temp_stop_times_out', postgres_engine)
                stop_times_day.to_sql('temp_stop_times_day', postgres_engine)
                
                # match with sql:
                if WriteDB.TableExists('temp1'): WriteDB.DropTable('temp1')
                # merge 2 tables
                c.execute(
                        """
                        SELECT 
                            COALESCE (out.trip_id, day.trip_id) as trip_id,
                            COALESCE (out.stop_sequence, day.stop_sequence) as stop_sequence,
                            COALESCE (out.stop_id, day.stop_id) as stop_id,
                            out.arrival_seconds as arrival_seconds_out,
                            out.departure_seconds as departure_seconds_out,
                            day.arrival_seconds as arrival_seconds_day,
                            day.departure_seconds as departure_seconds_day,
                            COALESCE(out.count, 0) as count_out,
                            COALESCE(day.count, 0) as count_day
                        INTO temp1
                        FROM temp_stop_times_out as out
                        FULL OUTER JOIN temp_stop_times_day as day
                        on out.trip_id = day.trip_id and out.stop_sequence = day.stop_sequence
                        ;
                        ALTER TABLE temp1 ALTER COLUMN stop_sequence type integer USING (stop_sequence::integer);
                        """)
                # take average of stop times
                c.execute(
                        """
                        SELECT trip_id, stop_sequence, stop_id,
                            CASE WHEN count_day = 0 THEN count_out
                                WHEN count_out = 0 THEN count_day
                                ELSE count_out + count_day
                                END as count,
                            CASE WHEN count_day = 0 then arrival_seconds_out
                                WHEN count_out = 0 then arrival_seconds_day
                                ELSE (arrival_seconds_out*count_out + arrival_seconds_day*count_day)/(count_out + count_day)
                                END as arrival_seconds,
                            CASE WHEN count_day = 0 then departure_seconds_out
                                WHEN count_out = 0 then departure_seconds_day
                                ELSE (departure_seconds_out*count_out + departure_seconds_day*count_day)/(count_out + count_day)
                                END as departure_seconds
                        FROM temp1      
                        ORDER BY trip_id, stop_sequence
                        ;
                        """)
                stop_times_out = pandas.DataFrame(c.fetchall())
                stop_times_out.columns = ['trip_id', 'stop_sequence', 'stop_id', 'count', 'arrival_seconds', 'departure_seconds']
                            
        else: # if not GTFS file folder, skip
            continue
        
    # end iteration, decorate stop_times table 
    stop_times_out['arrival_time'] = [seconds_to_time(s) for s in stop_times_out['arrival_seconds']]
    stop_times_out['departure_time'] = [seconds_to_time(s) for s in stop_times_out['departure_seconds']]
    stop_times = stop_times_out[['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'count']]
    
    # export:
    routes.to_csv(outdir + '/routes.txt', index = False)
    trips.to_csv(outdir + '/trips.txt', index = False)
    stops.to_csv(outdir + '/stops.txt', index = False)
    stop_times.to_csv(outdir + '/stop_times.txt', index = False)
    calendar.to_csv(outdir + '/calendar.txt', index = False)
    
    return

def time_to_seconds(time1):
    """ convert a time string to seconds """
    time1 = time1.split(":")
    time1 = [float(t) for t in time1]
    time1_seconds = time1[0]*3600 + time1[1]*60 + time1[2]
    return(time1_seconds)
    
def seconds_to_time(seconds):
    Time = list([0,0,0])
    Time[0] = math.floor(seconds/3600)
    Time[1] = math.floor((seconds - Time[0]*3600)/60)
    Time[2] = math.floor(seconds - Time[0]*3600 - Time[1]*60)   
    dt = datetime.datetime(1900, 1, 1, Time[0], Time[1], Time[2])
    return(dt.strftime("%H:%M:%S"))

def combine_GTFS(indiv_dir, outdir):
    # reset output directory
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)
    
    # get tables from DB
    routes = db.fetch(conf.conf['agency'] + '_routes_orig')
    stops = db.fetch(conf.conf['db']['tables']['stops'])
    trips = db.fetch(conf.conf['agency'] + '_trips_orig')[['route_id', 'trip_id']]
    # create stop_times table (hopefully you have enough RAM)
    for day in os.listdir(indiv_dir):
        # check if GTFS files exist
        if os.path.exists(indiv_dir + "/" + day + "/routes.txt"):
            print(day)
            # get stop_times table for that day
            stop_times_day = pandas.read_csv(indiv_dir + "/" + day + "/stop_times.txt", dtype = "str")
            # create trips table for that day
            trips_day = pandas.merge(stop_times_day, trips, how = 'left', on = 'trip_id')
            # alter trip_id on trips table and stop_times table
            stop_times_day['trip_id'] = [tid + '_' + str(day).replace('-', '') for tid in stop_times_day['trip_id']]
            trips_day['trip_id'] = [tid + '_' + str(day).replace('-', '') for tid in trips_day['trip_id']]
            trips_day['service_id'] = trips_day['trip_id']
            trips_day = trips_day[['route_id', 'trip_id', 'service_id']].drop_duplicates()
            # create calendar_dates table for that day
            calendar_dates_day = pandas.DataFrame({
                    'service_id': trips_day['service_id'],
                    })
            calendar_dates_day['date'] = str(day).replace('-','')
            calendar_dates_day['exception_type'] = 1
            
    
            # append to big stop_times, trips, and calendar_dates
            if 'stop_times_all' not in locals():
                stop_times_all = stop_times_day
                trips_all = trips_day
                calendar_dates_all = calendar_dates_day
            else:
                stop_times_all = pandas.concat([stop_times_all, stop_times_day], ignore_index = True)
                trips_all = pandas.concat([trips_all, trips_day], ignore_index = True)
                calendar_dates_all = pandas.concat([calendar_dates_all, calendar_dates_day], ignore_index = True)
                    # export:
    routes.to_csv(outdir + '/routes.txt', index = False)
    trips_all.to_csv(outdir + '/trips.txt', index = False)
    stops.to_csv(outdir + '/stops.txt', index = False)
    stop_times_all.to_csv(outdir + '/stop_times.txt', index = False)
    calendar_dates_all.to_csv(outdir + '/calendar_dates.txt', index = False)
    
