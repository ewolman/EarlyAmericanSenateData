from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import os

ordinal_dict = {1: "1st",  2: "2nd",  3: "3rd",  4: "4th",
                5: "5th",  6: "6th",  7: "7th",  8: "8th",
                9: "9th",  10: "10th",  11: "11th", 
                13: "13th",  14: "14th",  15: "15th"}

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Users\elswl\Release-24.08.0-0\poppler-24.08.0\Library\bin"


for ordinal in ordinal_dict.values():

  folder_path = 'Text/' + ordinal + ' Congress Committees (text files)'
  os.makedirs(folder_path, exist_ok=True)

  file_path = 'Committee Lists Scanned/' + ordinal +  ' Congress Committee List.pdf'
  images = convert_from_path(file_path, poppler_path= poppler_path)

  dict = {}


  for i, img in enumerate(images):
      pg = i + 1 
      if ordinal != '1st' or pg != 1: #1st congress 1st page is vertical
        rotated_img = img.rotate(90, expand=True)  # Rotate counterclockwise
      else:
        rotated_img = img

      text = pytesseract.image_to_string(rotated_img) 
      dict[pg] = text

      # save text file
      with open(folder_path + '/' + ordinal + ' Congress pg ' + str(pg) + '.txt', 'w') as f:
          f.write(text)