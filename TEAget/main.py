import sys
sys.path.append("..") # Adds higher directory to python modules path.
import time, WriteDB, GetGTFS, GetGTFSRT


# start and end time to pull data
start_time = '11/6/2017 12:50:00'
end_time = '11/12/2017 23:59:59'

def main():    
    global start_time, end_time
    # convert to POSIX
    start_time = int(time.mktime(time.strptime(start_time, '%m/%d/%Y %H:%M:%S')))
    end_time = int(time.mktime(time.strptime(end_time, '%m/%d/%Y %H:%M:%S')))
    
    # check if GTFS changed between start_time and end_time
    
    
    # ---- First get all GTFS feed from agency at start_time: ----------
    print(" - fetching route table ...")
    global routes
    GTFS_start = GetGTFS.GetAllRoutes(request_time = start_time)
    GTFS_end = GetGTFS.GetAllRoutes(request_time = end_time)
    
    if GTFS_start['timestamp'] != GTFS_end['timestamp']:
        print('GTFS feed changed in between {start} and {end}'.format(start = start_time, end = end_time))
        return
    else:
        routes = GTFS_start['routes']
    
    # Then get all trips given routes:
    print(" - fetching trips table ....")
    global trips; trips = GetGTFS.GetAllTrips(routes = routes, request_time = start_time)
    # then get all stop_times given trips:
    print("\n - fetching stop_times table ...")
    global stop_times; stop_times = GetGTFS.GetAllStopTImes(trips = trips, request_time = start_time)
    print("\n - fetching stop info ...")
    global stops; stops = GetGTFS.GetAllStops(stop_times = stop_times, request_time = start_time)

    print ("initiate tables in database")
    WriteDB.init_DB(reset = True)
    
    # ----- store stop table ----------------------
    print (" - write routes table to database ...")
    GetGTFS.StoreStops(stops)
    # -----stop directions table ---------------------
    print (" - create and write directions to database ...")
    GetGTFS.StoreDirections(trips, stop_times)
    
    # ---- Get Vehicle Positions between start_time and end_time, this function also store to DB
    GetGTFSRT.GetAllVehiclePositions(start_time = start_time, end_time = end_time, trips = trips)
    
if __name__ == '__main__':
    main()