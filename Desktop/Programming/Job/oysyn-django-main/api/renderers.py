import logging
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist
from xhtml2pdf import pisa
from documents.models import Report

logger = logging.getLogger(__name__)

def render_pdf_report(template_src, context_dict={}):
    logger.info("Starting render_pdf_report")
    # Load the template
    try:
        template = get_template(template_src)
    except TemplateDoesNotExist as e:
        logger.error(f"Template does not exist: {e}")
        return None
    
    # Render the template with the context
    html = template.render(context_dict)
    logger.debug(f"Rendered HTML: {html[:500]}")  # Log the first 500 characters of the HTML
    
    # Create a BytesIO buffer to hold the PDF data
    result = BytesIO()
    
    # Convert the HTML to PDF using UTF-8 encoding
    pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)
    
    # Check for errors during PDF generation
    if pdf.err:
        logger.error("Error generating PDF")
        return None
    
    # Save the PDF to the model
    result.seek(0)  # Rewind the buffer to the beginning
    report_id = context_dict.get('report_id')
    
    if not report_id:
        logger.error("No report ID provided in context")
        return None
    try:
        report = get_object_or_404(Report, pk=report_id)
        report.pdf_report.save(f"report_{report_id}.pdf", ContentFile(result.read()), save=True)
    except Exception as e:
        logger.error(f"Error saving PDF: {e}")
        return None
    # Return the PDF as bytes
    result.seek(0)  # Rewind the buffer to the beginning
    logger.info("PDF report rendered successfully")
    return result.getvalue()
    
def render_pdf_certificate(template_src, context_dict={}):
    logger.info("Starting render_pdf_certificate")
    # Load the template
    try:
        template = get_template(template_src)
    except TemplateDoesNotExist as e:
        logger.error(f"Template does not exist: {e}")
        return None
    
    # Render the template with the context
    html = template.render(context_dict)
    logger.debug(f"Rendered HTML: {html[:500]}")  # Log the first 500 characters of the HTML
    
    # Create a BytesIO buffer to hold the PDF data
    result = BytesIO()
    
    # Convert the HTML to PDF using UTF-8 encoding
    pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)
    
    # Check for errors during PDF generation
    if pdf.err:
        logger.error("Error generating PDF")
        return None
    
    # Save the PDF to the model
    result.seek(0)  # Rewind the buffer to the beginning
    report_id = context_dict.get('report_id')
    
    if not report_id:
        logger.error("No report ID provided in context")
        return None
    try:
        report = get_object_or_404(Report, pk=report_id)
        report.pdf_certificate.save(f"certificate_{report_id}.pdf", ContentFile(result.read()), save=True)
    except Exception as e:
        logger.error(f"Error saving PDF: {e}")
        return None
    # Return the PDF as bytes
    result.seek(0)  # Rewind the buffer to the beginning
    logger.info("PDF certificate rendered successfully")
    return result.getvalue()
