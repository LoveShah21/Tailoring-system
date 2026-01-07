# Database Queries Reference - Tailoring Management System

> **Purpose**: This document provides a comprehensive reference of all database queries used in the Tailoring Management System. It is specifically designed for viva and technical defense purposes, explaining what queries are executed, why they exist, and how they are optimized.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [ORM Query Categories Overview](#2-orm-query-categories-overview)
3. [Module-wise Query Documentation](#3-module-wise-query-documentation)
4. [Complex & Critical Queries (Viva Focus)](#4-complex--critical-queries-viva-focus)
5. [Raw SQL Queries](#5-raw-sql-queries)
6. [Transactional Queries](#6-transactional-queries)
7. [Read vs Write Patterns](#7-read-vs-write-patterns)
8. [Query Performance & Scaling Considerations](#8-query-performance--scaling-considerations)
9. [Common Viva Questions & Answers](#9-common-viva-questions--answers)

---

## 1. Introduction

### Purpose of Documenting Queries

This document serves as a technical reference for understanding all database interactions in the Tailoring Management System. It enables:
- **Viva preparation**: Explain any database query with confidence
- **Performance optimization**: Identify bottlenecks and optimization opportunities
- **Debugging**: Trace data flow through the application
- **Code review**: Validate query efficiency and correctness

### Difference Between ORM-Generated SQL and Raw SQL

| Aspect | Django ORM | Raw SQL |
|--------|------------|---------|
| **Abstraction** | High-level Python API | Direct database commands |
| **Portability** | Database-agnostic | Database-specific |
| **Safety** | Automatic SQL injection prevention | Manual parameterization required |
| **Performance** | May generate suboptimal queries | Full control, can be highly optimized |
| **Maintainability** | Easier to maintain with model changes | Requires manual updates |

**This project exclusively uses Django ORM**. No raw SQL queries are present, ensuring:
- Automatic SQL injection prevention
- Database portability (MySQL in production, SQLite for testing)
- Type-safe query construction

### Why Understanding Queries Matters for Scalability and Performance

1. **N+1 Query Problem**: Without proper `select_related`/`prefetch_related`, fetching N orders could trigger N+1 queries
2. **Index Utilization**: Queries must align with defined indexes for efficient execution
3. **Transaction Integrity**: Critical operations (payment → order status) require atomic transactions
4. **Memory Management**: Large result sets need pagination to avoid memory exhaustion

---

## 2. ORM Query Categories Overview

The project organizes database queries into the following logical modules:

| Category | Tables | Primary Operations |
|----------|--------|-------------------|
| **Authentication & IAM** | `users_user`, `users_role`, `users_user_role`, `users_permission`, `users_role_permission` | User login, role checks, permission verification |
| **Catalog & Configuration** | `catalog_garment_type`, `catalog_work_type`, `catalog_garment_work_type`, `config_system_configuration`, `config_pricing_rule` | Product catalog, pricing rules |
| **Customers** | `customers_customer_profile`, `measurements_measurement_set`, `measurements_measurement_value` | Customer management, measurements |
| **Orders** | `orders_order`, `orders_order_status`, `orders_order_status_transition`, `orders_order_status_history`, `orders_order_assignment`, `orders_order_material_allocation` | Order lifecycle management |
| **Billing & Payments** | `billing_order_bill`, `billing_invoice`, `payments_payment`, `payments_razorpay_order`, `payments_refund` | Billing, invoicing, payment processing |
| **Inventory** | `inventory_fabric`, `inventory_stock_transaction`, `inventory_low_stock_alert` | Stock management, alerts |
| **Trials & Delivery** | `trials_trial`, `trials_alteration`, `delivery_delivery`, `delivery_delivery_zone` | Trial scheduling, delivery tracking |
| **Notifications** | `notifications_notification`, `notifications_notification_type`, `notifications_notification_channel` | Customer communications |
| **Reporting & Analytics** | `reporting_monthly_revenue`, `reporting_pending_orders_snapshot`, `reporting_staff_workload` | Business intelligence |
| **Audit & Logs** | `audit_activity_log`, `audit_payment_audit_log` | Audit trails |

---

## 3. Module-wise Query Documentation

### 3.1 Users Module

#### 3.1.1 User Authentication Query

**Query Purpose**: Authenticate user during login, excluding soft-deleted users.

**Django ORM Code** (`users/models.py` - UserManager):
```python
def get_queryset(self):
    """Override to exclude soft-deleted users by default."""
    return super().get_queryset().filter(is_deleted=False)
```

**Generated SQL (Approximate)**:
```sql
SELECT * FROM users_user WHERE is_deleted = FALSE;
```

**Tables Involved**: `users_user`

**Query Type**: SELECT with filter

**Index Usage**:
- `idx_is_deleted` on `is_deleted` column - ensures fast filtering

**Optimization Notes**:
- Soft delete pattern prevents orphaned records
- Default manager excludes deleted users, reducing result set size

---

#### 3.1.2 Role Check Query

**Query Purpose**: Check if a user has a specific role (e.g., 'admin', 'tailor').

**Django ORM Code** (`users/models.py` - User.has_role()):
```python
def has_role(self, role_name):
    """Check if user has a specific role."""
    return self.user_roles.filter(
        role__name=role_name, 
        is_deleted=False
    ).exists()
```

**Generated SQL (Approximate)**:
```sql
SELECT EXISTS(
    SELECT 1 FROM users_user_role 
    INNER JOIN users_role ON users_user_role.role_id = users_role.id
    WHERE users_user_role.user_id = %s 
    AND users_role.name = %s 
    AND users_user_role.is_deleted = FALSE
    LIMIT 1
);
```

**Tables Involved**: `users_user_role`, `users_role`

**Query Type**: SELECT with EXISTS (subquery)

**Index Usage**:
- `idx_user_role_user` on `user_id` - FK index
- `idx_role_name` on `role.name` - unique constraint acts as index

**Optimization Notes**:
- `exists()` returns boolean without fetching all rows
- More efficient than `count() > 0` for existence checks

---

#### 3.1.3 Permission Check Query

**Query Purpose**: Check if user has a specific permission through any of their roles.

**Django ORM Code** (`users/models.py` - User.has_permission()):
```python
def has_permission(self, permission_name):
    """Check if user has a specific permission through any role."""
    return Permission.objects.filter(
        role_permissions__role__user_roles__user=self,
        role_permissions__role__user_roles__is_deleted=False,
        name=permission_name
    ).exists()
```

**Generated SQL (Approximate)**:
```sql
SELECT EXISTS(
    SELECT 1 FROM users_permission p
    INNER JOIN users_role_permission rp ON p.id = rp.permission_id
    INNER JOIN users_role r ON rp.role_id = r.id
    INNER JOIN users_user_role ur ON r.id = ur.role_id
    WHERE ur.user_id = %s 
    AND ur.is_deleted = FALSE 
    AND p.name = %s
    LIMIT 1
);
```

**Tables Involved**: `users_permission`, `users_role_permission`, `users_role`, `users_user_role`

**Query Type**: SELECT with multiple JOINs

**Index Usage**:
- `idx_permission_name` - filters by permission name
- `idx_user_role_user` - filters by user
- FK indexes on junction tables enable efficient joins

**Optimization Notes**:
- Multi-table join through RBAC hierarchy
- `exists()` prevents full table scan

---

#### 3.1.4 User List with Search and Filters

**Query Purpose**: List all users with search and role filtering for admin panel.

**Django ORM Code** (`users/views.py` - AdminUserListView):
```python
def get_queryset(self):
    queryset = User.objects.all().order_by('-created_at')
    
    # Search
    search = self.request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Filter by role
    role = self.request.GET.get('role', '')
    if role:
        queryset = queryset.filter(
            user_roles__role__name=role, 
            user_roles__is_deleted=False
        )
    
    return queryset.distinct()
```

**Generated SQL (Approximate)**:
```sql
SELECT DISTINCT u.* FROM users_user u
LEFT JOIN users_user_role ur ON u.id = ur.user_id
LEFT JOIN users_role r ON ur.role_id = r.id
WHERE (u.username ILIKE '%search%' 
    OR u.email ILIKE '%search%'
    OR u.first_name ILIKE '%search%')
AND r.name = 'admin'
AND ur.is_deleted = FALSE
ORDER BY u.created_at DESC;
```

**Tables Involved**: `users_user`, `users_user_role`, `users_role`

**Query Type**: SELECT with OR conditions, JOIN, DISTINCT

**Index Usage**:
- `idx_username`, `idx_email` - partial index usage for prefix searches
- `idx_created_at` - for ORDER BY optimization
- ILIKE searches may not use indexes efficiently

**Optimization Notes**:
- `distinct()` prevents duplicate rows from JOINs
- Consider full-text search for large user bases
- Q objects create OR conditions which can be slower than ANDs

---

### 3.2 Orders Module

#### 3.2.1 Order List Query

**Query Purpose**: Fetch paginated order list with related customer, garment type, and status.

**Django ORM Code** (`orders/views.py` - OrderListView):
```python
def get_queryset(self):
    queryset = Order.objects.filter(is_deleted=False).select_related(
        'customer__user', 'garment_type', 'current_status'
    ).order_by('-created_at')
    
    # Search
    search = self.request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(order_number__icontains=search) |
            Q(customer__user__first_name__icontains=search) |
            Q(customer__user__last_name__icontains=search) |
            Q(customer__phone_number__icontains=search)
        )
    
    # Status filter
    status = self.request.GET.get('status')
    if status:
        queryset = queryset.filter(current_status__status_name=status)
    
    return queryset
```

**Generated SQL (Approximate)**:
```sql
SELECT o.*, cp.*, u.*, gt.*, os.*
FROM orders_order o
INNER JOIN customers_customer_profile cp ON o.customer_id = cp.id
INNER JOIN users_user u ON cp.user_id = u.id
INNER JOIN catalog_garment_type gt ON o.garment_type_id = gt.id
INNER JOIN orders_order_status os ON o.current_status_id = os.id
WHERE o.is_deleted = FALSE
AND (o.order_number LIKE '%search%' 
    OR u.first_name LIKE '%search%'
    OR u.last_name LIKE '%search%')
AND os.status_name = 'stitching'
ORDER BY o.created_at DESC
LIMIT 20 OFFSET 0;
```

**Tables Involved**: `orders_order`, `customers_customer_profile`, `users_user`, `catalog_garment_type`, `orders_order_status`

**Query Type**: SELECT with multiple JOINs, filtering, pagination

**Index Usage**:
- `idx_order_deleted` - filters deleted orders
- `idx_order_number` - search by order number
- `idx_order_status` - FK index for status filter
- `idx_order_created` - ORDER BY optimization

**Optimization Notes**:
- `select_related()` prevents N+1 queries by fetching related objects in single query
- Without it, accessing `order.customer.user.first_name` would trigger 3 additional queries per order
- Pagination (`paginate_by = 20`) limits result set

---

#### 3.2.2 Order Detail Query

**Query Purpose**: Fetch single order with all related data for detail view.

**Django ORM Code** (`orders/views.py` - OrderDetailView):
```python
def get_queryset(self):
    return Order.objects.filter(is_deleted=False).select_related(
        'customer__user', 'garment_type', 'current_status',
        'measurement_set', 'design'
    )

def get_context_data(self, **kwargs):
    # Status history with related objects
    context['status_history'] = order.status_history.select_related(
        'from_status', 'to_status', 'changed_by'
    ).order_by('-changed_at')
    
    # Assignments with staff info
    context['assignments'] = order.assignments.select_related(
        'staff', 'assigned_by'
    )
    
    # Work types
    context['work_types'] = order.order_work_types.select_related('work_type')
    
    # Material allocations
    context['allocations'] = order.material_allocations.select_related(
        'fabric', 'allocated_by'
    )
```

**Generated SQL (Approximate)**:
```sql
-- Main order query
SELECT o.*, cp.*, u.*, gt.*, os.*, ms.*, d.*
FROM orders_order o
INNER JOIN customers_customer_profile cp ON o.customer_id = cp.id
-- ... additional joins for all select_related tables

-- Status history (separate query)
SELECT h.*, fs.*, ts.*, u.*
FROM orders_order_status_history h
INNER JOIN orders_order_status fs ON h.from_status_id = fs.id
INNER JOIN orders_order_status ts ON h.to_status_id = ts.id
INNER JOIN users_user u ON h.changed_by_id = u.id
WHERE h.order_id = %s
ORDER BY h.changed_at DESC;

-- Similar pattern for assignments, work_types, allocations
```

**Tables Involved**: 10+ tables including all order-related models

**Query Type**: Multiple SELECT queries with JOINs

**Index Usage**:
- `idx_status_history_order` - filters history by order
- `idx_assignment_order` - filters assignments by order
- `idx_allocation_order` - filters allocations by order

**Optimization Notes**:
- Uses `select_related` for ForeignKey traversal (single query with JOINs)
- Separate queries for reverse relations are unavoidable but indexed
- Could use `prefetch_related` for reverse FK relations to batch queries

---

#### 3.2.3 Order Number Generation Query

**Query Purpose**: Generate unique sequential order number for new orders.

**Django ORM Code** (`orders/models.py` - Order.generate_order_number()):
```python
@classmethod
def generate_order_number(cls):
    """Generate a unique order number."""
    today = timezone.now()
    prefix = f"ORD-{today.year}-"
    
    # Get the latest order number for this year
    latest = cls.objects.filter(
        order_number__startswith=prefix
    ).order_by('-order_number').first()
    
    if latest:
        last_num = int(latest.order_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:04d}"
```

**Generated SQL (Approximate)**:
```sql
SELECT * FROM orders_order
WHERE order_number LIKE 'ORD-2026-%'
ORDER BY order_number DESC
LIMIT 1;
```

**Tables Involved**: `orders_order`

**Query Type**: SELECT with LIKE prefix match, ORDER BY, LIMIT

**Index Usage**:
- `idx_order_number` - B-tree index supports prefix LIKE queries

**Optimization Notes**:
- `first()` limits result to 1 row
- B-tree index on `order_number` enables efficient prefix search
- Pattern: `ORD-2026-0001`, `ORD-2026-0002`, etc.

---

#### 3.2.4 Status Transition Validation Query

**Query Purpose**: Validate that a status transition is allowed in the state machine.

**Django ORM Code** (`orders/services.py` - OrderService.transition_status()):
```python
# Validate transition exists
valid = OrderStatusTransition.objects.filter(
    from_status=old_status,
    to_status=new_status
).exists()

if not valid:
    raise InvalidTransitionError(...)
```

**Generated SQL (Approximate)**:
```sql
SELECT EXISTS(
    SELECT 1 FROM orders_order_status_transition
    WHERE from_status_id = %s AND to_status_id = %s
    LIMIT 1
);
```

**Tables Involved**: `orders_order_status_transition`

**Query Type**: SELECT EXISTS

**Index Usage**:
- `idx_transition_from` on `from_status` - filters source status
- Composite unique constraint on `(from_status, to_status)`

**Optimization Notes**:
- State machine pattern: only allowed transitions are in the table
- `exists()` is optimal for boolean checks

---

#### 3.2.5 Payment Check Before Delivery

**Query Purpose**: Verify payment exists before allowing order to be marked as delivered.

**Django ORM Code** (`orders/services.py` - OrderService.transition_status()):
```python
# Check payment for delivered status
if to_name == 'delivered':
    from payments.models import Payment
    has_payment = Payment.objects.filter(
        invoice__bill__order=order,
        status='COMPLETED'
    ).exists()
    if not has_payment:
        raise InvalidTransitionError(
            'Cannot mark as delivered: Order has no completed payment.'
        )
```

**Generated SQL (Approximate)**:
```sql
SELECT EXISTS(
    SELECT 1 FROM payments_payment p
    INNER JOIN billing_invoice i ON p.invoice_id = i.id
    INNER JOIN billing_order_bill b ON i.bill_id = b.id
    WHERE b.order_id = %s AND p.status = 'COMPLETED'
    LIMIT 1
);
```

**Tables Involved**: `payments_payment`, `billing_invoice`, `billing_order_bill`

**Query Type**: SELECT EXISTS with multi-table JOIN

**Index Usage**:
- `idx_payment_invoice` - FK index
- `idx_payment_status` - filters by payment status

**Optimization Notes**:
- Critical business rule: prevents delivery without payment
- Multi-hop traversal: `Payment → Invoice → Bill → Order`

---

### 3.3 Inventory Module

#### 3.3.1 Low Stock Detection Query

**Query Purpose**: Find all fabrics where stock is at or below reorder threshold.

**Django ORM Code** (`inventory/services.py` - InventoryService.get_low_stock_fabrics()):
```python
def get_low_stock_fabrics():
    """Get all fabrics below reorder threshold."""
    from django.db.models import F
    return Fabric.objects.filter(
        is_deleted=False,
        quantity_in_stock__lte=F('reorder_threshold')
    ).order_by('quantity_in_stock')
```

**Generated SQL (Approximate)**:
```sql
SELECT * FROM inventory_fabric
WHERE is_deleted = FALSE
AND quantity_in_stock <= reorder_threshold
ORDER BY quantity_in_stock ASC;
```

**Tables Involved**: `inventory_fabric`

**Query Type**: SELECT with F expression comparison

**Index Usage**:
- `idx_fabric_quantity` - index on stock quantity
- `idx_fabric_reorder` - index on reorder threshold

**Optimization Notes**:
- `F('reorder_threshold')` enables column-to-column comparison at database level
- Without F(), would need to fetch all rows and filter in Python

---

#### 3.3.2 Stock Value Aggregation Query

**Query Purpose**: Calculate total inventory value across all fabrics.

**Django ORM Code** (`inventory/services.py` - InventoryService.get_stock_value()):
```python
def get_stock_value():
    """Calculate total inventory value."""
    from django.db.models import Sum, F
    result = Fabric.objects.filter(is_deleted=False).aggregate(
        total_value=Sum(F('quantity_in_stock') * F('cost_per_meter'))
    )
    return result['total_value'] or Decimal('0.00')
```

**Generated SQL (Approximate)**:
```sql
SELECT SUM(quantity_in_stock * cost_per_meter) AS total_value
FROM inventory_fabric
WHERE is_deleted = FALSE;
```

**Tables Involved**: `inventory_fabric`

**Query Type**: SELECT with SUM aggregation and arithmetic expression

**Index Usage**:
- No index directly helps aggregation
- Full table scan required for SUM

**Optimization Notes**:
- Aggregation performed at database level, not in Python
- For large tables, consider materialized view or caching
- `F()` expressions enable database-level arithmetic

---

### 3.4 Payments Module

#### 3.4.1 Payment Verification Query

**Query Purpose**: Retrieve Razorpay order for payment verification.

**Django ORM Code** (`payments/services.py` - PaymentService.verify_and_capture_payment()):
```python
# Update Razorpay order
rp_order = RazorpayOrder.objects.get(razorpay_order_id=razorpay_order_id)
```

**Generated SQL (Approximate)**:
```sql
SELECT * FROM payments_razorpay_order
WHERE razorpay_order_id = %s;
```

**Tables Involved**: `payments_razorpay_order`

**Query Type**: SELECT single row by unique key

**Index Usage**:
- `idx_rp_order_id` - unique index on `razorpay_order_id`

**Optimization Notes**:
- Unique constraint ensures O(1) lookup
- Critical for payment security

---

#### 3.4.2 Webhook Idempotency Check

**Query Purpose**: Check if a webhook event has already been processed to prevent duplicate processing.

**Django ORM Code** (`payments/services.py` - PaymentService.process_webhook()):
```python
# Check if already processed
existing = WebhookEvent.objects.filter(event_id=event_id).first()
if existing:
    logger.info(f"Duplicate webhook ignored: {event_id}")
    return False
```

**Generated SQL (Approximate)**:
```sql
SELECT * FROM payments_webhook_event
WHERE event_id = %s
LIMIT 1;
```

**Tables Involved**: `payments_webhook_event`

**Query Type**: SELECT with unique filter, LIMIT 1

**Index Usage**:
- `idx_webhook_event_id` - unique index ensures fast lookup

**Optimization Notes**:
- Idempotency pattern: prevents double-processing of payments
- Critical for financial data integrity

---

### 3.5 Billing Module

#### 3.5.1 Invoice Total Paid Calculation

**Query Purpose**: Calculate total amount paid for an invoice (may have multiple partial payments).

**Django ORM Code** (`billing/models.py` - Invoice.get_total_paid()):
```python
def get_total_paid(self):
    """Get total amount paid for this invoice."""
    return sum(
        p.amount_paid 
        for p in self.payments.filter(status='COMPLETED')
    )
```

**Generated SQL (Approximate)**:
```sql
SELECT amount_paid FROM payments_payment
WHERE invoice_id = %s AND status = 'COMPLETED';
```

**Tables Involved**: `payments_payment`

**Query Type**: SELECT with filter, Python aggregation

**Index Usage**:
- `idx_payment_invoice` - FK index
- `idx_payment_status` - status filter

**Optimization Notes**:
- Uses Python `sum()` on queryset - acceptable for small payment counts
- Could use `aggregate(Sum('amount_paid'))` for database-level SUM

---

### 3.6 Reporting Module

#### 3.6.1 Monthly Revenue Aggregation

**Query Purpose**: Calculate revenue grouped by month for charts.

**Django ORM Code** (`reporting/views.py` - RevenueReportView):
```python
from django.db.models.functions import TruncMonth

monthly_data = Payment.objects.filter(
    status='COMPLETED',
    created_at__date__gte=timezone.now().date() - timedelta(days=365)
).annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    total=Sum('amount_paid'),
    count=Count('id')
).order_by('month')
```

**Generated SQL (Approximate)**:
```sql
SELECT 
    DATE_TRUNC('month', created_at) AS month,
    SUM(amount_paid) AS total,
    COUNT(id) AS count
FROM payments_payment
WHERE status = 'COMPLETED'
AND DATE(created_at) >= %s
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month;
```

**Tables Involved**: `payments_payment`

**Query Type**: SELECT with GROUP BY, multiple aggregations

**Index Usage**:
- `idx_payment_status` - filters completed payments
- `idx_payment_date` - date range filter

**Optimization Notes**:
- `TruncMonth` truncates timestamp to month for grouping
- Database-level aggregation is efficient
- Consider pre-aggregated `reporting_monthly_revenue` table for historical data

---

#### 3.6.2 Orders by Status Aggregation

**Query Purpose**: Count orders grouped by their current status for dashboard.

**Django ORM Code** (`reporting/views.py` - ReportingDashboardView):
```python
context['orders_by_status'] = Order.objects.filter(
    is_deleted=False
).values('current_status__status_name').annotate(
    count=Count('id')
).order_by('current_status__status_name')
```

**Generated SQL (Approximate)**:
```sql
SELECT os.status_name, COUNT(o.id) AS count
FROM orders_order o
INNER JOIN orders_order_status os ON o.current_status_id = os.id
WHERE o.is_deleted = FALSE
GROUP BY os.status_name
ORDER BY os.status_name;
```

**Tables Involved**: `orders_order`, `orders_order_status`

**Query Type**: SELECT with JOIN, GROUP BY, COUNT

**Index Usage**:
- `idx_order_status` - FK index for JOIN
- `idx_order_deleted` - filters deleted orders

**Optimization Notes**:
- Efficient single query for status distribution
- Used in dashboard widgets

---

### 3.7 Audit Module

#### 3.7.1 Entity Activity History Query

**Query Purpose**: Retrieve all audit logs for a specific entity (order, payment, etc.).

**Django ORM Code** (`audit/services.py` - AuditService.get_entity_history()):
```python
def get_entity_history(entity_type, entity_id, limit=50):
    """Get activity history for an entity."""
    return ActivityLog.objects.filter(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by('-performed_at')[:limit]
```

**Generated SQL (Approximate)**:
```sql
SELECT * FROM audit_activity_log
WHERE entity_type = 'order' AND entity_id = %s
ORDER BY performed_at DESC
LIMIT 50;
```

**Tables Involved**: `audit_activity_log`

**Query Type**: SELECT with composite filter, ORDER BY, LIMIT

**Index Usage**:
- `idx_audit_entity` - composite index on `(entity_type, entity_id)`
- `idx_audit_performed_at` - for ORDER BY

**Optimization Notes**:
- Composite index optimizes filtering by both entity type and ID
- Limit prevents unbounded result sets

---

## 4. Complex & Critical Queries (Viva Focus)

### 4.1 Order Status Transition with Role-Based Authorization

**Location**: `orders/services.py` - `OrderService.transition_status()`

**Why This Query Is Complex**:
This involves multiple queries and business logic:
1. Validate transition exists in state machine
2. Check user roles
3. Verify payment for delivery status
4. Update order, create history, log audit

**Full ORM Code**:
```python
@staticmethod
@transaction.atomic
def transition_status(order, new_status, changed_by, reason=None, request=None):
    old_status = order.current_status
    
    # Query 1: Validate transition exists
    valid = OrderStatusTransition.objects.filter(
        from_status=old_status,
        to_status=new_status
    ).exists()
    
    if not valid:
        raise InvalidTransitionError(...)
    
    # Query 2: Get user roles
    user_roles = list(changed_by.get_roles().values_list('name', flat=True))
    
    # Role-based validation logic...
    
    # Query 3: Check payment for delivery
    if to_name == 'delivered':
        has_payment = Payment.objects.filter(
            invoice__bill__order=order,
            status='COMPLETED'
        ).exists()
        
    # Query 4: Update order
    order.current_status = new_status
    order.save(update_fields=['current_status', 'updated_at'])
    
    # Query 5: Create history entry
    OrderStatusHistory.objects.create(...)
    
    # Query 6: Create audit log
    AuditService.log_order_status_change(...)
```

**Time Complexity at Scale**: O(1) for all queries due to indexed lookups

**Optimization Potential**:
- All queries use indexed columns
- Wrapped in `@transaction.atomic` for consistency
- Could combine role check with validation in single query

---

### 4.2 Analytics Dashboard Aggregation

**Location**: `reporting/views.py` - `ReportingDashboardView`

**Why This Query Is Complex**:
Multiple aggregation queries for dashboard widgets.

**Full ORM Code**:
```python
# Total revenue
context['total_revenue'] = Payment.objects.filter(
    status='COMPLETED'
).aggregate(total=Sum('amount_paid'))['total'] or 0

# Monthly revenue
context['monthly_revenue'] = Payment.objects.filter(
    status='COMPLETED',
    created_at__date__gte=thirty_days_ago
).aggregate(total=Sum('amount_paid'))['total'] or 0

# Order counts
context['total_orders'] = Order.objects.filter(is_deleted=False).count()
context['pending_orders'] = Order.objects.filter(
    is_deleted=False,
    current_status__status_name__in=[
        'booked', 'fabric_allocated', 'stitching', 
        'trial_scheduled', 'alteration', 'ready'
    ]
).count()

# Customer counts
context['total_customers'] = CustomerProfile.objects.filter(
    is_deleted=False
).count()

# Low stock count with F expression
context['low_stock_count'] = Fabric.objects.filter(
    is_deleted=False,
    quantity_in_stock__lte=F('reorder_threshold')
).count()

# Inventory value calculation
context['inventory_value'] = Fabric.objects.filter(
    is_deleted=False
).aggregate(
    total=Sum(F('quantity_in_stock') * F('cost_per_meter'))
)['total'] or 0

# Orders by status distribution
context['orders_by_status'] = Order.objects.filter(
    is_deleted=False
).values('current_status__status_name').annotate(
    count=Count('id')
).order_by('current_status__status_name')
```

**Time Complexity at Scale**:
- COUNT queries: O(N) without covering index, O(log N) with
- SUM aggregations: O(N) full table scan
- GROUP BY: O(N log N) for sorting

**Optimization Potential**:
1. Cache dashboard metrics with 5-minute TTL
2. Use pre-aggregated tables (`reporting_monthly_revenue`)
3. Add covering indexes for COUNT queries
4. Consider read replicas for analytics queries

---

### 4.3 Bill Generation with Multi-Table Traversal

**Location**: `billing/services.py` - `BillingService.generate_bill()`

**Why This Query Is Complex**:
Calculates derived pricing from multiple related entities.

**Full ORM Code**:
```python
@transaction.atomic
def generate_bill(order, advance_amount=Decimal('0.00')):
    # Query 1: Get system configuration (singleton)
    config = SystemConfiguration.get_config()
    
    # Query 2: Base price from garment type (already loaded via order.garment_type)
    base_price = order.garment_type.base_price
    
    # Query 3: Work type charges - iterates order work types
    work_type_charges = order.get_total_work_type_charges()
    
    # Query 4: Alteration charges from trial
    alteration_charges = Decimal('0.00')
    if hasattr(order, 'trial') and order.trial:
        for alt in order.trial.alterations.filter(is_included_in_original=False):
            alteration_charges += alt.estimated_cost
    
    # Query 5: Update or create bill (upsert pattern)
    bill, created = OrderBill.objects.update_or_create(
        order=order,
        defaults={...}
    )
```

**Time Complexity**: O(A) where A = number of alterations (typically < 5)

**Optimization Potential**:
- `update_or_create` is atomic (SELECT FOR UPDATE + INSERT/UPDATE)
- Alteration loop could use `aggregate(Sum('estimated_cost'))`

---

## 5. Raw SQL Queries

### **No raw SQL queries are used in this project.**

**Justification**:

1. **Security**: Django ORM provides automatic SQL injection prevention through parameterized queries. Every `filter()`, `get()`, and `create()` call is safely parameterized.

2. **Maintainability**: ORM queries automatically adapt when model fields change. Raw SQL would require manual updates.

3. **Portability**: The project uses MySQL in production but can use SQLite for testing. ORM abstracts database-specific syntax.

4. **Sufficiency**: All required queries (including complex aggregations, F expressions, and subqueries) are expressible via Django ORM.

**Evidence from codebase search**: No instances of:
- `Model.objects.raw()`
- `connection.cursor()`
- `RawSQL()`

---

## 6. Transactional Queries

### 6.1 Order Creation Transaction

**Location**: `orders/services.py` - `OrderService.create_order()`

**Transaction Scope**:
```python
@staticmethod
@transaction.atomic
def create_order(...):
    # 1. INSERT: Create order
    order = Order.objects.create(...)
    
    # 2. INSERT: Create work types (loop)
    for wt in work_types:
        OrderWorkType.objects.create(...)
    
    # 3. INSERT: Create audit log
    AuditService.log_activity(...)
    
    # 4. INSERT: Generate bill
    bill = BillingService.generate_bill(order)
    
    # 5. INSERT: Generate invoice
    BillingService.generate_invoice(bill, ...)
    
    # 6. INSERT: Create notification
    NotificationService.notify_order_created(order)
```

**Why Atomic**:
If any step fails (e.g., bill generation), all changes are rolled back. Prevents orphaned orders without bills.

**Rollback Scenarios**:
- Database constraint violation
- External service failure (caught and handled)
- Validation error

---

### 6.2 Payment Capture Transaction

**Location**: `payments/services.py` - `PaymentService.verify_and_capture_payment()`

**Transaction Scope**:
```python
@transaction.atomic
def verify_and_capture_payment(...):
    # 1. UPDATE: Mark Razorpay order as PAID
    rp_order = RazorpayOrder.objects.get(razorpay_order_id=razorpay_order_id)
    rp_order.order_status = 'PAID'
    rp_order.save()
    
    # 2. INSERT: Create payment record
    payment = Payment.objects.create(...)
    
    # 3. UPDATE: Update invoice status
    cls._update_invoice_status(rp_order.invoice)
    
    # 4. INSERT: Create audit log
    AuditService.log_payment(...)
```

**Why Atomic**:
Payment processing must be all-or-nothing. Partial completion could result in:
- Payment recorded but invoice not updated
- Duplicate payment records

---

### 6.3 Inventory Stock Out Transaction

**Location**: `inventory/services.py` - `InventoryService.record_stock_out()`

**Transaction Scope**:
```python
@transaction.atomic
def record_stock_out(fabric, quantity, ...):
    # Validation
    if fabric.quantity_in_stock < quantity:
        raise ValidationError(...)
    
    # 1. UPDATE: Deduct from fabric stock
    fabric.quantity_in_stock = new_qty
    fabric.save(update_fields=['quantity_in_stock', 'updated_at'])
    
    # 2. INSERT: Create transaction record
    StockTransaction.objects.create(...)
    
    # 3. INSERT/UPDATE: Check and create low stock alert
    InventoryService._check_low_stock_alert(fabric)
```

**Why Atomic**:
Stock deduction must be atomic with transaction logging. Prevents:
- Stock deducted but no transaction record
- Race conditions in stock levels

---

## 7. Read vs Write Patterns

### 7.1 High-Frequency Read Operations

| Operation | Location | Frequency | Tables |
|-----------|----------|-----------|--------|
| Order list with filters | `orders/views.py` | Very High | orders, customers, users, statuses |
| Order detail view | `orders/views.py` | Very High | 10+ tables |
| Dashboard metrics | `reporting/views.py` | High | orders, payments, inventory |
| User role check | `users/models.py` | Very High | user_roles, roles |
| Low stock alerts | `inventory/views.py` | Medium | fabrics, alerts |

### 7.2 Write-Heavy Operations

| Operation | Location | Frequency | Tables |
|-----------|----------|-----------|--------|
| Order status transitions | `orders/services.py` | High | orders, status_history, audit_log |
| Payment capture | `payments/services.py` | Medium | payments, razorpay_orders, invoices |
| Stock transactions | `inventory/services.py` | Medium | fabrics, stock_transactions, alerts |
| Audit logging | `audit/services.py` | Very High | activity_log |

### 7.3 Performance-Critical Queries

1. **Order List**: Most frequently accessed page
   - Optimization: `select_related()`, pagination, indexed filters
   
2. **Role/Permission Checks**: Called on every protected route
   - Optimization: `exists()` instead of `count()`, indexed lookups
   
3. **Dashboard Aggregations**: Computed on every admin dashboard load
   - Optimization: Consider caching or pre-aggregation

---

## 8. Query Performance & Scaling Considerations

### 8.1 Index Strategy

All models define explicit indexes in `Meta.indexes`:

```python
class Order(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['order_number'], name='idx_order_number'),
            models.Index(fields=['customer'], name='idx_order_customer'),
            models.Index(fields=['current_status'], name='idx_order_status'),
            models.Index(fields=['created_at'], name='idx_order_created'),
            models.Index(fields=['expected_delivery_date'], name='idx_order_delivery'),
            models.Index(fields=['is_deleted'], name='idx_order_deleted'),
        ]
```

**Index Types Used**:
- **Single-column B-tree**: Most common, for equality and range queries
- **Unique constraints**: `order_number`, `email`, `username` - act as unique indexes
- **Foreign key indexes**: Automatically created by Django for FK fields
- **Composite indexes**: `(entity_type, entity_id)` in audit_log

### 8.2 Where Caching Could Be Introduced

| Query | Cache Strategy | TTL |
|-------|---------------|-----|
| Dashboard metrics | Redis/Memcached | 5 minutes |
| System configuration | Application memory | Until update event |
| Active order statuses | Application memory | 24 hours |
| Role permissions | Request-level cache | Per request |

### 8.3 Read Replicas / Sharding (Conceptual)

For scaling beyond single database:

1. **Read Replicas**:
   - Route reporting/analytics queries to replica
   - Use Django's database routers

2. **Sharding by Customer**:
   - Partition `orders`, `measurements`, `payments` by customer_id
   - Keep `users`, `config`, `catalog` in single database

3. **Time-based Partitioning**:
   - Partition `audit_activity_log` by month
   - Archive old partitions

### 8.4 Expected Bottlenecks at Scale

| Bottleneck | Threshold | Mitigation |
|------------|-----------|------------|
| Dashboard aggregations | 100K orders | Pre-aggregate into reporting tables |
| Order search (LIKE queries) | 50K orders | Full-text search (Elasticsearch) |
| Audit log writes | High write volume | Async queue (Celery) |
| Status history growth | 10+ per order | Archive old history |

---

## 9. Common Viva Questions & Answers

### Q1: "How does Django ORM generate SQL?"

**Answer**: Django ORM uses a QuerySet abstraction that builds SQL incrementally. When you chain methods like `.filter().select_related().order_by()`, Django constructs an internal query representation. SQL is only generated when the QuerySet is evaluated (iterated, sliced, or converted to list).

**Example from this project**:
```python
Order.objects.filter(is_deleted=False).select_related('customer__user')
```
Generates:
```sql
SELECT orders_order.*, customers_customer_profile.*, users_user.*
FROM orders_order
INNER JOIN customers_customer_profile ON ...
INNER JOIN users_user ON ...
WHERE orders_order.is_deleted = FALSE;
```

### Q2: "What is the N+1 query problem and where do you prevent it?"

**Answer**: N+1 occurs when fetching N related objects triggers N additional queries.

**Without optimization** (in `OrderListView`):
```python
orders = Order.objects.filter(is_deleted=False)
for order in orders:  # 1 query
    print(order.customer.user.first_name)  # N queries!
```

**Prevention in this project** (actual code):
```python
Order.objects.filter(is_deleted=False).select_related(
    'customer__user', 'garment_type', 'current_status'
)  # Single query with JOINs
```

### Q3: "When should you use select_related vs prefetch_related?"

**Answer**: 

| Aspect | select_related | prefetch_related |
|--------|----------------|------------------|
| **Use for** | ForeignKey, OneToOne | ManyToMany, reverse ForeignKey |
| **Mechanism** | SQL JOIN | Separate queries + Python merge |
| **Memory** | One large result set | Two smaller result sets |

**Example from this project**:
```python
# select_related: Order -> Customer (ForeignKey)
Order.objects.select_related('customer__user')

# prefetch_related would be used for:
# Customer -> Orders (reverse FK, one customer has many orders)
Customer.objects.prefetch_related('orders')
```

### Q4: "How do you ensure transactional integrity?"

**Answer**: Critical operations use `@transaction.atomic` decorator. This wraps multiple database operations in a single transaction with automatic rollback on exception.

**Example from `orders/services.py`**:
```python
@transaction.atomic
def create_order(...):
    order = Order.objects.create(...)       # INSERT
    OrderWorkType.objects.create(...)       # INSERT
    BillingService.generate_bill(order)     # INSERT
    # If any fails, all are rolled back
```

**Reference**: The payment capture in `payments/services.py` similarly uses atomic transactions to ensure Razorpay order update and Payment creation are atomic.

### Q5: "How do F expressions help performance?"

**Answer**: F expressions reference database column values without fetching them to Python. Operations happen at database level.

**Example from `inventory/services.py`**:
```python
# Without F: Fetch all rows, filter in Python
fabrics = Fabric.objects.all()
low_stock = [f for f in fabrics if f.quantity_in_stock <= f.reorder_threshold]

# With F: Filter at database level
Fabric.objects.filter(quantity_in_stock__lte=F('reorder_threshold'))
```

### Q6: "What indexes are most important in your schema?"

**Answer**: 

1. **`idx_order_number`**: Unique order lookups
2. **`idx_order_status`**: Status-based filtering (most common filter)
3. **`idx_audit_entity`**: Composite index for audit log lookups
4. **`idx_payment_invoice`**: FK lookups for payment verification

These directly support the most frequent query patterns identified in Section 7.

### Q7: "How would you optimize the dashboard for 1 million orders?"

**Answer**:

1. **Pre-aggregate metrics** into `reporting_monthly_revenue`, `reporting_pending_orders_snapshot` tables
2. **Cache dashboard results** in Redis with 5-minute TTL
3. **Use read replicas** for analytics queries
4. **Partition orders table** by year
5. **Replace LIKE searches** with full-text search index

---

## Appendix: Table Index Summary

| Table | Indexes | Purpose |
|-------|---------|---------|
| `users_user` | `idx_username`, `idx_email`, `idx_is_deleted`, `idx_created_at` | Login, search, soft delete |
| `users_role` | `idx_role_name`, `idx_role_is_deleted` | Role lookups |
| `orders_order` | `idx_order_number`, `idx_order_customer`, `idx_order_status`, `idx_order_created`, `idx_order_delivery`, `idx_order_deleted` | Full order management |
| `payments_payment` | `idx_payment_invoice`, `idx_payment_date`, `idx_payment_status`, `idx_payment_rp_id` | Payment processing |
| `inventory_fabric` | `idx_fabric_quantity`, `idx_fabric_reorder` | Stock management |
| `audit_activity_log` | `idx_audit_entity`, `idx_audit_performed_at`, `idx_audit_performed_by` | Audit trail queries |

---

*This document was generated based on analysis of the actual Tailoring Management System codebase. All queries reference real implementations.*
