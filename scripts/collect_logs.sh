#!/bin/bash
set -euo pipefail

# ==============================================================================
# LinuxGuard - System & Security Log Collector
# ==============================================================================

OUTPUT_DIR="./logs_archive_$(date '+%Y%m%d_%H%M%S')"
mkdir -p "$OUTPUT_DIR"

echo "=========================================================="
echo "          LINUXGUARD LOG COLLECTION UTILITY               "
echo "  Target Output: $OUTPUT_DIR                              "
echo "=========================================================="

echo "[1/4] Collecting kernel & systemd error journal..."
if command -v journalctl &>/dev/null; then
    journalctl -p err..alert -n 200 --no-pager > "$OUTPUT_DIR/systemd_errors.log" 2>&1 || true
fi

echo "[2/4] Collecting authentication and SSH logs..."
if [ -f "/var/log/auth.log" ]; then
    tail -n 300 /var/log/auth.log > "$OUTPUT_DIR/auth.log" 2>&1 || true
elif command -v journalctl &>/dev/null; then
    journalctl -u ssh -n 300 --no-pager > "$OUTPUT_DIR/ssh_journal.log" 2>&1 || true
fi

echo "[3/4] Collecting web & database service logs..."
if [ -d "/var/log/nginx" ]; then
    tail -n 200 /var/log/nginx/error.log > "$OUTPUT_DIR/nginx_error.log" 2>&1 || true
fi

if [ -d "/var/log/mysql" ]; then
    tail -n 200 /var/log/mysql/error.log > "$OUTPUT_DIR/mysql_error.log" 2>&1 || true
fi

echo "[4/4] Generating system telemetry manifest..."
{
    echo "--- UPTIME ---"
    uptime
    echo "--- FREE MEMORY ---"
    free -m
    echo "--- DISK SPACE ---"
    df -h
} > "$OUTPUT_DIR/system_telemetry_summary.txt"

echo "=========================================================="
echo "  Logs successfully archived to: $OUTPUT_DIR"
echo "=========================================================="
