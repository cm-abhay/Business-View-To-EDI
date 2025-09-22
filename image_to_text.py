import cv2
import numpy as np
import os
import pytesseract
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
import easyocr
from PIL import Image
import json
import asyncio
# from langchain_ibm import ChatWatsonx
# from ibm_watsonx_ai.foundation_models.schema import TextChatParameters
# from dotenv import load_dotenv


def preprocess_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)



def extract_text_from_image(image_path, lang='eng', psm=6, oem=3, extra_config=''):
    image = preprocess_image(image_path)
    config = f'--oem {oem} --psm {psm} {extra_config}'
    text = pytesseract.image_to_string(image, lang=lang, config=config)
    return text



# def extract_text_from_image(image_path):
#     # image = Image.open(image_path)
#     # text = pytesseract.image_to_string(image)

#     reader = easyocr.Reader(['en'])
#     result = reader.readtext(image_path)
    
#     # Sort detections by their vertical position (y-coordinate)
#     # This groups text by rows (approximately)
#     sorted_by_y = {}
#     for detection in result:
#         # Get the bounding box coordinates
#         bbox = detection[0]
#         # Calculate the middle y-coordinate of the bounding box
#         mid_y = (bbox[0][1] + bbox[2][1]) / 2
#         # Round to the nearest 10 pixels to group text in the same line
#         y_key = round(mid_y / 10) * 10
        
#         if y_key not in sorted_by_y:
#             sorted_by_y[y_key] = []
        
#         # Store the detection along with its x-coordinate for later sorting
#         x_coord = bbox[0][0]  # Left edge x-coordinate
#         sorted_by_y[y_key].append((x_coord, detection[1]))
    
#     # Build the text by processing each row from top to bottom
#     text = ""
#     for y_key in sorted(sorted_by_y.keys()):
#         # Sort each row's text from left to right
#         row_text = sorted(sorted_by_y[y_key], key=lambda x: x[0])
#         # Join the text in this row with spaces
#         line = " ".join([item[1] for item in row_text])
#         text += line + "\n"
    
#     return text

print(extract_text_from_image("BusinessViews/PurchaseOrders/PO1.png"))