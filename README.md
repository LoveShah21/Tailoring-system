# Tailoring Management System 🧵

A comprehensive, production-grade **Django-based tailoring shop management system** designed to streamline order tracking, inventory management, billing, and customer communications for tailoring businesses.

## ✨ Features

- **Customer Management**: Customer profiles with measurements and order history
- **Order Lifecycle**: Full state machine with status tracking (Booked → In Progress → Ready → Delivered)
- **Measurements**: Customizable measurement templates per garment type
- **Inventory Management**: Fabric tracking with stock alerts and transaction history
- **Billing & Payments**: Razorpay integration + cash payment support with PDF invoices
- **Notifications**: Email notifications for order updates and payment confirmations
- **Role-Based Access**: Admin, Staff, Tailor, Designer, and Delivery roles
- **Audit Logging**: Complete activity tracking for compliance

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tailoring_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env with your database and email settings
   ```

5. **Create database**
   ```sql
   CREATE DATABASE tailoring_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Load initial data**
   ```bash
   python manage.py seed_data
   ```

9. **Start development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - Application: http://localhost:8000
    - Login: http://localhost:8000/users/login/

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) folder:

- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed codebase organization
- [Database Design](docs/DATABASE_DESIGN.md) - ER diagrams and table schemas
- [Use Cases](docs/USE_CASES.md) - System use case diagrams
- [Sequence Diagrams](docs/SEQUENCE_DIAGRAMS.md) - Key workflow sequences
- [API Reference](docs/API_REFERENCE.md) - URL endpoints and views
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions

## 🗂️ Project Structure

```
tailoring_system/
├── audit/             # Activity and payment audit logging
├── billing/           # Bills and invoice generation
├── catalog/           # Garment types, work types, images
├── config/            # System configuration and pricing rules
├── core/              # Security validators and sanitizers
├── customers/         # Customer profiles
├── delivery/          # Delivery scheduling and tracking
├── designs/           # Design uploads and customization
├── feedback/          # Customer feedback and ratings
├── inventory/         # Fabric stock management
├── measurements/      # Measurement templates and values
├── notifications/     # Email notifications
├── orders/            # Order lifecycle management
├── payments/          # Payment processing (Razorpay + Cash)
├── reporting/         # Business reports and analytics
├── templates/         # HTML templates
├── trials/            # Trial fittings and alterations
├── users/             # Authentication and RBAC
└── tailoring_system/  # Django project settings
```

## 🔐 Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `DEBUG` | Set to `False` in production |
| `SECRET_KEY` | Django secret key (min 50 chars) |
| `DB_NAME` | MySQL database name |
| `DB_USER` | MySQL username |
| `DB_PASSWORD` | MySQL password |
| `RAZORPAY_KEY_ID` | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | Razorpay secret |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail app password |

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test orders.tests
python manage.py test inventory.tests
python manage.py test payments.tests
python manage.py test core.tests
```

## 🛡️ Security Features

- CSRF protection on all forms
- Secure file upload validation (MIME type + magic bytes)
- Input sanitization with HTML stripping
- Role-based access control (RBAC)
- Password hashing with PBKDF2
- Production security headers (HTTPS, HSTS)

## 📧 Email Configuration

The system uses Gmail SMTP. To configure:

1. Enable 2-Step Verification on your Google Account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the App Password (not your regular password) in `.env`

## 💳 Payment Integration

Razorpay is integrated for online payments:

1. Get API keys from [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Add keys to `.env`
3. For testing, use Razorpay test keys

## 📄 License

This project is developed as a university final year project.

## 👨‍💻 Author

Developed by Love Shah
