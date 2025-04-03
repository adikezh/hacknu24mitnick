from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Payment
import logging

logger = logging.getLogger(__name__)

class PurchaseChecksView(LoginRequiredMixin, View):
    """View for purchasing document checks."""
    template_name = 'payments/purchase_checks.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request):
        user = request.user
        if not user.city or not user.address or not user.zip_code:
            return JsonResponse({'status': 'failure', 'message': 'Please complete your profile with city, address, and zip code before making a payment.'}, status=400)
        
        tracking_id = request.POST.get('tracking_id')
        success = request.POST.get('success') == 'true'
        amount = 0  # Set payment amount to zero
        number_of_checks = int(request.POST.get('number_of_checks'))
        
        if not tracking_id:
            return JsonResponse({'status': 'failure', 'message': 'No tracking_id provided'}, status=400)

        # Create or update the payment record
        payment = Payment.objects.create(
            created_by=self.request.user,
            number_of_checks=number_of_checks,
            tracking_id=tracking_id,
            success=success,
            amount=amount
        )

        # Update checks available if the payment was successful
        if success:
            self.request.user.checks_available += number_of_checks
            self.request.user.save()

        return JsonResponse({'status': 'success'})


class PaymentNotificationView(View):
    """View for handling payment notifications."""
    
    def post(self, request):
        logger.info("Payment Notification Data: %s", request.POST)
        tracking_id = request.POST.get('tracking_id')
        success = request.POST.get('success') == 'true'
        amount = 0  # Set payment amount to zero

        if not tracking_id:
            return JsonResponse({'status': 'failure', 'message': 'No tracking_id provided'}, status=400)

        # Fetch the payment object based on tracking_id
        try:
            payment = Payment.objects.get(tracking_id=tracking_id)
        except Payment.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Payment not found'}, status=404)

        # Update payment record
        payment.success = success
        payment.amount = amount  # Optionally verify this amount
        payment.save()

        # Update user checks if the payment was successful
        if success:
            request.user.checks_available += payment.number_of_checks
            request.user.save()

        return JsonResponse({'status': 'success'})
    
