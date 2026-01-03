# Project Structure

This document provides a detailed explanation of the Tailoring Management System's codebase organization.

## Overview

The project follows Django's app-based architecture with **16 domain-specific apps** managing 49 database tables. Each app encapsulates a specific business domain with its own models, views, forms, and services.

## Directory Structure

```
tailoring_system/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (not in git)
├── .env.example                 # Environment template
│
├── tailoring_system/            # Django project configuration
│   ├── __init__.py
│   ├── settings.py              # Main settings file
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI application
│   └── asgi.py                  # ASGI application
│
├── core/                        # Security utilities
│   ├── __init__.py
│   ├── validators.py            # File upload validators
│   ├── sanitizers.py            # Input sanitization
│   └── tests.py                 # Security tests
│
├── users/                       # Authentication & Authorization
│   ├── models.py                # User, Role, Permission models
│   ├── views.py                 # Login, logout, dashboard views
│   ├── forms.py                 # Authentication forms
│   ├── services.py              # User management logic
│   ├── permissions.py           # RBAC decorators and mixins
│   └── management/commands/     # Management commands
│       └── seed_data.py         # Sample data seeding
│
├── customers/                   # Customer Management
│   ├── models.py                # CustomerProfile model
│   ├── views.py                 # Customer CRUD views
│   └── forms.py                 # Customer forms
│
├── catalog/                     # Product Catalog
│   ├── models.py                # GarmentType, WorkType, ProductImage
│   ├── views.py                 # Catalog management views
│   └── templatetags/            # Custom template tags
│       └── catalog_tags.py
│
├── inventory/                   # Stock Management
│   ├── models.py                # Fabric, StockTransaction, LowStockAlert
│   ├── views.py                 # Inventory views
│   ├── services.py              # Stock in/out logic
│   └── tests.py                 # Inventory tests
│
├── measurements/                # Measurement System
│   ├── models.py                # MeasurementTemplate, MeasurementSet, Value
│   ├── views.py                 # Measurement entry views
│   └── forms.py                 # Dynamic measurement forms
│
├── designs/                     # Design Management
│   ├── models.py                # Design, CustomizationNote
│   ├── views.py                 # Design upload/approval views
│   └── forms.py                 # Design forms
│
├── orders/                      # Order Lifecycle
│   ├── models.py                # Order, OrderStatus, OrderStatusHistory
│   ├── views.py                 # Order management views
│   ├── services.py              # Order state machine
│   ├── forms.py                 # Order forms
│   └── tests.py                 # Order tests
│
├── trials/                      # Trial Fittings
│   ├── models.py                # Trial, Alteration, RevisedDeliveryDate
│   ├── views.py                 # Trial scheduling views
│   └── forms.py                 # Trial forms
│
├── billing/                     # Billing & Invoicing
│   ├── models.py                # OrderBill, Invoice
│   ├── views.py                 # Bill/Invoice views
│   └── services.py              # Bill generation, PDF export
│
├── payments/                    # Payment Processing
│   ├── models.py                # Payment, Refund, RazorpayOrder
│   ├── views.py                 # Payment views, webhooks
│   ├── services.py              # Payment logic, Razorpay integration
│   └── tests.py                 # Payment tests
│
├── delivery/                    # Delivery Management
│   ├── models.py                # DeliveryZone, Delivery
│   └── views.py                 # Delivery scheduling views
│
├── notifications/               # Notification System
│   ├── models.py                # NotificationType, Notification
│   ├── views.py                 # Notification views
│   └── email_service.py         # Email sending logic
│
├── feedback/                    # Customer Feedback
│   ├── models.py                # Feedback model
│   └── views.py                 # Feedback submission/moderation
│
├── reporting/                   # Business Analytics
│   ├── models.py                # MonthlyRevenue, StaffWorkload, etc.
│   └── views.py                 # Report generation views
│
├── audit/                       # Audit Logging
│   ├── models.py                # ActivityLog, PaymentAuditLog
│   ├── middleware.py            # Audit middleware
│   └── services.py              # Audit logging service
│
├── config/                      # System Configuration
│   ├── models.py                # SystemConfiguration, PricingRule
│   └── views.py                 # Configuration views
│
├── templates/                   # HTML Templates
│   ├── base.html                # Base template with navigation
│   ├── users/                   # Auth templates
│   ├── dashboard/               # Dashboard templates
│   ├── orders/                  # Order templates
│   ├── customers/               # Customer templates
│   ├── inventory/               # Inventory templates
│   ├── billing/                 # Billing templates
│   ├── payments/                # Payment templates
│   ├── designs/                 # Design templates
│   ├── measurements/            # Measurement templates
│   ├── trials/                  # Trial templates
│   ├── delivery/                # Delivery templates
│   ├── feedback/                # Feedback templates
│   ├── reporting/               # Report templates
│   ├── audit/                   # Audit templates
│   ├── configuration/           # Config templates
│   └── emails/                  # Email templates
│
├── static/                      # Static Assets
│   ├── css/                     # Stylesheets
│   └── js/                      # JavaScript files
│
├── media/                       # User Uploads
│   ├── designs/                 # Design files
│   └── catalog/                 # Product images
│
├── logs/                        # Application Logs
│   └── tailoring.log
│
└── docs/                        # Documentation
    ├── PROJECT_STRUCTURE.md     # This file
    ├── DATABASE_DESIGN.md       # Database documentation
    ├── USE_CASES.md             # Use case diagrams
    ├── SEQUENCE_DIAGRAMS.md     # Sequence diagrams
    └── DEPLOYMENT.md            # Deployment guide
```

## App Responsibilities

### Core Business Apps

| App | Tables | Responsibility |
|-----|--------|----------------|
| `users` | 5 | User authentication, roles, permissions |
| `customers` | 1 | Customer profiles and contact info |
| `catalog` | 4 | Garment types, work types, product images |
| `inventory` | 3 | Fabric stock, transactions, alerts |
| `measurements` | 3 | Measurement templates and customer measurements |
| `designs` | 2 | Design uploads and customization notes |
| `orders` | 7 | Order lifecycle, assignments, material allocation |
| `trials` | 3 | Trial fittings, alterations, revised dates |

### Financial Apps

| App | Tables | Responsibility |
|-----|--------|----------------|
| `billing` | 2 | Bill generation, invoice management |
| `payments` | 6 | Payment processing, refunds, Razorpay |

### Operations Apps

| App | Tables | Responsibility |
|-----|--------|----------------|
| `delivery` | 2 | Delivery zones and scheduling |
| `notifications` | 3 | Email notifications to customers |
| `feedback` | 1 | Customer feedback and ratings |

### System Apps

| App | Tables | Responsibility |
|-----|--------|----------------|
| `reporting` | 4 | Business analytics and reports |
| `audit` | 2 | Activity logging for compliance |
| `config` | 2 | System configuration and pricing rules |
| `core` | 0 | Security utilities (validators, sanitizers) |

## Key Design Patterns

### 1. Service Layer Pattern

All business logic is encapsulated in `services.py` files:
- `OrderService` - Order creation and status transitions
- `PaymentService` - Payment processing
- `InventoryService` - Stock management
- `BillingService` - Bill and invoice generation
- `AuditService` - Activity logging

### 2. State Machine Pattern

Orders follow a state machine with explicit transitions:
- Defined in `OrderStatus` and `OrderStatusTransition` models
- Validated in `OrderService.transition_status()`
- History tracked in `OrderStatusHistory`

### 3. Soft Delete Pattern

All critical records use `is_deleted=False` instead of hard deletes for:
- Data integrity
- Audit compliance
- Recovery capability

### 4. Immutable Financial Records

Payments, invoices, and bills are never modified after creation:
- New records created for corrections
- Refunds tracked separately
- Complete audit trail maintained

## Middleware Stack

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',  # Custom audit logging
]
```

## Template Hierarchy

```
templates/
├── base.html              # Master template (Bootstrap 5)
│   ├── dashboard/*.html   # Role-specific dashboards
│   ├── orders/*.html      # Order management
│   └── ...                # Other module templates
```

The base template includes:
- Responsive navigation
- Role-based menu items
- Flash messages
- Footer with system info
