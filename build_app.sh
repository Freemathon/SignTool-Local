#!/bin/bash

# LocalSignTools .app bundle build script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="SignTools"
APP_BUNDLE="$SCRIPT_DIR/${APP_NAME}.app"
EXECUTABLE="$SCRIPT_DIR/$APP_NAME"
APP_EXECUTABLE="$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LocalSignTools .app Bundle Build ===${NC}"
echo ""

# Build Go application
echo -e "${YELLOW}Building Go application...${NC}"
cd "$SCRIPT_DIR" || exit 1
go build -o "$APP_NAME" || exit 1
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# Create .app bundle directory structure
echo -e "${YELLOW}Creating .app bundle structure...${NC}"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# Copy executable to .app bundle
echo -e "${YELLOW}Copying executable to .app bundle...${NC}"
cp "$EXECUTABLE" "${APP_EXECUTABLE}.bin"
chmod +x "${APP_EXECUTABLE}.bin"
echo -e "${GREEN}✓ Copy complete${NC}"
echo ""

# Create Info.plist
echo -e "${YELLOW}Creating Info.plist...${NC}"
cat > "$APP_BUNDLE/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>SignTools</string>
    <key>CFBundleIdentifier</key>
    <string>com.localsigntools.SignTools</string>
    <key>CFBundleName</key>
    <string>SignTools</string>
    <key>CFBundleDisplayName</key>
    <string>LocalSignTools</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF
echo -e "${GREEN}✓ Info.plist created${NC}"
echo ""

# Create wrapper script (modified to pass command-line arguments)
echo -e "${YELLOW}Creating wrapper script...${NC}"
cat > "$APP_EXECUTABLE" <<'WRAPPER_EOF'
#!/bin/bash

# LocalSignTools wrapper script
# Sets working directory to project root when executed from .app bundle
# Modified to pass command-line arguments

# Get .app bundle location
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_ROOT="$(dirname "$APP_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Actual executable path (binary inside .app bundle)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTUAL_EXECUTABLE="$SCRIPT_DIR/SignTools.bin"

# Check if executable exists
if [ ! -f "$ACTUAL_EXECUTABLE" ]; then
    osascript -e 'display dialog "SignTools.bin not found.\n\nPlease run build_app.sh to rebuild the .app bundle." buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Get all arguments
ARGS="$@"

# If headless mode (CLI mode), run directly without opening terminal
if [[ "$ARGS" == *"-headless"* ]]; then
    # CLI mode: run directly (output to stdout)
    exec "$ACTUAL_EXECUTABLE" $ARGS
else
    # Normal mode: open terminal window and run
    osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$PROJECT_ROOT' && '$ACTUAL_EXECUTABLE' $ARGS"
end tell
EOF
fi
WRAPPER_EOF

chmod +x "$APP_EXECUTABLE"
echo -e "${GREEN}✓ Wrapper script created${NC}"
echo ""

echo -e "${GREEN}=== Build Complete ===${NC}"
echo ""
echo "You can run the application using:"
echo ""
echo "1. Double-click (Normal mode):"
echo "   Double-click ${APP_NAME}.app in Finder"
echo ""
echo "2. CLI mode (with arguments):"
echo "   SignTools.app/Contents/MacOS/SignTools -headless -ipa app.ipa -profile profile_name -output signed.ipa"
echo ""
echo "3. Direct executable (Recommended):"
echo "   SignTools.app/Contents/MacOS/SignTools.bin -headless -ipa app.ipa -profile profile_name -output signed.ipa"
echo ""
