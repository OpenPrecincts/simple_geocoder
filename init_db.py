import psycopg2

import config

print("initiating DB connection...")
myConnection = psycopg2.connect(host=config.db['hostname'], user=config.db['username'], password=config.db['password'], dbname=config.db['database'])
curr = myConnection.cursor()
print("connected... ")

table_name = input("Enter table name: ")

query = 'create table {} ( id serial PRIMARY KEY, is_geocoded bool NOT NULL, voterbase_id VARCHAR (100) NOT NULL,address VARCHAR (355) NOT NULL,state VARCHAR (2) NOT NULL,zipcode integer not null,vb_vf_precinct_id VARCHAR (100) NOT NULL,vb_vf_precinct_name	VARCHAR (100) NOT NULL,vb_vf_national_precinct_code VARCHAR (100) NOT NULL,voter_status VARCHAR (20) NOT NULL,vf_reg_cd VARCHAR (100) NOT NULL,vf_reg_hd VARCHAR (100) NOT NULL,vf_reg_sd VARCHAR (100) NOT NULL,geocoded_address VARCHAR (355),is_match VARCHAR (100),is_exact VARCHAR (100),returned_address VARCHAR (355),coordinates VARCHAR (355),tiger_line integer,side VARCHAR (1),state_fips integer,county_fips integer,tract VARCHAR (355),block VARCHAR (355),longitude float8,latitude float8);'.format(table_name)
print("Executing creation query")
curr.execute(query)

print("Setting is_geocoded default to false")
query = "ALTER TABLE {} ALTER COLUMN is_geocoded SET DEFAULT FALSE;".format(table_name)
curr.execute(query)

myConnection.commit()
curr.close()
print("closing connection...")
myConnection.close()