import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os


def extract_text_or_ocr(pdf_path):
    text_output = ""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # First try to extract text directly
        text = page.get_text()
        if not text.strip():  # If no text found, fall back to OCR
            pix = page.get_pixmap()
            img_path = f"temp_{page_num}.png"
            pix.save(img_path)
            text = pytesseract.image_to_string(
                Image.open(img_path), lang='eng')
            os.remove(img_path)
        text_output += text + "\n"
    doc.close()
    return text_output
