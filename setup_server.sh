#!/bin/bash

# Auto-installer for FoodTech project on Ubuntu 24.04
# Usage: curl -sSL https://github.com/carman72tmn/foodzuka/raw/main/setup_server.sh | bash

set -e

echo "🚀 Starting FoodTech Auto-Installer for Ubuntu 24.04..."

# 1. Update System
echo "Updating package lists..."
sudo apt update
sudo apt upgrade -y

# 2. Install Dependencies
echo "Installing Docker, Git and utilities..."
sudo apt install -y docker.io docker-compose git curl ufw

# 3. Enable Docker
sudo systemctl enable --now docker

# 4. Configure Firewall
echo "Configuring Firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 8081/tcp
sudo ufw allow 5173/tcp
sudo ufw --force enable

# 5. Clone Project (if not already in folder)
if [ ! -d "foodtech" ]; then
    echo "Cloning repository..."
    git clone https://github.com/carman72tmn/foodzuka.git foodtech
    cd foodtech
else
    echo "Using existing foodtech directory..."
    cd foodtech
fi

# 6. Environment Setup
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "DB_DATABASE=foodtech_db" > .env
        echo "DB_USERNAME=foodtech_user" >> .env
        echo "DB_PASSWORD=postgres" >> .env
    fi
    echo "⚠️  Please update your .env file with correct credentials later!"
fi

# 7. Launch
echo "Launching project with Docker Compose..."
# Using --no-cache to avoid package integrity issues from previous failed attempts
sudo docker-compose build --no-cache
sudo docker-compose up -d

echo "✅ Installation complete!"
echo "API: http://your-vps-ip:8000"
echo "Admin: http://your-vps-ip:8081"
echo "Frontend: http://your-vps-ip:5173"
