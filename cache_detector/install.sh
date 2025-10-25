#!/bin/bash
# ============================================================================
# Proxy Cache Detector - Unix/Linux/macOS Installation Script
# ============================================================================
# This script creates a virtual environment and installs dependencies
# Compatible with Linux, macOS, BSD, and other Unix-like systems
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Banner
echo ""
echo "================================================================================"
echo "  Proxy Cache Detector - Installation"
echo "================================================================================"
echo ""

# Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    OS_TYPE="FreeBSD"
elif [[ "$OSTYPE" == "openbsd"* ]]; then
    OS_TYPE="OpenBSD"
else
    OS_TYPE="Unix-like"
fi

print_info "Detected OS: $OS_TYPE"
echo ""

# Step 1: Check for Python 3
echo "[1/7] Checking Python installation..."

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if 'python' is Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    print_error "Python 3 is not installed"
    echo ""
    echo "Please install Python 3.8 or higher:"

    if [ "$OS_TYPE" == "macOS" ]; then
        echo "  brew install python3"
        echo "  or download from https://www.python.org/downloads/"
    elif [ "$OS_TYPE" == "Linux" ]; then
        echo "  Ubuntu/Debian:  sudo apt update && sudo apt install python3 python3-pip"
        echo "  RHEL/Fedora:    sudo dnf install python3 python3-pip"
        echo "  Arch:           sudo pacman -S python python-pip"
    else
        echo "  Visit: https://www.python.org/downloads/"
    fi
    echo ""
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
print_success "$PYTHON_VERSION found at $(which $PYTHON_CMD)"
echo ""

# Step 2: Check Python version
echo "[2/7] Verifying Python version..."

$PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)"
if [ $? -ne 0 ]; then
    print_error "Python 3.6 or higher is required"
    echo ""
    echo "Current version: $PYTHON_VERSION"
    echo "Please upgrade your Python installation"
    echo ""
    exit 1
fi

print_success "Python version is compatible (3.6+)"
echo ""

# Step 3: Check for pip
echo "[3/7] Checking pip installation..."

PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
elif $PYTHON_CMD -m pip --version &> /dev/null; then
    PIP_CMD="$PYTHON_CMD -m pip"
fi

if [ -z "$PIP_CMD" ]; then
    print_error "pip is not installed"
    echo ""
    echo "Please install pip:"

    if [ "$OS_TYPE" == "macOS" ]; then
        echo "  brew install python3  (includes pip)"
    elif [ "$OS_TYPE" == "Linux" ]; then
        echo "  Ubuntu/Debian:  sudo apt install python3-pip"
        echo "  RHEL/Fedora:    sudo dnf install python3-pip"
        echo "  Arch:           sudo pacman -S python-pip"
    fi
    echo ""
    exit 1
fi

PIP_VERSION=$($PIP_CMD --version 2>&1 | head -n1)
print_success "$PIP_VERSION"
echo ""

# Step 4: Create virtual environment
echo "[4/7] Setting up virtual environment..."

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists at 'venv'"
    print_info "Skipping creation..."
else
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created successfully"
    else
        print_error "Failed to create virtual environment"
        echo ""
        echo "Try running manually:"
        echo "  $PYTHON_CMD -m venv venv"
        echo ""
        exit 1
    fi
fi

echo ""

# Step 5: Activate virtual environment
echo "[5/7] Activating virtual environment..."

# Check which shell activation script to use
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_error "Virtual environment activation script not found"
    exit 1
fi

echo ""

# Step 6: Install dependencies
echo "[6/7] Installing dependencies in virtual environment..."
echo ""

# Upgrade pip first
print_info "Upgrading pip..."
python -m pip install --upgrade pip --quiet

if [ -f "requirements.txt" ]; then
    print_info "Installing from requirements.txt..."

    python -m pip install -r requirements.txt

    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        echo ""
        echo "Try running manually:"
        echo "  source venv/bin/activate"
        echo "  python -m pip install -r requirements.txt"
        echo ""
        exit 1
    fi
else
    print_warning "requirements.txt not found"
    print_info "Installing requests library directly..."

    python -m pip install "requests>=2.31.0"

    if [ $? -eq 0 ]; then
        print_success "requests library installed successfully"
    else
        print_error "Failed to install requests library"
        echo ""
        exit 1
    fi
fi

echo ""

# Step 7: Make script executable
echo "[7/7] Setting executable permissions..."

if [ -f "proxy_cache_detector.py" ]; then
    chmod +x proxy_cache_detector.py
    print_success "proxy_cache_detector.py is now executable"
else
    print_warning "proxy_cache_detector.py not found in current directory"
fi

echo ""

# Installation complete
echo "================================================================================"
echo "  Installation Complete!"
echo "================================================================================"
echo ""
echo "A virtual environment has been created in the 'venv' directory."
echo ""
print_info "IMPORTANT: To use the tool, you must activate the virtual environment first:"
echo ""
echo "  Activation:"
echo "    source venv/bin/activate"
echo ""
echo "  Then run commands:"
echo "    python proxy_cache_detector.py detect https://example.com"
echo "    ./proxy_cache_detector.py detect https://example.com"
echo "    python proxy_cache_detector.py purge-varnish https://example.com/page"
echo "    python proxy_cache_detector.py --help"
echo ""
echo "  Deactivate when done:"
echo "    deactivate"
echo ""
echo "For more information, see docs/README.md"
echo ""

# Optional: Add activation to shell profile
CURRENT_DIR=$(pwd)
echo "================================================================================"
echo "  Optional: Quick Activation Alias"
echo "================================================================================"
echo ""
print_info "Add an alias to quickly activate the virtual environment:"
echo ""

if [ "$OS_TYPE" == "macOS" ] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "  For bash, add to ~/.bashrc or ~/.bash_profile:"
    echo "    alias cache-detector='cd $CURRENT_DIR && source venv/bin/activate'"
    echo ""
    echo "  For zsh, add to ~/.zshrc:"
    echo "    alias cache-detector='cd $CURRENT_DIR && source venv/bin/activate'"
    echo ""
    echo "  Then simply run: cache-detector"
fi

echo ""
print_success "Installation complete!"
echo ""
print_warning "The virtual environment is currently ACTIVE for this shell session."
echo ""
