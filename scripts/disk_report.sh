#!/bin/bash
set -euo pipefail

# ==============================================================================
# LinuxGuard - Disk Space & Large Directory Diagnostic Report
# ==============================================================================

echo "=========================================================="
echo "          LINUXGUARD STORAGE & DISK REPORT                "
echo "  Timestamp: $(date '+%Y-%m-%d %H:%M:%S')                 "
echo "=========================================================="

echo ""
echo "--- [1] MOUNTED FILESYSTEM CAPACITY ---"
df -hT -x tmpfs -x devtmpfs -x squashfs

echo ""
echo "--- [2] INODE UTILIZATION ---"
df -ih -x tmpfs -x devtmpfs -x squashfs

echo ""
echo "--- [3] TOP 10 LARGEST DIRECTORIES IN /var/log ---"
if [ -d "/var/log" ]; then
    du -sh /var/log/* 2>/dev/null | sort -rh | head -n 10 || true
else
    echo "Directory /var/log not accessible."
fi

echo ""
echo "--- [4] TEMPORARY FILE DUMPS (/tmp) ---"
if [ -d "/tmp" ]; then
    du -sh /tmp 2>/dev/null || true
fi

echo ""
echo "=========================================================="
echo "              DISK REPORT COMPLETE                        "
echo "=========================================================="
