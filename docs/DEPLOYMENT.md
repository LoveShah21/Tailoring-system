# Deployment Guide

This document provides comprehensive instructions for deploying the Tailoring Management System to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Server Requirements](#server-requirements)
3. [Production Setup](#production-setup)
4. [Database Configuration](#database-configuration)
5. [Static Files](#static-files)
6. [Email Configuration](#email-configuration)
7. [Security Settings](#security-settings)
8. [Web Server Setup](#web-server-setup)
9. [SSL/HTTPS](#sslhttps)
10. [Monitoring & Logging](#monitoring--logging)
11. [Backup Strategy](#backup-strategy)
12. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All tests pass: `python manage.py test`
- [ ] `DEBUG = False` in production
- [ ] `SECRET_KEY` is unique and secure (50+ characters)
- [ ] Database credentials are secure
- [ ] Razorpay live keys configured
- [ ] Email credentials configured
- [ ] Static files collected
- [ ] Migrations applied
- [ ] Superuser created
- [ ] All sensitive data in environment variables

---

## Server Requirements

### Minimum Specifications

| Component | Requirement |
|-----------|-------------|
| **OS** | Ubuntu 22.04 LTS / Windows Server 2019+ |
| **RAM** | 2 GB minimum, 4 GB recommended |
| **CPU** | 2 cores minimum |
| **Storage** | 20 GB SSD |
| **Python** | 3.11+ |
| **Database** | MySQL 8.0+ |

### Software Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
sudo apt install mysql-server mysql-client libmysqlclient-dev
sudo apt install nginx certbot python3-certbot-nginx
sudo apt install libmagic1  # For python-magic file validation
```

---

## Production Setup

### 1. Clone Repository

```bash
cd /var/www
git clone <repository-url> tailoring_system
cd tailoring_system
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Production `.env` settings:**

```ini
# SECURITY - CRITICAL
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-at-least-50-characters

# Database
DB_NAME=tailoring_db
DB_USER=tailoring_user
DB_PASSWORD=secure_database_password
DB_HOST=localhost
DB_PORT=3306

# Razorpay - USE LIVE KEYS
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_live_secret

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=Tailoring System <your_email@gmail.com>

# Hosts
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 5. Apply Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Load Initial Data (Optional)

```bash
python manage.py seed_data
```

---

## Database Configuration

### Create Database and User

```sql
-- Connect as root
mysql -u root -p

-- Create database
CREATE DATABASE tailoring_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'tailoring_user'@'localhost' 
    IDENTIFIED BY 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON tailoring_db.* 
    TO 'tailoring_user'@'localhost';

FLUSH PRIVILEGES;
```

### MySQL Production Settings

Edit `/etc/mysql/mysql.conf.d/mysqld.cnf`:

```ini
[mysqld]
# Performance
innodb_buffer_pool_size = 1G
max_connections = 200

# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Logging
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
```

---

## Static Files

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This creates `staticfiles/` directory with all static assets.

### Configure Media Directory

```bash
mkdir -p /var/www/tailoring_system/media
chmod 755 /var/www/tailoring_system/media
```

---

## Email Configuration

### Gmail App Password Setup

1. Enable 2-Step Verification on Google Account
2. Go to: Google Account → Security → App Passwords
3. Generate new app password for "Mail"
4. Use this password in `EMAIL_HOST_PASSWORD`

### Test Email Configuration

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

---

## Security Settings

Django automatically enables these when `DEBUG=False`:

```python
# settings.py (already configured)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### Additional Security

1. **Firewall**: Allow only ports 22, 80, 443
2. **Fail2Ban**: Protect against brute force
3. **Regular Updates**: Keep OS and packages updated

---

## Web Server Setup

### Gunicorn Configuration

Create `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=Gunicorn daemon for Tailoring System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/tailoring_system
ExecStart=/var/www/tailoring_system/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    tailoring_system.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/gunicorn
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### Nginx Configuration

Create `/etc/nginx/sites-available/tailoring`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Static files
    location /static/ {
        alias /var/www/tailoring_system/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/tailoring_system/media/;
        expires 7d;
    }
    
    # Application
    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
    
    # File upload size
    client_max_body_size 10M;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/tailoring /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/HTTPS

### Using Let's Encrypt (Free)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot automatically:
- Obtains certificates
- Configures Nginx
- Sets up auto-renewal

### Test Renewal

```bash
sudo certbot renew --dry-run
```

---

## Monitoring & Logging

### Application Logs

Logs are stored in:
- `/var/www/tailoring_system/logs/tailoring.log` - Application logs
- `/var/log/gunicorn/access.log` - HTTP access logs
- `/var/log/gunicorn/error.log` - Gunicorn errors

### Log Rotation

Create `/etc/logrotate.d/tailoring`:

```
/var/www/tailoring_system/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

### Health Check Endpoint

Add a health check view:

```python
# In views.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})
```

---

## Backup Strategy

### Database Backup

Create backup script `/opt/scripts/backup_db.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/var/backups/tailoring
mkdir -p $BACKUP_DIR

mysqldump -u tailoring_user -p'password' tailoring_db \
    --single-transaction \
    --routines \
    --triggers \
    > $BACKUP_DIR/tailoring_db_$DATE.sql

# Compress
gzip $BACKUP_DIR/tailoring_db_$DATE.sql

# Keep last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### Schedule Backup (Cron)

```bash
crontab -e
```

Add:
```
0 2 * * * /opt/scripts/backup_db.sh
```

### Media Backup

```bash
# Daily media backup
rsync -avz /var/www/tailoring_system/media/ /var/backups/tailoring/media/
```

---

## Troubleshooting

### Common Issues

#### 1. 502 Bad Gateway

```bash
# Check Gunicorn status
sudo systemctl status gunicorn

# Check socket
ls -la /run/gunicorn.sock

# Restart services
sudo systemctl restart gunicorn nginx
```

#### 2. Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --noinput

# Check Nginx permissions
sudo chown -R www-data:www-data /var/www/tailoring_system/staticfiles
```

#### 3. Database Connection Refused

```bash
# Check MySQL status
sudo systemctl status mysql

# Test connection
mysql -u tailoring_user -p tailoring_db
```

#### 4. Email Not Sending

```bash
# Test from shell
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
```

Check:
- Gmail app password is correct
- Less secure apps or app passwords enabled
- Firewall allows outbound port 587

#### 5. File Upload Errors

```bash
# Check permissions
ls -la /var/www/tailoring_system/media/

# Fix permissions
sudo chown -R www-data:www-data /var/www/tailoring_system/media/
sudo chmod 755 /var/www/tailoring_system/media/
```

### Debug Mode (Temporarily)

If needed for debugging:

```bash
# Edit .env
DEBUG=True

# Restart
sudo systemctl restart gunicorn
```

**⚠️ Remember to set `DEBUG=False` after debugging!**

---

## Update Deployment

### Deploy New Version

```bash
cd /var/www/tailoring_system

# Backup
./scripts/backup_db.sh

# Pull changes
git pull origin main

# Activate venv
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Collect static
python manage.py collectstatic --noinput

# Restart
sudo systemctl restart gunicorn
```

### Rollback

```bash
# Restore database
gunzip < /var/backups/tailoring/tailoring_db_YYYYMMDD.sql.gz | mysql -u tailoring_user -p tailoring_db

# Checkout previous version
git checkout <previous-commit>

# Restart
sudo systemctl restart gunicorn
```
