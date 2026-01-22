#!/usr/bin/env bash
#
# Matcher - VISIBLE STARTUP
#

echo "--- New Session: $(date) ---"
echo "Original execution path: $0"

# Detect if running inside .app bundle
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == *"/Contents/Resources" ]]; then
    # We are inside the App. Navigate up to Project Root.
    # .app/Contents/Resources -> .app/Contents -> .app -> ProjectRoot
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    echo "Running inside App Bundle. Jumping to Project Root: $PROJECT_ROOT"
    cd "$PROJECT_ROOT"
else
    # Regular run (assuming script is in scripts/ folder)
    # . -> scripts -> ProjectRoot
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    echo "Running from scripts folder. Jumping to Project Root: $PROJECT_ROOT"
    cd "$PROJECT_ROOT"
fi

echo "Working directory: $(pwd)"

# Function to text notification
notify() {
    local title="$1"
    local message="$2"
    osascript -e "display notification \"$message\" with title \"$title\""
}

notify "Matcher" "🚀 Đang khởi động..."

# 1. Check Docker
if ! docker info &> /dev/null; then
    echo "Docker not running. Starting Docker..."
    notify "Matcher" "⏳ Đang bật Docker Desktop..."
    
    # Start Docker Desktop
    open -a Docker
    
    # Attempt to hide Docker Dashboard immediately using AppleScript
    osascript -e '
    delay 2
    tell application "System Events"
        set visible of process "Docker" to false
    end tell' &
    
    # Wait for Docker
    MAX_WAIT=120
    COUNT=0
    while [ $COUNT -lt $MAX_WAIT ]; do
        if docker info &> /dev/null; then
            echo "Docker started successfully."
            break
        fi
        sleep 2
        COUNT=$((COUNT + 2))
    done
    
    if [ $COUNT -ge $MAX_WAIT ]; then
        notify "Lỗi Khởi Động" "❌ Docker không phản hồi. Vui lòng mở thủ công."
        exit 1
    fi
fi

# 2. Check & Clean Services
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# 3. Start Services
echo "Starting services..."
notify "Matcher" "⚙️ Đang khởi chạy Services..."

# Run detached
$COMPOSE_CMD up -d --remove-orphans

# 4. Wait for Web Server
echo "Waiting for web server..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        break
    fi
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    notify "Lỗi Khởi Động" "❌ Không thể kết nối Web Server. Xem app.log để biết chi tiết."
    exit 1
fi

# 5. Success
echo "App is ready!"
notify "Matcher" "✅ Ứng dụng đã sẵn sàng!"

# Open Browser
open http://localhost:8000
