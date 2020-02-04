import concurrent
import datetime
import time
import traceback
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor

import censusbatchgeocoder
import pandas as pd
import psycopg2

import config

def gen_update_q(d):
    if d['is_match'] == 'Match':
        return "UPDATE {} SET is_geocoded = {}, geocoded_address = '{}', is_match = '{}', is_exact = '{}', returned_address = '{}', coordinates = '{}', tiger_line = {}, side= '{}', state_fips= '{}', county_fips= '{}', tract= '{}', block= '{}', longitude= '{}', latitude= '{}' WHERE id = {}".format(
                table,
                True, 
                d.get('geocoded_address',''), 
                d.get('is_match',''), 
                d.get('is_exact',''), 
                (d.get('returned_address','')).replace("'",r"''"), 
                d.get('coordinates',''), 
                d.get('tiger_line','NULL') if len(d['tiger_line']) > 0 else 'NULL',
                d.get('side',''), 
                d.get('state_fips',''),
                d.get('county_fips',''),
                d.get('tract',''),
                d.get('block',''),
                d.get('longitude',''), 
                d.get('latitude',''), 
                d.get('id',''))
    else:
        return "UPDATE {} SET is_geocoded = {}, geocoded_address = '{}', is_match = '{}' WHERE id = {}".format(
                table,
                True, 
                d.get('geocoded_address',''), 
                d.get('is_match',''), 
                d.get('id',''))

def geocode_batch(start_idx, batch_size=batch_size):
    try:
        end_idx = start_idx + batch_size
        start_time = time.time()
        batch_df = df_raw.iloc[start_idx:end_idx][:]
        # Put batch through census API pooling is set to false because we are handling the pooling ourselves in this script
        result_dicts = censusbatchgeocoder.geocode(batch_df.to_dict('records'), pooling=False)
        update_query = ';'.join([gen_update_q(d) for d in result_dicts])
        curr.execute(update_query)
        print('thread finished for batch {} size: {} in {} seconds'.format((start_idx,end_idx), batch_size, time.time() - start_time))
        return True
    except:
        traceback.print_exc(file=sys.stdout)
        return False

warnings.filterwarnings("ignore")
print("initiating DB connection...")
myConnection = psycopg2.connect(host=config.db['hostname'], user=config.db['username'], password=config.db['password'], dbname=config.db['database'])
curr = myConnection.cursor()
print("connected... ")
thereExistRowToGeocode = True
n_coded = 0
db_chunk_idx = 0
batch_size = 25
db_chunk_size = 10000
enter the table name for the database
table = 'geo_tbl'
print("ENTERING MAIN LOOP -  db chunk size: {}".format(db_chunk_size))
try:
    print("Starting the geocoding script - All states remaining")
    start = time.time()
    while thereExistRowToGeocode:
        chunk_start = time.time()
        query = "SELECT id, address, state, zipcode FROM {} WHERE NOT is_geocoded LIMIT {};".format(table, db_chunk_size)
        print("Executing Query: ", query)
        curr.execute(query)
        df_raw = pd.DataFrame(curr.fetchall(), columns=['id', 'address', 'state', 'zipcode'])
        n_entries_chunk,_  = df_raw.shape
        if n_entries_chunk == 0:
            thereExistRowToGeocode = False
            break
        df_raw = df_raw.set_index('id')
        df_raw['city'] = ''

        indices = [idx for idx in range(0, n_entries_chunk, batch_size)]
        retry_set = set()
        print("starting threadpool for chunk[{}]".format(db_chunk_idx))
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_idx = {executor.submit(geocode_batch, idx): idx for idx in indices}
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    success = future.result()
                    if not success:
                        retry_set.add(idx)
                except Exception as exc:
                    print("error for idx: ", idx, " execption: ", exc)
                    retry_set.add(idx)
            print("Before individual retries | need to retry for the following indices: ", retry_set)
            retry_entries = set()
            for idx in retry_set:
                future_to_idx = {executor.submit(geocode_batch, i, batch_size=1): i for i in range(idx, idx+batch_size)}
                for future in concurrent.futures.as_completed(future_to_idx):
                    i = future_to_idx[future]
                    try:
                        success = future.result()
                        if not success:
                            retry_entries.add(idx)
                    except Exception as exc:
                        print("error for idx: ", i, " execption: ", exc)
                        retry_entries.add(i)
            print("After individual retries | was unable to geocode these entries: ", retry_entries)
        n_coded += n_entries_chunk
        print("Threads done for db chunk[{}], geocoded {} entries in {} seconds".format(db_chunk_idx, n_entries_chunk, time.time() - chunk_start))
        print("Commiting Transaction")
        myConnection.commit()
        seconds = time.time() - start
        print("Geocoded {} entries in {} seconds".format(n_coded, seconds))
        db_chunk_idx += db_chunk_size
except Exception as err:
    print("Exception while geocoding:  {}".format(err))
    traceback.print_exc(file='traceback_all_geo')

curr.close()
print("closing connection...")
myConnection.close()
