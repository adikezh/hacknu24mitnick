from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    CITY_CHOICES = [
        ('ALA', 'Алматы'),
        ('NQZ', 'Астана'),
        ('SCO', 'Актау'),
        ('AKX', 'Актобе'),
        ('GUW', 'Атырау'),
        ('AYK', 'Аркалык'),
        ('BXH', 'Балхаш'),
        ('BXY', 'Байконур'),
        ('DMB', 'Тараз'),
        ('DZN', 'Жезказган'),
        ('KGF', 'Караганда'),
        ('KOV', 'Кокшетау'),
        ('KSN', 'Костанай'),
        ('KZO', 'Кызылорда'),
        ('PWQ', 'Павлодар'),
        ('PPK', 'Петропавловск'),
        ('TSE', 'Талдыкорган'),
        ('TTT', 'Темиртау'),
        ('UKK', 'Усть-Каменогорск'),
        ('URA', 'Уральск'),
        ('PLX', 'Семей'),
        ('CIT', 'Шымкент'),
        ('CAY', 'Зайсан'),
    ]

    # required fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='organizations'
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    title = models.CharField(
        _('Title'),
        max_length=200,
        help_text=_("Name of the organization")
    )
    city = models.CharField(
        _('City'), 
        max_length=3, 
        choices=CITY_CHOICES,
        help_text=_("City where the organization is based")
    )
    address = models.CharField(
        _('Address'), 
        max_length=300,
        help_text=_("Full address of the organization")
    )
    logo = models.ImageField(
        upload_to='organization/',
        blank=True,
        null=True,
        help_text='Logo of the organization'
    )

    # not-required fields
    description = models.TextField(_('Description'), blank=True,
                                   help_text=_("Short information about the organization"))
    checks_available = models.PositiveIntegerField(
        _('checks available'),
        default=10,
        help_text=_('Number of documents the organization can check.')
    )

    # Threshold fields for document originality
    article_threshold = models.IntegerField(
        _('Article originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for articles")
    )
    course_work_threshold = models.IntegerField(
        _('Course work originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for course works")
    )
    doctoral_threshold = models.IntegerField(
        _('Doctoral originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for doctoral works")
    )
    diploma_thesis_threshold = models.IntegerField(
        _('Diploma thesis originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for diploma theses")
    )
    diploma_project_threshold = models.IntegerField(
        _('Diploma project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for diploma projects")
    )
    masters_thesis_threshold = models.IntegerField(
        _('Masters thesis project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for masters thesis")
    )
    study_guide_threshold = models.IntegerField(
        _('Study guide project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for study guides")
    )
    textbook_threshold = models.IntegerField(
        _('Textbook project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for textbooks")
    )
    book_threshold = models.IntegerField(
        _('Book project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for books")
    )
    research_threshold = models.IntegerField(
        _('Research project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for researches")
    )
    monograph_threshold = models.IntegerField(
        _('Monograph project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for monographs")
    )
    abstract_threshold = models.IntegerField(
        _('Abstract project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for abstracts")
    )
    other_threshold = models.IntegerField(
        _('Other documents project originality threshold'),
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum originality percentage required for other documents")
    )
    
    def __str__(self):
        return self.title
