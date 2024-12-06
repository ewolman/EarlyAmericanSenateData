import sqlite3, pandas as pd, os, re

                 
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

def Rebuild():
    
    try:
        # load in senator 
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
        data['age'] = data['age'].astype('Int32')
        tSenator = data[['senator_id', 'first_name', 'middle_name','last_name', 'birth_year', 'death_year']]        
        
        # Building the database
        conn = sqlite3.connect('database.db')
        curs = conn.cursor()
        curs.execute("PRAGMA foreign_keys=ON;")
        print(pd.read_sql("PRAGMA foreign_keys;", conn))

        curs.execute('DROP TABLE IF EXISTS tSenator')
        curs.execute("""CREATE TABLE tSenator(
                        senator_id TEXT PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        middle_name TEXT,
                        last_name TEXT NOT NULL,
                        birth_year INTEGER,
                        death_year INTEGER);""")

        curs.execute('DROP TABLE IF EXISTS tSenatorByCongress')
        curs.execute("""CREATE TABLE tSenatorByCongress(
                        senator_congress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        senator_id TEXT REFERENCES tSenator(senator_id),
                        congress INTEGER NOT NULL CHECK (congress < 17),
                        age INTEGER, 
                        state TEXT NOT NULL CHECK (length(state) == 2),
                        party TEXT);""")

#                        committee_type TEXT,
        curs.execute('DROP TABLE IF EXISTS tCommittee')
        curs.execute("""CREATE TABLE tCommittee(
                        committee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        committee_name TEXT NOT NULL,
                        month TEXT NOT NULL CHECK ((month LIKE '___') OR (month = 'n.d.')),
                        day TEXT NOT NULL CHECK ((length(day) < 3) OR (day = 'n.d.')),
                        year TEXT NOT NULL CHECK (year LIKE '____' OR 'n.d.'),
                        congress INTEGER NOT NULL CHECK (congress < 17),
                        page TEXT NOT NULL CHECK ((length(page) < 3) OR (length(page) == 5)));""")

        curs.execute('DROP TABLE IF EXISTS tVotes')
        curs.execute("""CREATE TABLE tVotes(
                        senator_id TEXT REFERENCES tSenator(senator_id),
                        senator_congress_id INTEGER REFERENCES tSenatorByCongress(senator_congress_id),
                        votes INTEGER NOT NULL CHECK (votes < 100),
                        committee_id INTEGER REFERENCES tCommittee(committee_id));""")
    
        tSenator = tSenator.drop_duplicates(['senator_id'])
        FillTable('tSenator', tSenator, curs) # Fill senator table

        # Views
        curs.execute('DROP VIEW IF EXISTS vVotesBySenator')
        curs.execute("""CREATE VIEW vVotesBySenator as 
                WITH SenInfo AS
                    (SELECT senator_id, senator_congress_id, first_name, middle_name, last_name, age, congress, state, party
                      FROM(tSenatorByCongress 
                      LEFT JOIN tSenator
                      USING(senator_id))) 
                SELECT first_name, middle_name, last_name, age, congress, state, party, votes, committee_name, senator_id, senator_congress_id, committee_id
                  FROM(SELECT senator_congress_id, votes, committee_name, committee_id
                        FROM tVotes
                        LEFT JOIN tCommittee
                        USING(committee_id))
                        LEFT JOIN SenInfo
                        USING(senator_congress_id);""")
        
        curs.execute('DROP VIEW IF EXISTS vTotalVotesByCongress')
        curs.execute("""CREATE VIEW vTotalVotesByCongress as
                         With VByC as
                            (SELECT senator_id, senator_congress_id, first_name, middle_name, last_name, age, congress, state, party, sum(votes) as TotalVotes, max(votes) as MaxVotes, COUNT(DISTINCT committee_id) as TotalCommittees
                             FROM vVotesBySenator
                             GROUP BY senator_congress_id
                             ORDER BY TotalVotes DESC)
                        SELECT *, (TotalVotes*1.0 / TotalCommittees) as VotesPerCmte FROM VByC;""")

        curs.execute('DROP VIEW IF EXISTS vTotalVotesAllTime')
        curs.execute("""CREATE VIEW vTotalVotesAllTime as
                        WITH VAT as
                        (SELECT senator_id, first_name, middle_name, last_name, sum(votes) as TotalVotes, max(votes) as MaxVotes, COUNT(DISTINCT committee_id) as TotalCommittees
                            FROM vVotesBySenator
                            GROUP BY senator_id
                            ORDER BY TotalVotes DESC)
                        SELECT *, (TotalVotes*1.0 / TotalCommittees) as VotesPerCmte FROM VAT;""")

        curs.execute('DROP VIEW IF EXISTS vVotesByParty')
        curs.execute("""CREATE VIEW vVotesByParty as
                            SELECT congress, party, sum(Votes) as TotalVotes FROM vVotesBySenator 
                            GROUP BY party, congress
                            ORDER BY congress asc""")     
        

    except Exception as err:
        print(err)
        # Revert all changes, quit and return 0
        conn.rollback()
        return 0
    conn.commit()
    conn.close()
    return 1

def GetSenatorCongressID(senator_id, congress, age, state, party, conn, curs):

    sql = """SELECT senator_congress_id FROM tSenatorByCongress
                WHERE senator_id = ?
                AND congress = ?
                AND age = ?
                AND state = ?
                AND party = ?;"""
    
    insert_sql = "INSERT INTO tSenatorByCongress (senator_id, congress, age, state, party)" + \
                 " VALUES (:senator_id, :congress, :age, :state, :party);"
    
    row = {'senator_id': senator_id, 
           'congress': congress, 
           'age': age, 
           'state': state,
           'party': party}

    # select senator_congress_id for given senator and congress
    df = pd.read_sql(sql, conn, params = (senator_id,congress,age,state,party))
    
    # If the senator is not in the database (tSenatorByCongress)
    if len(df) == 0:
        curs.execute(insert_sql, row)
    
        sen_congress_id = pd.read_sql(sql,conn, params = (senator_id,congress,age,state,party))['senator_congress_id'][0]
        
    # Extract sen_congress_id
    else:
        sen_congress_id = df['senator_congress_id'][0]

    return sen_congress_id

def GetCmteID(cmte_name, month, day, year, congress, pg, conn, curs):

#                AND committee_type = ?

    sql = """SELECT committee_id FROM tCommittee
                WHERE committee_name = ?
                AND month = ?
                AND day = ?
                AND year = ?
                AND congress = ?
                AND page = ?;"""
    
    insert_sql = "INSERT INTO tCommittee (committee_name, month, day, year, congress, page)" + \
                 " VALUES (:committee_name, :month, :day, :year, :congress, :page);"
    
    row = {'committee_name': cmte_name, 
           'month': month, 
           'day': day, 
           'year': year,
           'congress': congress,
           'page': pg}

    # Select cmte_id for the name -- nothing if it's not in already
    df = pd.read_sql(sql, conn, params = (cmte_name, month, day, year, congress, pg))
    #print('df:', df)
    # If the committee is not in the database (tCommittee)
    if len(df) == 0:
        #print('no cmte found')
        curs.execute(insert_sql, row)
        #print('curs.execute ran')
        cmte_id = pd.read_sql(sql,conn, params = (cmte_name, month, day, year, congress, pg))['committee_id'][0]
        #print('cmte_id:', cmte_id)
    # Extract cmte_id
    else:
        #print(df.loc[0])
        cmte_id = df['committee_id'][0]
    
    return cmte_id
    

def LoadVoteData(data, conn, curs):

    try:
        i = 0
        # read in row by row
        for row in data.to_dict(orient = 'records'):
            # Get senator and committee id
            # insert committee into db if doesn't exist
            senator_id = row['senator_id']
            #print('senator_id, type:', senator_id, type(senator_id))
            sen_congress_id = GetSenatorCongressID(senator_id,row['congress'], row['age'], row['state'], row['party'], conn, curs)
            #print('senator_congress_id, type: ', sen_congress_id, type(sen_congress_id))
            cmte_id = GetCmteID(row['committee'], row['month'], row['day'], row['year'], row['congress'], row['page'], conn, curs)
            #print('committee id, type:', cmte_id, type(cmte_id))
            insert_sql = "INSERT INTO tVotes (senator_id, senator_congress_id, votes, committee_id)" + \
                            "VALUES (?,?,?,?);"

            parameters = (senator_id, int(sen_congress_id), row['votes'], int(cmte_id))
            #print(parameters)

            curs.execute(insert_sql, parameters)
            i += 1

    except Exception as err:
        print(err)
        print(row)
        print(i)
        conn.rollback()
        return 0
    
    conn.commit()
    conn.close()
    return 1
