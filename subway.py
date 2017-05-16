# call this file to grab subway locations
from subway_api import get_incoming_trains
from vehicle import Vehicle
from fleet import Fleet
from time import sleep
import threading

# create the fleet object 
fleet = Fleet()

# seed the script with trains from one station
updates = get_incoming_trains('Don Mills Station')
fleet.take_updates(updates)


print fleet.vehicles




