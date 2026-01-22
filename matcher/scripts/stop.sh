#!/usr/bin/env bash
#
# Matcher - STOP SCRIPT
#

cd "$(dirname "$0")"

# Check docker compose
if command -v docker-compose &> /dev/null; then
    docker-compose down
else
    docker compose down
fi

echo "✅ Đã dừng ứng dụng."
# Close browser tab if possible? (Hard to do cross-platform/browser)
