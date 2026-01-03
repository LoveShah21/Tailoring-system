# API Reference

This document lists all URL endpoints and views in the Tailoring Management System.

## URL Structure

The application uses Django's URL routing. All URLs are organized by app module.

---

## Authentication URLs (`/users/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/users/login/` | `LoginView` | GET, POST | User login |
| `/users/logout/` | `LogoutView` | POST | User logout |
| `/users/password-reset/` | `PasswordResetView` | GET, POST | Request password reset |
| `/users/password-reset/done/` | `PasswordResetDoneView` | GET | Reset email sent confirmation |
| `/users/reset/<uidb64>/<token>/` | `PasswordResetConfirmView` | GET, POST | Set new password |
| `/users/reset/done/` | `PasswordResetCompleteView` | GET | Password reset complete |
| `/users/register/` | `RegisterView` | GET, POST | Customer registration |

---

## Dashboard URLs (`/dashboard/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/dashboard/` | `DashboardView` | GET | Role-based dashboard redirect |
| `/dashboard/admin/` | `AdminDashboardView` | GET | Admin dashboard |
| `/dashboard/staff/` | `StaffDashboardView` | GET | Staff dashboard |
| `/dashboard/customer/` | `CustomerDashboardView` | GET | Customer dashboard |
| `/dashboard/tailor/` | `TailorDashboardView` | GET | Tailor dashboard |
| `/dashboard/designer/` | `DesignerDashboardView` | GET | Designer dashboard |
| `/dashboard/delivery/` | `DeliveryDashboardView` | GET | Delivery dashboard |

---

## Customer URLs (`/customers/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/customers/` | `CustomerListView` | GET | List all customers |
| `/customers/create/` | `CustomerCreateView` | GET, POST | Create customer |
| `/customers/<pk>/` | `CustomerDetailView` | GET | View customer details |
| `/customers/<pk>/edit/` | `CustomerUpdateView` | GET, POST | Edit customer |

---

## Catalog URLs (`/catalog/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/catalog/garments/` | `GarmentTypeListView` | GET | List garment types |
| `/catalog/garments/create/` | `GarmentTypeCreateView` | GET, POST | Create garment type |
| `/catalog/garments/<pk>/` | `GarmentTypeDetailView` | GET | View garment details |
| `/catalog/garments/<pk>/edit/` | `GarmentTypeUpdateView` | GET, POST | Edit garment type |
| `/catalog/work-types/` | `WorkTypeListView` | GET | List work types |
| `/catalog/work-types/create/` | `WorkTypeCreateView` | GET, POST | Create work type |
| `/catalog/work-types/<pk>/edit/` | `WorkTypeUpdateView` | GET, POST | Edit work type |

---

## Inventory URLs (`/inventory/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/inventory/` | `FabricListView` | GET | List all fabrics |
| `/inventory/create/` | `FabricCreateView` | GET, POST | Add new fabric |
| `/inventory/<pk>/` | `FabricDetailView` | GET | View fabric details |
| `/inventory/<pk>/edit/` | `FabricUpdateView` | GET, POST | Edit fabric |
| `/inventory/<pk>/stock-in/` | `StockInView` | POST | Add stock |
| `/inventory/<pk>/stock-out/` | `StockOutView` | POST | Deduct stock |
| `/inventory/transactions/` | `TransactionListView` | GET | View transactions |
| `/inventory/alerts/` | `AlertListView` | GET | View low stock alerts |

---

## Measurement URLs (`/measurements/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/measurements/` | `MeasurementSetListView` | GET | List measurement sets |
| `/measurements/create/` | `MeasurementSetCreateView` | GET, POST | Create measurement set |
| `/measurements/<pk>/` | `MeasurementSetDetailView` | GET | View measurement set |
| `/measurements/<pk>/edit/` | `MeasurementSetUpdateView` | GET, POST | Edit measurements |
| `/measurements/templates/` | `TemplateListView` | GET | List templates |
| `/measurements/templates/create/` | `TemplateCreateView` | GET, POST | Create template |

---

## Design URLs (`/designs/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/designs/` | `DesignListView` | GET | List all designs |
| `/designs/create/` | `DesignCreateView` | GET, POST | Upload design |
| `/designs/<pk>/` | `DesignDetailView` | GET | View design |
| `/designs/<pk>/status/` | `DesignStatusUpdateView` | POST | Approve/reject design |
| `/designs/<pk>/notes/` | `AddCustomizationNoteView` | POST | Add customization note |

---

## Order URLs (`/orders/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/orders/` | `OrderListView` | GET | List all orders |
| `/orders/create/` | `OrderCreateView` | GET, POST | Create new order |
| `/orders/<pk>/` | `OrderDetailView` | GET | View order details |
| `/orders/<pk>/edit/` | `OrderUpdateView` | GET, POST | Edit order |
| `/orders/<pk>/status/` | `OrderStatusUpdateView` | POST | Update order status |
| `/orders/<pk>/assign/` | `OrderAssignmentView` | POST | Assign staff |
| `/orders/<pk>/allocate/` | `MaterialAllocationView` | POST | Allocate materials |

---

## Trial URLs (`/trials/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/trials/` | `TrialListView` | GET | List all trials |
| `/trials/create/<order_pk>/` | `TrialCreateView` | GET, POST | Schedule trial |
| `/trials/<pk>/` | `TrialDetailView` | GET | View trial details |
| `/trials/<pk>/edit/` | `TrialUpdateView` | GET, POST | Update trial |
| `/trials/<pk>/alterations/` | `AlterationCreateView` | POST | Add alteration |

---

## Billing URLs (`/billing/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/billing/bills/` | `BillListView` | GET | List all bills |
| `/billing/bills/<pk>/` | `BillDetailView` | GET | View bill |
| `/billing/generate/<order_pk>/` | `GenerateBillView` | POST | Generate bill for order |
| `/billing/invoices/` | `InvoiceListView` | GET | List invoices |
| `/billing/invoices/<pk>/` | `InvoiceDetailView` | GET | View invoice |
| `/billing/invoices/<pk>/pdf/` | `InvoicePDFView` | GET | Download invoice PDF |
| `/billing/invoices/create/<bill_pk>/` | `CreateInvoiceView` | POST | Create invoice |

---

## Payment URLs (`/payments/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/payments/` | `PaymentListView` | GET | List all payments |
| `/payments/<pk>/` | `PaymentDetailView` | GET | View payment |
| `/payments/create-order/<bill_pk>/` | `CreatePaymentOrderView` | POST | Create Razorpay order |
| `/payments/verify/` | `VerifyPaymentView` | POST | Verify Razorpay payment |
| `/payments/cash/<bill_pk>/` | `RecordCashPaymentView` | POST | Record cash payment |
| `/payments/webhook/` | `RazorpayWebhookView` | POST | Razorpay webhook |

---

## Delivery URLs (`/delivery/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/delivery/` | `DeliveryListView` | GET | List deliveries |
| `/delivery/schedule/<order_pk>/` | `ScheduleDeliveryView` | GET, POST | Schedule delivery |
| `/delivery/<pk>/` | `DeliveryDetailView` | GET | View delivery details |
| `/delivery/<pk>/confirm/` | `ConfirmDeliveryView` | POST | Confirm delivery |
| `/delivery/zones/` | `DeliveryZoneListView` | GET | List zones |

---

## Notification URLs (`/notifications/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/notifications/` | `NotificationListView` | GET | List notifications |
| `/notifications/<pk>/read/` | `MarkReadView` | POST | Mark as read |

---

## Feedback URLs (`/feedback/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/feedback/` | `FeedbackListView` | GET | List all feedback |
| `/feedback/submit/<order_pk>/` | `FeedbackSubmitView` | GET, POST | Submit feedback |
| `/feedback/<pk>/moderate/` | `FeedbackModerateView` | POST | Moderate feedback |

---

## Reporting URLs (`/reports/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/reports/` | `ReportDashboardView` | GET | Report dashboard |
| `/reports/revenue/` | `RevenueReportView` | GET | Revenue report |
| `/reports/pending-orders/` | `PendingOrdersReportView` | GET | Pending orders |
| `/reports/staff-workload/` | `StaffWorkloadView` | GET | Staff performance |
| `/reports/inventory/` | `InventoryReportView` | GET | Inventory report |
| `/reports/export/csv/` | `ExportCSVView` | GET | Export to CSV |
| `/reports/export/pdf/` | `ExportPDFView` | GET | Export to PDF |

---

## Audit URLs (`/audit/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/audit/` | `ActivityLogListView` | GET | View activity logs |
| `/audit/payments/` | `PaymentAuditListView` | GET | Payment audit logs |

---

## Configuration URLs (`/config/`)

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/config/` | `ConfigurationView` | GET, POST | System configuration |
| `/config/pricing-rules/` | `PricingRuleListView` | GET | List pricing rules |
| `/config/pricing-rules/create/` | `PricingRuleCreateView` | GET, POST | Create rule |

---

## HTTP Methods

| Method | Purpose |
|--------|---------|
| `GET` | Retrieve data (list, detail, forms) |
| `POST` | Create or update data |
| `PUT` | Full update (rarely used) |
| `DELETE` | Delete resource (rarely used, prefer soft delete) |

---

## Response Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `302` | Redirect |
| `400` | Bad Request |
| `403` | Forbidden |
| `404` | Not Found |
| `500` | Server Error |

---

## Authentication Required

All endpoints except login/register require authentication.

Unauthenticated requests redirect to `/users/login/`.

---

## Role-Based Access

| Role | Access Level |
|------|--------------|
| **Admin** | Full access to all endpoints |
| **Staff** | Orders, customers, inventory, billing, payments |
| **Tailor** | Assigned orders, status updates |
| **Designer** | Designs, customization notes |
| **Delivery** | Assigned deliveries, confirmation |
| **Customer** | Own profile, orders, feedback |
