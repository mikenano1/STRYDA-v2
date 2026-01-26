#!/bin/bash
# STRYDA Nightly Auditor Cron Setup
# Run this script once to install the cron job

# Add cron job for 2:00 AM daily
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/python3 /app/services/nightly_auditor.py >> /app/logs/cron.log 2>&1") | crontab -

echo "✅ Nightly Auditor cron job installed"
echo "   Schedule: Every day at 02:00 AM"
echo "   Script: /app/services/nightly_auditor.py"
echo "   Log: /app/logs/nightly_mastery.log"

# Verify
echo ""
echo "Current crontab:"
crontab -l
