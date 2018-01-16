# CONFIGURATION FILE
# set the parameters unique to your setup below
# then rename this file to "conf.py"

# for handling projections
from functools import partial
import pyproj

conf = {
	# PostgreSQL database connnection
	'db':
		{
			'host':'localhost',
			'name':'',
			'user':'',
			'password':'',
			'tables':{
				# these are SQL-safe table names used directly in queries
				'trips':'prefix_trips',
				'stops':'prefix_stops',
				'stop_times':'prefix_stop_times',
				'directions':'prefix_directions'
			}
		},
	# agency tag for the Nextbus API
	'agency':'ttc',
	# Where is the ORSM server? Give the root url
	'OSRMserver':{
		'url':'http://201.167.182.17:5002',
		'timeout':10 # seconds
	},
	# function for projecting from lat-lon for shapely
	# http://toblerity.org/shapely/manual.html#other-transformations
	# http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/
	'projection':partial(
		 pyproj.transform,
		 pyproj.Proj('+init=EPSG:4326'),
		 pyproj.Proj('+init=EPSG:32723')
	),
	'localEPSG':32723,
	'timezone':-4,
	# distance threshold for stop matching in meters
	'stop_dist':30,
	# estimated GPS error radius in meters
	# this applies to all points and effects map-matching
	# higher values include more potential matches but take longer to process
	'error_radius':20
}
