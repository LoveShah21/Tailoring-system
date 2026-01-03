"""
Notifications App - Services

Orchestrates notification creation and delivery via various channels.
"""

import logging
from django.db import transaction
from django.conf import settings
from .models import Notification, NotificationType, NotificationChannel
from .email_service import EmailService

logger = logging.getLogger('tailoring')


class NotificationService:
    """
    Service to manage notification lifecycle:
    1. Create Notification record
    2. Dispatch to appropriate channels (Email, SMS, etc.)
    3. Update status
    """
    
    @staticmethod
    @transaction.atomic
    def send_notification(recipient, type_name, context, related_object=None, channels=None):
        """
        Send a notification to a user.
        
        Args:
            recipient: User instance
            type_name: Notification type name (e.g. 'order_ready')
            context: Dictionary of context data for templates
            related_object: Optional related object (Order, Payment, etc.)
            channels: Optional list of channels (['email', 'sms']). Defaults to ['email'].
            
        Returns:
            List of created Notification objects
        """
        if channels is None:
            channels = ['email']
            
        # Get or create notification type
        try:
            notif_type = NotificationType.objects.get(type_name=type_name)
        except NotificationType.DoesNotExist:
            logger.warning(f"Notification type '{type_name}' not found. Creating default.")
            notif_type = NotificationType.objects.create(
                type_name=type_name,
                display_name=type_name.replace('_', ' ').title()
            )

        notifications = []
        
        # Prepare common data
        order = related_object if hasattr(related_object, 'order_number') else getattr(related_object, 'order', None)
        
        # Dispatch to each channel
        for channel in channels:
            if channel == 'email':
                result = NotificationService._send_email_notification(
                    recipient, notif_type, context, order, related_object
                )
                if result:
                    notifications.append(result)
            
            # Add other channels (SMS, Whatsapp) here when implemented
            
        return notifications

    @staticmethod
    def _send_email_notification(recipient, notif_type, context, order, related_object):
        """Internal method to handle email notifications."""
        
        # Create notification record in QUEUED state
        recipient_phone = ''
        if hasattr(recipient, 'customer_profile'):
            recipient_phone = recipient.customer_profile.phone_number
        
        notification = Notification.objects.create(
            notification_type=notif_type,
            recipient=recipient,
            recipient_email=recipient.email,
            recipient_phone=recipient_phone,
            channel='email',
            status='QUEUED',
            order=order,
            message_text=f"Notification: {notif_type.display_name}" # Placeholder, actual content depends on template
        )
        
        # Determine subject and template based on type
        # Ideally this mapping should be in DB or Config, but keeping it simple for now or delegate to EmailService
        subject_map = {
            'order_confirmation': f'Order Confirmation - {order.order_number}' if order else 'Order Confirmation',
            'order_status_update': f'Order Status Update - {order.order_number}' if order else 'Status Update',
            'order_ready': f'Your Order is Ready! - {order.order_number}' if order else 'Order Ready',
            'payment_success': 'Payment Received',
            'payment_failed': 'Payment Failed',
            'trial_scheduled': f'Trial Scheduled - {order.order_number}' if order else 'Trial Scheduled',
            'password_reset': 'Password Reset Request',
            # Add more as needed
        }
        
        template_map = {
            'order_confirmation': 'order_confirmation',
            'order_status_update': 'order_status_update', 
            'order_ready': 'order_ready',
            'payment_success': 'payment_success',
            'payment_failed': 'payment_failed',
            'trial_scheduled': 'delivery_scheduled', # Reusing or should create specific
            'password_reset': 'password_reset_email',
        }
        
        subject = subject_map.get(notif_type.type_name, f"Notification: {notif_type.display_name}")
        template_name = template_map.get(notif_type.type_name, 'default_notification')
        
        if notif_type.type_name == 'trial_scheduled':
             # Trial might use a specific template if available, otherwise delivery_scheduled is close, or create new.
             # Based on EmailService.send_trial_reminder, there is 'trial_reminder' template.
             if 'trial_reminder' in context: # Context hint?
                 template_name = 'trial_reminder'
             else:
                 template_name = 'trial_reminder' # Use trial_reminder as default for trial_scheduled for now
        
        notification.subject = subject
        notification.save()
        
        # Send Email
        success = EmailService.send_email(
            to_email=recipient.email,
            subject=subject,
            template_name=template_name,
            context=context
        )
        
        # Update Status
        if success:
            notification.status = 'SENT'
            notification.sent_at =  timezone.now()
        else:
            notification.status = 'FAILED'
            
        notification.save(update_fields=['status', 'sent_at'])
        return notification

    # Helper methods for specific workflows to keep calling code clean
    
    @staticmethod
    def notify_order_created(order):
        context = {
            'customer_name': order.customer.user.get_full_name(),
            'order_number': order.order_number,
            'garment_type': order.garment_type.name,
            'expected_delivery': order.expected_delivery_date,
            'special_instructions': order.special_instructions,
        }
        return NotificationService.send_notification(
            recipient=order.customer.user,
            type_name='order_confirmation',
            context=context,
            related_object=order
        )

    @staticmethod
    def notify_order_status_change(order, old_status, new_status):
        context = {
            'customer_name': order.customer.user.get_full_name(),
            'order_number': order.order_number,
            'old_status': old_status.display_label,
            'new_status': new_status.display_label,
            'garment_type': order.garment_type.name,
        }
        
        # If new status is READY, send specific 'order_ready'
        if new_status.status_name == 'ready': # Assuming 'ready' is the code
             return NotificationService.send_notification(
                recipient=order.customer.user,
                type_name='order_ready',
                context=context,
                related_object=order
            )
             
        return NotificationService.send_notification(
            recipient=order.customer.user,
            type_name='order_status_update',
            context=context,
            related_object=order
        )

    @staticmethod
    def notify_payment_success(payment):
        invoice = payment.invoice
        order = invoice.bill.order
        context = {
            'customer_name': invoice.customer_name,
            'invoice_number': invoice.invoice_number,
            'order_number': order.order_number,
            'amount_paid': payment.amount_paid,
            'payment_date': payment.created_at, # using created_at as proxy for payment_date
            'balance_due': invoice.get_balance_due(),
        }
        return NotificationService.send_notification(
            recipient=order.customer.user, # Ensure we get the user from order->customer->user
            type_name='payment_success',
            context=context,
            related_object=payment
        )

    @staticmethod
    def notify_trial_scheduled(trial):
        order = trial.order
        context = {
            'customer_name': order.customer.user.get_full_name(),
            'order_number': order.order_number,
            'trial_date': trial.trial_date,
            'trial_time': trial.trial_time,
            'trial_location': trial.get_trial_location_display(),
            'trial_reminder': True # Hint for template selection
        }
        return NotificationService.send_notification(
            recipient=order.customer.user,
            type_name='trial_scheduled',
            context=context,
            related_object=trial
        )

# Need to import timezone
from django.utils import timezone
