from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import os, re, pandas as pd

ordinal_dict = {'1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5, '6th': 6, '7th': 7, 
                 '8th': 8, '9th': 9, '10th': 10, '11th': 11, '13th': 13, '14th': 14, '15th': 15}

def get_dates(txt):
    date = re.compile(r'(\b[A-Za-z]+ \d{1,2}, \d{4}|n\.d\.).*?')
    dates = re.findall(date, txt)
    day_year = [d.replace("n.d.","n.d., n.d.").split(", ") for d in dates] #split out day year
    dat,year = [d[0] for d in day_year], [y[1] for y in day_year]
    month = [d[:3] if len(d) > 4 else d for d in dat] #first 3 letters of month
    day = [re.findall(r'(\d{1,2}$)', d)[0] if len(d)>4 else d for d in dat]  # day

    return month, day, year, dates

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Users\elswl\Release-24.08.0-0\poppler-24.08.0\Library\bin"

df_data = {'committee':[],'month':[],'day':[],'year':[],'congress':[], 'page':[]} # empty list to append data

for ordinal in ordinal_dict.keys():
  print(ordinal, ' Congress processing')
  folder_path = 'Text/' + ordinal + ' Congress Committees (text files)'
  os.makedirs(folder_path, exist_ok=True)

  file_path = 'Committee Lists Scanned/' + ordinal +  ' Congress Committee List.pdf'
  images = convert_from_path(file_path, poppler_path= poppler_path)

  dict = {}
  congress = ordinal_dict[ordinal]

  for i, img in enumerate(images):
      pg = i + 1 
      if ordinal != '1st' or pg != 1: #1st congress 1st page is vertical
        rotated_img = img.rotate(90, expand=True)  # Rotate counterclockwise
      else:
        rotated_img = img

      garbanzo = pytesseract.image_to_string(rotated_img) 
      dict[pg] = garbanzo

      # save text file
      with open(folder_path + '/' + ordinal + ' Congress pg ' + str(pg) + '.txt', 'w') as f:
          f.write(garbanzo)

          #get list of committe names and dates
          cmte = re.compile(r'(?:Jt\s|‘o|e|C|c*)?mte[^\.]*')
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

print('Creating spreadsheet ...')
# Create the spreadsheet
df = pd.DataFrame.from_dict(df_data)
m_dict = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6','Jul':'7',
          'Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}
df_nd = df.loc[df['day'].isnull()].copy() # make a copied df of no date observations
df_nd['date'] = None # set their date to n.d.
df = df.loc[~df['day'].isnull()]
df['month'] = df['month'].replace(m_dict) # replace months with numbers
#print('HEAD: ')
#print(df.head())
#print('TAIL: ')
#print(df.tail())
df['date'] = df['month'].astype(str) +'/' + df['day'].astype(str) + '/' +df['year'].astype(str) # combine to create date
df['date'] = pd.to_datetime(df['date'], format="%m/%d/%Y").dt.date # convert to datetime datatype
df = pd.concat([df, df_nd]) # add back n.d. committees
df = df[["committee","date", "congress", "page"]]
df = df.sort_values(
            by=['page', 'congress', 'date', 'committee'], 
            key=lambda col: col.str.lower() if col.name == 'committee' else col) # sort by date, page, committee
df.to_csv('committee_list.csv', index=True)
print('Spreadsheet saved')

# Still organized by page and clear what's missed