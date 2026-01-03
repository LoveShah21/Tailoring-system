"""
Payments App - Services

Business logic for payment processing with Razorpay integration.
All critical operations wrapped in @transaction.atomic.
"""

import hashlib
import logging
import razorpay
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import RazorpayOrder, Payment, Refund, WebhookEvent, PaymentMode
from audit.services import AuditService
from notifications.email_service import EmailService

logger = logging.getLogger('tailoring')


class PaymentService:
    """Service class for payment operations."""
    
    _client = None
    
    @classmethod
    def get_razorpay_client(cls):
        """Get or create Razorpay client singleton."""
        if cls._client is None:
            cls._client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        return cls._client
    
    @classmethod
    @transaction.atomic
    def create_razorpay_order(cls, invoice, amount_rupees):
        """
        Create a Razorpay order for payment.
        
        Args:
            invoice: Invoice instance
            amount_rupees: Amount in rupees
        
        Returns:
            RazorpayOrder instance
        """
        client = cls.get_razorpay_client()
        
        # Razorpay expects amount in paise
        amount_paise = int(amount_rupees * 100)
        
        # Create order with Razorpay
        rp_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': f'inv_{invoice.invoice_number}',
            'notes': {
                'invoice_number': invoice.invoice_number,
                'customer_email': invoice.customer_email,
            }
        })
        
        # Store in database
        order = RazorpayOrder.objects.create(
            invoice=invoice,
            razorpay_order_id=rp_order['id'],
            amount_paise=amount_paise,
            currency='INR',
            order_status='CREATED',
        )
        
        logger.info(f"Razorpay order created: {rp_order['id']} for invoice {invoice.invoice_number}")
        
        return order
    
    @classmethod
    @transaction.atomic
    def verify_and_capture_payment(
        cls,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
        recorded_by
    ):
        """
        Verify Razorpay payment signature and record payment.
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay signature for verification
            recorded_by: User recording the payment
        
        Returns:
            Payment instance
        
        Raises:
            Exception: If signature verification fails
        """
        client = cls.get_razorpay_client()
        
        # Verify signature
        params = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }
        
        try:
            client.utility.verify_payment_signature(params)
        except razorpay.errors.SignatureVerificationError:
            logger.error(f"Payment signature verification failed for order {razorpay_order_id}")
            raise
        
        # Update Razorpay order
        rp_order = RazorpayOrder.objects.get(razorpay_order_id=razorpay_order_id)
        rp_order.order_status = 'PAID'
        rp_order.razorpay_signature = razorpay_signature
        rp_order.save()
        
        # Get payment mode
        payment_mode = PaymentMode.objects.get(mode_name='razorpay')
        
        # Create payment record
        payment = Payment.objects.create(
            invoice=rp_order.invoice,
            payment_mode=payment_mode,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            amount_paid=rp_order.amount_rupees,
            status='COMPLETED',
            recorded_by=recorded_by,
        )
        
        # Update invoice status
        cls._update_invoice_status(rp_order.invoice)
        
        # Send confirmation email
        EmailService.send_payment_success(payment)
        
        # Audit log
        AuditService.log_payment(
            payment=payment,
            action_type='CAPTURED',
            performed_by=recorded_by,
            description=f'Payment captured: ₹{payment.amount_paid}',
        )
        
        logger.info(f"Payment captured: {razorpay_payment_id} for ₹{payment.amount_paid}")
        
        return payment
    
    @classmethod
    @transaction.atomic
    def record_cash_payment(cls, invoice, amount, recorded_by, receipt_reference=''):
        """
        Record a cash payment.
        
        Args:
            invoice: Invoice instance
            amount: Amount paid
            recorded_by: User recording the payment
            receipt_reference: Optional receipt reference
        
        Returns:
            Payment instance
        """
        payment_mode = PaymentMode.objects.get(mode_name='cash')
        
        payment = Payment.objects.create(
            invoice=invoice,
            payment_mode=payment_mode,
            amount_paid=amount,
            receipt_reference=receipt_reference,
            status='COMPLETED',
            recorded_by=recorded_by,
        )
        
        # Update invoice status
        cls._update_invoice_status(invoice)
        
        # Audit log
        AuditService.log_payment(
            payment=payment,
            action_type='RECORDED',
            performed_by=recorded_by,
            description=f'Cash payment recorded: ₹{payment.amount_paid}',
        )
        
        return payment
    
    @classmethod
    def _update_invoice_status(cls, invoice):
        """Update invoice status based on payments."""
        if invoice.is_fully_paid():
            invoice.status = 'PAID'
        elif invoice.get_total_paid() > 0:
            invoice.status = 'PARTIALLY_PAID'
        invoice.save()
    
    @classmethod
    @transaction.atomic
    def process_webhook(cls, event_data, payload_signature):
        """
        Process Razorpay webhook with idempotency.
        
        Args:
            event_data: Webhook event data
            payload_signature: Webhook signature
        
        Returns:
            bool indicating if event was processed
        """
        event_id = event_data.get('event_id', event_data.get('id'))
        event_type = event_data.get('event')
        
        # Calculate payload hash for idempotency
        payload_hash = hashlib.sha256(
            str(event_data).encode()
        ).hexdigest()
        
        # Check if already processed
        existing = WebhookEvent.objects.filter(event_id=event_id).first()
        if existing:
            logger.info(f"Duplicate webhook ignored: {event_id}")
            return False
        
        # Record webhook event
        webhook = WebhookEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            status='processing',
        )
        
        try:
            # Process based on event type
            if event_type == 'payment.captured':
                cls._handle_payment_captured(event_data)
            elif event_type == 'refund.processed':
                cls._handle_refund_processed(event_data)
            
            webhook.status = 'success'
            webhook.save()
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {event_id} - {e}")
            webhook.status = 'failed'
            webhook.save()
            raise
    
    @classmethod
    def _handle_payment_captured(cls, event_data):
        """Handle payment.captured webhook event."""
        payment_data = event_data.get('payload', {}).get('payment', {}).get('entity', {})
        razorpay_order_id = payment_data.get('order_id')
        razorpay_payment_id = payment_data.get('id')
        
        # Check if already recorded
        existing = Payment.objects.filter(razorpay_payment_id=razorpay_payment_id).first()
        if existing:
            return
        
        # Get order and record payment
        try:
            rp_order = RazorpayOrder.objects.get(razorpay_order_id=razorpay_order_id)
            
            payment_mode = PaymentMode.objects.get(mode_name='razorpay')
            
            Payment.objects.create(
                invoice=rp_order.invoice,
                payment_mode=payment_mode,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                amount_paid=rp_order.amount_rupees,
                status='COMPLETED',
                recorded_by=None,  # Webhook-created
                notes='Created via webhook',
            )
            
            rp_order.order_status = 'PAID'
            rp_order.save()
            
            cls._update_invoice_status(rp_order.invoice)
            
        except RazorpayOrder.DoesNotExist:
            logger.warning(f"Razorpay order not found for webhook: {razorpay_order_id}")
    
    @classmethod
    def _handle_refund_processed(cls, event_data):
        """Handle refund.processed webhook event."""
        refund_data = event_data.get('payload', {}).get('refund', {}).get('entity', {})
        razorpay_refund_id = refund_data.get('id')
        
        try:
            refund = Refund.objects.get(razorpay_refund_id=razorpay_refund_id)
            refund.refund_status = 'COMPLETED'
            refund.completed_at = timezone.now()
            refund.save()
        except Refund.DoesNotExist:
            logger.warning(f"Refund not found for webhook: {razorpay_refund_id}")
    
    @classmethod
    @transaction.atomic
    def initiate_refund(cls, payment, amount, reason, initiated_by):
        """
        Initiate a refund for a payment.
        
        Args:
            payment: Payment instance
            amount: Refund amount
            reason: Refund reason
            initiated_by: User initiating the refund
        
        Returns:
            Refund instance
        """
        if payment.payment_mode.mode_name != 'razorpay':
            # Manual refund for cash payments
            refund = Refund.objects.create(
                payment=payment,
                refund_reason=reason,
                refund_amount=amount,
                refund_status='COMPLETED',
                completed_at=timezone.now(),
                initiated_by=initiated_by,
                notes='Manual refund (non-Razorpay)',
            )
            return refund
        
        # Razorpay refund
        client = cls.get_razorpay_client()
        
        rp_refund = client.payment.refund(payment.razorpay_payment_id, {
            'amount': int(amount * 100),
            'notes': {'reason': reason},
        })
        
        refund = Refund.objects.create(
            payment=payment,
            refund_reason=reason,
            refund_amount=amount,
            razorpay_refund_id=rp_refund['id'],
            refund_status='PROCESSING',
            initiated_by=initiated_by,
        )
        
        # Update payment status
        payment.status = 'REFUNDED'
        payment.save()
        
        AuditService.log_payment(
            payment=payment,
            action_type='REFUND_INITIATED',
            performed_by=initiated_by,
            description=f'Refund initiated: ₹{amount}',
        )
        
        return refund
