import sys, os
sys.path.append("..") # Adds higher directory to python modules path.
import time, WriteDB, GetGTFS, GetGTFSRT, db, process, shutil, export, aggregate_GTFS
from datetime import timedelta, date, datetime

# start and end time to pull data
#start_date = date(2018, 5, 18)
#end_date = date(2018, 6, 12)

start = date(2018, 6, 16)
end = date(2018, 6, 18)

def main(start_date, end_date, aggregate_method):    
    global routes, trips, stop_times, stops
#    process.process_trip('1924523060')
    GTFS_timestamp = GetGTFS.latest_GTFS_update(int(time.mktime(datetime.combine(start_date, datetime.min.time()).timetuple())))
    routes, trips, stop_times, stops = GetGTFS.GetGTFS(GTFS_timestamp)
    for Day in daterange(start_date, end_date): # for each day in range
        print('----- Running day ' + str(Day) + ' --------------')
        # POSIX start and end time
        start_time = int(time.mktime(datetime.combine(Day, datetime.min.time()).timetuple()))
        end_time   = int(time.mktime(datetime.combine(Day, datetime.max.time()).timetuple()))
        # check if GTFS changed
        GTFS_new_timestamp = GetGTFS.latest_GTFS_update(start_time)
        if GTFS_new_timestamp != GTFS_timestamp:
            raise Exception('GTFS changed, we are assuming that GTFS is constant for now')
        
        # reset trips table in database
        WriteDB.init_DB(reset_all = False)
        
        # Get Vehicle Locations, this function also store to DB
        print(' - Getting Vehicle positions ... ')
        GetGTFSRT.GetAllVehiclePositions(start_time = start_time, end_time = end_time, trips = trips)
        
        # process vehicle positions in the day
        print('\n - Processing recorded trips ...')
        recorded_trip_ids = db.get_all_trip_ids()
        process.process_trips(trip_ids = recorded_trip_ids, max_procs = 7)
        # update stop_id in stop_times table
        WriteDB.Update_stop_id()
         
        # export retro GTFS files for each day
        print('\n - exporting retro-GTFS for ' + str(Day) + '.....')
        outdir = './output/individuals/' + str(Day)
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        os.mkdir(outdir)
        export.export(outdir)
        
    # aggregate retro GTFS files into 1 bundle
    print('\n - aggregating retro-GTFS files into one...')
    aggregate_GTFS.aggregate(indiv_dir = './output/individuals', outdir = './output/aggregated',
                             method = aggregate_method)    
        
def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)
    
    
if __name__ == '__main__':
    main(start, end, aggregate_method = 'average')