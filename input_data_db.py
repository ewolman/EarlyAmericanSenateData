import sqlite3, pandas as pd, os, numpy as np, re
import build_db

# delete db if exists
if os.path.exists('database.db'):
    print('it exists')
    os.remove('database.db')

# Create the database
build_db.Rebuild()


# Find the latest file in merged_data
csvs = os.listdir('data/merged_data')
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
data = pd.read_csv('data/merged_data/' + file)
conn = sqlite3.connect('database.db')
curs = conn.cursor()        
build_db.LoadVoteData(data, conn, curs)

print('Generating spreadsheets ...')
# create spreadsheets of views for easy use
conn = sqlite3.connect('database.db')  
votes = pd.read_sql('SELECT * FROM vIndividualVotes;', conn)
votes.to_csv('useful_tables/IndividualVotesByCmte.csv', index = False)

all_time = pd.read_sql('SELECT * FROM vTotalVotesAllTime;', conn)
all_time['VotesPerCmte'] = all_time['VotesPerCmte'].round(2)
all_time['VotesPerCongress'] = all_time['VotesPerCongress'].round(2)
all_time.to_csv('useful_tables/TotalVotesAllTime.csv', index = False)

congress = pd.read_sql('SELECT * FROM vTotalVotesByCongress;', conn)
congress['VotesPerCmte'] = congress['VotesPerCmte'].round(2)
congress.to_csv('useful_tables/TotalVotesByCongress.csv', index = False)

party_votes = pd.read_sql('SELECT * FROM vVotesByParty;', conn)
party_votes.to_csv('useful_tables/VotesByParty.csv', index = False)

# votes per year per party
all_t = votes[votes['date'] != 'n.d.']
all_t['year'] = [i[0] for i in all_t['date'].str.split('-')] 
party_year_votes = all_t.groupby(by = ['year','party'],as_index=False).sum('votes')
party_year_votes = party_year_votes[['year','party','votes']]
party_year_votes.to_csv('useful_tables/VotesByPartyByYear.csv', index = False)

conn.close()