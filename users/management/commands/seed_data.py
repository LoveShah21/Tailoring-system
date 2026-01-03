"""
Management Command: seed_data

Seeds the database with initial data:
- Roles (admin, staff, customer, tailor, delivery, designer)
- Permissions
- Order statuses and transitions
- Payment modes
- Notification types and channels
- Delivery zones
- Sample garment and work types
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import Role, Permission, RolePermission
from orders.models import OrderStatus, OrderStatusTransition
from payments.models import PaymentMode
from notifications.models import NotificationType, NotificationChannel
from delivery.models import DeliveryZone
from catalog.models import GarmentType, WorkType, GarmentWorkType
from config.models import SystemConfiguration


class Command(BaseCommand):
    help = 'Seeds the database with initial data'
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        self._seed_roles()
        self._seed_permissions()
        self._seed_role_permissions()
        self._seed_order_statuses()
        self._seed_order_transitions()
        self._seed_payment_modes()
        self._seed_notification_types()
        self._seed_notification_channels()
        self._seed_delivery_zones()
        self._seed_garment_types()
        self._seed_work_types()
        self._seed_garment_work_types()
        self._seed_system_config()
        self._seed_users()
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
    
    def _seed_users(self):
        from users.models import User, UserRole
        from customers.models import CustomerProfile
        
        # 1. Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@tailoring.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            # Assign admin role
            admin_role = Role.objects.get(name='admin')
            UserRole.objects.get_or_create(user=admin, role=admin_role)
            self.stdout.write('  ✓ Created admin user')
        else:
             self.stdout.write('  - Admin user already exists')

        # 2. Staff (3 users)
        staff_data = [
            ('staff1', 'staff1@tailoring.com', 'Sarah', 'Manager'),
            ('staff2', 'staff2@tailoring.com', 'Mike', 'Coordinator'),
            ('staff3', 'staff3@tailoring.com', 'Emily', 'Receptionist'),
        ]
        
        staff_role = Role.objects.get(name='staff')
        for user, email, first, last in staff_data:
            u, created = User.objects.get_or_create(
                username=user,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                u.set_password('staff123')
                u.save()
                UserRole.objects.get_or_create(user=u, role=staff_role)
        self.stdout.write(f'  ✓ Processed {len(staff_data)} staff users')

        # 3. Tailors (4 users)
        tailor_data = [
            ('tailor1', 'tailor1@tailoring.com', 'Rahul', 'Master'),
            ('tailor2', 'tailor2@tailoring.com', 'Amit', 'Stitcher'),
            ('tailor3', 'tailor3@tailoring.com', 'Suresh', 'Cutter'),
            ('tailor4', 'tailor4@tailoring.com', 'Priya', 'Finisher'),
        ]
        
        tailor_role = Role.objects.get(name='tailor')
        for user, email, first, last in tailor_data:
            u, created = User.objects.get_or_create(
                username=user,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                u.set_password('tailor123')
                u.save()
                UserRole.objects.get_or_create(user=u, role=tailor_role)
        self.stdout.write(f'  ✓ Processed {len(tailor_data)} tailors')

        # 4. Designers (2 users)
        designer_data = [
            ('designer1', 'designer1@tailoring.com', 'Zara', 'Lead'),
            ('designer2', 'designer2@tailoring.com', 'Leo', 'Sketch'),
        ]
        
        designer_role = Role.objects.get(name='designer')
        for user, email, first, last in designer_data:
            u, created = User.objects.get_or_create(
                username=user,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                u.set_password('designer123')
                u.save()
                UserRole.objects.get_or_create(user=u, role=designer_role)
        self.stdout.write(f'  ✓ Processed {len(designer_data)} designers')
        
        # 5. Delivery (2 users)
        delivery_data = [
            ('delivery1', 'delivery1@tailoring.com', 'Vikram', 'Rider'),
            ('delivery2', 'delivery2@tailoring.com', 'Arjun', 'Driver'),
        ]
        
        delivery_role = Role.objects.get(name='delivery')
        for user, email, first, last in delivery_data:
            u, created = User.objects.get_or_create(
                username=user,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                u.set_password('delivery123')
                u.save()
                UserRole.objects.get_or_create(user=u, role=delivery_role)
        self.stdout.write(f'  ✓ Processed {len(delivery_data)} delivery users')

        # 6. Customers (15 users)
        customer_role = Role.objects.get(name='customer')
        created_count = 0
        for i in range(1, 16):
            username = f'customer{i}'
            email = f'customer{i}@example.com'
            
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Customer',
                    'last_name': f'{i}',
                    'is_staff': False,
                    'is_active': True
                }
            )
            if created:
                u.set_password('customer123')
                u.save()
                UserRole.objects.get_or_create(user=u, role=customer_role)
                
                # Create profile
                CustomerProfile.objects.get_or_create(
                    user=u,
                    defaults={
                        'phone_number': f'9876543{i:03d}',
                        'address_line_1': f'{i} Market Street',
                        'city': 'Mumbai',
                        'state': 'Maharashtra',
                        'postal_code': f'4000{i:02d}',
                        'country': 'India'
                    }
                )
                created_count += 1
                
        self.stdout.write(f'  ✓ Created {created_count} new customers')

        # Print Credentials Summary
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('USER CREDENTIALS (COPY THESE):'))
        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write(f"{'Username':<20} | {'Role':<15} | {'Password':<15}")
        self.stdout.write('-'*60)
        
        # Admin
        self.stdout.write(f"{'admin':<20} | {'Admin':<15} | {'admin123':<15}")
        
        # Staff
        for i, (u, _, _, _) in enumerate(staff_data, 1):
            self.stdout.write(f"{u:<20} | {'Staff':<15} | {'staff123':<15}")
            
        # Tailors
        for i, (u, _, _, _) in enumerate(tailor_data, 1):
             self.stdout.write(f"{u:<20} | {'Tailor':<15} | {'tailor123':<15}")

        # Designers
        for i, (u, _, _, _) in enumerate(designer_data, 1):
             self.stdout.write(f"{u:<20} | {'Designer':<15} | {'designer123':<15}")

        # Delivery
        for i, (u, _, _, _) in enumerate(delivery_data, 1):
             self.stdout.write(f"{u:<20} | {'Delivery':<15} | {'delivery123':<15}")

        # Customers (Sample 5)
        for i in range(1, 6):
            self.stdout.write(f"{f'customer{i}':<20} | {'Customer':<15} | {'customer123':<15}")
        self.stdout.write(f"... and {10} more customers with password 'customer123'")
        self.stdout.write(self.style.WARNING('='*60 + '\n'))
    
    def _seed_roles(self):
        roles = [
            ('admin', 'Full system access - manage all modules'),
            ('staff', 'General staff - manage orders and customers'),
            ('customer', 'Customer portal access'),
            ('tailor', 'Tailor - view and update assigned orders'),
            ('delivery', 'Delivery personnel - manage deliveries'),
            ('designer', 'Designer - manage designs and customizations'),
        ]
        
        for name, description in roles:
            Role.objects.get_or_create(name=name, defaults={'description': description})
        
        self.stdout.write(f'  ✓ Created {len(roles)} roles')
    
    def _seed_permissions(self):
        permissions = [
            # User management
            ('view_users', 'View user list'),
            ('manage_users', 'Create, edit, delete users'),
            ('manage_roles', 'Manage roles and permissions'),
            
            # Customer management
            ('view_customers', 'View customer list'),
            ('manage_customers', 'Create, edit customers'),
            
            # Catalog management
            ('view_catalog', 'View catalog'),
            ('manage_catalog', 'Manage garment types, work types'),
            
            # Inventory management
            ('view_inventory', 'View inventory'),
            ('manage_inventory', 'Manage stock levels'),
            
            # Order management
            ('view_orders', 'View orders'),
            ('create_orders', 'Create new orders'),
            ('edit_orders', 'Edit order details'),
            ('manage_order_status', 'Change order status'),
            
            # Billing & Payments
            ('view_billing', 'View bills and invoices'),
            ('manage_billing', 'Generate invoices'),
            ('view_payments', 'View payments'),
            ('manage_payments', 'Record payments, refunds'),
            
            # Delivery
            ('view_deliveries', 'View deliveries'),
            ('manage_deliveries', 'Schedule and update deliveries'),
            
            # Reporting
            ('view_reports', 'View reports'),
            ('export_reports', 'Export reports to PDF/CSV'),
            
            # Audit
            ('view_audit_logs', 'View audit logs'),
            
            # Configuration
            ('manage_config', 'Manage system configuration'),
        ]
        
        for name, description in permissions:
            Permission.objects.get_or_create(name=name, defaults={'description': description})
        
        self.stdout.write(f'  ✓ Created {len(permissions)} permissions')
    
    def _seed_role_permissions(self):
        role_permissions = {
            'admin': [
                'view_users', 'manage_users', 'manage_roles',
                'view_customers', 'manage_customers',
                'view_catalog', 'manage_catalog',
                'view_inventory', 'manage_inventory',
                'view_orders', 'create_orders', 'edit_orders', 'manage_order_status',
                'view_billing', 'manage_billing',
                'view_payments', 'manage_payments',
                'view_deliveries', 'manage_deliveries',
                'view_reports', 'export_reports',
                'view_audit_logs', 'manage_config',
            ],
            'staff': [
                'view_customers', 'manage_customers',
                'view_catalog', 'view_inventory',
                'view_orders', 'create_orders', 'edit_orders', 'manage_order_status',
                'view_billing', 'manage_billing',
                'view_payments', 'manage_payments',
                'view_deliveries', 'manage_deliveries',
            ],
            'tailor': [
                'view_orders', 'manage_order_status',
                'view_catalog', 'view_inventory',
            ],
            'delivery': [
                'view_orders', 'view_deliveries', 'manage_deliveries',
            ],
            'designer': [
                'view_orders', 'view_catalog',
            ],
            'customer': [
                'view_orders',
            ],
        }
        
        count = 0
        for role_name, perms in role_permissions.items():
            try:
                role = Role.objects.get(name=role_name)
                for perm_name in perms:
                    try:
                        permission = Permission.objects.get(name=perm_name)
                        RolePermission.objects.get_or_create(role=role, permission=permission)
                        count += 1
                    except Permission.DoesNotExist:
                        pass
            except Role.DoesNotExist:
                pass
        
        self.stdout.write(f'  ✓ Assigned {count} role-permission mappings')
    
    def _seed_order_statuses(self):
        statuses = [
            ('booked', 'Booked', 'Order placed, awaiting fabric allocation', 1, False),
            ('fabric_allocated', 'Fabric Allocated', 'Fabric assigned to order', 2, False),
            ('stitching', 'Stitching', 'Order is being stitched', 3, False),
            ('trial_scheduled', 'Trial Scheduled', 'Trial appointment scheduled', 4, False),
            ('alteration', 'Alteration', 'Changes being made after trial', 5, False),
            ('ready', 'Ready', 'Order ready for delivery/pickup', 6, False),
            ('delivered', 'Delivered', 'Order delivered to customer', 7, True),
            ('closed', 'Closed', 'Order completed and closed', 8, True),
        ]
        
        for status_name, display, desc, seq, is_final in statuses:
            OrderStatus.objects.get_or_create(
                status_name=status_name,
                defaults={
                    'display_label': display,
                    'description': desc,
                    'sequence_order': seq,
                    'is_final_state': is_final,
                }
            )
        
        self.stdout.write(f'  ✓ Created {len(statuses)} order statuses')
    
    def _seed_order_transitions(self):
        transitions = [
            ('booked', 'fabric_allocated', 'staff,admin'),
            ('fabric_allocated', 'stitching', 'tailor,staff,admin'),
            ('stitching', 'trial_scheduled', 'staff,admin'),
            ('stitching', 'ready', 'staff,admin'),  # Skip trial if not needed
            ('trial_scheduled', 'alteration', 'staff,admin'),
            ('trial_scheduled', 'ready', 'staff,admin'),  # No alterations needed
            ('alteration', 'ready', 'tailor,staff,admin'),
            ('ready', 'delivered', 'delivery,staff,admin'),
            ('delivered', 'closed', 'staff,admin'),
        ]
        
        count = 0
        for from_name, to_name, roles in transitions:
            try:
                from_status = OrderStatus.objects.get(status_name=from_name)
                to_status = OrderStatus.objects.get(status_name=to_name)
                OrderStatusTransition.objects.get_or_create(
                    from_status=from_status,
                    to_status=to_status,
                    defaults={'allowed_roles': roles}
                )
                count += 1
            except OrderStatus.DoesNotExist:
                pass
        
        self.stdout.write(f'  ✓ Created {count} order status transitions')
    
    def _seed_payment_modes(self):
        modes = [
            ('razorpay', 'Online payment via Razorpay'),
            ('cash', 'Cash payment'),
            ('bank_transfer', 'Bank transfer / NEFT / RTGS'),
            ('cheque', 'Cheque payment'),
            ('upi', 'UPI payment (in person)'),
        ]
        
        for name, desc in modes:
            PaymentMode.objects.get_or_create(mode_name=name, defaults={'description': desc})
        
        self.stdout.write(f'  ✓ Created {len(modes)} payment modes')
    
    def _seed_notification_types(self):
        types = [
            ('order_confirmation', 'Order Confirmation'),
            ('order_status_update', 'Order Status Update'),
            ('order_ready', 'Order Ready'),
            ('payment_success', 'Payment Received'),
            ('payment_failed', 'Payment Failed'),
            ('trial_scheduled', 'Trial Scheduled'),
            ('delivery_scheduled', 'Delivery Scheduled'),
            ('delivery_completed', 'Delivery Completed'),
            ('password_reset', 'Password Reset Request'),
            ('feedback_request', 'Feedback Request'),
        ]
        
        for name, display in types:
            NotificationType.objects.get_or_create(type_name=name, defaults={'display_name': display})
        
        self.stdout.write(f'  ✓ Created {len(types)} notification types')
    
    def _seed_notification_channels(self):
        channels = [
            ('email', True, 'IMPLEMENTED'),
            ('sms', False, 'PLANNED'),
            ('whatsapp', False, 'PLANNED'),
            ('in_app', True, 'IMPLEMENTED'),
        ]
        
        for name, enabled, status in channels:
            NotificationChannel.objects.get_or_create(
                channel_name=name,
                defaults={'is_enabled': enabled, 'implementation_status': status}
            )
        
        self.stdout.write(f'  ✓ Created {len(channels)} notification channels')
    
    def _seed_delivery_zones(self):
        zones = [
            ('Zone A - City Center', 1),
            ('Zone B - Suburbs', 2),
            ('Zone C - Outskirts', 3),
            ('Zone D - Remote', 5),
        ]
        
        for name, days in zones:
            DeliveryZone.objects.get_or_create(name=name, defaults={'base_delivery_days': days})
        
        self.stdout.write(f'  ✓ Created {len(zones)} delivery zones')
    
    def _seed_garment_types(self):
        garments = [
            ('Blouse', 'Traditional blouse for sarees', 800.00, 1.5, 5),
            ('Kurti', 'Stylish kurti for everyday wear', 1200.00, 2.5, 7),
            ('Salwar Suit', 'Complete salwar kameez set', 2500.00, 5.0, 10),
            ('Lehenga', 'Bridal/party lehenga', 8000.00, 8.0, 21),
            ('Anarkali', 'Floor-length anarkali dress', 3500.00, 6.0, 14),
            ('Gown', 'Western style gown', 4000.00, 5.0, 14),
            ('Saree Petticoat', 'Inner petticoat for sarees', 400.00, 1.0, 3),
            ('Dupatta', 'Embroidered dupatta', 600.00, 2.0, 5),
        ]
        
        for name, desc, price, fabric, days in garments:
            GarmentType.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'base_price': price,
                    'fabric_requirement_meters': fabric,
                    'stitching_days_estimate': days,
                }
            )
        
        self.stdout.write(f'  ✓ Created {len(garments)} garment types')
    
    def _seed_work_types(self):
        works = [
            ('Mirror Work', 'Traditional mirror embellishment', 500.00, 8),
            ('Jardoshi', 'Gold/silver thread embroidery', 1500.00, 16),
            ('Zari Work', 'Metallic thread work', 1200.00, 12),
            ('Hand Embroidery', 'Hand-stitched embroidery', 800.00, 10),
            ('Machine Embroidery', 'Machine embroidered designs', 400.00, 4),
            ('Sequins', 'Sequin embellishments', 300.00, 6),
            ('Beadwork', 'Bead embellishments', 600.00, 8),
            ('Lace Border', 'Lace border attachment', 200.00, 2),
            ('Piping', 'Contrast piping', 150.00, 2),
            ('Pearl Work', 'Pearl embellishments', 700.00, 8),
        ]
        
        for name, desc, charge, hours in works:
            WorkType.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'extra_charge': charge,
                    'labor_hours_estimate': hours,
                }
            )
        
        self.stdout.write(f'  ✓ Created {len(works)} work types')
    
    def _seed_garment_work_types(self):
        # Map which work types are supported for which garments
        mappings = {
            'Blouse': ['Mirror Work', 'Jardoshi', 'Machine Embroidery', 'Piping', 'Lace Border'],
            'Kurti': ['Hand Embroidery', 'Machine Embroidery', 'Lace Border', 'Piping'],
            'Salwar Suit': ['Jardoshi', 'Zari Work', 'Hand Embroidery', 'Machine Embroidery', 'Lace Border'],
            'Lehenga': ['Mirror Work', 'Jardoshi', 'Zari Work', 'Beadwork', 'Sequins', 'Pearl Work'],
            'Anarkali': ['Jardoshi', 'Zari Work', 'Sequins', 'Hand Embroidery'],
            'Gown': ['Sequins', 'Beadwork', 'Lace Border', 'Pearl Work'],
        }
        
        count = 0
        for garment_name, work_names in mappings.items():
            try:
                garment = GarmentType.objects.get(name=garment_name)
                for work_name in work_names:
                    try:
                        work = WorkType.objects.get(name=work_name)
                        GarmentWorkType.objects.get_or_create(
                            garment_type=garment,
                            work_type=work,
                            defaults={'is_supported': True}
                        )
                        count += 1
                    except WorkType.DoesNotExist:
                        pass
            except GarmentType.DoesNotExist:
                pass
        
        self.stdout.write(f'  ✓ Created {count} garment-work type mappings')
    
    def _seed_system_config(self):
        config = SystemConfiguration.get_config()
        self.stdout.write('  ✓ System configuration initialized')
