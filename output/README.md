## Output directories
This directory contains empty CSV files which will be overwritten by PostgreSQL when the data is pulled out of the database and into GTFS format. For multiple agencies, you will likely want to copy this folder for each agency. To finish the GTFS data, you'll need to compress all the cSV files in ne folder into a `.zip` archive.

Note that PostgreSQL needs permission to access these files. If you're having any issues, check the file permissions where you're trying to write the output.
