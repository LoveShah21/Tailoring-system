"""
Notifications App - Email Service

Centralized email sending service using Gmail SMTP.

Features:
- Gmail SMTP configuration
- HTML + plain text support
- Retry handling (3 attempts)
- Success/failure logging
- Template rendering
"""

import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger('tailoring')


class EmailService:
    """
    Centralized email sending service.
    
    IMPORTANT: All apps should use this service instead of direct send_mail().
    This ensures consistent configuration, retry handling, and logging.
    """
    
    MAX_RETRIES = 3
    
    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None,
        max_retries: int = MAX_RETRIES
    ) -> bool:
        """
        Send email with retry logic and logging.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Template name (without extension)
            context: Template context dictionary
            from_email: Optional from address (uses DEFAULT_FROM_EMAIL if not provided)
            cc: Optional CC list
            bcc: Optional BCC list
            attachments: Optional list of (filename, content, mimetype) tuples
            max_retries: Maximum retry attempts
        
        Returns:
            True if email sent successfully, False otherwise
        """
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        # Render HTML template
        try:
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {e}")
            # Fallback to plain text if template fails
            text_content = context.get('message', 'No message content')
            html_content = None
        
        # Send with retries
        for attempt in range(1, max_retries + 1):
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[to_email],
                    cc=cc,
                    bcc=bcc,
                )
                
                if html_content:
                    email.attach_alternative(html_content, "text/html")
                
                if attachments:
                    for filename, content, mimetype in attachments:
                        email.attach(filename, content, mimetype)
                
                email.send(fail_silently=False)
                
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
                
            except Exception as e:
                logger.warning(
                    f"Email send attempt {attempt}/{max_retries} failed for {to_email}: {e}"
                )
                if attempt == max_retries:
                    logger.error(f"Email failed after {max_retries} attempts: {to_email}")
                    return False
        
        return False
    
    @classmethod
    def send_order_confirmation(cls, order) -> bool:
        """Send order confirmation email to customer."""
        customer = order.customer
        user = customer.user
        
        context = {
            'customer_name': user.get_full_name(),
            'order_number': order.order_number,
            'garment_type': order.garment_type.name,
            'expected_delivery': order.expected_delivery_date,
            'special_instructions': order.special_instructions,
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f'Order Confirmation - {order.order_number}',
            template_name='order_confirmation',
            context=context
        )
    
    @classmethod
    def send_payment_success(cls, payment) -> bool:
        """Send payment success notification."""
        invoice = payment.invoice
        bill = invoice.bill
        order = bill.order
        
        context = {
            'customer_name': invoice.customer_name,
            'invoice_number': invoice.invoice_number,
            'order_number': order.order_number,
            'amount_paid': payment.amount_paid,
            'payment_date': payment.payment_date,
            'balance_due': invoice.get_balance_due(),
        }
        
        # Generate Invoice PDF
        try:
            from billing.services import BillingService
            pdf_buffer = BillingService.generate_invoice_pdf(invoice)
            attachments = [(f'{invoice.invoice_number}.pdf', pdf_buffer.read(), 'application/pdf')]
        except Exception as e:
            logger.error(f"Failed to attach invoice PDF for payment {payment.id}: {e}")
            attachments = None
            
        return cls.send_email(
            to_email=invoice.customer_email,
            subject=f'Payment Received - {invoice.invoice_number}',
            template_name='payment_success',
            context=context,
            attachments=attachments
        )
    
    @classmethod
    def send_payment_failed(cls, invoice, error_message: str = '') -> bool:
        """Send payment failure notification."""
        context = {
            'customer_name': invoice.customer_name,
            'invoice_number': invoice.invoice_number,
            'error_message': error_message,
        }
        
        return cls.send_email(
            to_email=invoice.customer_email,
            subject=f'Payment Failed - {invoice.invoice_number}',
            template_name='payment_failed',
            context=context
        )
    
    @classmethod
    def send_order_ready(cls, order) -> bool:
        """Notify customer that order is ready for pickup/delivery."""
        customer = order.customer
        user = customer.user
        
        context = {
            'customer_name': user.get_full_name(),
            'order_number': order.order_number,
            'garment_type': order.garment_type.name,
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f'Your Order is Ready! - {order.order_number}',
            template_name='order_ready',
            context=context
        )
    
    @classmethod
    def send_delivery_scheduled(cls, delivery) -> bool:
        """Notify customer about scheduled delivery."""
        order = delivery.order
        customer = order.customer
        user = customer.user
        
        context = {
            'customer_name': user.get_full_name(),
            'order_number': order.order_number,
            'delivery_date': delivery.scheduled_delivery_date,
            'delivery_time': delivery.scheduled_delivery_time,
            'delivery_zone': delivery.delivery_zone.name,
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f'Delivery Scheduled - {order.order_number}',
            template_name='delivery_scheduled',
            context=context
        )
    
    @classmethod
    def send_low_stock_alert(cls, fabric, admin_emails: List[str]) -> bool:
        """Send low stock alert to admins."""
        context = {
            'fabric_name': str(fabric),
            'current_stock': fabric.quantity_in_stock,
            'threshold': fabric.reorder_threshold,
        }
        
        success = True
        for email in admin_emails:
            if not cls.send_email(
                to_email=email,
                subject=f'Low Stock Alert - {fabric.name}',
                template_name='low_stock_alert',
                context=context
            ):
                success = False
        
        return success
    
    @classmethod
    def send_trial_reminder(cls, trial) -> bool:
        """Send trial appointment reminder."""
        order = trial.order
        customer = order.customer
        user = customer.user
        
        context = {
            'customer_name': user.get_full_name(),
            'order_number': order.order_number,
            'trial_date': trial.trial_date,
            'trial_time': trial.trial_time,
            'trial_location': trial.get_trial_location_display(),
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f'Trial Reminder - {order.order_number}',
            template_name='trial_reminder',
            context=context
        )
