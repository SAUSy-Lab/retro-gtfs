# CONFIGURATION FILE
# set the parameters unique to your setup below
# then rename this file to "conf.py"

conf = {
	# PostgreSQL database connnection
	'db':
		{
			'host':'',
			'name':'',
			'user':'',
			'password':''
		},
	# agency tag for the Nextbus API
	'agency':'',
	# Where is the ORSM server? 
	'OSRMserver':{
		'url':'http://???',
		'timeout':10
	},
	# function for projecting from lat-lon for shapely
	# http://toblerity.org/shapely/manual.html#other-transformations
	# http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/
	'projection':partial(
		 pyproj.transform,
		 pyproj.Proj('+init=EPSG:4326'),
		 pyproj.Proj('+init=EPSG:26917')
	),
	# distance threshold for stop matching in meters
	'stop_dist':30
}
