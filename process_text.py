import re
import pandas as pd
import os
import statistics

# function to extract dates with years
def get_dates_w_years(txt):
    date = re.compile(r'(\b[A-Za-z]+ \d{1,2}, \d{4}|n\.d\.).*?')
    dates = re.findall(date, txt)
    day_year = [d.replace("n.d.","n.d., n.d.").split(", ") for d in dates] #split out day year
    dat,year = [d[0] for d in day_year], [y[1] for y in day_year]
    month = [d[:3] if len(d) > 4 else d for d in dat] #first 3 letters of month
    day = [re.findall(r'(\d{1,2}$)', d)[0] if len(d)>4 else d for d in dat]  # day

    return month, day, year, dates

congress = input('Input Congress number: ')
folder = congress + '_Congress'
edited = input('Have the text files been edited already? (y or n): ')
#yrs_exist = input('''Do all the sheets have dates with years? 
 #                   IF NO make sure there is a 'pg_years.csv' that has the years for each page!
  #                  (y or n - includes if only some pages have years): ''')

main_path = 'data/scans_and_text/' + folder
if edited == 'y':
    texts = [f for f in os.listdir(main_path + '/Text/Edited') if f.endswith('.txt')] #only edited .txt files
    path = main_path + '/Text/Edited/'
else:
    texts = [f for f in os.listdir(main_path + '/Text') if f.endswith('.txt')] #only .txt files
    path = main_path + '/Text/'

if int(congress) == 6: # only necessary for 6th congress - hence no input statement needed (line 20)
    yrs_exist_csv = pd.read_csv(main_path + '/pg_years.csv')
else:
    pass

df_data = [] # empty list to append data
for txt in texts:
  pg = re.search(r'(\d{1,2}|Extra)(?=.txt)', txt)[0] # numbers @ end of string
  n_dates = 0
  n_committees = 1 #initialize as unequal
  n_names = [] #empty list to collect number of names for each sheet
  while n_dates != n_committees: #process until n_dates = n_committees
    #data_n = [] #reset data for each time we process a file
    print(txt)
    with open(path + txt, 'r') as f:
        garbanzo = '\n' + f.read() #read text file and add \n new line character 
                                    # sometimes committees are at the very top of page and not read in
        # Regular expression pattern to match text to find committee, date
        cmte = re.compile(r'(?<=\n)((?!\w+\s\d{1,2}|\d|Type: ).+?)(?=[,.])')
        # Find all matches
        committees = re.findall(cmte, garbanzo)
        n_committees = len(committees)
        indices = re.finditer(cmte, garbanzo) #iterative object for each instance
        #print(len(committees), committees)

        # when we don't have years -- want to get the year based on page, w/ some condition for yes
        if int(congress) == 6:
            yr = yrs_exist_csv[(yrs_exist_csv['congress'] == int(congress)) & (yrs_exist_csv['pg'] == int(pg))]['year'].item()
            if yr == 'y': # run the years function if we have on this page
                print('running the function instead')
                month, day, year, dates = get_dates_w_years(garbanzo)
            else: # run with non-year regex
                print('running the non-year regex')
                date = re.compile(r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|March|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\S*\.?\s\d{1,2}\b|n\.d\.')
                dates = re.findall(date, garbanzo)
                month = [d[:3] if len(d) > 4 else d for d in dates] #first 3 letters of month
                day = [re.findall(r'(\d{1,2}$)', d)[0] if len(d)>4 else d for d in dates]  # day
                year = [yr] * len(dates)

        # when years exist run get_dates function
        else:
            month, day, year, dates = get_dates_w_years(garbanzo)
        
        n_dates = len(dates)

        #print(date[:5])
        print('I found', n_committees, 'committees and', n_dates, 'dates!')
        #print(dates)

        cmte_types = [None]*len(committees)

        starts = [m.start(0) for m in indices] #record first index of each committee
        newlines = [garbanzo.find('\n',start) for start in starts ] #record first new line after cmtes
        if len(starts) != len(newlines): # should be a rare error, but in case this happens
            n_dates += 100               # adding 100 to n_dates will avoid if block and open docs

        if n_dates == n_committees: #only process if equal
            
            name = r'(\b(?!Jan(?:uary)?\b|Feb(?:ruary)?\b|Mar(?:ch)?\b|Apr(?:il)?\b|May|Jun(?:e)?\b|Jul(?:y)?\b|Aug(?:ust)?\b|Sep(?:tember)?\b|Oct(?:ober)?\b|Nov(?:ember)?\b|Dec(?:ember)?\b)[A-Za-z \n.():,\'-]+\s\d{1,2}[)}>?,:;.])'
            names_votes = []
            for i in range(len(starts)):
                if i != len(starts)-1: # if not last
                    names_votes += [re.findall(name, garbanzo[newlines[i]:starts[i+1]])] #find all names and votes in the cmte range
                else:
                    names_votes += [re.findall(name, garbanzo[newlines[i]:len(garbanzo)])] # for last committee just look to end

            # Process the matches into a structured format
            for n in range(len(committees)):
            #print(committees[n], n)
            # Split the name-votes by ';'
                n_names += [len(names_votes[n])] #append number of names for committee n
                pattern = r'(\D+?)\s(\d+)' # get non-digit characters until a space before digits
                for nv in names_votes[n]:
                    nv = nv.replace('\n', ' ')[:-1] #remove new line and end punctuation
                    matches = re.findall(pattern, nv)
                    name, votes = matches[0][0], matches[0][1]
                    #print(name, votes)
                    df_data.append([name, votes, committees[n], cmte_types[n], month[n], day[n], year[n], congress, pg])
            print(' ')
            print('Summary Stats on Number of Names for each Commitee on page', pg)
            print('Min:', min(n_names), 'Max:', max(n_names), 'Median names per committee:', statistics.median(n_names))      
            print(' ')
        else:
            print('Error: Dates and Committees do not match. Last recorded date:',(dates[-1] if n_dates>0 else 'None') + '. Check page', pg)
            print('Opening file for editing...')
            print('Here are the committees:',committees)
            print('Here are the dates:',dates)
            # Open the text file in a text editor
            os.system('start ' + main_path + '/Scans/' + txt[:-4] + '.png &&'
                      'notepad ' + path + txt)

            print('File edited. Reprocessing...') #goes back into while loop and starts again

    f.close()
    
print('Done processing, creating .csv file ....')
# Create a DataFrame
df = pd.DataFrame(df_data, columns=["name", "votes", "committee", "cmte_type","month", "day", "year", "congress", "page"])
# Convert month, day, year to numerical date format - remove n.d. observations first
df_nd = df.loc[df['day'] == 'n.d.'].copy() # make a copied df of no date observations
df_nd['date'] = 'n.d.' # set their date to n.d.
df = df.loc[df['day'] != 'n.d.']
m_dict = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
df['month'] = df['month'].replace(m_dict) # replace months with numbers
df['date'] = df['month'].astype(str) +'/' + df['day'].astype(str) + '/' +df['year'].astype(str) # combine to create date
df['date'] = pd.to_datetime(df['date'], format="%m/%d/%Y").dt.date # convert to datetime datatype
df = pd.concat([df, df_nd]) # add back n.d. committees
df = df[["name", "votes", "committee", "cmte_type","date", "congress", "page"]]
df = df.sort_values(
            by=['date', 'page', 'committee'], 
            key=lambda col: col.str.lower() if col.name == 'committee' else col) # sort by date, page, committee
df.to_csv('data/vote_data/' + folder + '_Data.csv', index=False)
