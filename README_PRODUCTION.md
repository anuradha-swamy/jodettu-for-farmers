# Jodettu API - Production Setup Guide

## Overview

The Jodettu API is a production-ready FastAPI application that manages livestock data with AI-powered animal recognition. It uses a dual-database architecture:

- **PostgreSQL**: Master data (animal types, breeds)
- **MongoDB**: Transactional data (animal records, users, market data)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   PostgreSQL    │    │    MongoDB      │
│   (Port 8000)   │    │  Master Data    │    │ Transactional   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Nginx Proxy   │
                    │   (Port 80)     │
                    └─────────────────┘
```

## Prerequisites

### System Requirements
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- Python 3.12+
- PostgreSQL 14+
- MongoDB Atlas (cloud-based)
- Nginx
- systemd

### Environment Variables

Create a `.env` file with the following variables:

```bash
# MongoDB Configuration
MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/"

# PostgreSQL Configuration
DATABASE_URL="postgresql://jodettu_user:jodettu_password@localhost:5432/jodettu_db"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_DB="jodettu_db"
POSTGRES_USER="jodettu_user"
POSTGRES_PASSWORD="jodettu_password"

# JWT Configuration
HASH_SECRET_KEY="your-secret-key-here"
JWT_ALGORITHM="HS256"
TOKEN_EXPIRY_MINUTES="60"

# Twilio Configuration (optional)
ACCOUNT_SSID="your-twilio-account-sid"
AUTH_TOKEN="your-twilio-auth-token"
FROM_WHATSAPP_NUMBER="whatsapp:+14155238886"
```

## Quick Deployment

### 1. Automated Deployment

Run the provided deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
- Update system packages
- Install Python 3.12 and create virtual environment
- Install PostgreSQL and create database
- Run database migrations
- Setup systemd service
- Configure Nginx reverse proxy
- Start all services

### 2. Manual Deployment

#### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and system dependencies
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib nginx

# Install MongoDB dependencies (if using local MongoDB)
# sudo apt install -y mongodb
```

#### Step 2: Setup PostgreSQL

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER jodettu_user WITH PASSWORD 'jodettu_password';
CREATE DATABASE jodettu_db OWNER jodettu_user;
GRANT ALL PRIVILEGES ON DATABASE jodettu_db TO jodettu_user;
ALTER USER jodettu_user CREATEDB;
\q
EOF
```

#### Step 3: Setup Application

```bash
# Clone repository (if not already done)
cd /home/ubuntu/Jodettu

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Database Migrations

```bash
# Set environment
export DATABASE_URL="postgresql://jodettu_user:jodettu_password@localhost:5432/jodettu_db"

# Run migrations
alembic upgrade head

# Initialize default data (optional - done automatically on startup)
python -c "
import asyncio
from services.master_data_service import MasterDataService
from db.postgresql import AsyncSessionLocal

async def init_data():
    async with AsyncSessionLocal() as db:
        await MasterDataService.initialize_default_data(db)

asyncio.run(init_data())
"
```

#### Step 5: Configure systemd Service

```bash
# Copy service file
sudo cp jodettu-api.service /etc/systemd/system/

# Reload and start service
sudo systemctl daemon-reload
sudo systemctl enable jodettu-api
sudo systemctl start jodettu-api
```

#### Step 6: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/jodettu-api > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/jodettu-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl enable nginx && sudo systemctl start nginx
```

## Service Management

### Check Service Status
```bash
sudo systemctl status jodettu-api
sudo systemctl status nginx
sudo systemctl status postgresql
```

### View Logs
```bash
# Application logs
sudo journalctl -u jodettu-api -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Restart Services
```bash
sudo systemctl restart jodettu-api
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

## API Endpoints

### Health and Info
- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /info` - API information

### Authentication
- `POST /Jodettu/Auth/login` - User login
- `POST /Jodettu/Auth/register` - User registration
- `POST /Jodettu/Auth/verify-otp` - OTP verification

### Animals (MongoDB + PostgreSQL)
- `GET /Jodettu/Animals/animal-types` - Get animal types (PostgreSQL)
- `GET /Jodettu/Animals/breeds/{animal_type}` - Get breeds for animal type (PostgreSQL)
- `GET /Jodettu/Animals/master-data` - Get all master data (PostgreSQL)
- `POST /Jodettu/Animals/add-animal` - Add new animal (MongoDB)
- `GET /Jodettu/Animals/all-animals` - List all animals (MongoDB)
- `PUT /Jodettu/Animals/update/{animal_id}` - Update animal (MongoDB)
- `DELETE /Jodettu/Animals/delete/{animal_id}` - Delete animal (MongoDB)

### Market
- `GET /Jodettu/Market/market-animals` - Get market animals
- `POST /Jodettu/Animals/sell-animal/{animal_id}` - Sell animal
- `POST /Jodettu/Animals/buy-animal/{animal_id}` - Buy animal

### AI Classification
- `POST /classify` - Classify animal image

## Database Schema

### PostgreSQL (Master Data)

#### animal_types
```sql
CREATE TABLE animal_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### breeds
```sql
CREATE TABLE breeds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    animal_type_id INTEGER REFERENCES animal_types(id),
    description TEXT,
    origin VARCHAR(100),
    characteristics TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, animal_type_id)
);
```

### MongoDB (Transactional Data)

#### Collections
- `users` - User accounts and authentication
- `own_animals` - Animal records and ownership
- `market_animals` - Animals for sale
- `machines` - Equipment/machinery data
- `marketplace` - General marketplace data
- `otps` - One-time passwords for authentication

## Monitoring and Maintenance

### Health Monitoring
```bash
# Check if API is responding
curl -f http://localhost/health

# Check database connections
curl -f http://localhost/info | jq '.services'
```

### Database Maintenance

#### PostgreSQL
```bash
# Connect to database
psql -h localhost -U jodettu_user -d jodettu_db

# Backup database
pg_dump -h localhost -U jodettu_user jodettu_db > backup.sql

# Restore database
psql -h localhost -U jodettu_user jodettu_db < backup.sql

# Vacuum and analyze
psql -h localhost -U jodettu_user -d jodettu_db -c "VACUUM ANALYZE;"
```

#### MongoDB
```bash
# Backup collections (using mongodump)
mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/" --db=jodettu --out=backup/

# Restore collections (using mongorestore)
mongorestore --uri="mongodb+srv://user:pass@cluster.mongodb.net/" --db=jodettu backup/jodettu/
```

### Log Rotation
Log rotation is automatically configured for the application logs in `/var/log/jodettu-api/`.

### Performance Monitoring
Monitor key metrics:
- Response times
- Database connection pool usage
- Memory usage
- Disk space
- Error rates

## Security

### Network Security
- Firewall configured to allow only necessary ports (80, 443, 22)
- Nginx reverse proxy hides application server details
- Security headers configured in Nginx

### Application Security
- JWT-based authentication
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- NoSQL injection prevention (PyMongo)
- CORS configuration

### Database Security
- Separate database users with limited privileges
- Password authentication
- SSL/TLS for MongoDB Atlas
- Regular backups

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status jodettu-api

# Check logs for errors
sudo journalctl -u jodettu-api -n 50

# Common fixes:
# - Check environment variables in .env file
# - Verify PostgreSQL is running and accessible
# - Check virtual environment is properly set up
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U jodettu_user -d jodettu_db -c "SELECT 1;"

# Test MongoDB connection
python -c "
from general.database import client
print('MongoDB connected:', client.admin.command('ping'))
"
```

#### API Not Responding
```bash
# Check if port is listening
netstat -tlnp | grep :8000

# Check Nginx configuration
sudo nginx -t

# Restart services
sudo systemctl restart jodettu-api nginx
```

### Performance Issues
- Monitor database query performance
- Check for memory leaks
- Analyze slow queries
- Monitor system resources

## Development vs Production

### Development
```bash
# Run with auto-reload
uvicorn main_production:app --reload --host 0.0.0.0 --port 8000

# Use local databases
DATABASE_URL="postgresql://user:pass@localhost:5432/jodettu_dev"
MONGO_URI="mongodb://localhost:27017"
```

### Production
```bash
# Run with systemd
sudo systemctl start jodettu-api

# Use production databases
DATABASE_URL="postgresql://jodettu_user:secure_pass@localhost:5432/jodettu_db"
MONGO_URI="mongodb+srv://user:secure_pass@cluster.mongodb.net/"
```

## Scaling

### Horizontal Scaling
- Deploy multiple instances behind load balancer
- Use PostgreSQL connection pooling
- Implement caching (Redis)
- Use CDN for static assets

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement database indexing
- Use read replicas for PostgreSQL

## Backup and Recovery

### Automated Backups
```bash
# Add to crontab for daily backups
0 2 * * * /home/ubuntu/Jodettu/scripts/backup.sh
```

### Disaster Recovery
1. Restore from latest backup
2. Verify data integrity
3. Restart services
4. Monitor system health

## Support

For issues and support:
1. Check logs for error messages
2. Review troubleshooting section
3. Check system resource usage
4. Verify all services are running
5. Test database connections

## Version Updates

To update the application:
1. Backup current system
2. Pull latest code
3. Update dependencies
4. Run database migrations
5. Restart services
6. Verify functionality

```bash
# Update process
cd /home/ubuntu/Jodettu
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart jodettu-api
```
