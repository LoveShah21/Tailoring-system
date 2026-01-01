"""
Payments App - Models

Payment processing with Razorpay integration.
Maps to: payments_payment_mode, payments_razorpay_order, payments_payment,
         payments_refund, payments_payment_reconciliation_log, 
         payments_webhook_event (for idempotency) tables
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


class PaymentMode(models.Model):
    """
    Payment modes available.
    
    Maps to: payments_payment_mode table
    
    Modes: razorpay, cash, cheque
    """
    
    mode_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'payments_payment_mode'
        indexes = [
            models.Index(fields=['mode_name'], name='idx_payment_mode_name'),
        ]
    
    def __str__(self):
        return self.mode_name


class RazorpayOrder(models.Model):
    """
    Razorpay order records.
    
    Maps to: payments_razorpay_order table
    """
    
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]
    
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.RESTRICT,
        related_name='razorpay_orders'
    )
    
    # Razorpay-specific fields
    razorpay_order_id = models.CharField(max_length=50, unique=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    amount_paise = models.BigIntegerField()  # Razorpay stores in paise
    currency = models.CharField(max_length=3, default='INR')
    
    order_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CREATED'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_razorpay_order'
        indexes = [
            models.Index(fields=['razorpay_order_id'], name='idx_rp_order_id'),
            models.Index(fields=['invoice'], name='idx_rp_invoice'),
            models.Index(fields=['order_status'], name='idx_rp_status'),
        ]
    
    def __str__(self):
        return f"RP Order: {self.razorpay_order_id}"
    
    @property
    def amount_rupees(self):
        """Convert paise to rupees."""
        return Decimal(self.amount_paise) / Decimal('100')


class Payment(models.Model):
    """
    Payment records.
    
    Maps to: payments_payment table
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.RESTRICT,
        related_name='payments'
    )
    payment_mode = models.ForeignKey(
        PaymentMode,
        on_delete=models.RESTRICT,
        related_name='payments'
    )
    
    # Razorpay reference (null for cash)
    razorpay_payment_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=50, null=True, blank=True)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    # For manual cash entries
    receipt_reference = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='COMPLETED'
    )
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='recorded_payments'
    )
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_payment'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice'], name='idx_payment_invoice'),
            models.Index(fields=['payment_date'], name='idx_payment_date'),
            models.Index(fields=['status'], name='idx_payment_status'),
            models.Index(fields=['razorpay_payment_id'], name='idx_payment_rp_id'),
        ]
    
    def __str__(self):
        return f"Payment of ₹{self.amount_paid} for {self.invoice.invoice_number}"


class Refund(models.Model):
    """
    Refund records.
    
    Maps to: payments_refund table
    """
    
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.RESTRICT,
        related_name='refunds'
    )
    
    refund_reason = models.CharField(max_length=255)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    razorpay_refund_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    refund_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='INITIATED'
    )
    
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='initiated_refunds'
    )
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_refund'
        indexes = [
            models.Index(fields=['payment'], name='idx_refund_payment'),
            models.Index(fields=['refund_status'], name='idx_refund_status'),
        ]
    
    def __str__(self):
        return f"Refund of ₹{self.refund_amount} for Payment {self.payment_id}"


class PaymentReconciliationLog(models.Model):
    """
    Payment reconciliation tracking.
    
    Maps to: payments_payment_reconciliation_log table
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('MATCHED', 'Matched'),
        ('MISMATCH', 'Mismatch'),
        ('MANUAL_RESOLVED', 'Manually Resolved'),
    ]
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciliation_logs'
    )
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciliation_logs'
    )
    
    reconciliation_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    difference_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciliations'
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_payment_reconciliation_log'
        indexes = [
            models.Index(fields=['reconciliation_status'], name='idx_recon_status'),
            models.Index(fields=['created_at'], name='idx_recon_created'),
        ]
    
    def __str__(self):
        return f"Reconciliation {self.id}: {self.reconciliation_status}"


class WebhookEvent(models.Model):
    """
    Track processed webhook events for idempotency.
    
    Prevents duplicate payment processing from webhooks.
    """
    
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=50)  # payment.captured, refund.processed
    payload_hash = models.CharField(max_length=64)  # SHA256 of payload
    
    processed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)  # success, failed, duplicate
    
    class Meta:
        db_table = 'payments_webhook_event'
        indexes = [
            models.Index(fields=['event_id'], name='idx_webhook_event_id'),
            models.Index(fields=['processed_at'], name='idx_webhook_processed'),
        ]
    
    def __str__(self):
        return f"Webhook: {self.event_type} - {self.event_id}"
