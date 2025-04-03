from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from documents.models import Report

User = get_user_model()

class Comment(models.Model):
    report = models.ForeignKey(
        Report,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='comments'  # Allows accessing comments via report.comments
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    text = models.TextField(_('Text of the comment'))
    approved = models.BooleanField(_('Is text approved'), default=True)

    def __str__(self):
        return f"Comment by {self.created_by} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-created_at']  # Optional: order comments by creation date descending
