#!/bin/bash

# Production deployment script for Jodettu API
# This script sets up the application for production deployment

set -e  # Exit on any error

echo "🚀 Starting Jodettu API Production Deployment..."

# Configuration
PROJECT_DIR="/home/ubuntu/Jodettu"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="jodettu-api"
PORT=9090

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root. Run as ubuntu user."
   exit 1
fi

# Navigate to project directory
cd $PROJECT_DIR || {
    log_error "Failed to navigate to project directory: $PROJECT_DIR"
    exit 1
}

log_info "📁 Working directory: $(pwd)"

# Step 1: Update system packages
log_info "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install system dependencies
log_info "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx supervisor

# Step 3: Create virtual environment
log_info "🐍 Creating Python virtual environment..."
if [ -d "$VENV_DIR" ]; then
    log_warn "Virtual environment already exists. Removing and recreating..."
    rm -rf $VENV_DIR
fi

python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Step 4: Upgrade pip and install Python dependencies
log_info "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Setup PostgreSQL database
log_info "🗄️ Setting up PostgreSQL database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS jodettu_db;" || true
sudo -u postgres psql -c "DROP USER IF EXISTS jodettu_user;" || true
sudo -u postgres psql -c "CREATE USER jodettu_user WITH PASSWORD 'jodettu_password';"
sudo -u postgres psql -c "CREATE DATABASE jodettu_db OWNER jodettu_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE jodettu_db TO jodettu_user;"
sudo -u postgres psql -c "ALTER USER jodettu_user CREATEDB;"

# Step 6: Run database migrations
log_info "🔄 Running database migrations..."
source $VENV_DIR/bin/activate
export DATABASE_URL="postgresql://jodettu_user:jodettu_password@localhost:5432/jodettu_db"
alembic upgrade head

# Step 7: Create systemd service
log_info "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Jodettu API Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_DIR/bin
Environment=PYTHONPATH=$PROJECT_DIR
Environment=DATABASE_URL=postgresql://jodettu_user:jodettu_password@localhost:5432/jodettu_db
ExecStart=$VENV_DIR/bin/python -m uvicorn main_production:app --host 0.0.0.0 --port $PORT
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jodettu-api

[Install]
WantedBy=multi-user.target
EOF

# Step 8: Setup Nginx reverse proxy
log_info "🌐 Setting up Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Step 9: Setup log rotation
log_info "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/$SERVICE_NAME > /dev/null <<EOF
/var/log/jodettu-api/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Step 10: Create log directory
sudo mkdir -p /var/log/jodettu-api
sudo chown ubuntu:ubuntu /var/log/jodettu-api

# Step 11: Enable and start services
log_info "🚀 Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Step 12: Wait for service to start
log_info "⏳ Waiting for service to start..."
sleep 10

# Step 13: Check service status
log_info "🔍 Checking service status..."
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log_info "✅ $SERVICE_NAME is running"
else
    log_error "❌ $SERVICE_NAME failed to start"
    sudo systemctl status $SERVICE_NAME
    exit 1
fi

# Step 14: Health check
log_info "🏥 Performing health check..."
sleep 5
if curl -f http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
    log_info "✅ Health check passed"
else
    log_warn "⚠️ Health check failed, but service might still be starting"
fi

# Step 15: Display service information
log_info "📊 Deployment Summary:"
echo "=================================="
echo "Service: $SERVICE_NAME"
echo "Port: $PORT"
echo "Project Directory: $PROJECT_DIR"
echo "Virtual Environment: $VENV_DIR"
echo "Database: PostgreSQL (localhost:5432/jodettu_db)"
echo "=================================="
echo ""
echo "🔧 Useful Commands:"
echo "  Check status: sudo systemctl status $SERVICE_NAME"
echo "  View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Stop: sudo systemctl stop $SERVICE_NAME"
echo "  Database access: psql -h localhost -U jodettu_user -d jodettu_db"
echo ""
echo "🌐 API Endpoints:"
echo "  Health: http://$(curl -s ifconfig.me)/health"
echo "  Root: http://$(curl -s ifconfig.me)/"
echo "  Info: http://$(curl -s ifconfig.me)/info"
echo ""
log_info "🎉 Deployment completed successfully!"

# Display recent logs
echo ""
echo "📋 Recent service logs:"
sudo journalctl -u $SERVICE_NAME --no-pager -n 20
