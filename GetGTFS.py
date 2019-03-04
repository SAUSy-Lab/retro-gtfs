import sys
sys.path.append("..") # Adds higher directory to python modules path.
import requests, numpy, sys, db, pandasql, conf, warnings, WriteDB, sqlalchemy
from pandas.core.frame import DataFrame

def GetGTFS(time, Update = True):
    """ Get latest GTFS at timestamp time """
    global Time; Time = time
    if Update:
        # find exact GTFS timestamp on the database:
        GTFS_timestamp = find_exact_GTFS_timestamp(time)
        # First get all routes
        routes = GetAllRoutes(GTFS_timestamp)
        # Then get all trips given routes:
        print(" - fetching trips table ....")
        trips = GetAllTrips(routes = routes, request_time = GTFS_timestamp)
        # then get all stop_times given trips:
        print("\n - fetching stop_times table ...")
        stop_times = GetAllStopTImes(trips = trips, request_time = GTFS_timestamp)
        print("\n - fetching stop info ...")
        stops = GetAllStops(stop_times = stop_times, request_time = GTFS_timestamp)

    print ("initiate/reset tables in database")
    WriteDB.init_DB(reset_all = Update)
    
    # ----- store stop table ----------------------
    print ("\n - write routes table to database ...")
    StoreStops(stops)
    # -----stop directions table ---------------------
    print ("\n - create and write directions to database ...")
    StoreDirections(trips, stop_times)
    # ----- original stop times table -----------------------
#    print ("\n - create and write true stop times to database ...")
#    StoreTrueStopTimes(stop_times)
# ----- original routestimes table -----------------------
    print ("\n - create and write original routes table to database ...")
    StoreRoutes_orig(routes)
    # ----- original trips table -----------------------
    print ("\n - create and write original trips table to database ...")
    StoreTrips_orig(trips)
    print ("\n - write calendar table to database ...")
    GetCalendar(time)
    return routes, trips, stop_times, stops
    
""" These functions will use GTFS API to create GTFS tables"""
def GetAllRoutes(request_time):
    """ get all route_id's from agency"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    try:
        APICall = (URL + "api/gtfs/routes" +
                   "?gtfs_timestamp=" + repr(request_time) + 
                   "&source=" + agency
                   )
        Response = requests.get(APICall)
    except Exception as e:
        print('API problem: ' + e)
        return
    # response received, check if status is ok
    ResponseParse = Response.json()
    if ResponseParse['header']['status'] != 'OK':
        print('problem with API call: ' + APICall)
        return
    # get all routes
    routes = DataFrame(ResponseParse['data'])
    return routes

def GetAllTrips(routes, request_time):
    """Get all trips from given route_id's"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    Total = len(routes.route_id)
    count = 0
    print("Total routes: {0}".format(Total))
    
    for route_id in routes.route_id:
        count = count + 1;
        # progress status
        if round(count*100/Total) % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(round(count*100/Total)))
            sys.stdout.flush()
        try:
            APICall = (URL + "api/gtfs/trips" + 
                       "?source=" + agency +
                       "&gtfs_timestamp=" + repr(request_time) +
                       "&route_id=" + route_id
                       )
            Response = requests.get(APICall)
            ResponseParse = Response.json()
        except Exception as e:
            print('API problem: ' + str(e))
            continue
        # response received, check if status is ok        
        if ResponseParse['header']['status'] != 'OK':
            warnings.warn('problem with API call: '+ APICall, stacklevel = 3)
            continue
        # append trip_id
        trip_data = DataFrame(ResponseParse['data']['trips'])
        trip_data['route_id'] = route_id
        if 'trips' not in locals():
            trips = trip_data
        else:
            trips = trips.append(trip_data)
    return trips
            

def GetAllStopTImes(trips, request_time):
    """Get all stop times from an agency given trip_id's"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    # get all stops by matching trip_id with stop_times table
    Total = len(trips.trip_id)
    count = 0
    print("Total trips: {0}".format(Total))
    
    for trip_id in trips.trip_id:
        count = count + 1
        # progress status
        if round(count*100/Total) % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(round(count*100/Total)))
            sys.stdout.flush()
        try:
            APICall = (URL + "api/gtfs/stop_times" +                        
                       "?source=" + agency +
                       "&gtfs_timestamp=" + repr(request_time) +
                       "&trip_id=" + trip_id
                       )
            Response = requests.get(APICall)
            ResponseParse = Response.json()
        except Exception as e:
            print('API problem: ' + e)
            continue
        # response received, check if status is ok        
        if ResponseParse['header']['status'] != 'OK':
            warnings.warn('problem with API call: '+ APICall, stacklevel = 3)
            continue
        # append trip_id
        stop_data = DataFrame(ResponseParse['data']['stops'])
        stop_data['trip_id'] = trip_id
        if 'stop_times' not in locals():
            stop_times = stop_data
        else:
            stop_times = stop_times.append(stop_data)
    return stop_times

def GetAllStops(stop_times, request_time):
    """Get stops info from an agency given stop_times table by using /stops API call"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    stops = list()
    Total = len(numpy.unique(stop_times.stop_id))
    count = 0
    print("Total stops: {0}".format(Total))

    for stop_id in numpy.unique(stop_times.stop_id):
        count = count + 1
        # progress status
        if round(count*100/Total) % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(round(count*100/Total)))
            sys.stdout.flush()

        try:
            APICall = (URL + "api/gtfs/stops" + 
                       "?source=" + agency +
                       "&gtfs_timestamp=" + repr(request_time) +
                       "&stop_id=" + stop_id
                       )
            Response = requests.get(APICall)
            ResponseParse = Response.json()
        except Exception as e:
            print('API problem: ' + e)
            continue
        # response received, check if status is ok        
        if ResponseParse['header']['status'] != 'OK':
            warnings.warn('problem with API call: '+ APICall, stacklevel = 3)
            continue
        # parse response into stops
        try: 
            stop_name = ResponseParse['data']['properties']['stop_name']
        except: stop_name  = ''
        try:
            stop_code = ResponseParse['data']['properties']['stop_code']
        except: stop_code = ''
        try: 
            lon = ResponseParse['data']['coordinates'][0][0]
        except: lon = ''
        try: 
            lat = ResponseParse['data']['coordinates'][0][1]
        except: lat = ''
        uid = count
        report_time = repr(request_time)
        
        stops.append({'stop_name':stop_name,
                         'stop_id':stop_id,
                         'stop_code':stop_code,
                         'lon':lon, 
                         'lat':lat, 
                         'uid':uid, 
                         'report_time':report_time})
    return DataFrame(stops)

""" These functions format data and store to database"""
def StoreStops(stops):
    global Time
    count = 0
    Total = len(stops.index)
    for index, row in stops.iterrows():
        # progress status
        count = count + 1
        if round(count*100/Total) % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()
        # store data
        db.try_storing_stop(row['stop_id'],
                            row['stop_name'],
                            row['stop_code'],
                            row['lon'],
                            row['lat'],
                            Time)
        
def StoreDirections(trips, stop_times):
    global Time
    Directions = pandasql.sqldf(
            """
            select trips.trip_id, trips.route_id, trips.direction_id, trip_stops.stops
            from trips left join
                (SELECT trip_id, group_concat(stop_id) as stops
                FROM stop_times
                GROUP BY trip_id) as trip_stops
            on trips.trip_id = trip_stops.trip_id            
            """,
            locals()
    )
    count = 0
    Total = len(Directions.index)
    for index, row in Directions.iterrows():
        # progress status
        count = count + 1
        if round(count*100/Total) % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()
        # store data
        db.try_storing_direction(trip_id = row.trip_id, route_id = row.route_id, 
                                 did = row.direction_id, 
                                 title = '', name = '', branch = '', useforui = 'f',
                                 stops = '{' + str(row.stops) + '}', report_time = Time
                                 )

def StoreStopTimes_orig(stop_times):
    table_name = conf.conf['agency'] + "_stop_times_orig"
    # create table in database
    c = db.cursor()
    if WriteDB.TableExists(table_name): WriteDB.DropTable(table_name)
    c.execute("CREATE TABLE " + table_name + " (" +  " varchar,".join(list(stop_times)) + " varchar);" )
    
    Total = len(stop_times.index)
    count = 0
    for row in range(stop_times.shape[0]):
        # progress status
        count = count + 1
        if round(count*100/Total) %2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(round(count*100/Total)))
            sys.stdout.flush()
        
        # store data
        c.execute(
                """
                INSERT INTO {stop_times_orig}(
                      {column_names}  
                )
                VALUES(
                    {values}
                )
                """.format(
                    stop_times_orig = table_name,
                    column_names = ",".join(list(stop_times)),
                    values = "'" + "','".join(stop_times.iloc[row].values.tolist()) + "'"
                )
        )
                
def StoreTrips_orig(trips):
    """Store the original GTFS trips table into <agency_trip_orig> table"""
    table_name = conf.conf['agency'] + "_trips_orig"
    # create table in database
    c = db.cursor()
    if WriteDB.TableExists(table_name): WriteDB.DropTable(table_name)
    c.execute("CREATE TABLE " + table_name + " (" +  " varchar,".join(list(trips)) + " varchar);" )

    Total = len(trips.index)
    count = 0
    for row in range(trips.shape[0]):
        # progress status
        count = count + 1
        if round(count*100/Total) %2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(round(count*100/Total)))
            sys.stdout.flush()
        
        # store data
        c.execute(
                """
                INSERT INTO {trips_orig}(
                      {column_names}  
                )
                VALUES(
                    {values}
                )
                """.format(
                    trips_orig = table_name,
                    column_names = ",".join(list(trips)),
                    values = "'" + "','".join(trips.iloc[row].values.tolist()) + "'"
                )
        )
            
def StoreRoutes_orig(routes):
    """Store the original GTFS routes table into <agency_trip_orig> table"""
    table_name = conf.conf['agency'] + "_routes_orig"
    # create table in database
    c = db.cursor()
    if WriteDB.TableExists(table_name): WriteDB.DropTable(table_name)
    c.execute("CREATE TABLE " + table_name + " (" +  " varchar,".join(list(routes)) + " varchar);" )

    Total = len(routes.index)
    count = 0
    for row in range(routes.shape[0]):
        # progress status
        count = count + 1
        if round(count*100/Total) %2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(round(count*100/Total)))
            sys.stdout.flush()
        
        # store data
        c.execute(
                """
                INSERT INTO {routes_orig}(
                      {column_names}  
                )
                VALUES(
                    {values}
                )
                """.format(
                    routes_orig = table_name,
                    column_names = ",".join(list(routes)),
                    values = "'" + "','".join(routes.iloc[row].values.tolist()) + "'"
                )
        )            
    

def latest_GTFS_update(timestamp):
    """find the latest GTFS feed update """
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    try:
        APICall = (URL + "api/gtfs/utils/locate-timestamp" +                                      
                   "?source=" + agency + 
                   "&timestamp=" + repr(timestamp)
                   )
        Response = requests.get(APICall)
    except Exception as e:
        print('API problem: ' + e)
        return
        # response received, check if status is ok
    ResponseParse = Response.json()
    if ResponseParse['header']['status'] != 'OK':
        raise Exception('problem with API call: ' + APICall)
    return ResponseParse['result']

def GetCalendar(request_time):
    """ get and save calendar file from agency"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    try:
        APICall = (URL + "api/gtfs/calendar" +
                   "?gtfs_timestamp=" + repr(request_time) + 
                   "&source=" + agency
                   )
        Response = requests.get(APICall)
    except Exception as e:
        print('API problem: ' + e)
        return
    # response received, check if status is ok
    ResponseParse = Response.json()
    if ResponseParse['header']['status'] != 'OK':
        print('problem with API call: ' + APICall)
        return
    
    calendar = DataFrame(ResponseParse['data'])
    
    # save to db
    postgres_engine = sqlalchemy.create_engine('postgresql+psycopg2://' + 
                                  conf.conf['db']['user'] + 
                                  ':' + conf.conf['db']['password'] + 
                                  '@' + conf.conf['db']['host'] +
                                  '/' + conf.conf['db']['name'] 
                                  )
    table_name = conf.conf['agency'] + "_calendar"
    if WriteDB.TableExists(table_name): WriteDB.DropTable(table_name)
    calendar.to_sql(table_name, postgres_engine, index = False)
    return

def find_exact_GTFS_timestamp(request_time):
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    try:
        APICall = (URL + "api/gtfs/utils/locate-timestamp" +
                   "?timestamp=" + repr(request_time) + 
                   "&source=" + agency
                   )
        Response = requests.get(APICall)
    except Exception as e:
        print('API problem: ' + e)
        return
    # response received, check if status is ok
    ResponseParse = Response.json()
    if ResponseParse['header']['status'] != 'OK':
        raise Exception('problem with API call: ' + APICall)    
    return(ResponseParse['result'])
    
    