from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

path = input('Enter test file filepath:')

garbanzo = pytesseract.image_to_string(Image.open(path))

print(garbanzo[:100])