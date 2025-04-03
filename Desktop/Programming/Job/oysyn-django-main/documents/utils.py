import logging
import os
import ssl
import re
import warnings
from zlib import crc32
import docx
import fitz  # PyMuPDF
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pymorphy3
from elasticsearch.helpers import scan
from urllib3.exceptions import InsecureRequestWarning
from elasticsearch import Elasticsearch

from .models import PlagiarismInstance


def hide_warnings():
    """
    Suppress warnings related to insecure requests and deprecation.
    """
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

hide_warnings()

# Configure logging
logging.basicConfig(
    filename='/tmp/utils.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


# Elasticsearch configuration
ELASTICSEARCH_SCHEME = os.getenv('ELASTICSEARCH_SCHEME', 'http')
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
ELASTICSEARCH_PORT = os.getenv('ELASTICSEARCH_PORT', '9200')
ELASTICSEARCH_USERNAME = os.getenv('ELASTICSEARCH_USERNAME', None)
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD', None)

# Initialize Elasticsearch
es = Elasticsearch(
    [{'scheme': ELASTICSEARCH_SCHEME, 'host': ELASTICSEARCH_HOST, 'port': int(ELASTICSEARCH_PORT)}],
    http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    verify_certs=False
)


# Initialize NLP tools
morph = pymorphy3.MorphAnalyzer()
# stop_words = set(stopwords.words('russian'))

# Set up NLTK data path
nltk_data_path = '/home/oysyn/nltk_data'
nltk.data.path.append(nltk_data_path)

def load_all_stopwords():
    """
    Load stopwords from all available languages in the NLTK stopwords corpus and combine them into a single set.

    This function collects stopwords for various languages, including but not limited to English, Spanish, French, etc.,
    from the NLTK stopwords corpus. It updates a set with stopwords from each language and returns the combined set.
    
    Note:
        - Languages for which stopwords are not available will be skipped.
        - The set returned contains stopwords for all available languages in the corpus.
        
    Returns:
        set: A set containing stopwords from all available languages in the NLTK stopwords corpus.
    
    Example:
        >>> stop_words = load_all_stopwords()
        >>> 'the' in stop_words
        True
    """
    # List of all language codes available in stopwords
    languages = [
        'arabic', 'catalan', 'english', 'greek', 'indonesian', 'norwegian', 'russian', 'tajik',
        'azerbaijani', 'chinese', 'finnish', 'hebrew', 'italian', 'portuguese', 'slovene', 'turkish',
        'basque', 'danish', 'french', 'hinglish', 'kazakh', 'spanish', 'bengali', 'dutch',
        'german', 'hungarian', 'nepali', 'romanian', 'swedish'
    ]

    stop_words = set()
    
    # Add stopwords from each language to the set
    for lang in languages:
        try:
            stop_words.update(stopwords.words(lang))
        except OSError:
            # Handle case where stopwords for a specific language are not available
            print(f"Stop words for language '{lang}' are not available.")
    
    return stop_words
stop_words = load_all_stopwords()
logging.info(f"Total stop words: {len(stop_words)}.")


def check_and_download_nltk_data(packages, nltk_data_path):
    """
    Check and download required NLTK packages if they are not already downloaded.

    Args:
        packages (list): List of required NLTK packages.
        nltk_data_path (str): Path to the NLTK data directory.
    """
    # Disable SSL certificate verification
    ssl._create_default_https_context = ssl._create_unverified_context

    os.makedirs(nltk_data_path, exist_ok=True)
    nltk.data.path.append(nltk_data_path)

    for package in packages:
        try:
            logging.info(f"Attempting to download NLTK package: {package}.")
            nltk.download(package, download_dir=nltk_data_path)
            logging.info(f"Successfully downloaded NLTK package: {package}.")
        except Exception as e:
            logging.error(f"Failed to download NLTK package: {package}. Error: {e}.")

def preprocess_text(text):
    """
    Preprocess text: tokenization, stop-word removal, and lemmatization.

    Args:
        text (str): Input text.

    Returns:
        list: List of preprocessed words.
    """
    # Remove digits and punctuation, convert to lowercase
    text = re.sub(r'[^\w\s]', '', re.sub(r'\d+', '', text)).lower().strip()
    
    # Tokenize and lemmatize
    return [
        morph.parse(word)[0].normal_form
        for word in word_tokenize(text)
        if word.isalpha() and word not in stop_words
    ]

def generate_shingles(words, shingle_size=3):
    """
    Generate shingles from a list of words.

    Args:
        words (list): List of words.
        shingle_size (int): Size of the shingle (number of words in a shingle).

    Returns:
        set: Set of shingle hashes using CRC32.
    """
    return {
        crc32(' '.join(words[i:i + shingle_size]).encode())
        for i in range(len(words) - shingle_size + 1)
    }

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted text.
    """
    text = ""
    with fitz.open(pdf_path) as doc:
        text = '\n'.join(page.get_text() for page in doc)
    return text

def extract_text_from_txt(file_path):
    """
    Extract text from a TXT file.

    Args:
        file_path (str): Path to the TXT file.

    Returns:
        str: Extracted text.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.

    Args:
        file_path (str): Path to the DOCX file.

    Returns:
        str: Extracted text.
    """
    doc = docx.Document(file_path)
    return '\n'.join(paragraph.text for paragraph in doc.paragraphs)

def extract_text_from_file(file_path):
    """
    Extract text from a file based on its format (PDF, TXT, DOCX).
    Returns "Unsupported file format." if the format is not supported.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: Extracted text or an error message if the format is unsupported.
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


def search_similar_shingles(new_shingles, index_name='rmeb'):
    """
    Searches for similar shingles in Elasticsearch.

    Args:
        new_shingles (set): Set of shingles to search for.
        index_name (str): Name of the Elasticsearch index.

    Returns:
        list: List of search results containing matching shingles.
    """
    logger.info(f"Searching for similar shingles: {new_shingles}")
    search_results = []
    for shingle in new_shingles:
        try:
            response = es.search(index=index_name, body={
                "query": {
                    "terms": {
                        "shingles": [shingle]
                    }
                }
            })
            for hit in response['hits']['hits']:
                search_results.append({'doc_id': hit['_id'], 'shingle': shingle})
        except Exception as e:
            logger.error(f"Error searching for similar shingles: {e}")
    return search_results


def extract_matching_fragments(text, shingles, shingle_size=3):
    """
    Extracts text fragments that contain matching shingles.

    Args:
        text (list): List of words from the document.
        shingles (set): Set of shingles to find in the text.
        shingle_size (int): Size of the shingles.

    Returns:
        dict: Dictionary of matching shingles and their text fragments.
    """
    logger.info("Extracting matching fragments.")
    words = text
    text_shingles = {
        crc32(' '.join(words[i:i + shingle_size]).encode()): ' '.join(words[i:i + shingle_size])
        for i in range(len(words) - shingle_size + 1)
    }

    matching_fragments = {shingle: text_shingles[shingle] for shingle in shingles if shingle in text_shingles}
    return matching_fragments


def generate_report(similar_results, new_shingles, text_fragments, document_name, new_report_obj, index_name='documents'):
    """
    Generates a report of text similarity and plagiarism.

    Args:
        similar_results (list): Results from the similarity search.
        new_shingles (set): Set of shingles from the new document.
        text_fragments (dict): Text fragments corresponding to shingles.
        document_name (str): Name of the document.
        new_report_obj (Report): Report object to update.
        index_name (str): Elasticsearch index name.

    Returns:
        tuple: A tuple containing the report dictionary and HTML report path.
    """
    unique_shingles = set(new_shingles)
    total_shingles = len(unique_shingles)

    matching_fragments = {}
    for result in similar_results:
        doc_id = result['doc_id']
        shingle = result['shingle']
        if shingle not in matching_fragments:
            matching_fragments[shingle] = {'doc_id': doc_id, 'fragment': text_fragments.get(shingle, '')}

    total_matching_shingles = len(matching_fragments)
    
    if total_shingles == 0:
        logger.warning(f"No shingles found for document. Possible empty content or extraction issue.")
        plagiarism_percentage = 0
    else:
        plagiarism_percentage = 100 * total_matching_shingles / total_shingles
    
    unique_percentage = 100 - plagiarism_percentage

    doc_shingles = {}
    for shingle, data in matching_fragments.items():
        doc_id = data['doc_id']
        if doc_id not in doc_shingles:
            doc_shingles[doc_id] = {'shingles': set(), 'fragments': []}
        doc_shingles[doc_id]['shingles'].add(shingle)
        doc_shingles[doc_id]['fragments'].append(data['fragment'])

    for details in doc_shingles.values():
        details['count'] = len(details['shingles'])

    sorted_doc_shingles = sorted(doc_shingles.items(), key=lambda item: item[1]['count'], reverse=True)

    # Update the report object
    new_report_obj.originality_percentage = round(unique_percentage, 2)
    new_report_obj.plagiarism_percentage = round(plagiarism_percentage, 2)
    new_report_obj.shingles_total_number = total_shingles
    new_report_obj.save()

    for filename, details in sorted_doc_shingles:
        plagiarised_shingles = details.get('shingles', [])
        instance_plagiarism_percentage = len(plagiarised_shingles) / total_shingles * 100
        PlagiarismInstance.objects.create(
            report=new_report_obj,
            type=PlagiarismInstance.PLAGIARISM,
            title=filename,
            module='Local Indices',
            shingles=str(plagiarised_shingles),
            fragments=str(details.get('fragments', [])),
            plagiarism_percentage=round(instance_plagiarism_percentage, 2)
        )

    return {
        'unique_percentage': unique_percentage,
        'plagiarism_percentage': plagiarism_percentage,
        'doc_shingles': sorted_doc_shingles,
        'total_shingles': total_shingles
    }
