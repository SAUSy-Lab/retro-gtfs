# get all layers
all_layers = list( QgsProject.instance().mapLayers().values() )
# get the layers by name
for layer in all_layers:
    if layer.name() == 'trips.clean_geom':
        clean_geom = layer
    elif layer.name() == 'trips.match_geom':
        match_geom = layer
    elif layer.name() == 'direction_stops_view':
        direction_stops_view = layer
    elif layer.name() == 'stop_times_view':
        stop_times_view = layer
    elif layer.name() == 'directions.route_geom':
        default_geom = layer
        
# request trip_id from user
trip_id,whatever = QInputDialog.getText(None, "Input Requested", "Trip_id")

# subset trips table
clean_geom.setSubsetString("trip_id = '"+str(trip_id)+"'")
match_geom.setSubsetString("trip_id = '"+str(trip_id)+"'")
orig_geom.setSubsetString("trip_id = '"+str(trip_id)+"'")

stop_times_view.setSubsetString("trip_id = '"+str(trip_id)+"'")

# get the direction_id from the trips attribute table 
# there should only be one record, but this is an iterator
for record in clean_geom.getFeatures():
    direction_id = record['direction_id']

# subset the directions table
direction_stops_view.setSubsetString("direction_id = '"+str(direction_id)+"'")
default_geom.setSubsetString("direction_id = '"+str(direction_id)+"'")

# report on stuff
print('showing trip_id:',trip_id)
