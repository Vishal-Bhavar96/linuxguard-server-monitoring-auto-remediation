#!/bin/bash
set -euo pipefail

# ==============================================================================
# LinuxGuard - System Health Check Script
# Displays CPU, RAM, Disk, Uptime, Network, and Systemd Service Health
# ==============================================================================

echo "=========================================================="
echo "          LINUXGUARD HOST HEALTH REPORT                   "
echo "  Timestamp: $(date '+%Y-%m-%d %H:%M:%S')                 "
echo "  Host:      $(hostname) ($(hostname -I 2>/dev/null || echo '127.0.0.1'))"
echo "=========================================================="

echo ""
echo "--- [1] SYSTEM UPTIME & LOAD AVERAGE ---"
uptime

echo ""
echo "--- [2] CPU UTILIZATION ---"
if command -v mpstat &>/dev/null; then
    mpstat 1 1
else
    top -b -n 1 | head -n 10
fi

echo ""
echo "--- [3] MEMORY ALLOCATION (RAM & SWAP) ---"
free -h

echo ""
echo "--- [4] FILESYSTEM & STORAGE SPACE ---"
df -h -x tmpfs -x devtmpfs -x squashfs

echo ""
echo "--- [5] NETWORK INTERFACES & ACTIVE LISTENING SOCKETS ---"
echo "Active IP Configuration:"
ip -brief address || ifconfig || true
echo ""
echo "Open TCP/UDP Sockets:"
ss -tuln || netstat -tuln || true

echo ""
echo "--- [6] CRITICAL SERVICES STATUS (systemd) ---"
SERVICES=("ssh" "nginx" "docker" "mysql" "postgresql")

for svc in "${SERVICES[@]}"; do
    if systemctl list-unit-files "${svc}*" &>/dev/null; then
        STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
        if [ "$STATUS" = "active" ]; then
            echo "  [✓ ACTIVE]   Service: $svc"
        else
            echo "  [✗ $STATUS] Service: $svc"
        fi
    else
        echo "  [- UNSET]    Service: $svc (Not Installed)"
    fi
done

echo ""
echo "=========================================================="
echo "             HEALTH CHECK REPORT COMPLETE                 "
echo "=========================================================="
