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

# 1. Check & Install Docker
if ! docker info &> /dev/null; then
    echo "Docker is not running..."
    
    # Check if Docker app exists
    if [ ! -d "/Applications/Docker.app" ]; then
        echo "Docker app not found in /Applications"
        notify "Matcher" "⚠️ Docker chưa được cài đặt!"
        
        # Check if Homebrew is available
        if ! command -v brew &> /dev/null; then
             notify "Matcher" "⚠️ Homebrew chưa được cài đặt!"
             notify "Matcher" "⏳ Đang tự động cài Homebrew (Cần nhập mật khẩu)..."
             echo "Homebrew not found. Installing Homebrew..."
             echo "--- PLEASE ENTER PASSWORD IF ASKED ---"
             
             /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
             
             if [ $? -eq 0 ]; then
                 echo "Homebrew installed successfully."
                 # Add brew to PATH for this session (standard locations)
                 if [ -f "/opt/homebrew/bin/brew" ]; then
                     eval "$(/opt/homebrew/bin/brew shellenv)"
                 elif [ -f "/usr/local/bin/brew" ]; then
                     eval "$(/usr/local/bin/brew shellenv)"
                 fi
             else
                 notify "Lỗi" "❌ Cài đặt Homebrew thất bại."
                 exit 1
             fi
        fi

        # Install Docker via Homebrew
        notify "Matcher" "⏳ Đang thử cài Docker qua Homebrew..."
        brew install --cask docker
        
        if [ $? -eq 0 ]; then
            notify "Matcher" "✅ Cài đặt Docker thành công!"
            echo "Docker installed successfully via Homebrew."
        else
            echo "Homebrew install failed. Trying direct download..."
            notify "Matcher" "⚠️ Homebrew lỗi. Chuyển sang tải trực tiếp..."
            
            # DIRECT DOWNLOAD FALLBACK
            ARCH_NAME=$(uname -m)
            if [ "$ARCH_NAME" = "x86_64" ]; then
                DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
                echo "Detected Intel Architecture."
            elif [ "$ARCH_NAME" = "arm64" ]; then
                DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
                echo "Detected Apple Silicon (M1/M2/M3) Architecture."
            else
                notify "Lỗi" "❌ Không nhận diện được CPU: $ARCH_NAME"
                exit 1
            fi
            
            # Download
            notify "Matcher" "⬇️ Đang tải Docker.dmg ($ARCH_NAME)..."
            curl -L "$DOCKER_URL" -o /tmp/Docker.dmg
            
            if [ $? -ne 0 ]; then
                notify "Lỗi" "❌ Tải xuống thất bại."
                open "https://docs.docker.com/desktop/mac/install/"
                exit 1
            fi
            
            # Install
            notify "Matcher" "💿 Đang cài đặt Docker (Cần mật khẩu)..."
            echo "Mounting DMG..."
            hdiutil attach /tmp/Docker.dmg -nobrowse -mountpoint /Volumes/Docker
            
            echo "Copying to Applications..."
            # Use AppleScript to ask for Admin privileges for copying AND fixing permissions
            # We chain commands to ensure it's done with root privs
            osascript -e 'do shell script "cp -R /Volumes/Docker/Docker.app /Applications/ && xattr -d -r com.apple.quarantine /Applications/Docker.app" with administrator privileges'
            
            echo "Unmounting..."
            hdiutil detach /Volumes/Docker
            rm /tmp/Docker.dmg
            
            # Force register with LaunchServices so "open -a Docker" works immediately
            /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/Docker.app
            
            if [ -d "/Applications/Docker.app" ]; then
                 notify "Matcher" "✅ Cài đặt Docker thành công!"
            else
                 notify "Lỗi" "❌ Cài đặt thất bại."
                 open "https://docs.docker.com/desktop/mac/install/"
                 exit 1
            fi
        fi
    fi

    # Start Docker Desktop
    # Start Docker Desktop
    echo "Starting Docker..."
    # Attempt to open Docker using absolute path to avoid LaunchServices cache issues
    open /Applications/Docker.app
    
    # Wait for Docker to be ready
    echo "Waiting for Docker to initialize..."
    notify "Matcher" "⏳ Đang khởi động Docker ngầm..."
    
    MAX_WAIT=300
    COUNT=0
    DOCKER_READY=false
    
    while [ $COUNT -lt $MAX_WAIT ]; do
        if docker info &> /dev/null; then
            DOCKER_READY=true
            break
        fi
        
        # Every 5 seconds, ensure Docker is actually open (force bring to front/launch)
        # This helps if the first 'open' command was ignored or if user accidentally closed it
        if [ $((COUNT % 5)) -eq 0 ]; then
             echo "Ping: Ensuring Docker is running..."
             open -g /Applications/Docker.app
        fi
        
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    if [ "$DOCKER_READY" = true ]; then
        echo "Docker is ready."
        # HIDE Docker Window now that it IS running
        osascript -e 'tell application "System Events" to set visible of process "Docker" to false'
    else
        notify "Lỗi" "❌ Docker chưa sẵn sàng. Vui lòng kiểm tra ứng dụng Docker."
        # Don't exit, maybe it's just slow. Let it try to run compose.
    fi
    echo ""
    
    if [ $COUNT -ge $MAX_WAIT ]; then
        notify "Lỗi Khởi Động" "❌ Docker không phản hồi. Vui lòng kiểm tra."
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
