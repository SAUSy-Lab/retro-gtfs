# retro-gtfs

[TOC]

## Overview

This branch of Retro-GTFS application is designed to process real-time transit data from an archived [GTFS-Realtime](https://developers.google.com/transit/gtfs-realtime/) data set into a "retrospective" or "retroactive" GTFS package. Schedule-based GTFS data describes how transit is expected to operate. This produces GTFS that describes how it *did* operate. The output is not useful for routing actual people on a network, but can be used for a variety of analytical purposes such as comparing routing/accessibility outcomes on the schedule-based vs the retrospective GTFS datasets. Measures can be derived showing the differences between the schedule and the actual operations and these could be interpreted as a measure of performance either for the GTFS package (does it accurately describe reality?) or for the agency in question (do they adhere to their schedules?).

In short, the main difference between the main branch and this branch is that the former collects and processes data from the [NextBus API](https://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf) while the later processes data from archived GTFS-Realtime data. An example of an archived database of GTFS-Realtime data can be found [here](TBD).

## What the Program does

- Fetching GTFS and GTFS-Realtime information. (More details coming)
- Estimate stop times using OSRM, projection, and interpolation. This creates a retro-GTFS file for each day (More details coming)
- Aggregating the daily retro-GTFS files into one bundle by either averaging stop times or creating unique `trip_id` for all trips and using `calendar_dates.txt` with `exception_type=1`. (More details coming)

## Using the code

NOTE: the [wiki](https://github.com/SAUSy-Lab/retro-gtfs/wiki) page contains instructions for the main branch. Here are instructions  for this branch.

### Requirements

- Python3

- Python modules described in the [requirements.txt](./requirement.txt) file. You can simply run `pip install -r requirements.txt`

- A [Postgres](https://www.postgresql.org/) database and [PostGIS](https://postgis.net/install/)

- An [OSRM-backend](https://github.com/Project-OSRM/osrm-backend) server, local or otherwise.

- A server of archived GTFS-Realtime data that can be queried through HTTP request. An example of such a server can be found [here](TBD). The API calls are currently hard-coded in the [GetGTFS.py](./GetGTFS.py) and [GetGTFSRT.py](./GetGTFSRT.py) scripts. If you would like to use a server with different API syntaxes, you will need to modify [GetGTFS.py](./GetGTFS.py) and [GetGTFSRT.py](./GetGTFSRT.py) scripts in lines that look like:

  ```python
  ​```
  APICall = (URL + "api/gtfs/utils/locate-timestamp" +                                   
            "?source=" + agency + 
            "&timestamp=" + repr(timestamp)
            )
  ​```
  ```

  If you would like to access our data or need help setting up the server, please feel free to [contact us](#Contact us).

### Configurations

Change the file name of [sample conf.py](./sample conf.py) into `conf.py`, then go through the `conf.py` file and save information for your Postgres database, OSRM server, and API URL.

### Run

`python main.py`

Output: `./output/individuals` would contain daily retro-GTFS files, `./output/aggregated` would contain aggregated retro-GTFS bundle.

## Contact us

- Minh Pham: minhpham@usf.edu
- Sean Barbeau: barbeau@cutr.usf.edu


## Related projects

Related projects by other people:
* https://github.com/WorldBank-Transport/Transitime
* https://trid.trb.org/view.aspx?id=1394074 (does anyone have a link to the actual paper?)
