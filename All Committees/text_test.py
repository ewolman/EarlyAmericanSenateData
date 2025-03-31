import re
import pandas as pd
import os
import statistics

def get_dates(txt):
    date = re.compile(r'(\b[A-Za-z]+ \d{1,2}, \d{4}|n\.d\.).*?')
    dates = re.findall(date, txt)
    day_year = [d.replace("n.d.","n.d., n.d.").split(", ") for d in dates] #split out day year
    dat,year = [d[0] for d in day_year], [y[1] for y in day_year]
    month = [d[:3] if len(d) > 4 else d for d in dat] #first 3 letters of month
    day = [re.findall(r'(\d{1,2}$)', d)[0] if len(d)>4 else d for d in dat]  # day

    return month, day, year, dates

ordinal_dict = {1: "1st",  2: "2nd",  3: "3rd",  4: "4th",
                5: "5th",  6: "6th",  7: "7th",  8: "8th",
                9: "9th",  10: "10th",  11: "11th", 
                13: "13th",  14: "14th",  15: "15th"}

congress = 1#int(input('Input Congress number: '))
ordinal = ordinal_dict[congress]
file_path = 'Text/' + ordinal + ' Congress Committees (text files)'
texts = os.listdir(file_path)
print(texts[:2])
for txt in texts[:2]:
    pg = re.search(r'(\d{1,2}|Extra)(?=.txt)', txt)[0] # numbers @ end of string
    n_dates = 0
    n_committees = 1 #initialize as unequal

    #while n_dates != n_committees: 
    with open(file_path + '/' + txt, 'r') as f:
            garbanzo = f.read()
            print(garbanzo[:100])
            cmte = re.compile(r'(?:Jt\s|‘o|e|C|c*)?mte[^\.]*')
            committees = re.findall(cmte, garbanzo)
            month, day, year, dates = get_dates(garbanzo)
            print(len(committees))
            print(len(dates))


# just fill columns w/ as many comms and dates as there are -- extend with nulls to match
# Still organized by page and clear what's missed