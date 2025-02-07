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

# committee types
cmte_types = pd.read_excel('data/tCommittee_types.xlsx', sheet_name='tCommittee')
cmte_types = cmte_types[['committee_id', 'type']]
cmte_types.columns = ['committee_id', 'committee_type']

conn = sqlite3.connect('database.db')
curs = conn.cursor() 
cmtes = pd.read_sql('SELECT * FROM tCommittee;', conn)

try:
    if len(cmtes) == len(cmte_types):
        print('same length')
        r = 0 
        for row in cmte_types.to_dict(orient = 'records'):
            sql = "SELECT * FROM tCommittee WHERE committee_id = ?;"
            update_sql = "UPDATE tCommittee SET committee_type = ? WHERE committee_id = ?;"
            #print(row)
            check = pd.read_sql(sql, conn, params = [row['committee_id']])
            #print('we checked')
            if len(check) == 1: #committee in db
             #   print('trying to add to db')
                curs.execute(update_sql, (row['committee_type'], str(row['committee_id'])))
                #if r < 5:
              #  print('added to db')
               # r +=1
            else:
                print('committee_id not in db')
        conn.commit()
except Exception as err:
    print(row)
    print('the cmte types sheet and the database do not agree')
    conn.rollback()


print('Generating spreadsheets ...')
# create spreadsheets of views for easy use
# function to add full name col
def add_full_name_col(df, st = True):
    df['middle_name'] = df['middle_name'].fillna('')
    if st:
        col = (df['first_name'] + ' ' + df['middle_name'] + ' ' + 
                df['last_name'] + ' (' + df['state'] + ')').str.replace('  ',' ')
    else:
        col = (df['first_name'] + ' ' + df['middle_name'] + ' ' + df['last_name']).str.replace('  ',' ')
    return col

votes = pd.read_sql('SELECT * FROM vIndividualVotes;', conn)
votes['full_name_st'] = add_full_name_col(votes)
votes.to_csv('useful_tables/IndividualVotesByCmte.csv', index = False)

cmtes = pd.read_sql('SELECT * FROM tCommittee;', conn)
cmtes.to_csv('useful_tables/Committees.csv', index = False)

cmte_count = pd.read_sql('''SELECT congress, COUNT(DISTINCT committee_id) as NumCmtes 
                                FROM tCommittee GROUP BY congress;''', conn)
cmte_count.to_csv('useful_tables/CommitteeCount.csv', index = False)

all_time = pd.read_sql('SELECT * FROM vTotalVotesAllTime;', conn)
all_time['VotesPerCmte'] = all_time['VotesPerCmte'].round(2)
all_time['VotesPerCongress'] = all_time['VotesPerCongress'].round(2)
all_time['full_name'] = add_full_name_col(all_time, st = False)
# add vote totals by committee type
votes_by_type_at = votes.groupby(by = ['senator_id','committee_type'], as_index = False).agg({'votes':'sum'})
votes_by_type_at = votes_by_type_at.pivot(index='senator_id',columns='committee_type', values='votes')
all_time = all_time.join(votes_by_type_at, how = 'inner', on = 'senator_id')
all_time.to_csv('useful_tables/TotalVotesAllTime.csv', index = False)


congress = pd.read_sql('SELECT * FROM vTotalVotesByCongress;', conn)
congress['full_name_st'] = add_full_name_col(congress)
congress['VotesPerCmte'] = congress['VotesPerCmte'].round(2)
# add vote totals by committee type
votes_by_type_c = votes.groupby(by = ['senator_congress_id','committee_type'], as_index = False).agg({'votes':'sum'})
votes_by_type_c = votes_by_type_c.pivot(index='senator_congress_id',columns='committee_type', values='votes')
congress = congress.join(votes_by_type_c, how = 'inner', on = 'senator_congress_id')
congress.to_csv('useful_tables/TotalVotesByCongress.csv', index = False)
# more than 3 congresses (full term)
count_congress = congress.groupby(by = 'senator_id', as_index=False).agg({'congress':'nunique'})
full_term = congress[congress['senator_id'].isin(count_congress[count_congress['congress'] >= 3]['senator_id'])]
full_term.to_csv('useful_tables/TotalVotesByCongress_FullTerm.csv', index = False)


party_votes = pd.read_sql('SELECT * FROM vVotesByParty;', conn)
party_votes.to_csv('useful_tables/VotesByParty.csv', index = False)

# votes per year per party
all_t = votes[votes['date'] != 'n.d.']
all_t['year'] = [i[0] for i in all_t['date'].str.split('-')] 
party_year_votes = all_t.groupby(by = ['year','party'],as_index=False).agg({'votes':'sum', 'committee_id':'nunique'})
party_year_votes['VotesPerCmte'] = (party_year_votes['votes']/party_year_votes['committee_id']).round(2)

# get vote share
totals = party_year_votes.groupby(by = 'year', as_index=False).sum('votes')
shares = []
for year in totals['year']:
    total = totals.loc[totals['year'] == year]['votes'].values[0]
    #print(total)
    that_year = party_year_votes[party_year_votes['year'] == year]
    #print(that_year)
    shares += [round(party/total*100, 2) for party in that_year['votes']]
party_year_votes['VoteShare (%)'] = shares

party_year_votes.columns = ['year','party','NumVotes', 'NumCommittees', 'VotesPerCmte', 'VoteShare']
party_year_votes.to_csv('useful_tables/VotesByPartyByYear.csv', index = False)

conn.close()