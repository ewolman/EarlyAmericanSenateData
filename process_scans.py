from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print('Input Congress number:')
number = input()

main_path = 'scans_and_text/' + number +  '_Congress/'
scans = os.listdir(main_path + 'Scans')
print(scans)

for png in scans:
  print(png)
  path = main_path + 'Scans/' + png
  print(path)
  garbanzo = pytesseract.image_to_string(Image.open(path))
  with open(main_path + 'Text/' + png[:-4] + '.txt', 'w') as f:
    f.write(garbanzo)