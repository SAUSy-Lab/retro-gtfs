import sys, os
sys.path.append("..") # Adds higher directory to python modules path.
import time, WriteDB, GetGTFS, GetGTFSRT, db, process, shutil, export
from datetime import timedelta, date, datetime

# start and end time to pull data
#start_date = date(2018, 5, 18)
#end_date = date(2018, 6, 12)

start_date = date(2018, 5, 18)
end_date = date(2018, 5, 19)

def main():    
    global start_date, end_date, routes, trips, stop_times, stops
    
    GTFS_timestamp = 0
    for Day in daterange(start_date, end_date): # for each day in range
        print('----- Running day ' + str(Day) + ' --------------')
        # POSIX start and end time
        start_time = int(time.mktime(datetime.combine(Day, datetime.min.time()).timetuple()))
        end_time   = int(time.mktime(datetime.combine(Day, datetime.max.time()).timetuple()))
        # check if GTFS changed
        GTFS_new_timestamp = GetGTFS.latest_GTFS_update(start_time)
        if GTFS_new_timestamp != GTFS_timestamp:
            # update GTFS
            print('GTFS changed on ' + str(Day))
            routes, trips, stop_times, stops = GetGTFS.GetGTFS(GTFS_new_timestamp)
            GTFS_timestamp = GTFS_new_timestamp
        
        # reset trips table in database
        WriteDB.init_DB(reset_all = False)
        
        # Get Vehicle Locations, this function also store to DB
        print(' - Getting Vehicle positions ... ')
        GetGTFSRT.GetAllVehiclePositions(start_time = start_time, end_time = end_time, trips = trips)
        
        # process vehicle positions in the day
        print(' - Processing recorded trips ...')
        recorded_trip_ids = db.get_all_trip_ids()
        process.process_trips(trip_ids = recorded_trip_ids, max_procs = 4)
        
#        # export retro GTFS
#        print(' - exporting retro-GTFS ...')
#        outdir =  os.getcwd() + '/output/' + str(Day)
#        if os.path.exists(outdir):
#            shutil.rmtree(outdir)
#        os.mkdir(outdir)
#        export.export(outdir)
    
def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)
    
    
if __name__ == '__main__':
    main()