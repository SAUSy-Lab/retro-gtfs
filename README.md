# retro-gtfs

## Overview
This Python application is designed to collect real-time transit data from the [NextBus API](https://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf) and process it into a "retrospective" or "retroactive" GTFS package. Schedule-based GTFS data describes how transit is expected to operate. This produces GTFS that describes how it *did* operate. The output is not useful for routing actual people on a network, but can be used for a variety of analytical purposes such as comparing routing/accessibility outcomes on the schedule-based vs the retrospective GTFS datasets. Measures can be derived showing the differences between the schedule and the actual operations and these could be interpretted as a measure of performance either for the GTFS package (does it accurately describe reality?) or for the agency in question (do they adhere to their schedules?). 


## Using the code

As for actually using the code, please have a look at the [wiki](https://github.com/SAUSy-Lab/retro-gtfs/wiki), and feel free to [email Nate](mailto:nate.wessel@mail.utoronto.ca) or create an issue if you encounter any problems. 


## Related projects

Related projects by other people:
* https://github.com/WorldBank-Transport/Transitime
* https://trid.trb.org/view.aspx?id=1394074 (does anyone have a link to the actual paper?)
* ...


## Citation

A paper outlining the project and the basic algorithm has been [published in the Journal of Transport Geography](http://www.sciencedirect.com/science/article/pii/S0966692317300388). Any academic use of this code should please cite that work.

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
