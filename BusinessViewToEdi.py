import cv2
import os
import pytesseract
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
import easyocr
from PIL import Image
import json
import asyncio
from langchain_ibm import ChatWatsonx
from ibm_watsonx_ai.foundation_models.schema import TextChatParameters
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter

load_dotenv()

def extract_text_from_image_docling(image_path):
    converter = DocumentConverter()
    doc = converter.convert(image_path).document

    return doc.export_to_markdown()

# OCR/Tesseract Function
def extract_text_from_image(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    
    # Sort detections by their vertical position (y-coordinate)
    sorted_by_y = {}
    for detection in result:
        # Get the bounding box coordinates
        bbox = detection[0]
        # Calculate the middle y-coordinate of the bounding box
        mid_y = (bbox[0][1] + bbox[2][1]) / 2
        # Round to the nearest 10 pixels to group text in the same line
        y_key = round(mid_y / 10) * 10
        
        if y_key not in sorted_by_y:
            sorted_by_y[y_key] = []
        
        # Store the detection along with its x-coordinate for later sorting
        x_coord = bbox[0][0]  # Left edge x-coordinate
        sorted_by_y[y_key].append((x_coord, detection[1]))
    
    # Build the text by processing each row from top to bottom
    text = ""
    for y_key in sorted(sorted_by_y.keys()):
        # Sort each row's text from left to right
        row_text = sorted(sorted_by_y[y_key], key=lambda x: x[0])
        # Join the text in this row with spaces
        line = " ".join([item[1] for item in row_text])
        text += line + "\n"
    
    return text

parameters = TextChatParameters(
    max_tokens=4000,
    temperature=0.3,
    top_p=1,
)

llm = ChatWatsonx(
    model_id="meta-llama/llama-3-3-70b-instruct",
    url=os.getenv("WATSONX_URL"),
    apikey=os.getenv("WATSONX_API_KEY"),
    project_id=os.getenv("WATSONX_PROJECT_ID"),
    params=parameters,
)

def build_formatting_prompt(raw_text):

    return f"""
    You are a text-cleaning assistant. The following is raw OCR text extracted from a scanned business document.

    Your job is to:
    1. Identify what type of document it is (e.g., Purchase Order, Invoice, Request for Quotation, etc.) and include it in the first line of your response.
    2. Correct formatting issues (spacing, line breaks).
    3. Remove irrelevant or unreadable artifacts.
    4. Retain only meaningful business data.
    5. Present the cleaned text in a clear, structured format (with headings like 'Order Summary', 'Invoice Summary', 'Line Items', etc. depending on the document type).

    --- BEGIN RAW OCR TEXT ---
    {raw_text}
    --- END RAW OCR TEXT ---

    Return ONLY the cleaned and formatted document with its type clearly stated at the top.
    """

    # return f"""
    # You are an expert in creating Jinja2 templates for structured business documents. 
    # The following is raw OCR text extracted from a scanned business document.

    # Your job is to:
    # 1. Identify what type of document it is (e.g., Purchase Order, Invoice, Request for Quotation, etc.).
    # 2. Extract all relevant business fields (e.g., order number, date, supplier, buyer, line items, totals).
    # 3. Organize the extracted fields into a structured Jinja2 template.
    # 4. Ensure that the Jinja template is clean, readable, and uses placeholders for variable data.
    # 5. Return ONLY the Jinja2 template code, nothing else.

    # --- BEGIN RAW OCR TEXT ---
    # {raw_text}
    # --- END RAW OCR TEXT ---
    # """


# Prompt Template for EDI Generation
def build_prompt(cleaned_text):
    return f"""
    You are an expert in EDI formatting.

    Below is the extracted text from a scanned business document.
    1. Identify the correct EDI transaction type:
    - 850 = Purchase Order
    - 810 = Invoice
    - Others as appropriate
    2. Generate a valid EDI document of that type.

    Only output the EDI document, nothing else.

    --- BEGIN DOCUMENT TEXT ---
    {cleaned_text}
    --- END DOCUMENT TEXT ---
    """



async def generate_edi_from_image(image_path):
    raw_text = extract_text_from_image_docling(image_path)
    print(raw_text)
    # raw_text = """ """
    formatting_prompt = build_formatting_prompt(raw_text)
    formatted_response = await llm.ainvoke(formatting_prompt)
    formatted_text = formatted_response.content
    print("\n🧾 Cleaned & Formatted Text:\n")
    print(formatted_text)

    edi_prompt = build_prompt(formatted_text)
    edi_response = await llm.ainvoke(edi_prompt)
    print("\n📄 EDI Document Generated:\n")
    print(edi_response.content)


if __name__ == "__main__":
    image_path = "BusinessViews/PurchaseOrders/PO2.png"
    if not os.path.exists(image_path):
        print("❌ File does not exist.")
    else:
        asyncio.run(generate_edi_from_image(image_path))



