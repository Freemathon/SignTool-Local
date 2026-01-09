#!/bin/bash

# LocalSignTools .appバンドルビルドスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="SignTools"
APP_BUNDLE="$SCRIPT_DIR/${APP_NAME}.app"
EXECUTABLE="$SCRIPT_DIR/$APP_NAME"
APP_EXECUTABLE="$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LocalSignTools .appバンドルビルド ===${NC}"
echo ""

# Goのビルド
echo -e "${YELLOW}Goアプリケーションをビルド中...${NC}"
cd "$SCRIPT_DIR" || exit 1
go build -o "$APP_NAME" || exit 1
echo -e "${GREEN}✓ ビルド完了${NC}"
echo ""

# .appバンドルのディレクトリ構造を作成
echo -e "${YELLOW}.appバンドル構造を作成中...${NC}"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
echo -e "${GREEN}✓ ディレクトリ構造作成完了${NC}"
echo ""

# 実行可能ファイルを.appバンドルにコピー
echo -e "${YELLOW}実行可能ファイルを.appバンドルにコピー中...${NC}"
cp "$EXECUTABLE" "$APP_EXECUTABLE"
chmod +x "$APP_EXECUTABLE"
echo -e "${GREEN}✓ コピー完了${NC}"
echo ""

# Info.plistを作成
echo -e "${YELLOW}Info.plistを作成中...${NC}"
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
echo -e "${GREEN}✓ Info.plist作成完了${NC}"
echo ""

# ラッパースクリプトを作成（作業ディレクトリを設定）
echo -e "${YELLOW}ラッパースクリプトを作成中...${NC}"
# 元の実行可能ファイルをバックアップ
mv "$APP_EXECUTABLE" "${APP_EXECUTABLE}.bin"

# ラッパースクリプトを作成
cat > "$APP_EXECUTABLE" <<'WRAPPER_EOF'
#!/bin/bash

# LocalSignTools ラッパースクリプト
# .appバンドルから実行された場合、作業ディレクトリをプロジェクトルートに設定

# .appバンドルの場所を取得
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_ROOT="$(dirname "$APP_DIR")"

# プロジェクトルートに移動
cd "$PROJECT_ROOT" || exit 1

# 実際の実行可能ファイルのパス（.appバンドル内のバイナリ）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTUAL_EXECUTABLE="$SCRIPT_DIR/SignTools.bin"

# 実行可能ファイルが存在するか確認
if [ ! -f "$ACTUAL_EXECUTABLE" ]; then
    osascript -e 'display dialog "SignTools.binが見つかりません。\n\nbuild_app.shを実行して.appバンドルを再構築してください。" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# ターミナルウィンドウを開いて実行
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$PROJECT_ROOT' && '$ACTUAL_EXECUTABLE'"
end tell
EOF
WRAPPER_EOF

chmod +x "$APP_EXECUTABLE"
echo -e "${GREEN}✓ ラッパースクリプト作成完了${NC}"
echo ""

echo -e "${GREEN}=== ビルド完了 ===${NC}"
echo ""
echo "以下の方法で実行できます："
echo "  1. Finderで ${APP_NAME}.app をダブルクリック"
echo "  2. ターミナルから: open ${APP_NAME}.app"
echo ""
echo "アプリケーションはターミナルウィンドウで起動し、"
echo "Webインターフェースが http://localhost:8080 で利用可能になります。"
