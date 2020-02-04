# simple_geocoder

## Overview
simple_geocoder geocodes voterrolls at scale with a focus on throughput. In addition, simple_geocoder is apsirationally *simple* in the sense that every line of code is intended to be relavent and easy to understand. I hope that even if the scripts are not immediately useful, they will be simple enough to serve as a useful starting point for your project.

simple_geocoder works in two distinct phases. 1) Clean data and upload it to a PostgreSQL database instance. 2) Pull rows that have not been geocoded, geocoding them, and update the corresponding row in the database. 

## Database 
I used a PostgreSQL database instance hosted with Amazon's Relational Database Service (Amazon RDS). You can follow a tutorial on how to set one up [here](https://aws.amazon.com/getting-started/tutorials/create-connect-postgresql-db/). Of course you could also run a [local database instance instead if you prefer.](https://www.codementor.io/@engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb)

These scripts rely on a single table named 'geo_tbl'. It has the following columns 'id', 'is_geocoded', 'voterbase_id', 'address', 'state', 'zipcode', 'vb_vf_precinct_id', 'vb_vf_precinct_name', 'vb_vf_national_precinct_code', 'voter_status', 'vf_reg_cd', 'vf_reg_hd', 'vf_reg_sd', 'geocoded_address', 'is_match', 'is_exact', 'returned_address', 'coordinates', 'tiger_line', 'side', 'state_fips', 'county_fips', 'tract', 'block', 'longitude', 'latitude'. Your schema is likely to vary based on the columns names of your voterroll. If your column names are different, be sure to adjust the python script accordingly.

The database can be accessed programmatically with Python using the [psycopg2 library](https://pypi.org/project/psycopg2/). Alternatively, one might use an ‘administration and development platform for PostgreSQL’ such as [pgAdmin](https://www.pgadmin.org/). PgAdin is more visual and can be good for exploration and simple queries.

## Geocoding Scripts

### Phase 1: fill_db.py
Upload raw voterroll data to a PostgreSQL database instance

The *fill_db.py* script cleans raw voterroll data and uploads it into the database. The script leverages Python’s generator functionality to limit memory usage while still allowing massive files to be uploaded (a CSV with ~250 million rows in our case). This script skips rows that cannot be geocoded for whatever reason e.g. private address, missing a zip code etc. Additionally, the script performs string manipulation on certain entries (e.g. escaping single quotes) in order to make the row consitent with PostgreSQL's specifications. Such modifications are specific to our dataset so if one is attempting to geocode a different dataset they will likely need to make minor modifications tailored to that dataset.

### Phase 2: all_geo.py and states_geo.py
Geocode voterroll data from a database

Once the data is uploaded to the PostgreSQL instance, a geocoding script (all_geo.py or states_geo.py) pulls chunks of 10,000 rows. Then it locally creates batches which are in turn geocoded with the censusbatchgeocoder library, a wrapper on the US Census Geocoder. This script uses the ThreadPoolExecutor to increase throughput. The ThreadPoolExecutor asynchronously dispatches threads which each make an API call to geocode their assigned batch of 25 rows. From my empirical observations I have found that 10,000 row chunks, 25 row batches, and max_workers=50 (for the ThreadPoolExecutor) are good choices for performance.

Notably, without setting *pooling=False* I was running into an issue where the threads from a batch would persist even after the batch had completed. As a result I ran into an upper limit of about 2000 threads on my machine. Setting pooling=False resolved this issue and allowed ThreadPoolExecutor to work as intended. 
