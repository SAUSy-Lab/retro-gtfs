# custom shapely geometry functions
from shapely.geometry import Point, LineString, MultiLineString
from math import sqrt

def cut(lines, distance):
	"""Cuts a MultiLineString into two MultiLineStrings at a distance from 
		the starting point, returns a tuple."""
	assert distance >= 0
	assert lines.__class__.__name__ == 'MultiLineString'
	if distance <= 0:
		return ( MultiLineString(), lines )
	elif distance >= lines.length:
		return ( lines, MultiLineString() )
	# convert the multi-lines into a list of lines
	lines_list = [ line for line in lines ]
	cum_dist = 0
	lines_so_far = []
	for li, line in enumerate(lines):
		coords = list(line.coords)
		# iterate over the points
		for ci in range(1,len(coords)):
			# assign from tuples
			x1,y1 = coords[ci-1]
			x2,y2 = coords[ci]
			# add the length of this segment to the cumulative distance
			cum_dist += sqrt( (x1-x2)**2 + (y1-y2)**2 )
			if cum_dist == distance:
				head_end = MultiLineString( lines_list[:li] + [ LineString(coords[:ci+1]) ] )
				tail_end = MultiLineString( [LineString(coords[ci:])] + lines_list[li+1:] )
				# check that things are working before returning
				assert abs(head_end.length - distance) < 0.001
				assert abs((distance + tail_end.length) - lines.length ) < 0.001
				return (head_end,tail_end)
			if cum_dist > distance:
				# then insert cut point
				cp = lines.interpolate(distance) # cp = "cut point"
				head_end = MultiLineString( 
					lines_list[:li] + [ LineString(coords[:ci] + [(cp.x,cp.y)]) ]
				)
				tail_end = MultiLineString(
					[ LineString([(cp.x,cp.y)] + coords[ci:]) ] + lines_list[li+1:]
				)
				# check that things are working before returning
				assert abs(head_end.length - distance) < 0.001
				assert abs((distance + tail_end.length) - lines.length ) < 0.001
				return (head_end,tail_end)
	
#def cut2(line,distance1,distance2):
#	"""cut a line in two places, returning the middle segment"""
#	if distance1 < distance2:
#		p1,p2 = cut(line,distance1)
#		p2,p3 = cut(p2,distance2-distance1)
#		return p2
#	elif distance2 < distance1:
#		p1,p2 = cut(line,distance2)
#		p2,p3 = cut(p2,distance1-distance2)
#		return p2
#	else:
#		return LineString()
