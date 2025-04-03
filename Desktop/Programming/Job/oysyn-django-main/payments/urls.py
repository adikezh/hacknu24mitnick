from django.urls import path
from .views import PurchaseChecksView, PaymentNotificationView

app_name = 'payments'

urlpatterns = [
    path('purchase_checks/', PurchaseChecksView.as_view(), name='purchase_checks'),
    path('payment_notification/', PaymentNotificationView.as_view(), name='payment_notification'),
]
