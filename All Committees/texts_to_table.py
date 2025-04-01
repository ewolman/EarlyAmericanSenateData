import re
import pandas as pd
import os
import statistics

# use for if making small changes and don't want to run whole other thing
def get_dates(txt):
    date = re.compile(r'(?i)\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:tember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\d{1,2},\s*\d{4}|n\.d\.')
    dates = re.findall(date, txt)
    day_year = [d.replace("n.d.","n.d., n.d.").replace('\n',' ').split(", ") for d in dates] #split out day year
    try:
        dat,year = [d[0] for d in day_year], [y[1] for y in day_year]
    except IndexError:
        print(congress,pg,day_year)
    #try:
    month = [d[:3] if len(d) > 4 else d for d in dat] #first 3 letters of month
    #except UnboundLocalError:
     #   print(dates)
    try:
        day = [re.findall(r'(\d{1,2}$)', d)[0] if len(d)>4 else d for d in dat]  # day
    except UnboundLocalError:
        print(dates)
    return month, day, year, dates

ordinal_dict = {1: "1st",  2: "2nd",  3: "3rd",  4: "4th",
                5: "5th",  6: "6th",  7: "7th",  8: "8th",
                9: "9th",  10: "10th",  11: "11th", 
                13: "13th",  14: "14th",  15: "15th"}

df_data = {'committee':[],'month':[],'day':[],'year':[],'congress':[], 'page':[]} # empty list to append data

for congress in ordinal_dict.keys():
    ordinal = ordinal_dict[congress]
    file_path = 'Text/' + ordinal + ' Congress Committees (text files)'
    texts = os.listdir(file_path)
    print(texts[:2])
    for txt in texts:
        pg = re.search(r'(\d{1,2}|Extra)(?=.txt)', txt)[0] # numbers @ end of string
        n_dates = 0
        n_committees = 1 #initialize as unequal

        with open(file_path + '/' + txt, 'r') as f:
            garbanzo = f.read()
            cmte = re.compile(r'(?:Jt\s.|\\o|\\e|g|‘o|e|C|c*)?mte(?!r|\.)[^\.]*')
            committees = re.findall(cmte, garbanzo)
            n_committees = len(committees)
            month, day, year, dates = get_dates(garbanzo)         
            n_dates = len(dates)

            #find the max length
            max_len = max(n_committees,n_dates)
            if n_committees < max_len: #extend length of cmte list
                committees += [None]*(max_len-n_committees)
            elif n_dates < max_len: #extend length of date list
                month += [None]*(max_len-n_dates)
                day += [None]*(max_len-n_dates)
                year += [None]*(max_len-n_dates)

            df_data['committee'] += committees
            df_data['month'] += month
            df_data['day'] += day
            df_data['year'] += year
            df_data['congress'] += [congress]*max_len
            df_data['page'] += [pg]*max_len

        f.close()

df = pd.DataFrame.from_dict(df_data)
m_dict = {'Jan':'1','dan':'1','Feb':'2','feb':'2','Mar':'3','Apr':'4','apr':'4',
              'May':'5','Jun':'6','Jum':'6','Jul':'7','jul':'7','Aug':'8','Sep':'9','Oct':'10',
              'Nov':'11','Dec':'12'}
df_nd = df.loc[df['day'].isnull()].copy() # make a copied df of no date observations
df_nd['date'] = None # set their date to n.d.
df = df.loc[~df['day'].isnull()]
df['month'] = df['month'].replace(m_dict) # replace months with numbers
    #print('HEAD: ')
    #print(df.head())
    #print('TAIL: ')
    #print(df.tail())
df['date'] = df['month'].astype(str) +'/' + df['day'].astype(str) + '/' +df['year'].astype(str) # combine to create date
print(df.iloc[2430])
df['date'] = pd.to_datetime(df['date'], format="%m/%d/%Y").dt.date # convert to datetime datatype
df = pd.concat([df, df_nd]) # add back n.d. committees
df = df[["committee","date", "congress", "page"]]
#df = df.sort_values(
                #by=['congress','page', 'date', 'committee'], 
                #key=lambda col: col.str.lower() if col.name == 'committee' else col) # sort by date, page, committee
df.to_csv('committee_list.csv', index=True)
print('Spreadsheet made')
print('committee blanks:', sum(df['committee'].isnull()))
print('date blanks:', sum(df['date'].isnull()))


    # Still organized by page and clear what's missed

    # next step is to couple committees and dates