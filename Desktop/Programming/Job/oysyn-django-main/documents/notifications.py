from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Document


def notify_user(request, document):
    messages.success(request, _('All tasks are completed and the document status is now updated to Checked.'))
    document.status = Document.CHECKED
    document.save()
    