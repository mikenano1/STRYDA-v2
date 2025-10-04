#!/usr/bin/env python3
"""
Monitor ingestion progress and provide status updates
"""

import os
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_progress():
    """Check current ingestion progress"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get current counts
            cur.execute("""
                SELECT source, COUNT(*) as count, MAX(page) as max_page
                FROM documents 
                GROUP BY source 
                ORDER BY source;
            """)
            sources = cur.fetchall()
            
            current_time = time.strftime("%H:%M:%S")
            print(f"\n📊 PROGRESS UPDATE - {current_time}")
            print("=" * 40)
            
            total = 0
            for source in sources:
                count = source['count']
                max_page = source['max_page']
                total += count
                
                # Calculate progress for expected targets
                if source['source'] == 'NZ Building Code':
                    progress = (count / 226) * 100
                    print(f"• {source['source']}: {count}/226 docs ({progress:.1f}%) - up to page {max_page}")
                elif source['source'] == 'NZ Metal Roofing':
                    progress = (count / 593) * 100
                    print(f"• {source['source']}: {count}/593 docs ({progress:.1f}%) - up to page {max_page}")
                else:
                    print(f"• {source['source']}: {count} docs - up to page {max_page}")
            
            print(f"\nTotal: {total} documents")
            
            # Estimate completion
            building_code_complete = any(s['source'] == 'NZ Building Code' and s['count'] >= 220 for s in sources)
            metal_roofing_complete = any(s['source'] == 'NZ Metal Roofing' and s['count'] >= 580 for s in sources)
            
            if building_code_complete and metal_roofing_complete:
                print("✅ INGESTION APPEARS COMPLETE!")
                return True
            else:
                status = []
                if not building_code_complete:
                    status.append("Building Code continuing")
                if not metal_roofing_complete:
                    status.append("Metal Roofing continuing")
                print(f"🔄 Status: {', '.join(status)}")
                return False
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Progress check failed: {e}")
        return None

if __name__ == "__main__":
    print("🔍 STRYDA-v2 INGESTION MONITOR")
    
    while True:
        is_complete = check_progress()
        
        if is_complete:
            print("\n🎉 FULL INGESTION COMPLETED!")
            break
        elif is_complete is None:
            print("❌ Monitor failed")
            break
        
        # Wait 30 seconds before next check
        time.sleep(30)