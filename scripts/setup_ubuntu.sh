#!/bin/bash
set -euo pipefail

# ==============================================================================
# LinuxGuard - Ubuntu Deployment & Provisioning Script
# ==============================================================================

echo "=========================================================="
echo "  LinuxGuard - Server Monitoring & Auto-Remediation Setup"
echo "=========================================================="

# 1. Update package list & install system dependencies
echo "[1/5] Updating system packages & installing dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git curl net-tools iproute2

# 2. Setup Python Virtual Environment
echo "[2/5] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Upgrade pip and install Python packages
echo "[3/5] Installing required Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run Django Database Migrations
echo "[4/5] Executing database migrations..."
python manage.py makemigrations monitoring
python manage.py migrate

# 5. Seed Initial Demo Accounts & Monitored Nodes
echo "[5/5] Seeding default RBAC users and initial node data..."
python manage.py seed_demo_data

echo "=========================================================="
echo "  LinuxGuard Installation Complete!"
echo "  To start the Django web console:"
echo "    source venv/bin/activate"
echo "    python manage.py runserver 0.0.0.0:8000"
echo ""
echo "  To start the automated background monitoring daemon:"
echo "    python manage.py monitor_server --interval 30"
echo "=========================================================="
