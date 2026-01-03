"""
Billing App - Views

Billing and invoice management views.
"""

from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q

from .models import OrderBill, Invoice
from .services import BillingService
from users.permissions import StaffRequiredMixin
from orders.models import Order


class BillListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all bills."""
    
    model = OrderBill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = OrderBill.objects.select_related(
            'order__customer__user', 'order__garment_type'
        ).order_by('-created_at')
        
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(order__order_number__icontains=search) |
                Q(order__customer__user__first_name__icontains=search) |
                Q(order__customer__user__last_name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status == 'unpaid':
            queryset = queryset.filter(amount_paid__lt=models.F('final_amount'))
        elif status == 'paid':
            queryset = queryset.filter(amount_paid__gte=models.F('final_amount'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class BillDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View bill details."""
    
    model = OrderBill
    template_name = 'billing/bill_detail.html'
    context_object_name = 'bill'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoices'] = self.object.invoices.order_by('-created_at')
        context['work_types'] = self.object.order.order_work_types.select_related('work_type')
        return context


class GenerateBillView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Generate a bill for an order."""
    
    def post(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk, is_deleted=False)
        
        # Check if bill already exists
        if hasattr(order, 'bill'):
            messages.warning(request, 'Bill already exists for this order.')
            return redirect('billing:bill_detail', pk=order.bill.pk)
        
        try:
            bill = BillingService.generate_bill(order, request.user)
            messages.success(request, f'Bill generated for order {order.order_number}.')
            return redirect('billing:bill_detail', pk=bill.pk)
        except Exception as e:
            messages.error(request, f'Error generating bill: {str(e)}')
            return redirect('orders:order_detail', pk=order_pk)


class GenerateInvoiceView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Generate an invoice for a bill."""
    
    def post(self, request, bill_pk):
        bill = get_object_or_404(OrderBill, pk=bill_pk)
        
        try:
            invoice = BillingService.create_invoice(bill, request.user)
            messages.success(request, f'Invoice {invoice.invoice_number} generated.')
            return redirect('billing:bill_detail', pk=bill_pk)
        except Exception as e:
            messages.error(request, f'Error generating invoice: {str(e)}')
            return redirect('billing:bill_detail', pk=bill_pk)


class DownloadInvoicePDFView(LoginRequiredMixin, View):
    """Download invoice as PDF."""
    
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        
        # Security check: User must be staff OR the customer who owns the invoice
        is_staff = request.user.is_staff
        is_owner = (invoice.customer_email == request.user.email)
        
        if not (is_staff or is_owner):
            messages.error(request, "You do not have permission to view this invoice.")
            return redirect('dashboard:home')
        
        try:
            pdf_content = BillingService.generate_invoice_pdf(invoice)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
            return response
        except Exception as e:
            messages.error(request, f'Error generating PDF: {str(e)}')
            return redirect('dashboard:home') if not is_staff else redirect('billing:bill_detail', pk=invoice.bill.pk)


class InvoiceListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all invoices."""
    
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        return Invoice.objects.select_related(
            'bill__order__customer__user'
        ).order_by('-created_at')
