import pandas as pd
import numpy as np
import json
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys
import re

# functions to record correct names for a given error
# Includes dictionary to record changes and first names for given duplicates
try:
   with open('Data/name_changes.json', 'r') as f:
      name_changes = json.load(f)
except FileNotFoundError:
   name_changes = {}
try: 
   with open('Data/duplicate_dict.json', 'r') as f:
      duplicate_dict = json.load(f)
except FileNotFoundError:
   duplicate_dict = {}

# function to add correction to dictionary
def add_correction(name_changes, corrections, congress, old_name, new_name):
   if congress not in name_changes: # check if changes includes given congress
      name_changes[congress] = {}   # if not - create new dictionary for given congress
   name_changes[congress][old_name] = new_name # add a new correction 
   # save file
   with open('Data/name_changes.json', 'w') as f:
      json.dump(name_changes, f, indent = 4) # indent for readability
   corrections.append(new_name) # append to corrections list   
   return corrections

# function to get correction for a given name
def get_correction(name_changes, congress, name):
   return name_changes.get(str(congress), {}).get(name, None) # returns empty dict, None for nonexistent congresses/Names

#function to check and choose duplicate - record in dict. Should only run if new_name is a duplicate
def update_duplicate(info, data, congress, old_name, new_name, dupe_dict):
   # ADD IN DICTIONARY TO RECORD WHICH PAGE/CONGRESS INSTANCE OF EACH NAME MAPS TO EACH FIRST NAME TO AVOID REPEATING THIS
   if congress not in dupe_dict:
      dupe_dict[congress] = {}

   name_st = get_correction(dupe_dict, congress, old_name) # returns ['name', 'st']
   #print(name_st)
   # case where first name has already been given for this mistake
   if name_st is not None: # first name is known
      data.loc[(data['NAME'] == old_name), ['first']] = name_st[0] # update data
      data.loc[(data['NAME'] == old_name), ['st']] = name_st[1]

      return data
   
   else: # first name is unknown
      print(data[data['NAME'] == name]) # print instances of old_name
      # print first names of the duplicates
      dupes = (info[(info['congressNumber'] == int(congress)) & (info['unaccentedFamilyName'] == new_name)][['givenName','state']])
      print(dupes)
      d = int(input('Pick correct first name (and state) from list above: (number 1 to n) '))
      # remember this correction by adding the first name + st to vote data
      # this will allow for easy merging
      data.loc[(data['NAME'] == old_name), ['first']] = dupes.iloc[d-1]['givenName']
      data.loc[(data['NAME'] == old_name), ['st']] = dupes.iloc[d-1]['state']
      dupe_dict[congress][old_name] = [val for val in dupes.iloc[d-1].values] # add to dictionary
      with open('Data/duplicate_dict.json', 'w') as f: # save dictionary
         json.dump(dupe_dict, f, indent = 4) # indent for readability
      return data

# read in info data
info = pd.read_csv('Data/Info.csv')

# Take only necessary cols from info
info = info[['id','givenName','middleName','unaccentedFamilyName','birthYear','deathYear','congresses']]

# Process congresses column and split out into multiple cols
beans = info['congresses']
# read in the json files of the congresses col
pinto = beans.apply(json.loads)
# create an empty dictionary to read in info w/ id for each congress
congress_i = {'id': [],
              'congressNumber': [],
              'position': [],
              'state': [],
              'parties': []} # dictionary for ith congress
#print(len(pinto))
s = 0 #iterator to keep track of id
for sen in pinto:
   # print(sen) 
   # for each dict for each senator add the id and info
   for dict in sen:
      congress_i['id'].append(info['id'][s])
      congress_i['congressNumber'].append(dict.get('congressNumber'))
      congress_i['position'].append(dict.get('position'))
      congress_i['state'].append(dict.get('stateName'))
      congress_i['parties'].append(dict.get('parties'))
   s += 1
#print(s)

# create a df of the congress info and merge with the names
congress_i_df = pd.DataFrame(congress_i)
info = info.merge(congress_i_df,on='id',how = 'inner')

# keep only congress 1-16 and senators
info = info[(info['congressNumber'] < 17) & (info['position'] == 'Senator')]

# create a dict with start yr for each congress, add a column of the years and calc age
years = {1 : 1789, 2 : 1791, 3 : 1793, 4 : 1795, 5 : 1797, 6 : 1799, 7 : 1801, 8 : 1803, 
         9 : 1805, 10 : 1807, 11 : 1809, 12 : 1811, 13 : 1813, 14 : 1815, 15 : 1817, 16 : 1819}
info['congressYear'] = info['congressNumber'].map(years)
info['age'] = info['congressYear'] - info['birthYear']

# make names lowercase for easier matching
info['unaccentedFamilyName'] = info['unaccentedFamilyName'].str.lower()
# join first (middle) and last to create a full name column
info['middleName'] = info['middleName'].fillna('')
info['fullName'] = info['givenName'] + ' ' + info['middleName'] + ' ' + info['unaccentedFamilyName']
# take party out of its list format
info['parties'] = [p[0] for p in info['parties']]

# write to csv
info.to_csv('Data/info1st_16th.csv', index = False)

comb_all = pd.DataFrame() #empty dataframe
skips  = pd.read_csv('Data/skip_log.csv') # skippable names in a csv

# READ IN VOTES AND COMBINE -- Check Nans
vote_data = [file for file in os.listdir('Data/vote_data') if file.endswith('.csv')]
numbers = [] # to get latest congress
#print(vote_data)
for congress in vote_data:
   data = pd.read_csv('Data/vote_data/' + congress)
   #read in as text so needs to be converted
   c_num = re.search(r'^\d{1,2}', congress)[0]
   c = int(c_num), c_num # int and str
   numbers += [c[0]] 
   print('Congress -', c[1])

   # entries of correct names for given congress
   congress_names = info[info['congressNumber'] == c[0]]['unaccentedFamilyName'] 
   full_names = info[info['congressNumber'] == c[0]]['fullName']

   # find duplicate names by finding all names that appear more than once for a given congress
   duplicates = info[info['congressNumber'] == c[0]]['unaccentedFamilyName'].value_counts() > 1
   duplicates = [n for n in duplicates[duplicates].index] # save a list of these names
   print(duplicates)

   # lowercase names
   data['NAME'] = data['NAME'].str.lower()
   data['first'] = None # create a first name + st column for cases of duplicate last name
   data['st'] = None
   #print(data.head())

   # check for mistakes in data and get a list of non_matches AND DUPLICATES to the info csv
   nonmatches = data['NAME'][(~data['NAME'].isin(congress_names)) | (data['NAME'].isin(duplicates))].unique()
   corrections = [] # empty list to record corrections
   i = 0 # index
   for name in nonmatches: #iterate through unique nonmatches
      #print(name)
      # check if name can be skipped
      if sum(skips.iloc[:,0].str.fullmatch(name)) > 0: #check if name is in skip csv
         print(name)
         print('we in the skip zone')
         nonmatches = np.delete(nonmatches, i) # delete from nonmatch list
         continue #keep running loop

      # check if correction exists
      correction = get_correction(name_changes, c[0], name)
      if correction: 
         corrections.append(correction) # append to corrections list
         if correction in duplicates:
            #print(name, correction)
            data = update_duplicate(info, data, c[1], name, correction, duplicate_dict)

      # find correction
      else:
         pgs = data[data['NAME'] == name]['PAGE'] # record page appearances of incorrect name

         closest_matches = process.extract(name, congress_names, limit = 2) # find 2 closest matches
         # if the match score is above 80, append without asking
         if closest_matches[0][1] > 80: # catches obvious matches
            new_name = closest_matches[0][0]
            # update corrections dictionary file
            corrections = add_correction(name_changes, corrections, c[1], name, new_name) 
            if new_name in duplicates:
               data = update_duplicate(info, data, c[1], name, new_name, duplicate_dict)
         
         # else: ask for input to look at matches
         else:
            print(data[data['NAME'] == name]) # print mistake
            # open documents and ask for input
            look_q = input('Mistake above ^ - do you want to look at the documents? (y or n): ')
            if look_q == 'y': # open documents
               pg = str(data[data['NAME'] == name]['PAGE'].iloc[0])
               os.system('start Data/scans_and_text/' +  c[1] + '_Congress/Scans/' + c[1] + '_Congress_p' + pg + '.png' 
                    + '&& notepad Data/scans_and_text/' + c[1] + '_Congress/Text/Edited/' + c[1] + '_Congress_p' + pg) 

            print('Pick closest match ' + name + str(closest_matches) + ' (1 or 2, 3 if wrong): ')
            m = int(input())
            if m == 1 or m == 2:
               # append based on choice - 1 is index 0, 2 is index 1
               new_name = closest_matches[m-1][0]
               corrections = add_correction(name_changes, corrections, c[1], name, new_name)
               if new_name in duplicates:
                  data = update_duplicate(info, data, c[1], name, new_name, duplicate_dict)

            elif m == 3:
               # if no mistake, then delete nonmatch i from list, and add to file to skip in future
               # if mistake is fixable - ask for new name - change in txt file and vote csv
               q = input('1: Add to data without correction; 2: Name needs to be changed; 3: Error; : ')
               if  int(q) == 1:
                  nonmatches = np.delete(nonmatches, i)
                  skips = skips.append(name)
                  skips.to_csv('Data/skip_log.csv', index = False)

               elif int(q) == 2:
                  new_name = input('Corrected name: ')
                  corrections = add_correction(name_changes, corrections, c[1], name, new_name)
                  if new_name in duplicates:
                     data = update_duplicate(info, data, c[1], name, new_name, duplicate_dict)

               else: 
                  print('Something needs to be changed in the files, writing name to error file ....')
                  # writes wrong name and data to a log file
                  with open('Data/error_log.txt', 'a') as e:
                     e.write(str(data[data['NAME'] == name]))
            else:
               print('Something is wrong here')
               sys.exit(1)
      i += 1
   # replace incorrect nonmatches from data sheet and save in updated folder
   #print(nonmatches, corrections)   
   data = data.replace(nonmatches, corrections)
   data.to_csv('Data/vote_data/updated/' + congress, index = False)



   # merge using info from given congress, c. 
   # Left join to include all votes and committees
   comb = pd.merge(data, info[info['congressNumber'] == c[0]], how = 'left', 
                   left_on='NAME', right_on='unaccentedFamilyName')
   comb_all = pd.concat([comb_all, comb])   


# comb_all to csv
# When merging, duplicate last names get 2 entries per entry 
# (e.g. Stevens Mason also merges with Jonathan Mason because it's based on last name)
# Remove entries here since most entries have nonetype first names in their data files
# remove all entries where the first name and state are equal to given name in info and state or are none (non-dupes)
comb_all = comb_all[((comb_all['first'] == comb_all['givenName']) & (comb_all['st'] == comb_all['state'])) |  (comb_all['first'].isna())]
# lowercase and rename columns
comb_all.columns = [c.lower() for c in comb_all.columns]
comb_all = comb_all.rename(columns={'id' : 'senator_id', 'givenname' : 'first_name', 
                            'middlename' : 'middle_name', 'unaccentedfamilyname' : 'last_name',
                            'parties' : 'party', 'cmte_type':'committee_type', 'birthyear': 'birth_year',
                            'deathyear': 'death_year'})
comb_all = comb_all.sort_values(by=['congress', 'page','year'])
comb_all.to_csv('Data/Merged_Data/info_data_upto_congress_' + str(max(numbers)) + '.csv', index=False)
print('Data successfully merged, writing to file ...')