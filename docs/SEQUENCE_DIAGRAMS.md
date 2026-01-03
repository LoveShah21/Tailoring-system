# Sequence Diagrams

This document contains sequence diagrams for all major workflows in the Tailoring Management System.

## Order Lifecycle

### 1. Order Creation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant OrderView
    participant OrderService
    participant OrderModel
    participant AuditService
    participant DB
    
    Staff->>OrderView: Submit order form
    OrderView->>OrderView: Validate form data
    OrderView->>OrderService: create_order(customer, garment_type, ...)
    
    activate OrderService
    OrderService->>DB: BEGIN TRANSACTION
    OrderService->>OrderModel: Generate order_number
    OrderModel-->>OrderService: ORD-2026-001
    
    OrderService->>DB: INSERT orders_order
    DB-->>OrderService: order_id
    
    loop For each work_type
        OrderService->>DB: INSERT orders_order_work_type
    end
    
    OrderService->>AuditService: log_activity(CREATE, order)
    AuditService->>DB: INSERT audit_activity_log
    
    OrderService->>DB: COMMIT
    OrderService-->>OrderView: Order object
    deactivate OrderService
    
    OrderView->>Staff: Redirect to order detail
```

### 2. Order Status Transition Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant OrderView
    participant OrderService
    participant TransitionModel
    participant HistoryModel
    participant AuditService
    participant NotificationService
    
    Staff->>OrderView: Click "Update Status"
    OrderView->>OrderView: Show available transitions
    Staff->>OrderView: Select new status
    
    OrderView->>OrderService: transition_status(order, new_status, user)
    
    activate OrderService
    OrderService->>TransitionModel: Validate transition exists
    TransitionModel-->>OrderService: Valid/Invalid
    
    alt Invalid Transition
        OrderService-->>OrderView: InvalidTransitionError
        OrderView->>Staff: Show error message
    else Valid Transition
        OrderService->>OrderService: Update order.current_status
        OrderService->>HistoryModel: Create status history
        OrderService->>AuditService: log_order_status_change()
        
        OrderService->>NotificationService: Send notification
        activate NotificationService
        NotificationService->>NotificationService: Create notification record
        NotificationService->>NotificationService: Send email
        deactivate NotificationService
        
        OrderService-->>OrderView: Updated order
        OrderView->>Staff: Show success message
    end
    deactivate OrderService
```

### 3. Complete Order Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Customer
    participant Staff
    participant Tailor
    participant System
    participant DeliveryPerson
    
    Customer->>Staff: Request tailoring
    Staff->>System: Create order (Booked)
    System->>Customer: Email: Order created
    
    Staff->>System: Allocate fabric (Fabric Allocated)
    System->>System: Deduct inventory
    
    Staff->>System: Assign to tailor
    System->>Tailor: Notification: New assignment
    Tailor->>System: Start work (Stitching)
    
    Tailor->>System: Complete stitching
    Staff->>System: Schedule trial (Trial Scheduled)
    System->>Customer: Email: Trial scheduled
    
    Customer->>Staff: Attend trial
    
    alt Alterations needed
        Staff->>System: Record alterations
        Tailor->>System: Complete alterations
    end
    
    Tailor->>System: Mark ready (Ready)
    System->>Customer: Email: Order ready
    
    Staff->>System: Generate bill & invoice
    Customer->>System: Make payment
    System->>Customer: Email: Payment confirmed
    
    Staff->>System: Schedule delivery
    DeliveryPerson->>System: Confirm delivery (Delivered)
    System->>Customer: Email: Delivered
    
    Customer->>System: Submit feedback
```

---

## Payment Workflows

### 4. Cash Payment Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant PaymentView
    participant PaymentService
    participant Invoice
    participant Payment
    participant AuditService
    
    Staff->>PaymentView: Record cash payment
    Staff->>PaymentView: Enter amount, receipt ref
    
    PaymentView->>PaymentService: record_cash_payment(invoice, amount, user)
    
    activate PaymentService
    PaymentService->>Payment: Create payment record
    Payment-->>PaymentService: payment_id
    
    PaymentService->>Invoice: Calculate total payments
    
    alt Fully Paid
        PaymentService->>Invoice: Update status = PAID
    else Partially Paid
        PaymentService->>Invoice: Update status = PARTIALLY_PAID
    end
    
    PaymentService->>AuditService: Log payment activity
    PaymentService-->>PaymentView: Payment object
    deactivate PaymentService
    
    PaymentView->>Staff: Success: Payment recorded
```

### 5. Razorpay Online Payment Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Frontend
    participant PaymentView
    participant PaymentService
    participant Razorpay
    participant Invoice
    
    Customer->>Frontend: Click "Pay Online"
    Frontend->>PaymentView: Create payment order
    
    PaymentView->>PaymentService: create_razorpay_order(invoice, amount)
    activate PaymentService
    PaymentService->>Razorpay: orders.create()
    Razorpay-->>PaymentService: razorpay_order_id
    PaymentService->>PaymentService: Store RazorpayOrder
    PaymentService-->>PaymentView: order details
    deactivate PaymentService
    
    PaymentView-->>Frontend: order_id, key, amount
    Frontend->>Razorpay: Open checkout modal
    
    Customer->>Razorpay: Enter card details
    Razorpay->>Razorpay: Process payment
    Razorpay-->>Frontend: payment_id, signature
    
    Frontend->>PaymentView: Verify payment
    PaymentView->>PaymentService: verify_and_capture_payment()
    
    activate PaymentService
    PaymentService->>Razorpay: Verify signature
    
    alt Signature Valid
        PaymentService->>PaymentService: Create Payment record
        PaymentService->>Invoice: Update status = PAID
        PaymentService->>PaymentService: Send confirmation email
        PaymentService-->>PaymentView: Success
        PaymentView-->>Frontend: Success response
        Frontend->>Customer: Payment successful!
    else Signature Invalid
        PaymentService-->>PaymentView: Error
        PaymentView-->>Frontend: Error response
        Frontend->>Customer: Payment failed
    end
    deactivate PaymentService
```

### 6. Razorpay Webhook Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Razorpay
    participant WebhookView
    participant PaymentService
    participant WebhookEvent
    participant Invoice
    
    Razorpay->>WebhookView: POST /payments/webhook/
    Note over Razorpay,WebhookView: payment.captured event
    
    WebhookView->>PaymentService: process_webhook(payload, signature)
    
    activate PaymentService
    PaymentService->>PaymentService: Verify webhook signature
    PaymentService->>PaymentService: Extract event_id
    
    PaymentService->>WebhookEvent: Check if already processed
    
    alt Already Processed (Idempotent)
        WebhookEvent-->>PaymentService: Event exists
        PaymentService-->>WebhookView: Skip (already handled)
    else New Event
        PaymentService->>WebhookEvent: Create event record
        
        alt Event: payment.captured
            PaymentService->>PaymentService: Find RazorpayOrder
            PaymentService->>PaymentService: Create Payment record
            PaymentService->>Invoice: Update status
        else Event: refund.processed
            PaymentService->>PaymentService: Update Refund status
        end
        
        PaymentService-->>WebhookView: Processed
    end
    deactivate PaymentService
    
    WebhookView-->>Razorpay: 200 OK
```

---

## Inventory Workflows

### 7. Stock In Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant InventoryView
    participant InventoryService
    participant Fabric
    participant StockTransaction
    
    Staff->>InventoryView: Add stock form
    Staff->>InventoryView: Enter quantity, notes
    
    InventoryView->>InventoryService: record_stock_in(fabric, qty, user)
    
    activate InventoryService
    InventoryService->>Fabric: Get current quantity
    Fabric-->>InventoryService: previous_qty
    
    InventoryService->>InventoryService: new_qty = previous_qty + qty
    
    InventoryService->>Fabric: Update quantity_in_stock
    InventoryService->>StockTransaction: Create IN transaction
    
    InventoryService-->>InventoryView: Transaction record
    deactivate InventoryService
    
    InventoryView->>Staff: Stock added successfully
```

### 8. Stock Out (Material Allocation) Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant OrderView
    participant OrderService
    participant InventoryService
    participant Fabric
    participant LowStockAlert
    
    Staff->>OrderView: Allocate materials to order
    Staff->>OrderView: Select fabric, quantity
    
    OrderView->>OrderService: allocate_material(order, fabric, qty)
    
    activate OrderService
    OrderService->>Fabric: Check stock availability
    
    alt Insufficient Stock
        Fabric-->>OrderService: Insufficient
        OrderService-->>OrderView: ValidationError
        OrderView->>Staff: Error: Not enough stock
    else Sufficient Stock
        OrderService->>InventoryService: record_stock_out(fabric, qty, order)
        
        activate InventoryService
        InventoryService->>Fabric: Deduct quantity
        InventoryService->>InventoryService: Create OUT transaction
        
        InventoryService->>Fabric: Check reorder threshold
        alt Below Threshold
            InventoryService->>LowStockAlert: Create alert
        end
        
        InventoryService-->>OrderService: Transaction
        deactivate InventoryService
        
        OrderService->>OrderService: Create allocation record
        OrderService-->>OrderView: Allocation
        OrderView->>Staff: Material allocated
    end
    deactivate OrderService
```

---

## Authentication Workflows

### 9. User Login Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant LoginView
    participant AuthBackend
    participant Session
    participant AuditService
    
    User->>LoginView: Enter username, password
    LoginView->>AuthBackend: authenticate(username, password)
    
    AuthBackend->>AuthBackend: Verify credentials
    
    alt Invalid Credentials
        AuthBackend-->>LoginView: None
        LoginView->>User: Invalid username or password
    else Valid Credentials
        AuthBackend-->>LoginView: User object
        LoginView->>Session: Create session
        LoginView->>AuthBackend: Update last_login
        LoginView->>AuditService: Log login activity
        
        LoginView->>LoginView: Determine dashboard by role
        
        alt Admin Role
            LoginView->>User: Redirect to Admin Dashboard
        else Staff Role
            LoginView->>User: Redirect to Staff Dashboard
        else Customer Role
            LoginView->>User: Redirect to Customer Dashboard
        end
    end
```

### 10. Password Reset Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant ResetView
    participant EmailService
    participant TokenGenerator
    
    User->>ResetView: Enter email
    ResetView->>ResetView: Find user by email
    
    alt User Not Found
        ResetView->>User: If email exists, you'll receive a link
        Note over ResetView: Security: Don't reveal if user exists
    else User Found
        ResetView->>TokenGenerator: Generate reset token
        TokenGenerator-->>ResetView: token
        
        ResetView->>EmailService: Send reset email
        activate EmailService
        EmailService->>EmailService: Build email with token link
        EmailService->>EmailService: Send via SMTP
        deactivate EmailService
        
        ResetView->>User: Check your email
    end
    
    User->>ResetView: Click link in email
    ResetView->>TokenGenerator: Validate token
    
    alt Token Valid
        User->>ResetView: Enter new password
        ResetView->>ResetView: Update password
        ResetView->>User: Password reset successful
    else Token Invalid/Expired
        ResetView->>User: Invalid or expired link
    end
```

---

## Billing Workflows

### 11. Bill Generation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant BillingView
    participant BillingService
    participant Config
    participant OrderBill
    
    Staff->>BillingView: Generate bill for order
    
    BillingView->>BillingService: generate_bill(order, advance)
    
    activate BillingService
    BillingService->>Config: Get tax rate, settings
    Config-->>BillingService: SystemConfiguration
    
    BillingService->>BillingService: base_price = garment_type.base_price
    BillingService->>BillingService: work_type_charges = SUM(work_types)
    BillingService->>BillingService: alteration_charges = SUM(alterations)
    
    alt Is Urgent
        BillingService->>BillingService: urgency_surcharge = subtotal * 20%
    end
    
    BillingService->>OrderBill: Create/Update bill
    Note over OrderBill: MySQL computed columns:<br/>subtotal, tax_amount,<br/>total_amount, balance_amount
    
    BillingService-->>BillingView: OrderBill
    deactivate BillingService
    
    BillingView->>Staff: Bill generated
```

### 12. Invoice PDF Generation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant InvoiceView
    participant BillingService
    participant ReportLab
    participant FileSystem
    
    Staff->>InvoiceView: Download invoice PDF
    
    InvoiceView->>BillingService: generate_invoice_pdf(invoice)
    
    activate BillingService
    BillingService->>BillingService: Get invoice details
    BillingService->>BillingService: Get customer details
    BillingService->>BillingService: Get bill breakdown
    
    BillingService->>ReportLab: Create PDF document
    BillingService->>ReportLab: Add header
    BillingService->>ReportLab: Add invoice details table
    BillingService->>ReportLab: Add line items table
    BillingService->>ReportLab: Add totals
    BillingService->>ReportLab: Build PDF
    
    ReportLab-->>BillingService: BytesIO buffer
    BillingService-->>InvoiceView: PDF buffer
    deactivate BillingService
    
    InvoiceView->>Staff: Download PDF
```

---

## Notification Workflows

### 13. Email Notification Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Trigger
    participant NotificationService
    participant EmailService
    participant SMTP
    participant Notification
    
    Trigger->>NotificationService: Send order ready email
    
    activate NotificationService
    NotificationService->>NotificationService: Get notification type
    NotificationService->>NotificationService: Get email template
    NotificationService->>NotificationService: Render template with context
    
    NotificationService->>Notification: Create notification record
    Note over Notification: status = QUEUED
    
    NotificationService->>EmailService: send_email(recipient, subject, body)
    
    activate EmailService
    EmailService->>SMTP: Connect to Gmail SMTP
    EmailService->>SMTP: Send email
    
    alt Email Sent
        SMTP-->>EmailService: Success
        EmailService-->>NotificationService: True
        NotificationService->>Notification: status = SENT, sent_at = now
    else Email Failed
        SMTP-->>EmailService: Error
        EmailService-->>NotificationService: False
        NotificationService->>Notification: status = FAILED
    end
    deactivate EmailService
    deactivate NotificationService
```

---

## Trial & Alteration Workflows

### 14. Trial Scheduling Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Staff
    participant TrialView
    participant Trial
    participant NotificationService
    participant Customer
    
    Staff->>TrialView: Schedule trial for order
    Staff->>TrialView: Enter date, time, location
    
    TrialView->>Trial: Create trial record
    Note over Trial: status = SCHEDULED
    
    TrialView->>NotificationService: Send trial notification
    NotificationService->>Customer: Email: Trial scheduled
    
    TrialView->>Staff: Trial scheduled
    
    Note over Staff,Customer: Customer attends trial
    
    Staff->>TrialView: Update trial status
    
    alt Fits perfectly
        Staff->>Trial: status = COMPLETED
        Staff->>TrialView: Mark order ready
    else Needs alterations
        Staff->>TrialView: Record alterations needed
        TrialView->>TrialView: Create Alteration records
        Staff->>TrialView: Update revised delivery date
    end
```
