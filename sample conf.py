# CONFIGURATION FILE
# set the parameters unique to your setup below
# then rename this file to "conf.py"

# for handling projections
from functools import partial
import pyproj

# this must be a meter-based projection appropriate for your region
# UTM projections are suggested. 
PROJECT_EPSG = 26759 # look up on https://www.epsg-registry.org/

conf = {
	# PostgreSQL database connnection
	'db':
		{
			'host':'localhost',
			'name':'db1', # database name
			'user':'username',
			'password':'password',
			'tables':{
				# these are table names used directly in queries. You can simply change the prefix of agency name (in this case, 'psta')
				'trips':'psta_trips',
				'stops':'psta_stops',
				'stop_times':'psta_stop_times',
				'directions':'psta_directions'
			}
		},
	# agency name or accronym
	'agency':'psta',
	# Where is the ORSM server? Give the root url
	'OSRMserver':{
		'url':'http://localhost:5002',
		'timeout':10 # seconds
	},
	'min_OSRM_match_quality':0.3,
	# function for projecting from lat-lon for shapely
	# http://toblerity.org/shapely/manual.html#other-transformations
	# http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/
	'projection':partial(
		 pyproj.transform,
		 pyproj.Proj('+init=EPSG:4326'),
		 pyproj.Proj('+init=EPSG:'+str(PROJECT_EPSG))
	),
	'localEPSG':PROJECT_EPSG,
	# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
	# This must be an unabreviated timezone name to allow postgresql to account 
	# for daylight savings time.
	'timezone': 'America/Toronto',
	# distance threshold for stop matching in meters; stops more than this far 
	# away from the matched route will not be included
	'stop_dist':30,
	# estimated GPS error radius in meters
	# this applies to all points and effects map-matching
	# higher values include more potential matches but take longer to process
	'error_radius':20,
    'API_URL': "http://example.com",
	# This is the URL where you can send queries to get archived data of GTFS and GTFS-Realtime.
		# This is the URL where you can send queries to get archived data of GTFS and GTFS-Realtime.
	'aggregate_method': 'average',
	# method to aggregate individual retro-GTFS files. 'average' means taking the mean of stop_times. 'combine' mean creating a unique trip_id for trips in each day and using calendar_dates with exception_type = 1
	'n_processes': 7
	# number of parallel processes. Using too many may increase the processing time from OSRM and the program will time out OSRM, resulting in non-matching trips that will not be saved in the result.
}
