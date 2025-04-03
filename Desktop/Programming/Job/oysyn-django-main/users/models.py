from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        MODERATOR = 'MOD', 'Moderator'
        EXPERT = 'EXP', 'Expert'
    
    role = models.CharField(
        _('role'),
        max_length=3,
        choices=Role.choices,
        default=Role.EXPERT,
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    checks_available = models.PositiveIntegerField(
        _('checks available'),
        default=1,
        help_text=_('Number of documents user can check.')
    )
    middle_name = models.CharField(_('middle name'), max_length=100, blank=True, null=True) # Patronymic
    iin = models.PositiveBigIntegerField(_('IIN'), blank=True, null=True)  # Individual Identification Number
    city = models.CharField(_('city'), max_length=100, blank=True, null=True)
    address = models.CharField(_('address'), max_length=255, blank=True, null=True)
    zip_code = models.CharField(_('zip code'), max_length=20, blank=True, null=True)

    def __str__(self):
        return self.email

    @property
    def is_moderator(self):
        """Check if the user is a moderator."""
        return self.role == self.Role.MODERATOR

    @property
    def is_expert(self):
        """Check if the user is an expert."""
        return self.role == self.Role.EXPERT
