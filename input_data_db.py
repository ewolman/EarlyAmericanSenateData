import sqlite3, pandas as pd, os, numpy as np, re
import build_db

# delete db if exists
if os.path.exists('data.db'):
    os.remove('data.db')

# Create the database
build_db.Rebuild()


# Find the latest file in merged_data
csvs = os.listdir('Merged_Data')
num = re.compile(r'(?<=_)(\d{1,2}[.csv])')
ns = []
for c in csvs:
    if len(re.findall(num, c)) >0:
        ns += re.findall(num, c)
    else:
        ns += ['0.']
# open highest number
ns = [int(i[:-1]) for i in ns]
file = csvs[ns.index(max(ns))]
data = pd.read_csv('Merged_Data/' + file)

conn = sqlite3.connect('data.db')
curs = conn.cursor()        
build_db.LoadVoteData(data, conn, curs)

conn.close()