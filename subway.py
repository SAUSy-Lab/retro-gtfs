# call this file to grab subway locations
from subway_api import get_incoming_trains
from time import sleep
import threading, time

# DEFINE THE SUBWAYS 
one = {
	'id':1,
	'stations':[ 'Sheppard West Station', 'Wilson Station', 'Yorkdale Station', 'Lawrence West Station', 'Glencairn Station', 'Eglinton West Station', 'St Clair West Station', 'Dupont Station', 'Spadina Station', 'St George Station',	'Museum Station', "Queen's Park Station", 'St Patrick Station', 'Osgoode Station', 'St Andrew Station', 'Union Station', 'King Station', 'Queen Station', 'Dundas Station', 'College Station', 'Wellesley Station', 'Bloor-Yonge Station', 'Rosedale Station', 'Summerhill Station', 'St Clair Station', 'Davisville Station', 'Eglinton Station', 'Lawrence Station', 'York Mills Station', 'Sheppard-Yonge Station', 'North York Centre Station', 'Finch Station' ]
}
two = {
	'id':2,
	'stations':[ 'Kipling Station', 'Islington Station', 'Royal York Station', 'Old Mill Station', 'Jane Station', 'Runnymede Station', 'High Park Station', 'Keele Station', 'Dundas West Station', 'Lansdowne Station', 'Dufferin Station', 'Ossington Station', 'Christie Station', 'Bathurst Station', 'Spadina Station', 'St George Station', 'Bay Station', 'Bloor-Yonge Station', 'Sherbourne Station', 'Castle Frank Station', 'Broadview Station', 'Chester Station', 'Pape Station', 'Donlands Station', 'Greenwood Station', 'Coxwell Station', 'Woodbine Station', 'Main Street Station', 'Victoria Park Station', 'Warden Station', 'Kennedy Station' ]
}
four = {
	'id':4,
	'dir':['West','East'],
	'stations':[ 'Sheppard-Yonge Station', 'Bayview Station', 'Bessarion Station', 'Leslie Station', 'Don Mills Station' ]
}


fleet = {} 			# operating vehicles in the fleet keyed by id
# 
for stationName in four['stations']:
	print stationName
	# get the trains coming in to station
	trains = get_incoming_trains(stationName)
	# 	
	for train in trains:
		if train['dir'] in ['North','South']:
			continue
		if train['id'] not in fleet:
			# store info for first time
			fleet[train['id']] = {
				'next': stationName,
				'timeAway': train['timeAway'],
				'dir': train['dir']
			}
		else:
			# update info if train is closer to this station than another
			if fleet[train['id']]['timeAway'] > train['timeAway']:
				fleet[train['id']] = {
					'next':stationName,
					'timeAway':train['timeAway'],
					'dir': train['dir']
				}
				
print fleet

class fleet():
	"""Hold references to all active vehicles, manage means of accessing them."""
	def __init__(self):
		# this should hold a list of references to vehicle objects
		self.vehicles = {}
	
	def add_vehicle(self,vehicle):
		pass
		
	def del_vehicle(self,vid):
		pass
		


	




