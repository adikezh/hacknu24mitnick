import os
from datetime import datetime
from django.db import models
from users.models import CustomUser
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


User = get_user_model()


def user_directory_path(instance, filename):
    date = datetime.now().strftime('%Y/%m/%d')
    max_filename_length = 100
    base_filename, file_extension = os.path.splitext(filename)
    if len(base_filename) > max_filename_length:
        base_filename = base_filename[:max_filename_length]
    filename = f"documents/{instance.created_by.email}/{date}/{base_filename}{file_extension}"
    return filename
    

class Folder(models.Model):
    name = models.CharField(_('Folder Name'), max_length=512)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='folders')
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE,
                                      null=True, blank=True,
                                      related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'created_by', 'parent_folder')
        verbose_name = _('Folder')
        verbose_name_plural = _('Folders')
    
    def __str__(self):
        return self.name
    

class Document(models.Model):

    # Document status choices
    UPLOADED = 'UP'
    PROCESSING = 'PR'
    CHECKED = 'CH'
    FAILED = 'FA'
    DOCUMENT_STATUS_CHOICES = {
        UPLOADED: _('Uploaded'),
        PROCESSING: _('Checking'),
        CHECKED: _('Checked'),
        FAILED: _('Error'),
    }

    # Document type choices
    ARTICLE = 'ARTICLE'
    COURSE_WORK = 'COURSE WORK'
    DOCTORAL = 'DOCTORAL'
    DIPLOMA_THESIS = 'DIPLOMA THESIS'
    DIPLOMA_PROJECT = 'DIPLOMA PROJECT'
    MASTERS = 'MASTERS'
    STUDYGUIDE = 'STUDYGUIDE'
    TEXTBOOK = 'TEXTBOOK'
    BOOK = 'BOOK'
    RESEARCH = 'RESEARCH'
    MONOGRAPH = 'MONOGRAPH'
    ABSTRACT = 'ABSTRACT'
    OTHER = 'OTHER'
    DOCUMENT_TYPE_CHOICES = {
        ARTICLE: _('Article'),
        COURSE_WORK: _('Course work'),
        DOCTORAL: _('Doctoral dissertation'),
        DIPLOMA_THESIS: _('Diploma thesis'),
        DIPLOMA_PROJECT: _('Diploma project'),
        MASTERS: _('Masters dissertation'),
        STUDYGUIDE: _('Study guide'),
        TEXTBOOK: _('Textbook'),
        BOOK: _('Book'),
        RESEARCH: _('Research'),
        MONOGRAPH: _('Monograph'),
        ABSTRACT: _('Abstract'),
        OTHER: _('Other'),
    }

    # Required fields
    title = models.CharField(_('title'), max_length=1024)
    author = models.CharField(_('author'), max_length=512, default='')
    department = models.CharField(
        _('Department'),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("Department name")
    )
    document_type = models.CharField(
        _('Document type'),
        max_length=16,
        choices=DOCUMENT_TYPE_CHOICES,
        default=ARTICLE
    )
    document = models.FileField(
        _('description'),
        upload_to=user_directory_path,
        validators=[FileExtensionValidator(['pdf', 'docx', 'txt'])],
        max_length=1024
    )
    
    # auto fields
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Not-required fields
    text_content = models.TextField(
        _('text content'),
        null=True,
        blank=True,
        help_text=_('Stores the extracted text of the document')
    )
    status = models.CharField(
        _('status'),
        max_length=2,
        choices=DOCUMENT_STATUS_CHOICES,
        default=PROCESSING
    )
    tasks_completed = models.IntegerField(
        default=0,
        help_text=_('How many tasks is completed')
    )
    include_ocr = models.BooleanField(
        _("Enable OCR"), default=False,
        help_text=_("Extract text using OCR recognition (only pdf files)")
    )
    ocr_languages = models.CharField(
        _("OCR languages"), max_length=30, default="rus",
        help_text=_("For example: 'eng+rus+kaz'")
    ) 
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents')
    
    estimated_completion = models.DateTimeField(
        _('estimated check completion'), 
        null=True, blank=True, 
        help_text=_("The estimated time when the document will be fully processed")
    )

    def __str__(self):
        return self.title

    def is_checked(self):
        return self.status == self.CHECKED

    def increment_tasks(self):
        """Increment the number of completed tasks atomically."""
        Document.objects.filter(pk=self.pk).update(tasks_completed=models.F('tasks_completed') + 1)

    def all_tasks_completed(self):
        return self.tasks_completed == 4
    
    def set_estimated_completion(self, processing_duration=timedelta(minutes=3)):
        """Set the estimated completion time based on the start time and duration."""
        if self.status == self.PROCESSING:
            self.estimated_completion = timezone.now() + processing_duration
            self.save()


class Report(models.Model):
    # Required fields
    title = models.CharField(_('title'), max_length=1024)
    document = models.ForeignKey(Document, on_delete=models.CASCADE,
                                   related_name='reports')
    created_at = models.DateTimeField(
        _('created at'), auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Not-required fields
    internet_originality_percentage = models.FloatField(
        _('originality percentage (internet)'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text=_('Text originality percentage from Internet module'),
    )
    internet_plagiarism_percentage = models.FloatField(
        _('plagiarism percentage (internet)'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text=_('Text plagiarism percentage from Internet module'),
    )
    uniqueness = models.IntegerField(
        _('uniqueness'), 
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)]
    )
    human_written_percentage = models.FloatField(
        _('human written percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)]
    )
    chatgpt_generated_percentage = models.FloatField(
        _('chatgpt generated percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)]
    )
    formulas_result = models.JSONField(
        _('formulas result'), blank=True, default=dict)
    invisible_symbols_result = models.JSONField(
        _('invisible symbols result'), blank=True, default=dict)
    white_spaces_result = models.JSONField(
        _('white spaces result'), blank=True, default=dict)
    latin_letters_result = models.JSONField(
        _('latin letters result'), blank=True, default=dict)
    pdf_report  = models.FileField(
        _('pdf report'),
        upload_to=user_directory_path,
        blank=True, null=True,
    )
    pdf_certificate = models.FileField(
        _('certificate'),
        upload_to=user_directory_path,
        blank=True, null=True,   
    )

    # Index comparison results
    originality_percentage = models.FloatField(
        _('originality percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)]
    )
    plagiarism_percentage = models.FloatField(
        _('plagiarism percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
    )
    citation_percentage = models.FloatField(
        _('citation percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
    )
    selfcitation_percentage = models.FloatField(
        _('selfcitation percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
    )
    shingles_total_number = models.IntegerField(
        _('shingles total number'),
        default=0,
        help_text=_("Total number of shingles in the document")
    )
    
    def calculate_final_originality(self):
        """
        Calculate the final originality percentage based on internet and local metrics.
        """
        final_originality = (100 -
                             self.internet_plagiarism_percentage -
                             self.plagiarism_percentage -
                             self.citation_percentage - 
                             self.selfcitation_percentage)
        return max(0, min(100, round(final_originality, 2)))

    def calculate_final_plagiarism(self):
        """
        Calculate the final plagiarism percentage based on internet and local metrics.
        """
        final_plagiarism = (
            self.internet_plagiarism_percentage +
            self.plagiarism_percentage
        )
        return min(100, round(final_plagiarism, 2))
    
    @property
    def final_originality(self):
        """Property to get the calculated final originality percentage."""
        return self.calculate_final_originality()

    @property
    def final_plagiarism(self):
        """Property to get the calculated final plagiarism percentage."""
        return self.calculate_final_plagiarism()

    @property
    def has_passed_originality_check(self):
        """
        Returns True if the report's final originality is greater than the minimum threshold
        defined by the organization (if available) or the default values.
        """
        document = self.document
        document_type = document.document_type

        # If user has an organization, get thresholds from there
        organization = getattr(document.created_by, 'organization', None)
        if organization:
            if document_type == Document.ARTICLE:
                min_threshold = organization.article_threshold
            elif document_type == Document.COURSE_WORK:
                min_threshold = organization.course_work_threshold
            elif document_type == Document.DOCTORAL:
                min_threshold = organization.doctoral_threshold
            elif document_type == Document.DIPLOMA_THESIS:
                min_threshold = organization.diploma_thesis_threshold
            elif document_type == Document.DIPLOMA_PROJECT:
                min_threshold = organization.diploma_project_threshold
            elif document_type == Document.MASTERS:
                min_threshold = organization.masters_thesis_threshold
            elif document_type == Document.STUDYGUIDE:
                min_threshold = organization.study_guide_threshold
            elif document_type == Document.TEXTBOOK:
                min_threshold = organization.textbook_threshold
            elif document_type == Document.BOOK:
                min_threshold = organization.book_threshold
            elif document_type == Document.RESEARCH:
                min_threshold = organization.research_threshold
            elif document_type == Document.MONOGRAPH:
                min_threshold = organization.monograph_threshold
            elif document_type == Document.ABSTRACT:
                min_threshold = organization.abstract_threshold
            else:
                min_threshold = organization.other_threshold
        else:
            # Fall back to default thresholds if no organization is associated
            defaults = {
                Document.ARTICLE: 80,
                Document.COURSE_WORK: 50,
                Document.DOCTORAL: 75,
                Document.DIPLOMA_THESIS: 50,
                Document.DIPLOMA_PROJECT: 50,
                Document.MASTERS: 75,
                Document.STUDYGUIDE: 80,
                Document.TEXTBOOK: 80,
                Document.BOOK: 80,
                Document.RESEARCH: 80,
                Document.MONOGRAPH: 75,
                Document.ABSTRACT: 80,
            }
            min_threshold = defaults.get(document_type, 0)
        
        return self.final_originality >= min_threshold
    
    def __str__(self):
        return self.title
    

class PlagiarismInstance(models.Model):

    PLAGIARISM = 'PLAGIARISM'
    QUOTE = 'QUOTE'
    SELFQUOTE = 'SELFQUOTE'
    PLAGIARISM_INSTANCE_TYPE_CHOICES = {
        PLAGIARISM: _('Plagiarism'),
        QUOTE: _('Citation'),
        SELFQUOTE: _('Selfcitation'),
    }

    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    url = models.TextField(
        _('url'), blank=True,
        help_text=_('Link to the document from which the text was borrowed.'))
    plagiarism_ranges = models.JSONField(
        _('plagiarism ranges'),
        blank=True, default=dict,
        help_text=_("range of borrowed characters: start, end, length."))
    plagiarism_characters_count = models.IntegerField(
        _("plagiarism characters count"),
        default=0,
        help_text=_("Characters count of plagiarism instance."),
    )
    indices = models.JSONField(_('indices'), blank=True, default=dict)
    type = models.CharField(
        _('type'),
        max_length=16,
        choices=PLAGIARISM_INSTANCE_TYPE_CHOICES,
        default=PLAGIARISM
    )

    # data from local indices check
    title = models.CharField(
        _('title'),
        max_length=1024,
        help_text=_("The title of the document from which the text was borrowed."),
        blank=True,
    )
    module = models.CharField(
        _('module'),
        max_length=200,
        help_text=_("The module containing original document."),
        blank=True,
    )
    shingles = models.JSONField(
        _('shingles'),
        blank=True, default=dict,
        help_text=_("Intersecting shingles."),
    )
    fragments = models.JSONField(
        _('fragments'),
        blank=True, default=dict,
        help_text=_("Borrowed text in preprocessed format."),
    )
    plagiarism_percentage = models.FloatField(
        _('plagiarism percentage'),
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text=_("Counted by formula: plagiarised_shingles / total_shingles * 100")
    )

    def __str__(self):
        title = self.title
        if title:
            return title
        else:
            return f"Plagiarism instance {self.id}"
