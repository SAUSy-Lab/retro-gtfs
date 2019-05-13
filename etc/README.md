## Various other files

`create_agency_tables.sql` is required to create the necessary database tables before running the script. You will probably want to edit this file to set a table name prefix specific to your agency. This is required if you plan to analyze more than one agency. 

`pull_data.sql` pulls data from those tables into a set of GTFS-formatted CSV files. Edit this file to set the table name prefix for you project.

`ttc.lua` is an OSRM profile modified to allow access to streetcar tracks. Consider this as a starting point; a more general transit profile is needed and this has not been extensively in other cities than Toronto.
