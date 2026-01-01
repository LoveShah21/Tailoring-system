"""
Billing App - Models

Order billing and invoicing.
Maps to: billing_order_bill, billing_invoice tables
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


class OrderBill(models.Model):
    """
    Order bill with derived pricing.
    
    Maps to: billing_order_bill table
    
    All price fields are computed/derived, never manually edited.
    """
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.RESTRICT,
        related_name='bill'
    )
    
    # Price Breakdown (All derived, not manually entered)
    base_garment_price = models.DecimalField(max_digits=10, decimal_places=2)
    work_type_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    alteration_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    urgency_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Tax configuration
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Advance payment
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    bill_generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'billing_order_bill'
        indexes = [
            models.Index(fields=['bill_generated_at'], name='idx_bill_generated'),
        ]
    
    def __str__(self):
        return f"Bill for {self.order.order_number}"
    
    @property
    def subtotal(self):
        """Calculate subtotal (base + work + alteration + urgency)."""
        return (
            self.base_garment_price +
            self.work_type_charges +
            self.alteration_charges +
            self.urgency_surcharge
        )
    
    @property
    def tax_amount(self):
        """Calculate tax amount."""
        return self.subtotal * (self.tax_rate / Decimal('100'))
    
    @property
    def total_amount(self):
        """Calculate total amount including tax."""
        return self.subtotal + self.tax_amount
    
    @property
    def balance_amount(self):
        """Calculate balance remaining after advance."""
        return self.total_amount - self.advance_amount


class Invoice(models.Model):
    """
    Immutable invoice for orders.
    
    Maps to: billing_invoice table
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Paid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)  # 'INV-2026-001'
    bill = models.OneToOneField(
        OrderBill,
        on_delete=models.RESTRICT,
        related_name='invoice'
    )
    
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    # Immutable customer snapshots
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # PDF storage
    invoice_pdf_url = models.CharField(max_length=500, blank=True, null=True)
    invoice_filename = models.CharField(max_length=255, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='generated_invoices'
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_invoice'
        indexes = [
            models.Index(fields=['invoice_number'], name='idx_invoice_number'),
            models.Index(fields=['status'], name='idx_invoice_status'),
            models.Index(fields=['due_date'], name='idx_invoice_due'),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"
    
    @classmethod
    def generate_invoice_number(cls):
        """Generate a unique invoice number."""
        from django.utils import timezone
        today = timezone.now()
        prefix = f"INV-{today.year}-"
        
        latest = cls.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if latest:
            try:
                last_num = int(latest.invoice_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:04d}"
    
    def get_total_paid(self):
        """Get total amount paid for this invoice."""
        return sum(
            p.amount_paid 
            for p in self.payments.filter(status='COMPLETED')
        )
    
    def get_balance_due(self):
        """Get remaining balance due."""
        return self.bill.total_amount - self.get_total_paid()
    
    def is_fully_paid(self):
        """Check if invoice is fully paid."""
        return self.get_balance_due() <= 0
