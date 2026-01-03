"""
Payments App - Views

Payment processing and history views.
"""

from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Payment, RazorpayOrder
from .services import PaymentService
from users.permissions import StaffRequiredMixin
from billing.models import OrderBill


class PaymentListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all payments."""
    
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        return Payment.objects.select_related(
            'bill__order__customer__user', 'payment_mode'
        ).order_by('-created_at')


class PaymentDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View payment details."""
    
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'


class CreatePaymentOrderView(LoginRequiredMixin, View):
    """Create a Razorpay order for payment."""
    
    def post(self, request, bill_pk):
        bill = get_object_or_404(OrderBill, pk=bill_pk)
        
        if bill.balance_due <= 0:
            messages.warning(request, 'This bill has already been paid.')
            return redirect('billing:bill_detail', pk=bill_pk)
        
        try:
            amount = request.POST.get('amount', bill.balance_due)
            razorpay_order = PaymentService.create_razorpay_order(
                bill=bill,
                amount=float(amount),
                user=request.user
            )
            
            return JsonResponse({
                'order_id': razorpay_order.razorpay_order_id,
                'amount': razorpay_order.amount_paise,  # In paise
                'currency': 'INR',
                'key': razorpay_order.razorpay_key_id,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class VerifyPaymentView(LoginRequiredMixin, View):
    """Verify Razorpay payment and record it."""
    
    def post(self, request):
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        try:
            payment = PaymentService.verify_and_capture_payment(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                user=request.user
            )
            messages.success(request, f'Payment of ₹{payment.amount_paid} recorded successfully.')
            return JsonResponse({'success': True, 'payment_id': payment.pk})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class RecordCashPaymentView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Record a cash/offline payment."""
    
    def post(self, request, bill_pk):
        bill = get_object_or_404(OrderBill, pk=bill_pk)
        amount = request.POST.get('amount')
        notes = request.POST.get('notes', '')
        
        if not amount:
            messages.error(request, 'Amount is required.')
            return redirect('billing:bill_detail', pk=bill_pk)
        
        try:
            payment = PaymentService.record_offline_payment(
                bill=bill,
                amount=float(amount),
                payment_mode='cash',
                notes=notes,
                user=request.user
            )
            messages.success(request, f'Cash payment of ₹{payment.amount_paid} recorded.')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
        
        return redirect('billing:bill_detail', pk=bill_pk)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(View):
    """Handle Razorpay webhooks."""
    
    def post(self, request):
        try:
            PaymentService.handle_webhook(
                payload=request.body,
                signature=request.headers.get('X-Razorpay-Signature', '')
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
