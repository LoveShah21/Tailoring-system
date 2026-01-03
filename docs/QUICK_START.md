# Quick Start Guide

Get the Tailoring Management System running in under 10 minutes.

## Prerequisites

- Python 3.11+
- MySQL 8.0+
- Git

## Step 1: Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd tailoring_system

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Database

### Create MySQL Database

```sql
CREATE DATABASE tailoring_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Configure Environment

```bash
# Copy template
copy .env.example .env    # Windows
cp .env.example .env       # Linux/Mac

# Edit .env with your settings
```

**Minimum required settings in `.env`:**

```ini
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

DB_NAME=tailoring_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```

## Step 3: Initialize Database

```bash
# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Load sample data (optional)
python manage.py seed_data
```

## Step 4: Run

```bash
python manage.py runserver
```

Open http://localhost:8000 in your browser.

## Step 5: Login

- **URL**: http://localhost:8000/users/login/
- Use the superuser credentials you created

## What's Next?

1. **Create Garment Types**: Go to Catalog → Add garment types like Blouse, Kurti, etc.
2. **Add Customers**: Create customer profiles with contact info
3. **Create Orders**: Start placing orders for customers
4. **Manage Inventory**: Add fabric stock to the inventory

## Sample Data

If you ran `python manage.py seed_data`, you'll have:

- **Admin User**: admin / admin123
- **Sample Roles**: Admin, Staff, Tailor, Designer, Delivery, Customer
- **Sample Order Statuses**: Booked, In Progress, Ready, Delivered, Cancelled
- **Sample Garment Types**: Blouse, Kurti, Suit, Lehenga, Saree
- **Sample Work Types**: Embroidery, Mirror Work, Handwork, Beadwork

## Directory Structure Overview

```
tailoring_system/
├── users/          # Authentication
├── customers/      # Customer profiles
├── catalog/        # Garment & work types
├── inventory/      # Fabric stock
├── measurements/   # Customer measurements
├── designs/        # Design files
├── orders/         # Order management
├── billing/        # Bills & invoices
├── payments/       # Payment processing
├── templates/      # HTML templates
└── static/         # CSS, JS files
```

## Need Help?

- Check the [Project Structure](PROJECT_STRUCTURE.md) for codebase details
- See [Database Design](DATABASE_DESIGN.md) for schema information
- Review [Use Cases](USE_CASES.md) for feature explanations
- Follow [Deployment Guide](DEPLOYMENT.md) for production setup
