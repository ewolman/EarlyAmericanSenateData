import sqlite3, pandas as pd, os, re

# block of code to open the most up to date file
# list of 
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


def FillTable(TableName, Data, curs):
    '''Load data from a dataframe to a table, 
    assumes that the columns in the dataframe and the table have the same name'''
    
    i=0
    
    sql = "INSERT INTO " + TableName + " (" + \
           ",".join([c for c in Data.columns]) + \
           ") VALUES (" + ",".join([':' + c for c in Data.columns]) + ");"
    
    for row in Data.to_dict(orient='records'):
        try:
            i+=1
            curs.execute(sql,row)
        except Exception as e:
            print(e)
            print(row)
            print(i)
            return 0
    return 1

def Rebuild(data):
    
    try:

        # Building the database
        conn = sqlite3.connect('data.db')
        curs = conn.cursor()
        curs.execute("PRAGMA foreign_keys=ON;")
        print(pd.read_sql("PRAGMA foreign_keys;", conn))

        curs.execute('DROP TABLE IF EXISTS tSenator')
        curs.execute("""CREATE TABLE tSenator(
                        id TEXT PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        congress INTEGER NOT NULL CHECK (congress < 17),
                        age INTEGER,
                        postion TEXT NOT NULL, 
                        state TEXT NOT NULL CHECK (length(state) == 2),
                        party TEXT);""")
        
        curs.execute('DROP TABLE IF EXISTS tCommittee')
        curs.execute("""CREATE TABLE tCommittee(
                        committee_id INTEGER PRIMARY KEY,
                        committee TEXT NOT NULL,
                        committee_type TEXT,
                        month TEXT NOT NULL CHECK (month LIKE '___' OR 'n.d.'),
                        day TEXT NOT NULL CHECK (day LIKE '__' OR 'n.d.'),
                        year TEXT NOT NULL CHECK (length(year) == 4),
                        congress INTEGER NOT NULL CHECK (congress < 17),
                        page TEXT NOT NULL CHECK ((length(page) < 3) OR (length(page) == 5)));""")

        curs.execute('DROP TABLE IF EXISTS tVotes')
        curs.execute("""CREATE TABLE tVotes(
                        id TEXT REFERENCES tSenator(id),
                        votes INTEGER NOT NULL CHECK (votes < 100),
                        committee_id INTEGER REFERENCES tCommittee(committee_id));""")

        FillTable('tState', tState, curs)
        FillTable('tZip', tZip, curs)
        FillTable('tProd', tProd, curs)
        
    except Exception as err:
        print(err)
        # Revert all changes, quit and return 0
        conn.rollback()
        return 0
    conn.commit()
    conn.close()
    return 1