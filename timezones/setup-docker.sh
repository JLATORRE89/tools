#!/bin/bash
#
# Timezone API Docker Setup Script
# For CloudPanel or any Docker-based hosting
#

set -e

echo "=========================================="
echo "Timezone API - Docker Setup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root${NC}"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo ""

# Create geodb directory
echo "Creating geodb directory..."
mkdir -p geodb

# Download GeoIP database
echo ""
echo "=========================================="
echo "GeoIP Database Setup"
echo "=========================================="
echo ""
echo "The GeoLite2 database is required for IP geolocation."
echo ""
echo "Options:"
echo "  1) I already have the database file"
echo "  2) Download it now (requires MaxMind license key)"
echo "  3) Skip for now (app will use fallback)"
echo ""
read -p "Choose option (1-3): " db_option

case $db_option in
    1)
        echo ""
        echo "Please place GeoLite2-City.mmdb in the ./geodb/ directory"
        echo "Press Enter when ready..."
        read
        if [ -f "./geodb/GeoLite2-City.mmdb" ]; then
            echo -e "${GREEN}✓ Database file found${NC}"
        else
            echo -e "${YELLOW}Warning: Database file not found. Continuing anyway...${NC}"
        fi
        ;;
    2)
        echo ""
        python3 download_geodb.py
        ;;
    3)
        echo -e "${YELLOW}Skipping database download. App will use UTC fallback.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

# Build Docker image
echo ""
echo "=========================================="
echo "Building Docker Image"
echo "=========================================="
echo ""
docker-compose build

# Ask about port configuration
echo ""
echo "=========================================="
echo "Port Configuration"
echo "=========================================="
echo ""
echo "Default port: 8000"
read -p "Change port? (y/N): " change_port

if [[ $change_port =~ ^[Yy]$ ]]; then
    read -p "Enter new port: " new_port
    # Update docker-compose.yml
    sed -i.bak "s/8000:8000/${new_port}:8000/g" docker-compose.yml
    echo -e "${GREEN}✓ Port changed to ${new_port}${NC}"
    PORT=$new_port
else
    PORT=8000
fi

# Start the container
echo ""
echo "=========================================="
echo "Starting Container"
echo "=========================================="
echo ""
docker-compose up -d

# Wait for container to be healthy
echo ""
echo "Waiting for service to start..."
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Container is running${NC}"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

# Test the API
echo ""
echo "=========================================="
echo "Testing API"
echo "=========================================="
echo ""

if curl -f http://localhost:${PORT}/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${YELLOW}⚠ API health check failed (may still be starting)${NC}"
fi

# Display CloudPanel setup instructions
echo ""
echo "=========================================="
echo "CloudPanel Setup Instructions"
echo "=========================================="
echo ""
echo "1. In CloudPanel, create a new site:"
echo "   Domain: time.voidguardsecurity.com"
echo "   Type: Generic"
echo ""
echo "2. Add a reverse proxy rule:"
echo "   Go to: Sites → time.voidguardsecurity.com → Vhost"
echo ""
echo "3. Add this location block inside the server block:"
echo ""
echo "   location / {"
echo "       proxy_pass http://127.0.0.1:${PORT};"
echo "       proxy_set_header Host \$host;"
echo "       proxy_set_header X-Real-IP \$remote_addr;"
echo "       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "       proxy_set_header X-Forwarded-Proto \$scheme;"
echo "   }"
echo ""
echo "4. Enable SSL certificate in CloudPanel"
echo ""
echo "=========================================="
echo "Container Management"
echo "=========================================="
echo ""
echo "View logs:    docker-compose logs -f"
echo "Stop:         docker-compose stop"
echo "Start:        docker-compose start"
echo "Restart:      docker-compose restart"
echo "Remove:       docker-compose down"
echo "Rebuild:      docker-compose up -d --build"
echo ""
echo "=========================================="
echo "API Endpoints"
echo "=========================================="
echo ""
echo "Health:       http://localhost:${PORT}/health"
echo "Auto-detect:  http://localhost:${PORT}/timezone/auto"
echo "Specific IP:  http://localhost:${PORT}/timezone/8.8.8.8"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
