# contains shapely geometry functions
from shapely.geometry import Point, LineString
from math import sqrt

def cut(line, distance):
	"""Cuts a line into two at a distance from its starting point,
		returns a tuple of the resulting segments"""
	if distance == 0:
		return ( LineString(), line )
	elif distance >= line.length:
		return ( line, LineString() )
	cum_dist = 0
	coords = list(line.coords)
	# get the first point
	p1 = coords[0]
	# iterate over the rest
	for i, p2 in enumerate(coords):
		# assign from tuples
		x1,y1 = p1
		x2,y2 = p2
		# add the length of this segment to the cumulative distance
		cum_dist += sqrt( (x1-x2)**2 + (y1-y2)**2 )
		# assign for next iteration
		p1 = p2
		if cum_dist == distance:
			l1 = LineString(coords[:i+1])	# first section
			l2 = LineString(coords[i:]) 	# second section
			assert l1.length - distance < 0.001
			return (l1,l2)
		if cum_dist > distance:
			# then insert cut point
			cut_point = line.interpolate(distance)
			l1 = LineString(coords[:i] + [(cut_point.x,cut_point.y)])	# first section 
			l2 = LineString([(cut_point.x,cut_point.y)] + coords[i:])	# second section
			assert l1.length - distance < 0.001
			return (l1,l2)
	
def cut2(line,distance1,distance2):
	"""cut a line in two places, returning the middle segment"""
	if distance1 < distance2:
		p1,p2 = cut(line,distance1)
		p2,p3 = cut(p2,distance2-distance1)
		return p2
	elif distance2 < distance1:
		p1,p2 = cut(line,distance2)
		p2,p3 = cut(p2,distance1-distance2)
		return p2
	else:
		return LineString()
