# Use Cases

This document describes the primary use cases for the Tailoring Management System, organized by actor.

## Actors

| Actor | Description |
|-------|-------------|
| **Customer** | End user who places orders and tracks their status |
| **Staff** | General shop employee with order and customer management |
| **Tailor** | Specialist worker who performs stitching and alterations |
| **Designer** | Creates and manages design templates and customizations |
| **Delivery Person** | Handles order delivery and confirmation |
| **Admin** | Full system access including configuration and reports |

## Actor Use Case Diagram

```mermaid
flowchart TB
    subgraph Actors
        Customer((Customer))
        Staff((Staff))
        Tailor((Tailor))
        Designer((Designer))
        Delivery((Delivery))
        Admin((Admin))
    end
    
    subgraph "Customer Portal"
        UC1[View Order Status]
        UC2[View Order History]
        UC3[Submit Feedback]
        UC4[Update Profile]
    end
    
    subgraph "Order Management"
        UC5[Create Order]
        UC6[Update Order Status]
        UC7[Assign Staff]
        UC8[Allocate Materials]
        UC9[Schedule Trial]
        UC10[Record Alteration]
    end
    
    subgraph "Inventory Management"
        UC11[Add Fabric Stock]
        UC12[Record Stock Out]
        UC13[View Low Stock Alerts]
        UC14[Resolve Alert]
    end
    
    subgraph "Billing & Payments"
        UC15[Generate Bill]
        UC16[Create Invoice]
        UC17[Record Payment]
        UC18[Process Refund]
    end
    
    subgraph "Delivery Management"
        UC19[Schedule Delivery]
        UC20[Confirm Delivery]
    end
    
    subgraph "Design Management"
        UC21[Upload Design]
        UC22[Approve Design]
        UC23[Add Customization Notes]
    end
    
    subgraph "Administration"
        UC24[Manage Users]
        UC25[Configure System]
        UC26[View Audit Logs]
        UC27[Generate Reports]
        UC28[Manage Catalog]
    end
    
    Customer --> UC1
    Customer --> UC2
    Customer --> UC3
    Customer --> UC4
    
    Staff --> UC5
    Staff --> UC6
    Staff --> UC7
    Staff --> UC8
    Staff --> UC9
    Staff --> UC15
    Staff --> UC16
    Staff --> UC17
    Staff --> UC19
    
    Tailor --> UC10
    Tailor --> UC6
    
    Designer --> UC21
    Designer --> UC22
    Designer --> UC23
    
    Delivery --> UC20
    
    Admin --> UC18
    Admin --> UC24
    Admin --> UC25
    Admin --> UC26
    Admin --> UC27
    Admin --> UC28
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
```

## Detailed Use Cases

### UC1: View Order Status

| Field | Description |
|-------|-------------|
| **Actor** | Customer |
| **Precondition** | Customer is logged in |
| **Main Flow** | 1. Customer navigates to dashboard<br>2. System displays list of orders<br>3. Customer clicks on order<br>4. System shows current status and timeline |
| **Postcondition** | Customer views order details |

---

### UC5: Create Order

| Field | Description |
|-------|-------------|
| **Actor** | Staff, Admin |
| **Precondition** | User is logged in with appropriate role |
| **Main Flow** | 1. Staff clicks "New Order"<br>2. Selects customer (or creates new)<br>3. Selects garment type<br>4. Adds measurements<br>5. Selects work types<br>6. Sets delivery date<br>7. System calculates estimate<br>8. Staff confirms order |
| **Postcondition** | Order created with status "Booked" |
| **Alternative Flow** | 3a. Customer doesn't exist - Create new customer profile |

```mermaid
flowchart TD
    A[Start] --> B[Select Customer]
    B --> C{Customer Exists?}
    C -->|Yes| D[Select Garment Type]
    C -->|No| E[Create Customer]
    E --> D
    D --> F[Enter/Select Measurements]
    F --> G[Select Work Types]
    G --> H[Set Delivery Date]
    H --> I[Set Urgency]
    I --> J[Add Special Instructions]
    J --> K[Calculate Estimate]
    K --> L[Confirm Order]
    L --> M[Order Created - Status: Booked]
    M --> N[End]
```

---

### UC6: Update Order Status

| Field | Description |
|-------|-------------|
| **Actor** | Staff, Tailor, Admin |
| **Precondition** | Order exists, User has permission |
| **Main Flow** | 1. User views order<br>2. Clicks "Update Status"<br>3. Selects new status from allowed transitions<br>4. Adds reason/notes<br>5. System validates transition<br>6. System updates status and logs history |
| **Postcondition** | Order status updated, history recorded |
| **Alternative Flow** | 5a. Invalid transition - Error message shown |

```mermaid
flowchart TD
    A[View Order] --> B[Click Update Status]
    B --> C[Show Available Transitions]
    C --> D[Select New Status]
    D --> E[Add Reason/Notes]
    E --> F{Valid Transition?}
    F -->|Yes| G[Update Status]
    G --> H[Create History Entry]
    H --> I[Send Notification]
    I --> J[End]
    F -->|No| K[Show Error]
    K --> B
```

---

### UC11: Add Fabric Stock

| Field | Description |
|-------|-------------|
| **Actor** | Staff, Admin |
| **Precondition** | User is logged in |
| **Main Flow** | 1. Navigate to Inventory<br>2. Click "Add Stock"<br>3. Select fabric (or create new)<br>4. Enter quantity received<br>5. Enter unit cost<br>6. Add notes<br>7. System creates transaction<br>8. System updates stock level |
| **Postcondition** | Stock increased, transaction recorded |

---

### UC15: Generate Bill

| Field | Description |
|-------|-------------|
| **Actor** | Staff, Admin |
| **Precondition** | Order exists |
| **Main Flow** | 1. View order<br>2. Click "Generate Bill"<br>3. System calculates:<br>   - Base garment price<br>   - Work type charges<br>   - Alteration charges<br>   - Urgency surcharge<br>   - Tax<br>4. System creates OrderBill<br>5. Staff enters advance amount<br>6. System calculates balance |
| **Postcondition** | Bill created with computed totals |

---

### UC17: Record Payment

| Field | Description |
|-------|-------------|
| **Actor** | Staff, Admin |
| **Precondition** | Invoice exists |
| **Main Flow** | 1. View invoice<br>2. Click "Record Payment"<br>3. Select payment mode (Cash/Razorpay)<br>4. For Razorpay:<br>   - Create Razorpay order<br>   - Customer completes payment<br>   - Verify signature<br>5. For Cash:<br>   - Enter amount<br>   - Enter receipt reference<br>6. System records payment<br>7. System updates invoice status |
| **Postcondition** | Payment recorded, invoice status updated |

```mermaid
flowchart TD
    A[View Invoice] --> B[Click Record Payment]
    B --> C{Payment Mode?}
    C -->|Cash| D[Enter Amount]
    D --> E[Enter Receipt Reference]
    E --> F[Record Payment]
    C -->|Razorpay| G[Create Razorpay Order]
    G --> H[Customer Pays Online]
    H --> I[Receive Webhook/Callback]
    I --> J[Verify Signature]
    J --> F
    F --> K[Update Invoice Status]
    K --> L{Fully Paid?}
    L -->|Yes| M[Status: PAID]
    L -->|No| N[Status: PARTIALLY_PAID]
```

---

### UC21: Upload Design

| Field | Description |
|-------|-------------|
| **Actor** | Designer, Staff |
| **Precondition** | User has designer/staff role |
| **Main Flow** | 1. Navigate to Designs<br>2. Click "Upload Design"<br>3. Select file (PDF/JPG/PNG)<br>4. Enter name and description<br>5. Optionally link to order<br>6. System validates file<br>7. System saves design |
| **Postcondition** | Design uploaded, pending approval |
| **Alternative Flow** | 6a. Invalid file type - Error shown |

---

### UC24: Manage Users

| Field | Description |
|-------|-------------|
| **Actor** | Admin |
| **Precondition** | User is admin |
| **Main Flow** | 1. Navigate to User Management<br>2. View user list<br>3. Click user to edit<br>4. Modify roles/permissions<br>5. Save changes |
| **Postcondition** | User updated |

---

## Use Case by Module

### Customer Module

```mermaid
flowchart LR
    subgraph Customer Module
        direction TB
        A[View Profile]
        B[Update Profile]
        C[View Orders]
        D[View Order Details]
        E[Submit Feedback]
    end
    
    Customer((Customer)) --> A
    Customer --> B
    Customer --> C
    Customer --> D
    Customer --> E
```

### Order Module

```mermaid
flowchart LR
    subgraph Order Module
        direction TB
        A[Create Order]
        B[View Orders]
        C[Update Status]
        D[Assign Staff]
        E[Allocate Materials]
        F[Cancel Order]
    end
    
    Staff((Staff)) --> A
    Staff --> B
    Staff --> C
    Staff --> D
    Staff --> E
    Admin((Admin)) --> F
```

### Inventory Module

```mermaid
flowchart LR
    subgraph Inventory Module
        direction TB
        A[View Stock]
        B[Add Stock]
        C[Record Damage]
        D[View Alerts]
        E[Resolve Alert]
    end
    
    Staff((Staff)) --> A
    Staff --> B
    Staff --> C
    Staff --> D
    Staff --> E
```

### Reporting Module

```mermaid
flowchart LR
    subgraph Reporting Module
        direction TB
        A[Revenue Report]
        B[Pending Orders]
        C[Staff Workload]
        D[Inventory Consumption]
        E[Export to CSV/PDF]
    end
    
    Admin((Admin)) --> A
    Admin --> B
    Admin --> C
    Admin --> D
    Admin --> E
```
