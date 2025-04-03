import fitz
import pytesseract
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor


def preprocess_image(img):
    """
    Preprocesses an image by converting it to grayscale, enhancing OCR accuracy.

    Args:
        img (PIL.Image.Image): Original image.

    Returns:
        PIL.Image.Image: Grayscale image.
    """
    img = img.convert('L')  # Convert to grayscale
    return img

def extract_text_from_page(page, lang):
    """
    Extracts text from a single PDF page using Tesseract OCR.

    Args:
        page (fitz.Page): PDF page to be processed.
        lang (str): Tesseract language(s) for OCR (e.g., "rus+kaz+eng").

    Returns:
        str: Extracted text from the page.
    """
    # Render page to an image, preprocess it, and run OCR
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img = preprocess_image(img)
    text = pytesseract.image_to_string(img, lang=lang)
    return text

def extract_text_from_pdf_ocr(pdf_path, lang):
    """
    Extracts text from each page of a PDF using Tesseract OCR, processing pages in parallel.

    Args:
        pdf_path (str): Path to the PDF file.
        lang (str): Tesseract language(s) for OCR (e.g., "rus+kaz+eng").

    Returns:
        str: Concatenated text from all pages in the PDF.
    """
    pdf_document = fitz.open(pdf_path)
    extracted_text = ""

    # Use ThreadPoolExecutor to process pages concurrently
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(extract_text_from_page, pdf_document[i], lang) for i in range(len(pdf_document))]
        for future in futures:
            extracted_text += f"\n\n{future.result()}\n\n"

    return extracted_text