import base64
import logging
import os
import re
import requests
from celery import shared_task, group, chain
from django.shortcuts import get_object_or_404

from .models import Document, Report, PlagiarismInstance
from .text_processing import (process_formulas, process_invisible_symbols,
                              get_lang_tool_results, process_lang_tool_results,
                              extract_text_from_file, find_quotes)
from .plagiarism_processing import (process_plagiarism_entities, calculate_percentages,
                                    GPTCheck)
from .utils import (preprocess_text, generate_shingles,
                    search_similar_shingles, extract_matching_fragments,
                    generate_report)
from .ocr_utils import extract_text_from_pdf_ocr


# Configure logging
logging.basicConfig(
    filename='/tmp/celery_tasks.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def task_save_text_to_db(self, document_id: int, *args, **kwargs) -> int:
    """
    Celery task to extract and save the text content of a document to the database.
    This is the first task in the chain to ensure the document's text is saved before further processing.

    Args:
        document_id (int): ID of the document to extract and save text for.
    Returns:
        document_id (int): Returns the document ID for the next task in the chain.
    """
    try:
        document = Document.objects.get(pk=document_id)
        file_path = document.document.path
        text = extract_text_from_file(file_path)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive newlines
        document.text_content = cleaned_text
        document.save()
        logger.info(f"Document {document_id} text saved successfully.")
        return document_id
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found. Retrying...")
        raise self.retry(countdown=5, exc=Document.DoesNotExist)
    except Exception as e:
        logger.error(f"Error saving text for document {document_id}: {e}")
        raise self.retry(countdown=5, exc=e)


@shared_task(bind=True, max_retries=3)
def task_find_citations(self, document_id, *args, **kwargs):
    """
    Celery task to find citations in the text content of a document.

    Args:
        document_id (int): ID of the document to search for citations.
    """
    try:
        # Fetch the document
        document = Document.objects.get(pk=document_id)

        # Get the text from the text_content field
        text = document.text_content
        if not text:
            logger.warning(f"No text content found for document {document_id}. Skipping citation extraction.")
            return

        # Calculate the total length of the text
        total_length = len(text)

        # Find quotes in the text
        quotes = find_quotes(text, total_length)

        if not quotes:
            logger.info(f"No citations found in document {document_id}.")
            return document_id

        # Get or create a report associated with the document
        report, _ = Report.objects.get_or_create(document=document)

        # Variable to accumulate the total percentage of citations
        total_citation_percentage = 0

        # Create instances of PlagiarismInstance for each quote found
        for quote, start, end, length, percentage in quotes:
            # Create a dictionary for the plagiarism_ranges field
            plagiarism_ranges = {
                'start': start,
                'end': end,
                'length': length
            }

            # Save each citation as a PlagiarismInstance
            PlagiarismInstance.objects.create(
                report=report,
                title=f"Citation: {quote[:50]}",
                fragments={"text": quote},
                plagiarism_percentage=round(percentage, 2),
                type=PlagiarismInstance.QUOTE,
                module='Citation Finder',
                plagiarism_ranges=plagiarism_ranges  # Save the range information
            )

            # Accumulate the percentage of each quote
            total_citation_percentage += percentage

        # Update the report with the total percentage of citations
        report.citation_percentage = round(total_citation_percentage, 2)
        report.save()

        # Increment the task count for the document
        document.increment_tasks()
        logger.info(f"Citations found and saved for document {document_id}. Total citation percentage: {total_citation_percentage:.2f}%")
        return document_id
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found. Retrying...")
        raise self.retry(countdown=5, exc=Document.DoesNotExist)
    except Exception as e:
        logger.error(f"Error finding citations in document {document_id}: {e}")
        raise self.retry(countdown=5, exc=e)


@shared_task(bind=True, max_retries=3)
def task_process_file(self, document_id, *args, **kwargs):
    """
    Celery task to process the document's file for specific formatting and language checks.

    Args:
        document_id (int): ID of the document to process.
    """
    try:
        try:
            document = Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            # Log error and optionally stop retrying if document is critical
            logger.error(f"Document with ID {document_id} not found.")
            return  # Stop further processing for this task if document is essential
        file_path = document.document.path
        text = extract_text_from_file(file_path)

        # Perform various processing tasks
        formulas_result = process_formulas(file_path)
        invisible_symbols_result = process_invisible_symbols(file_path)
        white_spaces_result, latin_letters_result = process_lang_tool_results(get_lang_tool_results(text))

        # Save the results to the associated report
        report, _ = Report.objects.get_or_create(document=document)
        report.formulas_result = formulas_result
        report.invisible_symbols_result = invisible_symbols_result
        report.white_spaces_result = white_spaces_result
        report.latin_letters_result = latin_letters_result
        report.save()

        document.increment_tasks()
        logger.info(f"Document {document_id} processed successfully.")
        return document_id
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found. Retrying...")
        raise self.retry(countdown=5, exc=Document.DoesNotExist)
    except Exception as e:
        logger.error(f"Error processing file for document {document_id}: {e}")
        raise self.retry(countdown=5, exc=e)






@shared_task(bind=True, max_retries=3)
def task_check_plagiarism(self, document_id, *args, **kwargs):
    """
    Celery task to check for plagiarism in the document using an external service.

    Args:
        document_id (int): ID of the document to check for plagiarism.
    """
    try:
        document = Document.objects.get(pk=document_id)
        text = document.text_content
        google_searcher_url = os.getenv("GOOGLE_SEARCHER_URL")

        if not google_searcher_url:
            logger.error("GOOGLE_SEARCHER_URL environment variable is not set.")
            return

        # Encode text content and prepare search input
        file_content = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        search_input = {
            "file_content": f"data:text/plain;base64,{file_content}",
            "max_query_len": 400,
            "min_match_len": 3,
            "min_plagiarism_len": 10,
            "min_plagiarism_in_document": 50,
            "max_plagiarism_sources": 10,
            "min_link_frequency": 2,
            "min_gap_length": 10
        }

        # Send request to the external plagiarism checker service
        response = requests.post(google_searcher_url, json=search_input)
        if response.status_code != 200:
            logger.error(f"Error in plagiarism check request for document {document_id}: {response.status_code}")
            return

        plagiarism_response = response.json()
        character_count = len(text)
        plagiarism_results = process_plagiarism_entities(plagiarism_response.get('plagiarism_entities', []), text)

        # Calculate plagiarism percentages
        uniqueness_percent, error = calculate_percentages(character_count, plagiarism_results)
        if error:
            logger.error(f"Error calculating percentages: {error}")

        GPTGeneratedPercentage, HumanWrittenPercentage, error = GPTCheck(text)
        if error:
            logger.error(f"Error in GPTCheck: {error}")

        # Save plagiarism results in the report
        report = Report.objects.get(document=document)
        report.uniqueness = uniqueness_percent
        report.human_written_percentage = HumanWrittenPercentage
        report.chatgpt_generated_percentage = GPTGeneratedPercentage
        report.internet_originality_percentage = plagiarism_response.get('originality_percentage', 0)
        report.internet_plagiarism_percentage = plagiarism_response.get('plagiarism_percentage', 0)
        report.save()

        # Create plagiarism instances for each detected plagiarism entity
        for item in plagiarism_results:
            indices = item.get('indices', [])
            if indices:  # Ensure indices list is not empty
                indices_count = len(indices)
                plagiarism_percentage = 0 if indices_count == 0 else 100 - (100 * (character_count - indices_count) / character_count)
                PlagiarismInstance.objects.create(
                    report=report,
                    url=item['url'],
                    indices=str(indices),
                    type=PlagiarismInstance.PLAGIARISM,
                    module='Internet',
                    plagiarism_ranges={
                        'start': indices[0], 
                        'end': indices[-1], 
                        'length': indices_count
                    },
                    plagiarism_percentage=round(plagiarism_percentage, 2)
                )
            else:
                logger.warning(f"No indices found for entity {item['url']} in document {document_id}")

        document.increment_tasks()
        logger.info(f"Plagiarism check completed for document {document_id}.")
        return document_id

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found. Retrying...")
        raise self.retry(countdown=5, exc=Document.DoesNotExist)
    except Exception as e:
        logger.error(f"Error in plagiarism check for document {document_id}: {e}")
        raise self.retry(countdown=5, exc=e)




@shared_task(bind=True, max_retries=3)
def task_check_doc(self, document_id, *args, **kwargs):
    """
    Celery task to perform additional document checks (e.g., shingles and local comparisons).

    Args:
        document_id (int): ID of the document to check.
        new_report_id (int): ID of the report associated with the document.
    """
    try:
        document = Document.objects.get(pk=document_id)
        extracted_text = document.text_content
        preprocessed_text = preprocess_text(extracted_text)
        new_shingles = generate_shingles(preprocessed_text)
        similar_results = search_similar_shingles(new_shingles)
        text_fragments = extract_matching_fragments(preprocessed_text, new_shingles)
        report_obj = Report.objects.get(document=document)
        report = generate_report(
            similar_results,
            new_shingles,
            text_fragments,
            document.title,
            report_obj
        )

        document.increment_tasks()
        logger.info(f"Document {document_id} fully checked. Report generated.")
        return document_id
    except (Document.DoesNotExist):
        logger.error(f"Document {document_id} not found. Retrying...")
        raise self.retry(countdown=5)
    except Exception as e:
        logger.error(f"Error in document check for document {document_id}: {e}")
        raise self.retry(countdown=5, exc=e)

@shared_task
def finalize_document_status(results):
    """
    Final task to update the status of the document to 'CHECKED' after all other tasks are completed.

    Args:
        results (list): A list of document IDs from previous tasks.
    """
    try:
        document_id = results[0]
        document = Document.objects.get(pk=document_id)
        document.status = Document.CHECKED
        document.save()
        logger.info(f'Document {document_id} status updated to CHECKED.')
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found during finalization.")
    except Exception as e:
        logger.error(f"Error finalizing document status for {document_id}: {e}")


@shared_task(bind=True, max_retries=2)
def perform_ocr(self, document_id: int, ocr_languages: str = 'rus'):
    """
    Run OCR on the document if requested and save the extracted text.
    """
    if not document_id:
        logger.error("perform_ocr received an invalid document_id.")
        return

    try:
        document = Document.objects.get(pk=document_id)
        text_content = extract_text_from_pdf_ocr(document.document.path, ocr_languages)
        if text_content:
            document.text_content = text_content
            document.save()
            logger.info(f"OCR performed successfully for Document ID {document_id}.")
            return document_id
        else:
            logger.warning(f"OCR produced no text for Document ID {document_id}.")
    except Document.DoesNotExist:
        logger.error(f"Document with ID {document_id} not found. Retrying...")
        raise self.retry(countdown=5)
    except Exception as e:
        logger.error(f"Unexpected error during OCR for Document ID {document_id}: {e}")
        raise self.retry(countdown=10, exc=e)






@shared_task
def process_document(document_id, include_ocr=False, ocr_languages='rus'):
    document = Document.objects.get(pk=document_id)

    # Create the report if it doesn't exist
    report = Report.objects.create(
        title=f"Report - {document.title}",
        document=document,
        created_by=document.created_by,
    )
    report_id = report.id

    # Proceed with the processing pipeline
    ocr_task = perform_ocr.s(document_id, ocr_languages) if include_ocr else task_save_text_to_db.s(document_id)
    task_chain = chain(
        ocr_task,
        group(
            task_process_file.s(document_id),
            task_check_plagiarism.s(document_id),
            task_check_doc.s(document_id),
            task_find_citations.s(document_id)
        ) | finalize_document_status.s()
    )
    task_chain.apply_async()
    logger.info(f"Document processing task chain started for Document {document_id}.")




