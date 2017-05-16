# define a graph-like network of lines, maybe?
class Network():
	def __init__():
		pass


class Line():
	"""A subway line for now"""
	def __init__(self,lineID,stop_list,directions):
		self.id = lineID
		# ordered list of stops
		self.stops = stop_list
		# geographic direction of the ordered list
		self.dirL,self.dirR = directions

	def next(self,this_stop_name,heading):
		"""return the name of the next stop from this one on the given heading"""
		# validate inputs
		if this_stop_name not in self.stops:
			raise ValueError('invalid name given')
		# get the position of the current stop
		i = self.stops.index(this_stop_name)
		# shift according to direction
		if heading == self.dirR:
			i += 1
		elif heading == self.dirL:
			i -= 1
		# check that we haven't overshot
		# TODO make this go back and forth?
		if i < 0 or i > len(self.stops)-1:	
			raise KeyError('no stop '+heading+' of '+this_stop_name)
		return self.stops[i]

four = Line( 'SHEP',[ 'Sheppard-Yonge Station', 'Bayview Station', 'Bessarion Station', 'Leslie Station', 'Don Mills Station' ],['West','East'] )



class Stop():
	"""A transit stop/station"""
	def __init__(self,name):
		self.name = name
		self.id = None # later
		self.next = None
		self.prev = None






#			1:{
#				'stations':[ 'Sheppard West Station', 'Wilson Station', 'Yorkdale Station', 'Lawrence West Station', 'Glencairn Station', 'Eglinton West Station', 'St Clair West Station', 'Dupont Station', 'Spadina Station', 'St George Station',	'Museum Station', "Queen's Park Station", 'St Patrick Station', 'Osgoode Station', 'St Andrew Station', 'Union Station', 'King Station', 'Queen Station', 'Dundas Station', 'College Station', 'Wellesley Station', 'Bloor-Yonge Station', 'Rosedale Station', 'Summerhill Station', 'St Clair Station', 'Davisville Station', 'Eglinton Station', 'Lawrence Station', 'York Mills Station', 'Sheppard-Yonge Station', 'North York Centre Station', 'Finch Station' ]
#			},
#			2:{
#				'stations':[ 'Kipling Station', 'Islington Station', 'Royal York Station', 'Old Mill Station', 'Jane Station', 'Runnymede Station', 'High Park Station', 'Keele Station', 'Dundas West Station', 'Lansdowne Station', 'Dufferin Station', 'Ossington Station', 'Christie Station', 'Bathurst Station', 'Spadina Station', 'St George Station', 'Bay Station', 'Bloor-Yonge Station', 'Sherbourne Station', 'Castle Frank Station', 'Broadview Station', 'Chester Station', 'Pape Station', 'Donlands Station', 'Greenwood Station', 'Coxwell Station', 'Woodbine Station', 'Main Street Station', 'Victoria Park Station', 'Warden Station', 'Kennedy Station' ]
#			}, 
