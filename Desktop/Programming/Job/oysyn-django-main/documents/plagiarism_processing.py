import os
import random
import requests
from typing import List, Tuple, Dict, Any

from .models import PlagiarismInstance

def process_plagiarism_entities(entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """
    Process plagiarism entities to consolidate and remove duplicates.
    
    :param entities: List of plagiarism entities where each entity is a dictionary with 'link' and 'plagiarism_ranges'.
    :param text: The text being analyzed for plagiarism.
    :return: List of unique plagiarism instances with consolidated indices.
    """
    unique_results = {}

    for entity in entities:
        link = entity.get('link')
        if link not in unique_results:
            unique_results[link] = {
                'url': link,
                'indices': set(),  # Use a set for uniqueness
                'type': 'plagiarism'
            }
        
        for source_index, _, range_length in entity.get('plagiarism_ranges', []):
            if 0 <= source_index < len(text) and source_index + range_length <= len(text):
                unique_results[link]['indices'].update(range(source_index, source_index + range_length))
    
    # Convert indices sets back to lists for output
    return [{'url': data['url'], 'indices': list(data['indices']), 'type': data['type']} for data in unique_results.values()]

def collect_all_indices(plagiarism_results: List[Dict[str, Any]]) -> List[int]:
    """
    Collect all indices from plagiarism results.
    
    :param plagiarism_results: List of plagiarism result dictionaries.
    :return: List of all indices associated with plagiarism.
    """
    return [index for instance in plagiarism_results if instance.get("type") == "plagiarism"
            for index in instance.get("indices", [])]

def deduplicate_indices(indices: List[int]) -> List[int]:
    """
    Remove duplicate indices.
    
    :param indices: List of indices.
    :return: List of unique indices.
    """
    return list(set(indices))

def calculate_percentages(character_count: int, plagiarism_results: List[Dict[str, Any]]) -> Tuple[float, str]:
    """
    Calculate the percentage of plagiarized content.
    
    :param word_count: Total number of words in the document.
    :param plagiarism_results: List of plagiarism result dictionaries.
    :return: Tuple containing the uniqueness percentage and an optional error message.
    """
    all_indices = collect_all_indices(plagiarism_results)
    unique_indices = deduplicate_indices(all_indices)
    plagiarized_word_count = len(unique_indices)

    if character_count > 0:
        uniqueness_percent = 100.0 * (character_count - plagiarized_word_count) / character_count
        # uniqueness_percent = plagiarized_word_count * 100 / character_count
        if uniqueness_percent < 2:
            return random.uniform(2, 4), None  # Return random value between 2 and 4 if below threshold
        return uniqueness_percent, None
    return 0, "word count is zero"

def recalculate_percentages(word_count: int, instances: List[PlagiarismInstance]) -> Tuple[float, float, float]:
    """
    Recalculate the percentages for plagiarism, citation, and self-citation based on word count.
    
    :param word_count: Total number of words in the document.
    :param instances: List of PlagiarismInstance objects.
    :return: Tuple with updated percentages for plagiarism, citation, and self-citation.
    """
    if word_count == 0:
        return 0, 0, 0  # Avoid division by zero if the document has no words

    totals = {'plagiarism': 0, 'citation': 0, 'selfcitation': 0}

    for instance in instances:
        word_indices_count = len(instance.indices)  # Assuming 'indices' contains word positions
        if instance.type == PlagiarismInstance.PLAGIARISM:
            totals['plagiarism'] += word_indices_count
        elif instance.type == PlagiarismInstance.QUOTE:
            totals['citation'] += word_indices_count
        elif instance.type == PlagiarismInstance.SELFQUOTE:
            totals['selfcitation'] += word_indices_count

    # Calculate percentages based on word counts
    plagiarism_percentage = (totals['plagiarism'] / word_count) * 100
    citation_percentage = (totals['citation'] / word_count) * 100
    selfcitation_percentage = (totals['selfcitation'] / word_count) * 100

    return (
        round(plagiarism_percentage, 2),
        round(citation_percentage, 2),
        round(selfcitation_percentage, 2)
    )




class GPTResponse:
    def __init__(self, success=False, data=None, code=0, message=''):
        """
        Initialize the GPTResponse object.
        
        :param success: Boolean indicating success status.
        :param data: Response data.
        :param code: Status code.
        :param message: Response message.
        """
        self.success = success
        self.data = data if data else {}
        self.code = code
        self.message = message

def GPTCheck(input_text: str) -> Tuple[float, float, Any]:
    """
    Check the input text using GPT to determine the proportions of human-written and GPT-generated content.
    
    :param input_text: Text to be checked.
    :return: Tuple with average GPT-generated and human-written scores, and an optional error message.
    """
    if not input_text:
        return 0, 0, None

    chunk_size = 10000
    chunks = split_into_chunks(input_text, chunk_size)

    total_human_written = 0.0
    total_gpt_generated = 0.0

    for key, chunk in enumerate(chunks):
        human_written, gpt_generated, err = sendGPTCheckRequest(chunk)
        if err:
            if key < len(chunks) - 1:
                continue  # Skip to next chunk if there's an error
            return 0, 0, err

        total_human_written += human_written
        total_gpt_generated += gpt_generated

    avg_human_written = total_human_written / len(chunks)
    avg_gpt_generated = total_gpt_generated / len(chunks)

    return avg_gpt_generated, avg_human_written, None

def sendGPTCheckRequest(chunk: str) -> Tuple[float, float, Any]:
    """
    Send a request to GPT service to check the provided chunk of text.
    
    :param chunk: Text chunk to be analyzed.
    :return: Tuple with GPT-generated and human-written scores, and an optional error message.
    """
    url = os.getenv("ZEROGPTURL")
    api_key = os.getenv("X-RAPIDAPI-KEY")
    api_host = os.getenv("X-RAPIDAPI-HOST")

    if not url or not api_key or not api_host:
        return 0, 0, ValueError("Environment variables not set correctly")

    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host,
    }

    request_body = {"input_text": chunk}

    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        if not response_data.get('success'):
            return 0, 0, ValueError(f"GPT service error: {response_data.get('message')}")
        
        is_human_written = response_data['data'].get('is_human_written', 0.0)
        is_gpt_generated = response_data['data'].get('is_gpt_generated', 0.0)
        return is_human_written, is_gpt_generated, None

    except requests.exceptions.RequestException as e:
        return 0, 0, e

def split_into_chunks(input_text: str, chunk_size: int) -> List[str]:
    """
    Split text into chunks of a specified size.
    
    :param input_text: Text to be split.
    :param chunk_size: Size of each chunk.
    :return: List of text chunks.
    """
    return [input_text[i:i + chunk_size] for i in range(0, len(input_text), chunk_size)]
