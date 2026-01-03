"""
Reporting App - Views

Reporting dashboard and analytics views.
"""

from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, F, Q
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import csv

from users.permissions import StaffRequiredMixin, AdminRequiredMixin
from orders.models import Order, OrderStatus
from billing.models import OrderBill
from payments.models import Payment
from inventory.models import Fabric
from customers.models import CustomerProfile


class ReportingDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Main reporting dashboard."""
    
    template_name = 'reporting/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Revenue stats
        context['total_revenue'] = Payment.objects.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        context['monthly_revenue'] = Payment.objects.filter(
            status='COMPLETED',
            created_at__date__gte=thirty_days_ago
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Order stats
        context['total_orders'] = Order.objects.filter(is_deleted=False).count()
        context['pending_orders'] = Order.objects.filter(
            is_deleted=False,
            current_status__status_name__in=[
                'booked', 'fabric_allocated', 'stitching', 
                'trial_scheduled', 'alteration', 'ready'
            ]
        ).count()
        
        context['completed_orders'] = Order.objects.filter(
            is_deleted=False,
            current_status__status_name='delivered'
        ).count()
        
        # Customer stats
        context['total_customers'] = CustomerProfile.objects.filter(is_deleted=False).count()
        context['new_customers'] = CustomerProfile.objects.filter(
            is_deleted=False,
            created_at__date__gte=thirty_days_ago
        ).count()
        
        # Inventory stats
        context['low_stock_count'] = Fabric.objects.filter(
            is_deleted=False,
            quantity_in_stock__lte=F('reorder_threshold')
        ).count()
        
        context['inventory_value'] = Fabric.objects.filter(is_deleted=False).aggregate(
            total=Sum(F('quantity_in_stock') * F('cost_per_meter'))
        )['total'] or 0
        
        # Recent orders
        context['recent_orders'] = Order.objects.filter(
            is_deleted=False
        ).select_related('customer__user', 'garment_type').order_by('-created_at')[:5]
        
        # Orders by status
        context['orders_by_status'] = Order.objects.filter(
            is_deleted=False
        ).values('current_status__status_name').annotate(
            count=Count('id')
        ).order_by('current_status__status_name')
        
        return context


class RevenueReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Revenue report."""
    
    template_name = 'reporting/revenue_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Monthly revenue for past 12 months
        from django.db.models.functions import TruncMonth
        
        monthly_data = Payment.objects.filter(
            status='COMPLETED',
            created_at__date__gte=timezone.now().date() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('amount_paid'),
            count=Count('id')
        ).order_by('month')
        
        context['monthly_data'] = list(monthly_data)
        return context


class OrdersReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Orders report."""
    
    template_name = 'reporting/orders_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Orders by garment type
        context['by_garment'] = Order.objects.filter(
            is_deleted=False
        ).values('garment_type__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Orders by urgency
        context['by_urgency'] = Order.objects.filter(
            is_deleted=False
        ).values('is_urgent').annotate(
            count=Count('id')
        ).order_by('is_urgent')
        
        # Average order value
        context['avg_order_value'] = OrderBill.objects.aggregate(
            avg=Avg('final_amount')
        )['avg'] or 0
        
        return context


class ExportRevenueCSVView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export revenue data as CSV."""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="revenue_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Order Number', 'Customer', 'Amount', 'Payment Mode'])
        
        payments = Payment.objects.filter(
            status='COMPLETED'
        ).select_related('invoice__bill__order__customer__user').order_by('-created_at')
        
        for p in payments[:1000]:  # Limit to 1000 rows
            # Traverse invoice -> bill -> order
            order = p.invoice.bill.order if (p.invoice and p.invoice.bill) else None
            writer.writerow([
                p.created_at.strftime('%Y-%m-%d %H:%M'),
                order.order_number if order else '-',
                order.customer.user.get_full_name() if order else '-',
                p.amount_paid,
                p.payment_mode.mode_name if p.payment_mode else '-'
            ])
        
        return response


class ExportOrdersCSVView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export orders data as CSV."""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order #', 'Date', 'Customer', 'Garment', 'Status', 'Urgent', 'Delivery Date'])
        
        orders = Order.objects.filter(
            is_deleted=False
        ).select_related(
            'customer__user', 'garment_type', 'current_status'
        ).order_by('-created_at')
        
        for o in orders[:1000]:
            writer.writerow([
                o.order_number,
                o.created_at.strftime('%Y-%m-%d'),
                o.customer.user.get_full_name(),
                o.garment_type.name,
                o.current_status.status_name if o.current_status else '-',
                'Yes' if o.is_urgent else 'No',
                o.expected_delivery_date.strftime('%Y-%m-%d') if o.expected_delivery_date else '-'
            ])
        
        return response
