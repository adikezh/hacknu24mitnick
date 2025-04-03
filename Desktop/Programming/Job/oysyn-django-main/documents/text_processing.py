import os
import re
import docx
import docxlatex
import PyPDF2
from pdfminer.high_level import extract_text
import language_tool_python

def extract_text_from_file(file_path):
    """
    Extract text from a file based on its format (PDF, TXT, DOCX).
    Returns text from the file or 'Unsupported file format.' if the format is not supported.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: Extracted text or an error message for unsupported formats.
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format."

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text.
    """
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ''
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    return text

def extract_text_from_txt(file_path):
    """
    Extract text from a TXT file.

    Args:
        file_path (str): Path to the TXT file.

    Returns:
        str: Extracted text.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading TXT file: {e}")
        return ""

def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.

    Args:
        file_path (str): Path to the DOCX file.

    Returns:
        str: Extracted text.
    """
    try:
        doc = docx.Document(file_path)
        return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return ""

def process_formulas(file_path):
    """
    Identify formulas in a document (DOCX, PDF, TXT) and return a list of objects describing the found formulas.

    Args:
        file_path (str): Path to the document.

    Returns:
        list: List of dictionaries with 'context', 'errorLength', and 'offset' describing each formula.
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.docx':
        return process_docx_formulas(file_path)
    elif file_extension == '.pdf':
        return process_pdf_formulas(file_path)
    elif file_extension == '.txt':
        return process_txt_formulas(file_path)
    else:
        raise ValueError("Unsupported file type")

def process_docx_formulas(file_path):
    """
    Identify formulas in a DOCX file using the docxlatex library.

    Args:
        file_path (str): Path to the DOCX file.

    Returns:
        list: List of dictionaries with 'context', 'errorLength', and 'offset' describing each formula.
    """
    pattern = re.compile("[а-яА-ЯёЁ]+")
    doc_latex = docxlatex.Document(file_path, inline_delimiter='$ineq$')
    text_with_formulas = doc_latex.get_text()
    text_formulas_with_russian = []
    global_offset = 0
    
    for formula in re.finditer(r'\$ineq\$.+?\$ineq\$', text_with_formulas):
        match = re.search(pattern, text_with_formulas[formula.start(): formula.end()])
        if match:
            formula_report = {
                'context': text_with_formulas[
                    max(formula.start() - 20, 0): formula.start()
                ] + match.group() + text_with_formulas[
                    formula.end(): min(formula.end() + 20, len(text_with_formulas))
                ],
                'errorLength': match.end() - match.start(),
                'offset': formula.start() - global_offset
            }
            global_offset += len(match.group())
            text_formulas_with_russian.append(formula_report)
    return text_formulas_with_russian

def process_pdf_formulas(file_path):
    """
    Identify formulas in a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: List of dictionaries with 'context', 'errorLength', and 'offset' describing each formula.
    """
    pdf_text = extract_text(file_path)
    return [
        {
            'context': pdf_text[max(match.start() - 20, 0): match.start()] + match.group() + pdf_text[match.end(): min(match.end() + 20, len(pdf_text))],
            'errorLength': match.end() - match.start(),
            'offset': match.start()
        }
        for match in re.finditer(r'\$ineq\$.+?\$ineq\$', pdf_text)
    ]

def process_txt_formulas(file_path):
    """
    Identify formulas in a TXT file.

    Args:
        file_path (str): Path to the TXT file.

    Returns:
        list: List of dictionaries with 'context', 'errorLength', and 'offset' describing each formula.
    """
    text = extract_text_from_txt(file_path)
    return [
        {
            'context': text[max(match.start() - 20, 0): match.start()] + match.group() + text[match.end(): min(match.end() + 20, len(text))],
            'errorLength': match.end() - match.start(),
            'offset': match.start()
        }
        for match in re.finditer(r'\$ineq\$.+?\$ineq\$', text)
    ]

def process_invisible_symbols(file_path):
    """
    Identify places where text is covered with invisible symbols in the document.

    Args:
        file_path (str): Path to the document.

    Returns:
        list: List of dictionaries with 'offset', 'context', and 'errorLength' describing each covered section.
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.docx':
        return process_docx_invisible_symbols(file_path)
    elif file_extension == '.pdf':
        return process_pdf_invisible_symbols(file_path)
    elif file_extension == '.txt':
        return process_txt_invisible_symbols(file_path)
    else:
        raise ValueError("Unsupported file type")

def process_docx_invisible_symbols(file_path):
    """
    Identify invisible symbols in a DOCX file.

    Args:
        file_path (str): Path to the DOCX file.

    Returns:
        list: List of dictionaries with 'offset', 'context', and 'errorLength' describing each covered section.
    """
    doc = docx.Document(file_path)
    white_symbols = []
    global_offset = 0
    
    for para in doc.paragraphs:
        para_text = para.text
        para_offset = global_offset
        global_offset += len(para_text)
        
        for run in para.runs:
            if run.font.color and run.font.color.rgb == docx.shared.RGBColor(255, 255, 255):
                run_text = run.text
                run_start = para_text.index(run_text) + para_offset
                run_end = run_start + len(run_text)
                
                # Get surrounding context
                context_start = max(run_start - 20, 0)
                context_end = min(run_end + 20, len(para_text))
                context = para_text[context_start:run_start] + run_text + para_text[run_end:context_end]
                
                white_symbols.append({
                    'offset': run_start,
                    'context': context,
                    'errorLength': len(run_text)
                })
    
    return white_symbols


def process_pdf_invisible_symbols(file_path):
    """
    Identify invisible symbols in a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: List of dictionaries with 'offset', 'context', and 'errorLength' describing each covered section.
    """
    pdf_text = extract_text(file_path)
    return [
        {
            'offset': match.start(),
            'context': pdf_text[max(match.start() - 20, 0): match.start()] + pdf_text[match.start(): match.end()] + pdf_text[match.end(): min(match.end() + 20, len(pdf_text))],
            'errorLength': match.end() - match.start()
        }
        for match in re.finditer(r'\s{5,}', pdf_text)
    ]

def process_txt_invisible_symbols(file_path):
    """
    Identify invisible symbols in a TXT file.

    Args:
        file_path (str): Path to the TXT file.

    Returns:
        list: List of dictionaries with 'offset', 'context', and 'errorLength' describing each covered section.
    """
    text = extract_text_from_txt(file_path)
    return [
        {
            'offset': match.start(),
            'context': text[max(match.start() - 20, 0): match.start()] + text[match.start(): match.end()] + text[match.end(): min(match.end() + 20, len(text))],
            'errorLength': match.end() - match.start()
        }
        for match in re.finditer(r'\s{5,}', text)
    ]

# def get_lang_tool_results(text):
#     """
#     Check text using LanguageTool for grammatical and style issues.

#     Args:
#         text (str): Text to be checked.

#     Returns:
#         list: List of LanguageTool matches.
#     """
#     tool = language_tool_python.LanguageTool('ru-RU')
#     matches = tool.check(text)
#     tool.close()
#     return matches
def get_lang_tool_results(text, server_url="http://127.0.0.1:8080", chunk_size=5000):
    """
    Process large texts by dividing them into smaller chunks.

    Args:
        text (str): Text to check.
        server_url (str): The LanguageTool server URL.
        chunk_size (int): Maximum size of each chunk.

    Returns:
        list: Combined matches for all chunks.
    """
    matches = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        try:
            tool = language_tool_python.LanguageTool(remote_server=server_url)
            chunk_matches = tool.check(chunk)
            matches.extend(chunk_matches)
            tool.close()
        except Exception as e:
            print(f"Error processing chunk: {e}")
    return matches


def process_lang_tool_results(results):
    """
    Process LanguageTool results to categorize errors.

    Args:
        results (list): List of LanguageTool matches.

    Returns:
        tuple: Two lists: whitespace errors and Latin letter errors.
    """
    errors_list = ['WHITESPACE_RULE', 'Latin_single_letter', 'Latin_letters']
    white_spaces = []
    latin_letters = []
    
    for match in results:
        report_cell = {
            'context': match.context,
            'errorLength': match.errorLength,
            'offsetInContext': getattr(match, 'offsetInContext', None),
            'offset': match.offset
        }
        if match.ruleId in errors_list:
            if match.ruleId in ['Latin_single_letter', 'Latin_letters']:
                latin_letters.append(report_cell)
            elif match.ruleId == 'WHITESPACE_RULE':
                white_spaces.append(report_cell)

    return white_spaces, latin_letters

def get_word_count(file_path):
    """
    Calculate the word count of a document based on its file type.

    Args:
        file_path (str): Path to the file.

    Returns:
        int: Word count.
    """
    if file_path.endswith('.pdf'):
        return count_words_in_pdf(file_path)
    elif file_path.endswith('.docx'):
        return count_words_in_docx(file_path)
    elif file_path.endswith('.txt'):
        return count_words_in_txt(file_path)
    else:
        return 0

def count_words_in_pdf(file_path):
    """
    Count words in a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        int: Word count.
    """
    word_count = 0
    try:
        reader = PyPDF2.PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                word_count += len(text.split())
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    return word_count

def count_words_in_docx(file_path):
    """
    Count words in a DOCX file.

    Args:
        file_path (str): Path to the DOCX file.

    Returns:
        int: Word count.
    """
    word_count = 0
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            word_count += len(paragraph.text.split())
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
    return word_count

def count_words_in_txt(file_path):
    """
    Count words in a TXT file.

    Args:
        file_path (str): Path to the TXT file.

    Returns:
        int: Word count.
    """
    word_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            word_count = len(text.split())
    except Exception as e:
        print(f"Error reading TXT file: {e}")
    return word_count


def find_quotes(text, total_length):
    """
    Finds quotes in the text that are enclosed in quotation marks and contain at least 3 words.

    Args:
        text (str): The full text extracted from the document.
        total_length (int): The total character count of the text.

    Returns:
        list: A list of tuples, each containing:
            - quote (str): The extracted quote.
            - start_index (int): The starting index of the quote in the text.
            - end_index (int): The ending index of the quote in the text.
            - length (int): The character count of the quote.
            - percentage (float): The percentage of the quote's length relative to the total text length.
    """
    pattern = r'[«"](.*?)[»"]'  # Pattern to match quotes enclosed in «» or ""
    matches = re.finditer(pattern, text)

    return [
        (match.group(1), match.start(), match.end(), len(match.group(1)), (len(match.group(1)) / total_length) * 100)
        for match in matches if len(match.group(1).split()) >= 5
    ]
