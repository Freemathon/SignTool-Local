#!/bin/bash

# LocalSignTools automated setup script
# Automates dependency checking, installation, and build

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== LocalSignTools Setup ===${NC}"
echo ""

# 1. Check Go
echo -e "${BLUE}Checking dependencies...${NC}"
echo ""

if ! command -v go &> /dev/null; then
    echo -e "${RED}✗ Go not found${NC}"
    echo "  Install with Homebrew: ${GREEN}brew install go${NC}"
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
echo -e "${GREEN}✓ Go ${GO_VERSION} found${NC}"

# 2. Check fastlane
if ! command -v fastlane &> /dev/null; then
    echo -e "${YELLOW}⚠ fastlane not found${NC}"
    echo "  Install with Homebrew: ${GREEN}brew install fastlane${NC}"
    echo "  or: ${GREEN}gem install fastlane${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    FASTLANE_VERSION=$(fastlane --version | head -n 1)
    echo -e "${GREEN}✓ ${FASTLANE_VERSION} found${NC}"
fi

# 3. Check Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "  Python 3 is typically included with macOS. Please install manually if needed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ ${PYTHON_VERSION} found${NC}"

# 4. Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    echo "  Install with Homebrew: ${GREEN}brew install node${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"

# 5. Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}⚠ npm not found${NC}"
    echo "  npm usually comes with Node.js. Please ensure Node.js is properly installed."
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm ${NPM_VERSION} found${NC}"
fi

# 6. Install npm dependencies
echo ""
echo -e "${BLUE}Installing npm dependencies...${NC}"
if [ ! -d "builder/node-utils/node_modules" ]; then
    cd builder/node-utils
    npm install
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ npm dependencies installed${NC}"
else
    echo -e "${GREEN}✓ npm dependencies already installed${NC}"
fi

# 7. Download Go dependencies
echo ""
echo -e "${BLUE}Downloading Go dependencies...${NC}"
go mod download
echo -e "${GREEN}✓ Go dependencies downloaded${NC}"

# 8. Build
echo ""
echo -e "${BLUE}Building application...${NC}"
go build -o SignTools
echo -e "${GREEN}✓ Build complete${NC}"

# 9. Initial setup notice
echo ""
if [ ! -d "data/profiles" ] || [ -z "$(ls -A data/profiles 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ No profiles configured${NC}"
    echo "  See ${GREEN}README.md${NC} for profile setup instructions."
fi

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "You can run the application using:"
echo -e "  1. ${GREEN}./SignTools${NC}  (Server mode)"
echo -e "  2. ${GREEN}./SignTools -headless -ipa <path> -profile <name> -output <path>${NC}  (CLI mode)"
echo -e "  3. ${GREEN}./build_app.sh${NC}  (Build .app bundle)"
echo ""
