from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Payment(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)    
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Amount of money paid by the user.')
    success = models.BooleanField(default=False)
    number_of_checks = models.IntegerField(default=1)
    tracking_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self) -> str:
        return f"{self.created_by.email} - {self.amount} - \
            {'Success' if self.success else 'Failed'}"
