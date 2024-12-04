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


folder = input('Input Congress number: ') + '_Congress'
edited = input('Have the text files been edited already? (y or n): ')
yrs_exist = input('''Do all the sheets have dates with years? 
                    IF NO make sure there is a 'pg_years.csv' that has the years for each page!
                    (y or n - includes if only some pages have years): ''')

main_path = 'data/scans_and_text/' + folder
if edited == 'y':
    texts = [f for f in os.listdir(main_path + '/Text/Edited') if f.endswith('.txt')] #only edited .txt files
    path = main_path + '/Text/Edited/'
else:
    texts = [f for f in os.listdir(main_path + '/Text') if f.endswith('.txt')] #only .txt files
    path = main_path + '/Text/'

if yrs_exist == 'y':
    pass
else:
    yrs_exist_csv = pd.read_csv(main_path + '/pg_years.csv')

df_data = [] # empty list to append data
for txt in texts:
  pg = re.search(r'\d{1,2}(?=.txt)', txt)[0] # numbers @ end of string
  congress = re.search(r'^\d{1,2}', txt)[0] # numbers @ beginning of string 
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

        # when years exist run get_dates function
        if yrs_exist == 'y':
            month, day, year, dates = get_dates_w_years(garbanzo)

        # when we don't have years -- NEEDS TO BE SOLVED want to get the year based on page, some condition for yes
        else:
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
    
        n_dates = len(dates)

    
        #print(date[:5])
        print('I found', n_committees, 'committees and', n_dates, 'dates!')
        #print(dates)

        #find types if they exist, else - none
        #types_exist = input('Are committee types on page '+ pg +'? (y or n): ')
        #if types_exist == 'y':
         #   c_type = re.compile(r'(?<=Type: )(.*?)(?=[\n])')
          #  cmte_types = re.findall(c_type, garbanzo)
        #else:
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
df = pd.DataFrame(df_data, columns=["NAME", "VOTES", "COMMITTEE", "CMTE_TYPE","MONTH", "DAY", "YEAR", "CONGRESS", "PAGE"])
df.to_csv('data/vote_data/' + folder + '_Data.csv', index=False)
