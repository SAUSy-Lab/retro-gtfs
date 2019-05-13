# get all layers
all_layers = list( QgsProject.instance().mapLayers().values() )
# get the layers by name
for layer in all_layers:
    if layer.name() == 'trips.clean_geom':
        clean_geom = layer
    elif layer.name() == 'trips.match_geom':
        match_geom = layer
    elif layer.name() == 'trip_sched_stops':
        trip_sched_stops = layer
    elif layer.name() == 'stop_times_view':
        stop_times_view = layer
    elif layer.name() == 'directions.route_geom':
        default_geom = layer
        
# request trip_id from user
trip_id,whatever = QInputDialog.getText(None, "Input Requested", "Trip_id")

# subset trips table
clean_geom.setSubsetString("trip_id = '"+str(trip_id)+"'")
match_geom.setSubsetString("trip_id = '"+str(trip_id)+"'")

stop_times_view.setSubsetString("trip_id = '"+str(trip_id)+"'")
trip_sched_stops.setSubsetString("trip_id = '"+str(trip_id)+"'")


# report on stuff
print('showing trip_id:',trip_id)
