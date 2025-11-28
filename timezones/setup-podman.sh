#!/bin/bash
#
# Timezone API Podman Setup Script
# For CloudPanel or any Podman-based hosting
#

set -e

echo "=========================================="
echo "Timezone API - Podman Setup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Not running as root. Some commands may require sudo.${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed${NC}"
    echo ""
    echo "Install Podman:"
    echo "  Ubuntu/Debian: sudo apt-get install -y podman"
    echo "  RHEL/CentOS:   sudo dnf install -y podman"
    echo ""
    read -p "Install Podman now? (y/N): " install_podman
    if [[ $install_podman =~ ^[Yy]$ ]]; then
        if command -v apt-get &> /dev/null; then
            $SUDO apt-get update
            $SUDO apt-get install -y podman
        elif command -v dnf &> /dev/null; then
            $SUDO dnf install -y podman
        else
            echo -e "${RED}Could not detect package manager${NC}"
            exit 1
        fi
    else
        exit 1
    fi
fi

echo -e "${GREEN}✓ Podman is installed${NC}"
podman --version
echo ""

# Check if podman-compose is installed
if ! command -v podman-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: podman-compose is not installed${NC}"
    echo ""
    read -p "Install podman-compose? (y/N): " install_compose
    if [[ $install_compose =~ ^[Yy]$ ]]; then
        $SUDO pip3 install podman-compose || $SUDO pip install podman-compose
    else
        echo -e "${YELLOW}Continuing without podman-compose (will use podman directly)${NC}"
        USE_COMPOSE=false
    fi
else
    USE_COMPOSE=true
    echo -e "${GREEN}✓ podman-compose is installed${NC}"
fi
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

# Build and run with Podman
echo ""
echo "=========================================="
echo "Building Container Image"
echo "=========================================="
echo ""

if [ "$USE_COMPOSE" = true ]; then
    # Use podman-compose
    podman-compose build

    echo ""
    echo "=========================================="
    echo "Starting Container"
    echo "=========================================="
    echo ""
    podman-compose up -d

    # Wait for container to be healthy
    echo ""
    echo "Waiting for service to start..."
    sleep 5

    # Check if container is running
    if podman-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✓ Container is running${NC}"
    else
        echo -e "${RED}✗ Container failed to start${NC}"
        echo "Check logs with: podman-compose logs"
        exit 1
    fi
else
    # Use podman directly
    IMAGE_NAME="timezone-api:latest"
    CONTAINER_NAME="timezone-api"

    # Build image
    podman build -t $IMAGE_NAME .

    # Stop and remove existing container if it exists
    podman stop $CONTAINER_NAME 2>/dev/null || true
    podman rm $CONTAINER_NAME 2>/dev/null || true

    echo ""
    echo "=========================================="
    echo "Starting Container"
    echo "=========================================="
    echo ""

    # Run container
    podman run -d \
        --name $CONTAINER_NAME \
        -p ${PORT}:8000 \
        -v ./geodb:/app/geodb:ro,z \
        -e TZ=UTC \
        --restart unless-stopped \
        --health-cmd "curl -f http://localhost:8000/health || exit 1" \
        --health-interval 30s \
        --health-timeout 10s \
        --health-retries 3 \
        --health-start-period 10s \
        $IMAGE_NAME

    # Wait for container to be healthy
    echo ""
    echo "Waiting for service to start..."
    sleep 5

    # Check if container is running
    if podman ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}✓ Container is running${NC}"
    else
        echo -e "${RED}✗ Container failed to start${NC}"
        echo "Check logs with: podman logs $CONTAINER_NAME"
        exit 1
    fi
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

# Generate systemd service
echo ""
echo "=========================================="
echo "Systemd Service Setup (Optional)"
echo "=========================================="
echo ""
read -p "Generate systemd service for auto-start? (y/N): " gen_service

if [[ $gen_service =~ ^[Yy]$ ]]; then
    if [ "$USE_COMPOSE" = true ]; then
        # Generate service for podman-compose
        cat > timezone-api.service << EOF
[Unit]
Description=Timezone API Service (Podman Compose)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/podman-compose up -d
ExecStop=/usr/bin/podman-compose down
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF
    else
        # Generate service for podman container
        podman generate systemd --new --name $CONTAINER_NAME > timezone-api.service
    fi

    echo -e "${GREEN}✓ Generated timezone-api.service${NC}"
    echo ""
    echo "To install the service:"
    echo "  $SUDO cp timezone-api.service /etc/systemd/system/"
    echo "  $SUDO systemctl daemon-reload"
    echo "  $SUDO systemctl enable timezone-api"
    echo "  $SUDO systemctl start timezone-api"
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

if [ "$USE_COMPOSE" = true ]; then
    echo "View logs:    podman-compose logs -f"
    echo "Stop:         podman-compose stop"
    echo "Start:        podman-compose start"
    echo "Restart:      podman-compose restart"
    echo "Remove:       podman-compose down"
    echo "Rebuild:      podman-compose up -d --build"
else
    echo "View logs:    podman logs -f $CONTAINER_NAME"
    echo "Stop:         podman stop $CONTAINER_NAME"
    echo "Start:        podman start $CONTAINER_NAME"
    echo "Restart:      podman restart $CONTAINER_NAME"
    echo "Remove:       podman rm -f $CONTAINER_NAME"
    echo "Rebuild:      podman build -t $IMAGE_NAME . && podman restart $CONTAINER_NAME"
fi

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
