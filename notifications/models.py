"""
Notifications App - Models

Notification types, channels, and notifications.
Maps to: notifications_notification_type, notifications_notification_channel,
         notifications_notification tables
"""

from django.db import models
from django.conf import settings


class NotificationType(models.Model):
    """
    Types of notifications.
    
    Maps to: notifications_notification_type table
    
    Types: order_ready, payment_confirmed, delivery_scheduled, etc.
    """
    
    type_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications_notification_type'
        indexes = [
            models.Index(fields=['type_name'], name='idx_notif_type_name'),
        ]
    
    def __str__(self):
        return self.display_name or self.type_name


class NotificationChannel(models.Model):
    """
    Notification delivery channels.
    
    Maps to: notifications_notification_channel table
    
    Channels: email, sms, whatsapp
    """
    
    IMPLEMENTATION_STATUS = [
        ('PLANNED', 'Planned'),
        ('IMPLEMENTED', 'Implemented'),
        ('TESTED', 'Tested'),
    ]
    
    channel_name = models.CharField(max_length=50, unique=True)
    is_enabled = models.BooleanField(default=True)
    implementation_status = models.CharField(
        max_length=20,
        choices=IMPLEMENTATION_STATUS,
        default='PLANNED'
    )
    
    class Meta:
        db_table = 'notifications_notification_channel'
        indexes = [
            models.Index(fields=['channel_name'], name='idx_notif_channel'),
        ]
    
    def __str__(self):
        return self.channel_name


class Notification(models.Model):
    """
    Individual notification records.
    
    Maps to: notifications_notification table
    """
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('in_app', 'In-App'),
    ]
    
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('BOUNCED', 'Bounced'),
    ]
    
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.RESTRICT,
        related_name='notifications'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    recipient_email = models.EmailField(blank=True, null=True)  # Snapshot at send time
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    
    subject = models.CharField(max_length=255, blank=True, null=True)
    message_text = models.TextField()
    
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='QUEUED'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient'], name='idx_notif_recipient'),
            models.Index(fields=['order'], name='idx_notif_order'),
            models.Index(fields=['status'], name='idx_notif_status'),
            models.Index(fields=['created_at'], name='idx_notif_created'),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
