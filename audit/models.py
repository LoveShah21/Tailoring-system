"""
Audit App - Models

Activity logging and payment audit tracking.
Maps to: audit_activity_log, audit_payment_audit_log tables
"""

from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    """
    General activity audit log.
    
    Maps to: audit_activity_log table
    
    Logs:
    - Order status changes
    - Payments
    - Inventory updates
    - Admin actions
    """
    
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('STATUS_CHANGE', 'Status Change'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    # Entity information
    entity_type = models.CharField(max_length=100)  # 'order', 'payment', 'inventory', 'user'
    entity_id = models.BigIntegerField()
    
    # Action information
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    action_description = models.TextField(blank=True, null=True)
    
    # Changes (JSON)
    changes_json = models.TextField(blank=True, null=True)
    
    # Actor information
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='activity_logs'
    )
    ip_address = models.CharField(max_length=45, blank=True, null=True)  # IPv4 or IPv6
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    
    performed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_activity_log'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id'], name='idx_audit_entity'),
            models.Index(fields=['performed_at'], name='idx_audit_performed_at'),
            models.Index(fields=['performed_by'], name='idx_audit_performed_by'),
        ]
    
    def __str__(self):
        return f"{self.action_type} on {self.entity_type}:{self.entity_id} by {self.performed_by}"


class PaymentAuditLog(models.Model):
    """
    Payment-specific audit trail.
    
    Maps to: audit_payment_audit_log table
    """
    
    payment = models.ForeignKey(
        'payments.Payment',
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    # Payment state at this point
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status_before = models.CharField(max_length=50, blank=True, null=True)
    status_after = models.CharField(max_length=50, blank=True, null=True)
    
    change_reason = models.TextField(blank=True, null=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_audit_logs'
    )
    
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_payment_audit_log'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['payment'], name='idx_payment_audit_payment'),
            models.Index(fields=['changed_at'], name='idx_payment_audit_changed'),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id}: {self.status_before} → {self.status_after}"
