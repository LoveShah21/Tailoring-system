"""
Inventory App - Tests

Comprehensive test cases for InventoryService.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from inventory.models import Fabric, StockTransaction, LowStockAlert
from inventory.services import InventoryService
from users.models import User


class InventoryServiceTests(TestCase):
    """Test cases for InventoryService."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        cls.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
    
    def test_create_fabric_success(self):
        """Test creating a new fabric."""
        fabric = InventoryService.create_fabric(
            name='Cotton Silk',
            color='Navy Blue',
            pattern='Plain',
            quantity_in_stock=100,
            cost_per_meter=Decimal('250.00'),
            reorder_threshold=10.0,
            created_by=self.staff_user
        )
        
        self.assertIsNotNone(fabric)
        self.assertEqual(fabric.name, 'Cotton Silk')
        self.assertEqual(fabric.quantity_in_stock, Decimal('100'))
        
        # Check initial stock transaction was created
        transactions = StockTransaction.objects.filter(fabric=fabric)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().transaction_type, 'IN')
    
    def test_record_stock_in_increases_quantity(self):
        """Test that stock in increases the fabric quantity."""
        fabric = Fabric.objects.create(
            name='Test Fabric',
            color='Red',
            pattern='Checkered',
            quantity_in_stock=Decimal('50'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('10')
        )
        
        transaction = InventoryService.record_stock_in(
            fabric=fabric,
            quantity=25,
            recorded_by=self.staff_user,
            notes='Restocking'
        )
        
        fabric.refresh_from_db()
        self.assertEqual(fabric.quantity_in_stock, Decimal('75'))
        self.assertEqual(transaction.transaction_type, 'IN')
        self.assertEqual(transaction.quantity_meters, Decimal('25'))
        self.assertEqual(transaction.previous_quantity, Decimal('50'))
        self.assertEqual(transaction.new_quantity, Decimal('75'))
    
    def test_record_stock_out_decreases_quantity(self):
        """Test that stock out decreases the fabric quantity."""
        fabric = Fabric.objects.create(
            name='Test Fabric Out',
            color='Blue',
            pattern='Plain',
            quantity_in_stock=Decimal('100'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('10')
        )
        
        transaction = InventoryService.record_stock_out(
            fabric=fabric,
            quantity=30,
            recorded_by=self.staff_user,
            notes='Allocated to order'
        )
        
        fabric.refresh_from_db()
        self.assertEqual(fabric.quantity_in_stock, Decimal('70'))
        self.assertEqual(transaction.transaction_type, 'OUT')
    
    def test_record_stock_out_insufficient_raises_error(self):
        """Test that insufficient stock raises ValidationError."""
        fabric = Fabric.objects.create(
            name='Low Stock Fabric',
            color='Green',
            pattern='Plain',
            quantity_in_stock=Decimal('10'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('5')
        )
        
        with self.assertRaises(ValidationError) as context:
            InventoryService.record_stock_out(
                fabric=fabric,
                quantity=20,  # More than available
                recorded_by=self.staff_user
            )
        
        self.assertIn('Insufficient stock', str(context.exception))
    
    def test_low_stock_alert_created_when_below_threshold(self):
        """Test that low stock alert is created when stock falls below threshold."""
        fabric = Fabric.objects.create(
            name='Alert Test Fabric',
            color='Yellow',
            pattern='Plain',
            quantity_in_stock=Decimal('15'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('10')
        )
        
        # Reduce stock below threshold
        InventoryService.record_stock_out(
            fabric=fabric,
            quantity=10,
            recorded_by=self.staff_user
        )
        
        # Check alert was created
        alert = LowStockAlert.objects.filter(fabric=fabric, is_resolved=False).first()
        self.assertIsNotNone(alert)
    
    def test_record_damage_decreases_stock(self):
        """Test that damage recording decreases stock."""
        fabric = Fabric.objects.create(
            name='Damage Test Fabric',
            color='Orange',
            pattern='Plain',
            quantity_in_stock=Decimal('50'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('5')
        )
        
        transaction = InventoryService.record_damage(
            fabric=fabric,
            quantity=5,
            recorded_by=self.staff_user,
            notes='Water damage'
        )
        
        fabric.refresh_from_db()
        self.assertEqual(fabric.quantity_in_stock, Decimal('45'))
        self.assertEqual(transaction.transaction_type, 'DAMAGE')
    
    def test_record_damage_insufficient_raises_error(self):
        """Test that damage greater than stock raises error."""
        fabric = Fabric.objects.create(
            name='Small Stock Fabric',
            color='Purple',
            pattern='Plain',
            quantity_in_stock=Decimal('3'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('5')
        )
        
        with self.assertRaises(ValidationError):
            InventoryService.record_damage(
                fabric=fabric,
                quantity=5,  # More than available
                recorded_by=self.staff_user
            )
    
    def test_get_low_stock_fabrics(self):
        """Test retrieving low stock fabrics."""
        # Create fabric at reorder threshold
        fabric = Fabric.objects.create(
            name='Low Fabric',
            color='Black',
            pattern='Plain',
            quantity_in_stock=Decimal('5'),  # At threshold
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('10')
        )
        
        low_stock = InventoryService.get_low_stock_fabrics()
        self.assertIn(fabric, low_stock)
    
    def test_resolve_alert(self):
        """Test resolving a low stock alert."""
        fabric = Fabric.objects.create(
            name='Resolve Alert Fabric',
            color='White',
            pattern='Plain',
            quantity_in_stock=Decimal('3'),
            cost_per_meter=Decimal('200.00'),
            reorder_threshold=Decimal('10')
        )
        
        # Create alert
        alert = LowStockAlert.objects.create(fabric=fabric)
        
        # Resolve it
        resolved = InventoryService.resolve_alert(alert)
        
        self.assertTrue(resolved.is_resolved)
        self.assertIsNotNone(resolved.resolved_at)
    
    def test_get_stock_value(self):
        """Test calculating total stock value."""
        # Clear existing fabrics
        Fabric.objects.filter(is_deleted=False).update(is_deleted=True)
        
        Fabric.objects.create(
            name='Value Test A',
            color='Red',
            pattern='Plain',
            quantity_in_stock=Decimal('10'),
            cost_per_meter=Decimal('100.00'),
            reorder_threshold=Decimal('5')
        )
        Fabric.objects.create(
            name='Value Test B',
            color='Blue',
            pattern='Plain',
            quantity_in_stock=Decimal('20'),
            cost_per_meter=Decimal('50.00'),
            reorder_threshold=Decimal('5')
        )
        
        # Expected: 10*100 + 20*50 = 1000 + 1000 = 2000
        value = InventoryService.get_stock_value()
        self.assertEqual(value, Decimal('2000.00'))
