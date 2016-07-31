# CONFIGURATION FILE
# set the parameters unique to your setup below

conf = {
	# database connnection
	'db':
		{
			'host':'localhost',
			'name':'',
			'user':'postgres',
			'password':''
		},
	# agency tag for nextbus API
	'agency':'ttc',
	# Where is the ORSM server? 
	'OSRMserver':{
		'url':'http://???/match/v1/transit/',
		'timeout':10
	}
}
