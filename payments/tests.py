"""
Payments App - Tests

Comprehensive test cases for PaymentService.
"""

from decimal import Decimal
from django.test import TestCase
from unittest.mock import patch, MagicMock

from payments.models import Payment, PaymentMode, RazorpayOrder
from billing.models import OrderBill, Invoice
from orders.models import Order, OrderStatus
from catalog.models import GarmentType
from customers.models import CustomerProfile
from users.models import User


class PaymentServiceTests(TestCase):
    """Test cases for PaymentService."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create staff user
        cls.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        
        # Create customer user
        cls.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        # Create customer profile
        cls.customer = CustomerProfile.objects.create(
            user=cls.customer_user,
            phone_number='1234567890',
            address_line_1='123 Test Street',
            city='Test City'
        )
        
        # Create garment type
        cls.garment_type = GarmentType.objects.create(
            name='Test Garment',
            base_price=Decimal('1500.00'),
            fabric_requirement_meters=Decimal('2.5'),
            stitching_days_estimate=7
        )
        
        # Create order status
        cls.status_booked = OrderStatus.objects.create(
            status_name='booked',
            display_label='Booked',
            sequence_order=1
        )
        
        # Create payment mode
        cls.cash_mode = PaymentMode.objects.create(
            mode_name='cash',
            description='Cash Payment'
        )
        
        cls.razorpay_mode = PaymentMode.objects.create(
            mode_name='razorpay',
            description='Razorpay Online Payment'
        )
    
    def _create_order_with_invoice(self):
        """Helper to create an order with bill and invoice."""
        from datetime import date, timedelta
        
        order = Order.objects.create(
            order_number='ORD-TEST-001',
            customer=self.customer,
            garment_type=self.garment_type,
            current_status=self.status_booked,
            expected_delivery_date=date.today() + timedelta(days=14)
        )
        
        bill = OrderBill.objects.create(
            order=order,
            base_garment_price=Decimal('1500.00'),
            work_type_charges=Decimal('0.00'),
            alteration_charges=Decimal('0.00'),
            urgency_surcharge=Decimal('0.00'),
            tax_rate=Decimal('18.00'),
            advance_amount=Decimal('0.00')
        )
        
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-001',
            bill=bill,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            customer_name='Test Customer',
            customer_email='customer@test.com',
            customer_phone='1234567890',
            status='ISSUED',
            generated_by=self.staff_user
        )
        
        return order, bill, invoice
    
    def test_record_cash_payment_success(self):
        """Test recording a cash payment."""
        from payments.services import PaymentService
        
        order, bill, invoice = self._create_order_with_invoice()
        
        payment = PaymentService.record_cash_payment(
            invoice=invoice,
            amount=Decimal('1000.00'),
            recorded_by=self.staff_user,
            receipt_reference='CASH-001'
        )
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount_paid, Decimal('1000.00'))
        self.assertEqual(payment.status, 'COMPLETED')
    
    def test_payment_updates_invoice_status(self):
        """Test that full payment updates invoice status to PAID."""
        from payments.services import PaymentService
        
        order, bill, invoice = self._create_order_with_invoice()
        
        # Pay full amount
        full_amount = bill.total_amount
        payment = PaymentService.record_cash_payment(
            invoice=invoice,
            amount=full_amount,
            recorded_by=self.staff_user
        )
        
        invoice.refresh_from_db()
        # After full payment, status should be PAID
        self.assertEqual(invoice.status, 'PAID')


class PaymentModeTests(TestCase):
    """Test cases for PaymentMode model."""
    
    def test_create_payment_mode(self):
        """Test creating a payment mode."""
        mode = PaymentMode.objects.create(
            mode_name='upi',
            description='UPI Payment'
        )
        
        self.assertEqual(mode.mode_name, 'upi')
        self.assertTrue(mode.is_active)


class RazorpayOrderTests(TestCase):
    """Test cases for RazorpayOrder model."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        
        cls.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        cls.customer = CustomerProfile.objects.create(
            user=cls.customer_user,
            phone_number='1234567890',
            address_line_1='123 Test Street',
            city='Test City'
        )
        
        cls.garment_type = GarmentType.objects.create(
            name='Test Garment',
            base_price=Decimal('1500.00'),
            fabric_requirement_meters=Decimal('2.5'),
            stitching_days_estimate=7
        )
        
        cls.status_booked = OrderStatus.objects.create(
            status_name='booked',
            display_label='Booked',
            sequence_order=1
        )
    
    def test_razorpay_order_creation(self):
        """Test creating a Razorpay order record."""
        from datetime import date, timedelta
        
        order = Order.objects.create(
            order_number='ORD-TEST-002',
            customer=self.customer,
            garment_type=self.garment_type,
            current_status=self.status_booked,
            expected_delivery_date=date.today() + timedelta(days=14)
        )
        
        bill = OrderBill.objects.create(
            order=order,
            base_garment_price=Decimal('1500.00'),
            work_type_charges=Decimal('0.00'),
            alteration_charges=Decimal('0.00'),
            urgency_surcharge=Decimal('0.00'),
            tax_rate=Decimal('18.00'),
            advance_amount=Decimal('0.00')
        )
        
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-002',
            bill=bill,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            customer_name='Test Customer',
            customer_email='customer@test.com',
            customer_phone='1234567890',
            status='ISSUED',
            generated_by=self.staff_user
        )
        
        razorpay_order = RazorpayOrder.objects.create(
            invoice=invoice,
            razorpay_order_id='order_test123',
            amount_paise=177000,  # 1770 INR in paise
            order_status='CREATED'
        )
        
        self.assertEqual(razorpay_order.razorpay_order_id, 'order_test123')
        self.assertEqual(razorpay_order.amount_paise, 177000)
        self.assertEqual(razorpay_order.order_status, 'CREATED')
