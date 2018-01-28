# CONFIGURATION FILE
# set the parameters unique to your setup below
# then rename this file to "conf.py"

# for handling projections
from functools import partial
import pyproj

# this must be a meter-based projection appropriate for your region
# UTM projections are suggested. 
PROJECT_EPSG = 32723

conf = {
	# PostgreSQL database connnection
	'db':
		{
			'host':'localhost',
			'name':'', # database name
			'user':'',
			'password':'',
			'tables':{
				# these are SQL-safe table names used directly in queries
				# if you set up the tables with create_nb_tables.sql, you have likely changed the prefix
				'trips':'prefix_trips',
				'stops':'prefix_stops',
				'stop_times':'prefix_stop_times',
				'directions':'prefix_directions'
			}
		},
	# agency tag for the Nextbus API, which can be found at
	# http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList
	'agency':'ttc',
	# Where is the ORSM server? Give the root url
	'OSRMserver':{
		'url':'http://localhost:5002',
		'timeout':10 # seconds
	},
	# function for projecting from lat-lon for shapely
	# http://toblerity.org/shapely/manual.html#other-transformations
	# http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/
	'projection':partial(
		 pyproj.transform,
		 pyproj.Proj('+init=EPSG:4326'),
		 pyproj.Proj('+init=EPSG:'+str(PROJECT_EPSG))
	),
	'localEPSG':PROJECT_EPSG,
	# timezone is given as the hours offset from Greenwich mean time
	'timezone':-4,
	# distance threshold for stop matching in meters; stops more than this far 
	# away from the matched route will not be included
	'stop_dist':30,
	# estimated GPS error radius in meters
	# this applies to all points and effects map-matching
	# higher values include more potential matches but take longer to process
	'error_radius':20
}
