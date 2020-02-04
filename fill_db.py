import csv
import time
import traceback

import psycopg2

import config

def isZip(arg):
    s = arg.strip()
    if len(s) == 0:
        return False
    else:
        try:
            i = int(s)
            return True
        except ValueError:
            return False

def stringify(row):
    for i in range(len(row)):
        row[i] = str(row[i]).replace("'", "")
    return str(tuple(row))

start_overall = time.time()
print("initiating DB connection...")
myConnection = psycopg2.connect(host=config.db['hostname'], user=config.db['username'], password=config.db['password'], dbname=config.db['database'])
curr = myConnection.cursor()
print("connected... ")

# TODO: enter the table name for the database
table_name = 'geo_tbl'
# TODO: enter the file path for the csv to be uploaded
file_path = ''

retry_set = set()
batch_size = 10000

with open(file_path) as f:
    n_entries = sum(1 for line in f)

with open(relative_path) as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    next(readCSV) 
    args_gen = (stringify(row) for row in readCSV if 'PRIVATE' not in row[1] and isZip(row[4]))

    counter = 0
    for idx in range(0,n_entries, batch_size):
        counter+=1

        #create the args_str for this batch
        isFirstRow = True
        row_count = 1
        while row_count < min(batch_size, n_entries):
            row = next(args_gen)
            if isFirstRow:
                args_str = row
                isFirstRow = False
            else:
                args_str += ',{}'.format(row)
            row_count += 1
        
        # insert the rows contained in args_str into the database
        querry = "INSERT INTO {} (voterbase_id, address, state, vf_reg_cd, zipcode, vf_reg_hd, vf_reg_sd, vb_vf_precinct_id, vb_vf_precinct_name, vb_vf_national_precinct_code, voter_status) VALUES {};".format(table_name, args_str)
        print("Executing Insert Query[{}]".format(counter))
        start = time.time()
        try:
            curr.execute(querry)
        except:
            traceback.print_exc(file='traceback_'+counter)
            retry_set.add(counter)
            with open("retry.txt", "a") as myfile:
                myfile.write(str(counter) + ",")
            
        myConnection.commit()
        print("Querry[",counter,"] executed in ", time.time()-start, " seconds")
        else:
            print("skipping idx: ", idx)

print("retry set: ", retry_set)

curr.execute("select count(*) from {}".format(table_name))
print("There are now: {} entries in {}".format(curr.fetchone(), table_name))
curr.close()
print("closing connection...")
myConnection.close()
print("Loaded {} entries in {} seconds".format(n_entries, time.time() - start_overall))
