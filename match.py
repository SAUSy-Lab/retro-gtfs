# testing the OSRM server
import psycopg2	# DB interaction
import json			# JSON parsing
import map_api		# map matching function

# DB connection
conn_string = "host='localhost' dbname='misc' user='nate' password='mink'"
conn = psycopg2.connect(conn_string)
c = conn.cursor()

# create an var for outputting feature geometry
out = {'type':'FeatureCollection','features':[]}
inp = {'type':'FeatureCollection','features':[]}

# get a short list of tracks to test
c.execute("""
	SELECT trip_id, count(*)
	FROM nb_vehicles
	GROUP BY trip_id
	LIMIT 30
""")
# iterate over trips
for (trip_id,count) in c.fetchall():
	j = map_api.map_match(trip_id)
	print trip_id, j['matchings'][0]['confidence']

c.close()
