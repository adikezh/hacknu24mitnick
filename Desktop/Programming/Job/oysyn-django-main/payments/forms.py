from django import forms
from django.utils.translation import gettext_lazy as _


class PurchaseChecksForm(forms.Form):
    number_of_checks = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        label=_("Enter number of checks"),
        help_text=_("Enter the number of checks you want to purchase.")
    )
