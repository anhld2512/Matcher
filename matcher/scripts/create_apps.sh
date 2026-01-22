#!/usr/bin/env bash
#
# Create macOS App with Custom Icon
#

# Ensure we are in the script directory
cd "$(dirname "$0")"
ICON_SOURCE="/Users/ducanh/Desktop/ListCV/cv-jd-matcher/image/iconApp.png"


# 1. Create Matcher App
osacompile -o "../Matcher.app" -e '
set scriptPath to POSIX path of (path to resource "start.sh")
tell application "Terminal"
    do script "\"" & scriptPath & "\""
    activate
end tell
'

# Copy start.sh INTO Matcher.app
cp "start.sh" "../Matcher.app/Contents/Resources/"
chmod +x "../Matcher.app/Contents/Resources/start.sh"

# 2. Create Uninstall App
osacompile -o "../Uninstall.app" -e '
set scriptPath to POSIX path of (path to resource "uninstall.sh")
tell application "Terminal"
    do script "\"" & scriptPath & "\""
    activate
end tell
'

# Copy uninstall.sh INTO Uninstall.app
cp "uninstall.sh" "../Uninstall.app/Contents/Resources/"
chmod +x "../Uninstall.app/Contents/Resources/uninstall.sh"

# 3. Process Icon
if [ -f "$ICON_SOURCE" ]; then
    
    # Create temporary iconset folder
    ICONSET_DIR="MyIcon.iconset"
    mkdir -p "$ICONSET_DIR"
    
    # Generate different sizes
    sips -z 16 16     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_16x16.png" > /dev/null
    sips -z 32 32     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_16x16@2x.png" > /dev/null
    sips -z 32 32     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_32x32.png" > /dev/null
    sips -z 64 64     "$ICON_SOURCE" --out "$ICONSET_DIR/icon_32x32@2x.png" > /dev/null
    sips -z 128 128   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_128x128.png" > /dev/null
    sips -z 256 256   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_128x128@2x.png" > /dev/null
    sips -z 256 256   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_256x256.png" > /dev/null
    sips -z 512 512   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_256x256@2x.png" > /dev/null
    sips -z 512 512   "$ICON_SOURCE" --out "$ICONSET_DIR/icon_512x512.png" > /dev/null
    sips -z 1024 1024 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_512x512@2x.png" > /dev/null
    
    # Convert to icns
    iconutil -c icns "$ICONSET_DIR"
    
    # Apply icon to BOTH apps
    cp MyIcon.icns "../Matcher.app/Contents/Resources/applet.icns"
    cp MyIcon.icns "../Uninstall.app/Contents/Resources/applet.icns"
    
    # Clean up
    rm -rf "$ICONSET_DIR"
    rm MyIcon.icns
    
    # Force refresh icon cache
    touch "../Matcher.app"
    touch "../Uninstall.app"
fi