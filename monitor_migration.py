#!/usr/bin/env python3
"""
MIGRATION MONITOR - Check status of Full Library Migration V2.0
Usage: python3 /app/monitor_migration.py
"""

import subprocess
import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

def main():
    print("=" * 70)
    print(f"MIGRATION MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Check if process is running
    result = subprocess.run(['pgrep', '-f', 'full_library_migration'], capture_output=True)
    is_running = result.returncode == 0
    
    # Get log progress
    try:
        with open('/app/migration_v2.log', 'r') as f:
            lines = f.readlines()
        
        progress_lines = [l for l in lines if l.startswith('[')]
        if progress_lines:
            last_progress = progress_lines[-1].strip()
            files_processed = len(progress_lines)
        else:
            last_progress = "Not started"
            files_processed = 0
        
        chunks_created = sum(1 for l in lines if '✅' in l)
        errors = sum(1 for l in lines if '❌' in l)
    except:
        last_progress = "Log not found"
        files_processed = 0
        chunks_created = 0
        errors = 0
    
    print(f"\n📋 STATUS: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}")
    print(f"📂 Files Processed: {files_processed} / 4272 ({100*files_processed/4272:.1f}%)")
    print(f"📄 Last: {last_progress[:70]}")
    print(f"✅ Successful Ingestions: {chunks_created}")
    print(f"❌ Errors: {errors}")
    
    # Database stats
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        cur.execute('SELECT COUNT(*) FROM documents;')
        total = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM documents WHERE page_hash IS NOT NULL;')
        v2_compliant = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM documents WHERE created_at > NOW() - INTERVAL '10 minutes';")
        recent = cur.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 DATABASE:")
        print(f"   Total Chunks: {total}")
        print(f"   V2.0 Compliant: {v2_compliant} ({100*v2_compliant/total:.1f}%)")
        print(f"   Created (last 10 min): {recent}")
    except Exception as e:
        print(f"\n❌ Database error: {e}")
    
    # If completed, show final stats
    if not is_running and files_processed > 0:
        print("\n" + "=" * 70)
        print("🏁 MIGRATION APPEARS COMPLETE")
        print("=" * 70)
        print("\nCheck final report in /app/migration_v2.log")

if __name__ == "__main__":
    main()
