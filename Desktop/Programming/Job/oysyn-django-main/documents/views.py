import json
import base64
from io import BytesIO
import qrcode
import logging
import matplotlib.pyplot as plt
from django.contrib.staticfiles import finders
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, Http404, HttpResponse
from django.template.exceptions import TemplateDoesNotExist
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now

from .forms import DocumentForm, FolderForm, DocumentUpdateForm
from .models import Document, Folder, Report, PlagiarismInstance
from .tasks import process_document
from .text_processing import get_word_count
from .plagiarism_processing import recalculate_percentages
from .renderers import render_pdf_report, render_pdf_certificate
from comments.models import Comment
from organizations.models import Organization

logger = logging.getLogger(__name__)

class HomePageView(TemplateView):
    """View for the home page."""
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = Organization.objects.exclude(logo='')
        return context

class DocumentListView(LoginRequiredMixin, ListView):
    """View to list documents created by the logged-in user."""
    model = Document
    template_name = 'document_list.html'
    ordering = ['-created_at']

    def get_queryset(self):
        """Return documents created by the current user."""
        return Document.objects.filter(created_by=self.request.user)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """View to display detailed information about a document."""
    model = Document
    template_name = 'document_detail.html'

    def get_context_data(self, **kwargs):
        """Add report and plagiarism instances to the context."""
        context = super().get_context_data(**kwargs)
        document = self.object
        report = get_object_or_404(Report, document=document)
        plagiarism_instances = PlagiarismInstance.objects.filter(report=report)
        context.update({
            'report': report,
            'plagiarism_instances': plagiarism_instances
        })
        return context


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """View to delete a document."""
    model = Document
    success_url = reverse_lazy('folder_list')
    template_name = 'document_confirm_delete.html'


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document_create.html'
    success_url = reverse_lazy('folder_list')
    
    def get_form_kwargs(self):
        """
        Pass additional keyword arguments to the form, including the user.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass the current user to the form
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('account_login'))
        
        user = request.user
        if user.organization:
            if user.organization.checks_available <= 0:
                return redirect(reverse('payments:purchase_checks'))
        else:
            if user.checks_available <= 0:
                return redirect(reverse('payments:purchase_checks'))
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        if self.request.user.organization:
            self.request.user.organization.checks_available -= 1
            self.request.user.organization.save()
        else:
            self.request.user.checks_available -= 1
            self.request.user.save()

        document_id = self.object.id
        self.object.set_estimated_completion()
        if document_id:
            # Call queue_tasks without form, as form data is already processed
            transaction.on_commit(lambda: self.queue_tasks(document_id))
        else:
            print(f"Document or report was not saved correctly. document_id: {document_id}")

        return response

    def queue_tasks(self, document_id):
        include_ocr = self.request.POST.get('include_ocr', False)
        ocr_languages = self.request.POST.getlist('ocr_languages')  # get as list
        
        # Join selected languages with "+" for pytesseract compatibility
        ocr_languages_str = "+".join(ocr_languages)
        
        process_document.apply_async(
            args=[document_id],
            kwargs={'include_ocr': include_ocr, 'ocr_languages': ocr_languages_str},
        )


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    """View to update document information."""
    model = Document
    template_name = 'document_update.html'
    form_class = DocumentUpdateForm
    def get_success_url(self):
        return reverse_lazy('report_new_details', kwargs={'pk': self.object.pk})
 
    def get_object(self):
        return Document.objects.get(pk=self.kwargs['pk'])

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'failure', 'errors': form.errors}, status=400)
        return response
    

class InstanceUpdateView(LoginRequiredMixin, UpdateView):
    """View to update a plagiarism instance."""
    model = PlagiarismInstance
    fields = ['type']
    template_name = 'instance_update.html'
    context_object_name = 'instance'

    def get_context_data(self, **kwargs):
        """Add report, instances, and highlighted text to the context."""
        context = super().get_context_data(**kwargs)
        instance = self.get_object()
        report = instance.report
        
        # instances = list(PlagiarismInstance.objects.filter(report=report))
        # Filter plagiarism instances for 'Internet' and 'Local Indices'
        plagiarism_instances_internet = (
            PlagiarismInstance.objects
            .filter(report=report, module='Internet')
            .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
        )
        plagiarism_instances_local = (
            PlagiarismInstance.objects
            .filter(report=report, module='Local Indices')
            .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
        )
        # Merge the two lists
        instances = list(plagiarism_instances_internet) + list(plagiarism_instances_local)

        # text = extract_text_from_file(report.document.document.path)
        document_id = report.document.pk
        text = get_object_or_404(Document, id=document_id).text_content
        
        highlighted_text = self.highlight_text(text, instance)
        context.update({
            'report': report,
            'instances': instances,
            'highlighted_text': highlighted_text
        })
        return context

    def form_valid(self, form):
        """Update plagiarism percentages after form validation."""
        response = super().form_valid(form)
        instance = form.instance
        report = instance.report

        word_count = get_word_count(report.document.document.path)
        instances = PlagiarismInstance.objects.filter(report=report)

        percentages = recalculate_percentages(word_count, instances)
        report.plagiarism_percentage, report.citation_percentage, report.selfcitation_percentage = percentages
        report.originality_percentage = report.calculate_final_originality()
        report.save()

        return response

    def get_success_url(self) -> str:
        """Return the URL to redirect after successful update."""
        return reverse_lazy('instance_update', kwargs={'pk': self.kwargs['pk']})

    def highlight_text(self, text, instance) -> str:
        """Highlight text in the document based on word indices."""
        # Split the text into words
        words = text.split()
        highlighted_text = ''
        last_index = 0
        indices = json.loads(instance.indices) if isinstance(instance.indices, str) else instance.indices

        if indices:
            start_word_index = indices[0]
            end_word_index = indices[-1] + 1  # Add 1 because slicing is exclusive

            # Join words before the highlighted segment
            highlighted_text += ' '.join(words[:start_word_index]) + ' '

            # Join and wrap the highlighted words
            highlighted_text += (
                f'<span class="highlight {instance.type.lower()}" '
                f'data-instance-id="{instance.id}">'
                f'{" ".join(words[start_word_index:end_word_index])}'
                f'</span> '
            )

            # Join words after the highlighted segment
            highlighted_text += ' '.join(words[end_word_index:])

        else:
            # If no indices are present, return the text as is
            highlighted_text = ' '.join(words)

        return highlighted_text


class ReportListView(LoginRequiredMixin, ListView):
    """View to list reports created by the logged-in user."""
    model = Report
    template_name = 'report_list.html'
    paginate_by = 20

    def get_queryset(self):
        """Return reports created by the current user, ordered by creation date."""
        return Report.objects.filter(created_by=self.request.user).order_by('-created_at')


class ReportDetailView(LoginRequiredMixin, DetailView):
    """View to display detailed information about a report."""
    model = Report
    template_name = 'report_detail.html'

    def get_context_data(self, **kwargs):
        """Add document and plagiarism instances to the context."""
        context = super().get_context_data(**kwargs)
        report = self.object
        document = get_object_or_404(Document, report=report)
        plagiarism_instances = PlagiarismInstance.objects.filter(report=report)
        context.update({
            'report': report,
            'document': document,
            'plagiarism_instances': plagiarism_instances
        })
        return context


class ReportNewDetailView(DetailView):
    """View to display detailed information about a new report."""
    model = Report
    template_name = 'report_new_detail.html'

    def get_context_data(self, **kwargs):
        """Add document and plagiarism instances to the context."""
        context = super().get_context_data(**kwargs)
        report = self.object
        document = get_object_or_404(Document, reports=report)

        # Filter plagiarism instances for 'Internet' and 'Local Indices'
        plagiarism_instances_internet = (
            PlagiarismInstance.objects
            .filter(report=report, module='Internet')
            .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
        )
        
        plagiarism_instances_local = (
            PlagiarismInstance.objects
            .filter(report=report, module='Local Indices')
            .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
        )

        comments = Comment.objects.filter(report=report, approved=True)
        context.update({
            'report': report,
            'document': document,
            'plagiarism_instances_internet': plagiarism_instances_internet,
            'plagiarism_instances_local': plagiarism_instances_local,
            'comments': comments,
        })
        return context


def generate_report_view(request) -> JsonResponse:
    """Generate and return a PDF with QR code for a report."""
    logger.info("Starting generate_report_view")
    report_id = request.GET.get('q')
    logger.debug(f"Report ID: {report_id}")
    report = get_object_or_404(Report, pk=report_id)
    
    # Filter plagiarism instances for 'Internet' and 'Local Indices'
    plagiarism_instances_internet = (
        PlagiarismInstance.objects
        .filter(report=report, module='Internet')
        .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
    )
    plagiarism_instances_local = (
        PlagiarismInstance.objects
        .filter(report=report, module='Local Indices')
        .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
    )
    # Merge the two lists
    plagiarism_instances = list(plagiarism_instances_internet) + list(plagiarism_instances_local)
    # Sort the merged list by plagiarism_percentage in descending order
    plagiarism_instances = sorted(plagiarism_instances, key=lambda instance: instance.plagiarism_percentage, reverse=True)

    title = report.document.title
    author = report.document.author
    document_type = report.document.get_document_type_display

    # Generate QR Code
    pdf_filename = f"report_{report_id}.pdf"
    pdf_url = request.build_absolute_uri(f"/media/documents/{report.document.created_by.email}/{report.created_at.strftime('%Y/%m/%d')}/{pdf_filename}")
    logger.debug(f"PDF URL: {pdf_url}")
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(pdf_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert QR code to base64
    qr_image_io = BytesIO()
    img.save(qr_image_io, format='PNG')
    qr_code_base64 = base64.b64encode(qr_image_io.getvalue()).decode('utf-8')
    logger.debug(f"QR Code Base64: {qr_code_base64}")

    context = {
        'report_id': report_id,
        'checked_by': report.created_by,
        'author': author,
        'document_type': document_type,
        'title': title,
        'final_originality_percentage': report.calculate_final_originality(),
        'final_plagiarism_percentage': report.calculate_final_plagiarism(),
        'final_citation_percentage': report.citation_percentage,
        'final_selfcitation_percentage': report.selfcitation_percentage,
        'chatgpt_generated_percentage': report.chatgpt_generated_percentage,
        'plagiarism_instances': plagiarism_instances,
        'qr_code_base64': qr_code_base64,
        'created_at': report.created_at,
    }

    try:
        # Generate PDF
        logger.info("Rendering PDF report")
        pdf_bytes = render_pdf_report("documents/report_template.html", context)
        if pdf_bytes is None:
            logger.error("Error generating PDF: PDF bytes are None")
            return JsonResponse({"detail": "Error generating PDF"}, status=500)
        
        # Create HttpResponse with PDF content
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"{title}.pdf"
        content = f"attachment; filename={filename}" if request.GET.get("download") else f"inline; filename={filename}"
        response["Content-Disposition"] = content
        logger.info("PDF report generated successfully")
        return response

    except TemplateDoesNotExist:
        logger.error("Template not found: documents/report_template.html")
        raise Http404("Template not found.")
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return JsonResponse({"detail": "Error generating report"}, status=500)
    

def generate_certificate_view(request) -> JsonResponse:
    """Generate and return a PDF with QR code for a certificate."""
    logger.info("Starting generate_certificate_view")
    report_id = request.GET.get('q')
    logger.debug(f"Report ID: {report_id}")
    report = get_object_or_404(Report, pk=report_id)
    title = report.document.title
    author = report.document.author
    document_type = report.document.get_document_type_display

    # Generate QR Code
    pdf_filename = f"certificate_{report_id}.pdf"
    pdf_url = request.build_absolute_uri(f"/media/documents/{report.document.created_by.email}/{report.created_at.strftime('%Y/%m/%d')}/{pdf_filename}")
    logger.debug(f"PDF URL: {pdf_url}")
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(pdf_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert QR code to base64
    qr_image_io = BytesIO()
    img.save(qr_image_io, format='PNG')
    qr_code_base64 = base64.b64encode(qr_image_io.getvalue()).decode('utf-8')
    logger.debug(f"QR Code Base64: {qr_code_base64}")

    context = {
        'report_id': report_id,
        'checked_by': report.created_by,
        'author': author,
        'document_type': document_type,
        'title': title,
        'final_originality_percentage': report.calculate_final_originality(),
        'final_plagiarism_percentage': report.calculate_final_plagiarism(),
        'final_citation_percentage': report.citation_percentage,
        'final_selfcitation_percentage': report.selfcitation_percentage,
        'chatgpt_generated_percentage': report.chatgpt_generated_percentage,
        'qr_code_base64': qr_code_base64,
        'created_at': report.created_at,
    }

    try:
        # Generate PDF
        logger.info("Rendering PDF certificate")
        pdf_bytes = render_pdf_certificate("documents/certificate_template.html", context)
        if pdf_bytes is None:
            logger.error("Error generating PDF: PDF bytes are None")
            return JsonResponse({"detail": "Error generating PDF"}, status=500)
        
        # Create HttpResponse with PDF content
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"{title}.pdf"
        content = f"attachment; filename={filename}" if request.GET.get("download") else f"inline; filename={filename}"
        response["Content-Disposition"] = content
        logger.info("PDF certificate generated successfully")
        return response

    except TemplateDoesNotExist:
        logger.error("Template not found: documents/certificate_template.html")
        raise Http404("Template not found.")
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        return JsonResponse({"detail": "Error generating certificate"}, status=500)


class DocumentHighlightView(View):
    template_name = 'document_highlight.html'

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        report = document.report_set.first()
        plagiarism_instances = list(PlagiarismInstance.objects.filter(report=report).values('id', 'plagiarism_ranges', 'type'))

        context = {
            'document': document,
            'plagiarism_instances': json.dumps(plagiarism_instances, cls=DjangoJSONEncoder),
        }
        return render(request, self.template_name, context)


class FolderListView(LoginRequiredMixin, View):
    """List folders and documents for the current user, including root documents."""

    def get(self, request):
        user = request.user
        # Fetch all folders created by the user, with document counts
        folders = Folder.objects.filter(created_by=user, parent_folder=None) \
            .annotate(document_count=Count('documents')) \
            .prefetch_related('subfolders')
        
        # Fetch documents that are not associated with any folder (root documents)
        root_documents = Document.objects.filter(created_by=user, folder__isnull=True).prefetch_related('reports')
        root_document_count = root_documents.count()
        
        # Add report details to each root document
        root_documents_with_reports = []
        for doc in root_documents:
            report = doc.reports.first()  # Fetch the first report if it exists
            root_documents_with_reports.append({
                'id': doc.id,
                'report_id': report.id if report else None,
                'title': doc.title,
                'status': doc.get_status_display(),
                'created_at': doc.created_at,
                'final_originality': report.final_originality if report else "N/A",
                'has_passed': report.has_passed_originality_check if report else False,
            })
        
        return render(request, 'folder_list_root.html', {
            'folders': folders,
            'root_documents': root_documents_with_reports,
            'root_documents_count': root_document_count,
        })
    

class FolderCreateAjaxView(LoginRequiredMixin, View):
    """View to handle AJAX folder creation."""
    def post(self, request, *args, **kwargs):
        parent_folder_id = request.POST.get('parent_folder_id')
        parent_folder = None
        
        if parent_folder_id:
            parent_folder = get_object_or_404(Folder, id=parent_folder_id, created_by=request.user)
        
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.created_by = request.user
            folder.parent_folder = parent_folder
            folder.save()
            return JsonResponse({'id': folder.id, 'name': folder.name, 'parent_folder_id': parent_folder_id}, status=201)
        
        return JsonResponse({"errors": form.errors}, status=400)


class FolderUpdateAjaxView(View):
    """View to handle AJAX folder updates using PUT."""

    def put(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id)
        
        # Parse JSON data from the PUT request
        try:
            data = json.loads(request.body)
            new_name = data.get('name', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data."}, status=400)

        # Validate new folder name
        if not new_name:
            return JsonResponse({"success": False, "message": "Folder name cannot be empty."}, status=400)

        # Update the folder's name
        folder.name = new_name
        folder.save()

        return JsonResponse({"success": True, "name": folder.name, "message": "Folder updated successfully."})


class FolderMoveAjaxView(View):
    """Handle folder move operations via AJAX."""

    def put(self, request, folder_id):
        try:
            folder = Folder.objects.get(id=folder_id, created_by=request.user)
            data = json.loads(request.body)
            new_parent_id = data.get('parent_folder_id')

            if new_parent_id:
                new_parent = Folder.objects.get(id=new_parent_id, created_by=request.user)
                folder.parent_folder = new_parent
            else:
                folder.parent_folder = None  # Move to root

            folder.save()
            return JsonResponse({'message': 'Folder moved successfully'}, status=200)
        except Folder.DoesNotExist:
            return JsonResponse({'error': 'Folder not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class FolderDeleteAjaxView(LoginRequiredMixin, View):
    """View to handle AJAX folder deletion."""
    
    def delete(self, request, pk, *args, **kwargs):
        folder = get_object_or_404(Folder, pk=pk, created_by=request.user)
        folder.delete()
        return JsonResponse({"success": True, "message": "Folder deleted successfully."}, status=200)


class DocumentListView(LoginRequiredMixin, View):
    def get(self, request, folder_id=None):
        search_keyword = request.GET.get('search', '').strip()  # Get the search keyword

        # Filter documents based on folder and search keyword
        if folder_id == 0:
            documents = Document.objects.filter(folder__isnull=True, created_by=request.user)
        else:
            folder = get_object_or_404(Folder, id=folder_id, created_by=request.user)
            documents = folder.documents.filter(created_by=request.user)

        # If there's a search keyword, filter documents by title
        if search_keyword:
            documents = documents.filter(title__icontains=search_keyword)

        documents = documents.order_by("-created_at")

        document_list = []
        for document in documents:
            # Calculate remaining time for processing documents
            remaining_seconds = (
                (document.estimated_completion - now()).total_seconds() 
                if document.status == Document.PROCESSING and document.estimated_completion 
                else None
            )

            report = document.reports.first()  # Get the related report if it exists
            document_list.append({
                "id": document.id,
                "title": document.title,
                "status": document.status,
                "created_at": document.created_at.isoformat(),
                "final_originality": report.final_originality if report else "N/A",  # Add final_originality
                "remaining_seconds": remaining_seconds,  # Include remaining time in seconds
                "report_id": report.id if report else None,  # Check if report is None
                "has_passed": report.has_passed_originality_check if report else False,
            })

        return JsonResponse(document_list, safe=False)


class MoveDocumentsView(View):
    """View to move documents to a selected folder."""

    def put(self, request):
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            folder_id = data.get('folder_id')
            document_ids = data.get('document_ids', [])

            # Validate and fetch the destination folder (None for root folder)
            if folder_id == 'root' or folder_id is None:
                target_folder = None
            else:
                target_folder = get_object_or_404(Folder, pk=folder_id, created_by=request.user)

            # Move each document to the target folder
            documents = Document.objects.filter(id__in=document_ids, created_by=request.user)
            updated_count = documents.update(folder=target_folder)

            return JsonResponse({
                "success": True,
                "message": f"{updated_count} document(s) moved successfully."
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data."}, status=400)
        except Folder.DoesNotExist:
            return JsonResponse({"success": False, "message": "Target folder not found."}, status=404)
        except Document.DoesNotExist:
            return JsonResponse({"success": False, "message": "One or more documents not found."}, status=404)


class DeleteDocumentsView(View):
    """View to delete selected documents."""

    def delete(self, request):
        try:
            data = json.loads(request.body)
            document_ids = data.get('document_ids', [])

            # Filter and delete documents owned by the current user
            deleted_count, _ = Document.objects.filter(id__in=document_ids, created_by=request.user).delete()

            return JsonResponse({"success": True, "message": f"{deleted_count} document(s) deleted successfully."}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data."}, status=400)


class DocumentSearchView(View):
    def get(self, request):
        keyword = request.GET.get('keyword', '')
        fields = request.GET.get('fields', '').split(',')
        sort_order = request.GET.get('sort', 'title')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # Filter documents based on selected fields and keyword
        query = Document.objects.filter(created_by=request.user)
        if 'title' in fields:
            query = query.filter(title__icontains=keyword)
        if 'author' in fields:
            query = query.filter(author__icontains=keyword)
        if 'text_content' in fields:
            query = query.filter(text_content__icontains=keyword)
        
        # Sort documents
        query = query.order_by(sort_order)

        # Paginate results
        paginator = Paginator(query, page_size)
        documents = paginator.get_page(page)

        # Prepare the document list
        document_list = [{
            'id': doc.id,
            'title': doc.title,
            'author': doc.author,
            'status': doc.get_status_display(),
            'created_at': doc.created_at.strftime('%d.%m.%y %H:%M'),
            'final_originality': doc.reports.first().final_originality if doc.reports.exists() else 'N/A'
        } for doc in documents]

        return JsonResponse({
            'documents': document_list,
            'total_pages': paginator.num_pages
        })


class DocumentSearchPageView(TemplateView):
    template_name = 'document_search.html'


class AboutOysynView(TemplateView):
    template_name = "about_oysyn.html"


def generate_new_certificate_view(request) -> JsonResponse:
    """Generate and return a PDF with QR code for a certificate."""
    logger.info("Starting generate_certificate_view")
    report_id = request.GET.get('q')
    report = get_object_or_404(Report, pk=report_id)
    organization = report.document.created_by.organization
    organization_logo_base64 = None
    if organization:
        organization_name = organization.title
        if organization.logo:
            with open(organization.logo.path, 'rb') as logo_file:
                organization_logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
    else:
        organization_name = ""
    document = report.document
    title = document.title
    author = document.author
    department = document.department
    document_type = document.get_document_type_display

    # Generate QR Code
    pdf_filename = f"certificate_{report_id}.pdf"
    correct_date = now().strftime('%Y/%m/%d') 
    pdf_url = request.build_absolute_uri(f"/media/documents/{report.document.created_by.email}/{correct_date}/{pdf_filename}")
    logger.debug(f"PDF URL: {pdf_url}")
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(pdf_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert QR code to base64
    qr_image_io = BytesIO()
    img.save(qr_image_io, format='PNG')
    qr_code_base64 = base64.b64encode(qr_image_io.getvalue()).decode('utf-8')
    logger.debug(f"QR Code Base64: {qr_code_base64}")

    # Load OySyn logo from static folder and convert to base64
    oysyn_logo_path = finders.find('images/oysyn-logo-blue-on-white.jpg')
    with open(oysyn_logo_path, 'rb') as logo_file:
        oysyn_logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')

    # Generate Chart
    labels = ['Оригинальность', 'Заимствования', 'Цитирования', 'Самоцитирования']
    sizes = [
        report.calculate_final_originality(),
        report.calculate_final_plagiarism(),
        report.citation_percentage,
        report.selfcitation_percentage
    ]
    colors = ['#4CAF50', '#FF5733', '#FFC300', '#C70039']
    fig, ax = plt.subplots()
    bars = ax.bar(labels, sizes, color=colors)
    ax.set_ylabel('Проценты')
    ax.set_title('')
    # Remove the border (spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    # Add text labels to the bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.1f}%', ha='center', va='bottom')
    # Convert chart to base64
    chart_image_io = BytesIO()
    plt.savefig(chart_image_io, format='PNG')
    chart_image_io.seek(0)
    chart_base64 = base64.b64encode(chart_image_io.getvalue()).decode('utf-8')
    plt.close(fig)

    context = {
        'report_id': report_id,
        'checked_by': report.created_by,
        'author': author,
        'department': department,
        'document_type': document_type,
        'title': title,
        'final_originality_percentage': report.calculate_final_originality(),
        'final_plagiarism_percentage': report.calculate_final_plagiarism(),
        'final_citation_percentage': report.citation_percentage,
        'final_selfcitation_percentage': report.selfcitation_percentage,
        'chatgpt_generated_percentage': report.chatgpt_generated_percentage,
        'qr_code_base64': qr_code_base64,
        'created_at': report.created_at,
        'organization_name': organization_name,
        'organization_logo_base64': organization_logo_base64,
        'oysyn_logo_base64': oysyn_logo_base64,  # Add OySyn logo to context
        'chart_base64': chart_base64,  # Add chart to context
    }

    try:
        # Generate PDF
        logger.info("Rendering PDF certificate")
        pdf_bytes = render_pdf_certificate("documents/certificate_new_template.html", context)
        if pdf_bytes is None:
            logger.error("Error generating PDF: PDF bytes are None")
            return JsonResponse({"detail": "Error generating PDF"}, status=500)
        
        # Create HttpResponse with PDF content
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"{title}.pdf"
        content = f"attachment; filename={filename}" if request.GET.get("download") else f"inline; filename={filename}"
        response["Content-Disposition"] = content
        logger.info("PDF certificate generated successfully")
        return response

    except TemplateDoesNotExist:
        logger.error("Template not found: documents/certificate_new_template.html")
        raise Http404("Template not found.")
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        return JsonResponse({"detail": "Error generating certificate"}, status=500)


def generate_new_report_view(request) -> JsonResponse:
    """Generate and return a PDF with QR code for a report."""
    logger.info("Starting generate_report_view")
    report_id = request.GET.get('q')
    logger.debug(f"Report ID: {report_id}")
    report = get_object_or_404(Report, pk=report_id)
    
    # Filter plagiarism instances for 'Internet' and 'Local Indices'
    plagiarism_instances_internet = (
        PlagiarismInstance.objects
        .filter(report=report, module='Internet')
        .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
    )
    plagiarism_instances_local = (
        PlagiarismInstance.objects
        .filter(report=report, module='Local Indices')
        .order_by('-plagiarism_percentage')[:10]  # Get top 10 by plagiarism_percentage
    )
    # Merge the two lists
    plagiarism_instances = list(plagiarism_instances_internet) + list(plagiarism_instances_local)
    # Sort the merged list by plagiarism_percentage in descending order
    plagiarism_instances = sorted(plagiarism_instances, key=lambda instance: instance.plagiarism_percentage, reverse=True)

    organization = report.document.created_by.organization
    organization_logo_base64 = None
    if organization:
        organization_name = organization.title
        if organization.logo:
            with open(organization.logo.path, 'rb') as logo_file:
                organization_logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
    else:
        organization_name = ""
    document = report.document
    title = document.title
    author = document.author
    department = document.department
    document_type = document.get_document_type_display

    # Generate QR Code
    pdf_filename = f"report_{report_id}.pdf"
    correct_date = now().strftime('%Y/%m/%d') 
    pdf_url = request.build_absolute_uri(f"/media/documents/{report.document.created_by.email}/{correct_date}/{pdf_filename}")
    logger.debug(f"PDF URL: {pdf_url}")
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(pdf_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert QR code to base64
    qr_image_io = BytesIO()
    img.save(qr_image_io, format='PNG')
    qr_code_base64 = base64.b64encode(qr_image_io.getvalue()).decode('utf-8')
    logger.debug(f"QR Code Base64: {qr_code_base64}")

    # Load OySyn logo from static folder and convert to base64
    oysyn_logo_path = finders.find('images/oysyn-logo-blue-on-white.jpg')
    with open(oysyn_logo_path, 'rb') as logo_file:
        oysyn_logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')

    # Generate Chart
    labels = ['Оригинальность', 'Заимствования', 'Цитирования', 'Самоцитирования']
    sizes = [
        report.calculate_final_originality(),
        report.calculate_final_plagiarism(),
        report.citation_percentage,
        report.selfcitation_percentage
    ]
    colors = ['#4CAF50', '#FF5733', '#FFC300', '#C70039']
    fig, ax = plt.subplots()
    bars = ax.bar(labels, sizes, color=colors)
    ax.set_ylabel('Проценты')
    ax.set_title('')
    # Remove the border (spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    # Add text labels to the bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.1f}%', ha='center', va='bottom')
    # Convert chart to base64
    chart_image_io = BytesIO()
    plt.savefig(chart_image_io, format='PNG')
    chart_image_io.seek(0)
    chart_base64 = base64.b64encode(chart_image_io.getvalue()).decode('utf-8')
    plt.close(fig)

    context = {
        'report_id': report_id,
        'checked_by': report.created_by,
        'author': author,
        'department': department,
        'document_type': document_type,
        'title': title,
        'final_originality_percentage': report.calculate_final_originality(),
        'final_plagiarism_percentage': report.calculate_final_plagiarism(),
        'final_citation_percentage': report.citation_percentage,
        'final_selfcitation_percentage': report.selfcitation_percentage,
        'chatgpt_generated_percentage': report.chatgpt_generated_percentage,
        'plagiarism_instances': plagiarism_instances,
        'qr_code_base64': qr_code_base64,
        'created_at': report.created_at,
        'organization_name': organization_name,
        'organization_logo_base64': organization_logo_base64,
        'oysyn_logo_base64': oysyn_logo_base64,
        'chart_base64': chart_base64,
    }

    try:
        # Generate PDF
        logger.info("Rendering PDF report")
        pdf_bytes = render_pdf_report("documents/report_new_template.html", context)
        if pdf_bytes is None:
            logger.error("Error generating PDF: PDF bytes are None")
            return JsonResponse({"detail": "Error generating PDF"}, status=500)
        
        # Create HttpResponse with PDF content
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"{title}.pdf"
        content = f"attachment; filename={filename}" if request.GET.get("download") else f"inline; filename={filename}"
        response["Content-Disposition"] = content
        logger.info("PDF report generated successfully")
        return response

    except TemplateDoesNotExist:
        logger.error("Template not found: documents/report_new_template.html")
        raise Http404("Template not found.")
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return JsonResponse({"detail": "Error generating report"}, status=500)