import csv
import psycopg2
import time

import pandas as pd

import config

print("initiating DB connection...")
myConnection = psycopg2.connect(host=config.db['hostname'], user=config.db['username'], password=config.db['password'], dbname=config.db['database'])
curr = myConnection.cursor()
print("connected... ")

table_name = 'geo_tbl'
state_abbreviation = 'NJ'

querry = "SELECT * FROM {} LIMIT 0;".format(table_name)
print("Executing Query")
curr.execute(querry)
colnames = [desc[0] for desc in curr.description]
print(colnames)

querry = "SELECT * FROM {} WHERE state = '{}' ORDER BY id ASC;".format(table_name, state_abbreviation)
print("Executing Query")
start = time.time()
curr.execute(querry)

rows = curr.fetchall()
df = pd.DataFrame(rows, columns=colnames)
df = df.set_index('id')

print(df.head())
df.to_csv('geocoded_{}.csv'.format(state_abbreviation))

myConnection.commit()
curr.close()
print("closing connection...")
myConnection.close()
