"""
Orders App - Tests

Comprehensive test cases for OrderService and order state machine.
"""

from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from orders.models import (
    Order, OrderStatus, OrderStatusTransition, OrderStatusHistory,
    OrderWorkType, OrderAssignment
)
from orders.services import OrderService, InvalidTransitionError
from catalog.models import GarmentType, WorkType
from customers.models import CustomerProfile
from users.models import User


class OrderServiceTests(TestCase):
    """Test cases for OrderService."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create admin user
        cls.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
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
        
        # Create tailor user
        cls.tailor = User.objects.create_user(
            username='tailor',
            email='tailor@test.com',
            password='testpass123'
        )
        
        # Create garment type
        cls.garment_type = GarmentType.objects.create(
            name='Test Blouse',
            base_price=Decimal('1500.00'),
            fabric_requirement_meters=Decimal('2.5'),
            stitching_days_estimate=7
        )
        
        # Create work types
        cls.work_type = WorkType.objects.create(
            name='Test Embroidery',
            extra_charge=Decimal('500.00')
        )
        
        # Create order statuses
        cls.status_booked = OrderStatus.objects.create(
            status_name='booked',
            display_label='Booked',
            sequence_order=1
        )
        
        cls.status_in_progress = OrderStatus.objects.create(
            status_name='in_progress',
            display_label='In Progress',
            sequence_order=2
        )
        
        cls.status_ready = OrderStatus.objects.create(
            status_name='ready',
            display_label='Ready',
            sequence_order=3
        )
        
        cls.status_delivered = OrderStatus.objects.create(
            status_name='delivered',
            display_label='Delivered',
            sequence_order=4,
            is_final_state=True
        )
        
        cls.status_cancelled = OrderStatus.objects.create(
            status_name='cancelled',
            display_label='Cancelled',
            sequence_order=5,
            is_final_state=True
        )
        
        # Create valid transitions
        OrderStatusTransition.objects.create(
            from_status=cls.status_booked,
            to_status=cls.status_in_progress
        )
        OrderStatusTransition.objects.create(
            from_status=cls.status_in_progress,
            to_status=cls.status_ready
        )
        OrderStatusTransition.objects.create(
            from_status=cls.status_ready,
            to_status=cls.status_delivered
        )
        OrderStatusTransition.objects.create(
            from_status=cls.status_booked,
            to_status=cls.status_cancelled
        )
    
    def test_create_order_success(self):
        """Test creating a basic order."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            created_by=self.admin_user
        )
        
        self.assertIsNotNone(order)
        self.assertIsNotNone(order.order_number)
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.garment_type, self.garment_type)
        self.assertEqual(order.current_status, self.status_booked)
        self.assertFalse(order.is_urgent)
    
    def test_create_urgent_order_with_multiplier(self):
        """Test that urgent orders have a higher multiplier."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=7),
            is_urgent=True,
            created_by=self.admin_user
        )
        
        self.assertTrue(order.is_urgent)
        self.assertEqual(order.urgency_multiplier, Decimal('1.20'))
    
    def test_create_order_with_work_types(self):
        """Test creating order with additional work types."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            work_types=[self.work_type],
            created_by=self.admin_user
        )
        
        order_work_types = OrderWorkType.objects.filter(order=order)
        self.assertEqual(order_work_types.count(), 1)
        self.assertEqual(order_work_types.first().work_type, self.work_type)
    
    def test_transition_status_valid(self):
        """Test valid status transition."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            created_by=self.admin_user
        )
        
        # Transition from booked to in_progress
        updated_order = OrderService.transition_status(
            order=order,
            new_status=self.status_in_progress,
            changed_by=self.admin_user,
            reason='Starting work'
        )
        
        self.assertEqual(updated_order.current_status, self.status_in_progress)
        
        # Check history
        history = OrderStatusHistory.objects.filter(order=order)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().from_status, self.status_booked)
        self.assertEqual(history.first().to_status, self.status_in_progress)
    
    def test_transition_status_invalid_raises_error(self):
        """Test that invalid transitions raise an error."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            created_by=self.admin_user
        )
        
        # Try to transition from booked directly to ready (invalid)
        with self.assertRaises(InvalidTransitionError):
            OrderService.transition_status(
                order=order,
                new_status=self.status_ready,
                changed_by=self.admin_user
            )
    
    def test_full_order_lifecycle(self):
        """Test complete order lifecycle: booked -> in_progress -> ready -> delivered."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            created_by=self.admin_user
        )
        
        # Booked -> In Progress
        order = OrderService.transition_status(
            order=order,
            new_status=self.status_in_progress,
            changed_by=self.admin_user
        )
        self.assertEqual(order.current_status.status_name, 'in_progress')
        
        # In Progress -> Ready
        order = OrderService.transition_status(
            order=order,
            new_status=self.status_ready,
            changed_by=self.admin_user
        )
        self.assertEqual(order.current_status.status_name, 'ready')
        
        # Ready -> Delivered
        order = OrderService.transition_status(
            order=order,
            new_status=self.status_delivered,
            changed_by=self.admin_user
        )
        self.assertEqual(order.current_status.status_name, 'delivered')
        self.assertTrue(order.current_status.is_final_state)
    
    def test_assign_staff_creates_assignment(self):
        """Test that assigning staff creates an OrderAssignment."""
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            created_by=self.admin_user
        )
        
        assignment = OrderService.assign_staff(
            order=order,
            staff=self.tailor,
            role_type='tailor',
            assigned_by=self.admin_user,
            notes='Expert tailor for this order'
        )
        
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.staff, self.tailor)
        self.assertEqual(assignment.role_type, 'tailor')
        self.assertEqual(assignment.assigned_by, self.admin_user)
    
    def test_get_pending_orders(self):
        """Test retrieving pending orders."""
        # Create an order (will be pending)
        OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() + timedelta(days=14),
            created_by=self.admin_user
        )
        
        pending = OrderService.get_pending_orders()
        self.assertGreaterEqual(pending.count(), 1)
    
    def test_get_overdue_orders(self):
        """Test retrieving overdue orders."""
        # Create an order with past delivery date
        order = OrderService.create_order(
            customer=self.customer,
            garment_type=self.garment_type,
            expected_delivery_date=date.today() - timedelta(days=1),  # Yesterday
            created_by=self.admin_user
        )
        
        overdue = OrderService.get_overdue_orders()
        self.assertIn(order, overdue)


class OrderStatusTransitionTests(TestCase):
    """Test cases for order state machine transitions."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test statuses and transitions."""
        cls.status_a = OrderStatus.objects.create(
            status_name='status_a',
            display_label='Status A',
            sequence_order=1
        )
        cls.status_b = OrderStatus.objects.create(
            status_name='status_b',
            display_label='Status B',
            sequence_order=2
        )
        cls.status_c = OrderStatus.objects.create(
            status_name='status_c',
            display_label='Status C',
            sequence_order=3
        )
        
        # A -> B is valid
        OrderStatusTransition.objects.create(
            from_status=cls.status_a,
            to_status=cls.status_b
        )
        # B -> C is valid
        OrderStatusTransition.objects.create(
            from_status=cls.status_b,
            to_status=cls.status_c
        )
    
    def test_valid_transition_exists(self):
        """Test checking if a valid transition exists."""
        exists = OrderStatusTransition.objects.filter(
            from_status=self.status_a,
            to_status=self.status_b
        ).exists()
        self.assertTrue(exists)
    
    def test_invalid_transition_does_not_exist(self):
        """Test that invalid transitions don't exist."""
        exists = OrderStatusTransition.objects.filter(
            from_status=self.status_a,
            to_status=self.status_c  # A -> C is not allowed
        ).exists()
        self.assertFalse(exists)
