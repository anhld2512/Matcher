#!/usr/bin/env bash
#
# Matcher - UNINSTALL SCRIPT
#

echo "--- New Session: $(date) ---"
echo "Original execution path: $0"

# Detect if running inside .app bundle
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == *"/Contents/Resources" ]]; then
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    echo "Running inside App Bundle. Jumping to Project Root: $PROJECT_ROOT"
    cd "$PROJECT_ROOT"
else
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    echo "Running from scripts folder. Jumping to Project Root: $PROJECT_ROOT"
    cd "$PROJECT_ROOT"
fi

echo "Working directory: $(pwd)"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║      MATCHER - UNINSTALL & CLEANUP TOOL                  ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  CẢNH BÁO: Hành động này sẽ xóa toàn bộ dữ liệu bao gồm:"
echo "   - Toàn bộ Containers đang chạy"
echo "   - Toàn bộ Docker Images của ứng dụng"
echo "   - Toàn bộ Dữ liệu Database (Lịch sử, Đánh giá, Settings)"
echo "   - Toàn bộ Dữ liệu Redis"
echo ""
echo -ne "Bạn có chắc chắn muốn tiếp tục không? (y/N): "
read -r response

if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    echo -e "\nĐã hủy bỏ."
    exit 0
fi

echo ""
echo "[1/3] Dừng và xóa Containers, Networks, Volumes..."
if command -v docker-compose &> /dev/null; then
    docker-compose down -v --remove-orphans
else
    docker compose down -v --remove-orphans
fi

echo "[2/3] Xóa Docker Images..."
docker rmi cv-jd-matcher-web cv-jd-matcher-worker 2>/dev/null || true
docker image prune -f --filter "label=com.docker.compose.project=cv-jd-matcher" 2>/dev/null || true

echo "[3/3] Dọn dẹp file tạm..."
rm -rf app/__pycache__
rm -rf app/ai_providers/__pycache__
rm -f /tmp/cvjd_app.log

echo ""
echo "✅ GỠ CÀI ĐẶT HOÀN TẤT!"
echo "Thư mục ứng dụng vẫn được giữ lại tại: $(pwd)"
echo ""
echo "Nhấn Enter để thoát..."
read
