import pandas as pd
import numpy as np
import json
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys

# read in info data
info = pd.read_csv('Info.csv')

# Take only necessary cols from info
info = info[['id','givenName','familyName','unaccentedFamilyName','birthYear','deathYear','congresses']]

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
# take party out of it's list format
info['parties'] = [p[0] for p in info['parties']]

# write to csv
info.to_csv('info1st_16th.csv', index = False)

comb_all = pd.DataFrame() #empty dataframe
skips  = pd.read_csv('skip_log.csv') # skippable names in a csv

# READ IN VOTES AND COMBINE -- Check Nans
vote_data = os.listdir('vote_data')
#print(vote_data)
for congress in vote_data:
   #read in as text so needs to be converted
   c = int(congress[0]), congress[0] # int and str 
   # entries of only correct names for given congress
   congress_names = info[info['congressNumber'] == c[0]]['unaccentedFamilyName'] 
   print(c)
   data = pd.read_csv('vote_data/' + congress)
   # lowercase name
   data['NAME'] = data['NAME'].str.lower()
   #print(data.head())

   # check for mistakes in data and change them
   nonmatches = data['NAME'][~data['NAME'].isin(congress_names)].unique()
   corrections = []
   i = 0 # index
   for name in nonmatches: #iterate through unique nonmatches
      print(name)
      # check if name can be skipped
      if sum(skips.iloc[:,0].str.fullmatch(name)) > 0: #check if name is in skip csv
         print(name)
         print('we in the skip zone')
         nonmatches = np.delete(nonmatches, i) # delete from nonmatch list
         continue #keep running loop

      closest_matches = process.extract(name, congress_names, limit = 2) # find 2 closest matches
      # if the match score is above 80, append
      if closest_matches[0][1] > 80:
         corrections.append(closest_matches[0][0])
      # else: ask for input to look at matches
      else:
         print(data[data['NAME'] == name]) # print mistake
         # open documents and ask for input
         print('Pick closest match ' + name + str(closest_matches) + ' (1 or 2, 3 if wrong): ')
         pg = str(data[data['NAME'] == name]['PAGE'].iloc[0])
         os.system('start ' +  c[1] + '_Congress/Scans/' + c[1] + '_Congress_p' + pg + '.png' 
                    + '&& notepad ' + c[1] + '_Congress/Text/Edited/' + c[1] + '_Congress_p' + pg) 
         m = int(input())
         if m == 1 or m == 2:
            # append based on choice - 1
            corrections.append(closest_matches[m-1][0])
         elif m == 3:

            # if no mistake, then delete nonmatch i from list, and add to file to skip in future
            if input('Is this actually correct (add to data w/o correction)? (y or n): ') == 'y':
               nonmatches = np.delete(nonmatches, i)
               skips = skips.append(name)
               skips.to_csv('skip_log.csv', index = False)

            else: 
               print('Something needs to be changed in the files, writing name to error file ....')
               # writes wrong name and data to a log file
               with open('error_log.txt', 'a') as e:
                  e.write(str(data[data['NAME'] == name]))
         else:
            print('Something is wrong here')
            sys.exit(1)
      i += 1
      # replace incorrect nonmatches from data sheet and resave
   #print(nonmatches, corrections)   
   data = data.replace(nonmatches, corrections)
   data.to_csv('vote_data/' + congress, index = False)



   # merge using info from given congress, c. 
   # Left join to include all votes and committees
   comb = pd.merge(data, info[info['congressNumber'] == c[0]], how = 'left', 
                   left_on='NAME', right_on='unaccentedFamilyName')
   comb_all = pd.concat([comb_all, comb])   


# comb_all to csv
comb_all.to_csv('Merged_Data/info_data_upto_congress_' + c[1] + '.csv', index=False)
print('Data successfully merged, writing to file ...')