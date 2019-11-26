# retro-gtfs

## Overview
This application is designed to collect real-time transit data from the [NextBus API](https://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf) and process it into a "retrospective" or "retroactive" GTFS package. Schedule-based GTFS data describes how transit is expected to operate. This produces GTFS that describes how it *did* operate. The output is not directly useful for routing actual people on a network, but can be used for a variety of analytical purposes such as comparing routing/accessibility outcomes on the schedule-based vs the retrospective GTFS datasets. Measures can be derived showing the differences between the schedule and the actual operations and these could be interpretted as a measure of performance either for the GTFS package (does it accurately describe reality?) or for the agency in question (do they adhere to their schedules?). 

The program was designed to ingest live-realtime data and store it in a PostgreSQL database. The data can be processed either on the fly or after the fact, and with a bit of work you should also be able to massage an outside source of historical AVL data into a suitable format.

The final output of the code is a set of CSV .txt files which conform to the GTFS standard. Specifically, we use the `calendar_dates.txt` file to define a unique service pattern for each day, with its own trip_id's and stop times. No two trips are exactly alike, and so there are no repeating service patterns; each day is unique. The output also includes a `shapes.txt` file, but as there is a unique shape for each trip, the file can become very large and you may wish to ignore it. 


## Using the code
As for actually using the code, please have a look at the [wiki](https://github.com/SAUSy-Lab/retro-gtfs/wiki), and feel free to [email Nate](mailto:nate@natewessel.com) or create an issue if you encounter any problems. 


## Related projects

Related projects by other people:
* https://github.com/CUTR-at-USF/retro-gtfs/tree/GTFS-Realtime (a fork of this code extending it to GTFS-realtime data sources)
* https://github.com/WorldBank-Transport/Transitime
* ...


## Academic Research
This project was developed around work conducted for my dissertation and several academic papers have resulted from that. If you use this code as part of a published work, please cite the following paper ([journal](https://www.sciencedirect.com/science/article/abs/pii/S0966692317300388),[pre-print](http://sausy.ca/wp-content/uploads/2017/11/retro-GTFS-paper.pdf)) outlining the basic methods:

```latex
@Article{Wessel2017,
  author    = {Wessel, Nate and Allen, Jeff and Farber, Steven},
  title     = {Constructing a Routable Retrospective Transit Timetable from a Real-time Vehicle Location Feed and GTFS},
  journal   = {Journal of Transport Geography},
  year      = {2017},
  volume    = {62},
  pages     = {92-97},
  url       = {http://sausy.ca/wp-content/uploads/2017/11/retro-GTFS-paper.pdf}
}
```

You may also be interested in:
* _On the Accuracy of Schedule-Based GTFS for Measuring Accessibility_. [pre-print](https://osf.io/preprints/socarxiv/hzgpd/)
* _The Effect of Route-choice Strategy on Transit Travel Time Estimates_. [pre-print](https://osf.io/preprints/socarxiv/3r4p6/)
* _Accessibility Beyond the Schedule_. [pre-print](https://osf.io/preprints/socarxiv/c4yvx/)

See also, similar methods used by:
* _Advancing accessibility : public transport and urban space_. [PDF](https://dspace.mit.edu/handle/1721.1/111444)
* _Comparing Accessibility in Urban Slums Using Smart Card and Bus GPS Data_. [useless TRB link](https://trid.trb.org/view.aspx?id=1394074)


