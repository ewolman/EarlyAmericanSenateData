from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print('Input Congress number:')
number = input()

scans = os.listdir(number +  '_Congress/Scans')
print(scans)

for png in scans:
  print(png)
  path = number + '_Congress/Scans/' + png
  print(path)
  garbanzo = pytesseract.image_to_string(Image.open(path))
  with open(number + '_Congress/Text/' + png[:-4] + '.txt', 'w') as f:
    f.write(garbanzo)