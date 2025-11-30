#!/usr/bin/env python3
"""
List all objects in Supabase Storage 'pdfs' bucket
"""

from supabase import create_client, Client

# Supabase config
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMjM4NDg2OCwiZXhwIjoyMDQ3OTYwODY4fQ.IWxBqO5vSPxBkN-TQnH7yS-j7q1SwY-RvdBzqVmOCMM"

print("="*80)
print("SUPABASE STORAGE - 'pdfs' BUCKET LISTING")
print("="*80)

try:
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # List all buckets first
    print("\n1. Available Buckets:")
    try:
        buckets = supabase.storage.list_buckets()
        for bucket in buckets:
            print(f"   - {bucket.name} (id: {bucket.id})")
    except Exception as e:
        print(f"   ❌ Error listing buckets: {e}")
    
    # List objects in 'pdfs' bucket
    print("\n2. Objects in 'pdfs' bucket:")
    try:
        files = supabase.storage.from_('pdfs').list(
            path='',
            options={'limit': 200}
        )
        
        if not files:
            print("   ⚠️  Bucket is empty or doesn't exist")
        else:
            print(f"   ✅ Found {len(files)} objects\n")
            
            total_size = 0
            for idx, file in enumerate(files, 1):
                name = file.get('name', 'unknown')
                size = file.get('metadata', {}).get('size', 0) if isinstance(file.get('metadata'), dict) else 0
                
                # Try alternate size locations
                if size == 0:
                    size = file.get('size', 0)
                
                total_size += size
                
                size_mb = size / (1024 * 1024) if size > 0 else 0
                print(f"   [{idx}] {name}")
                print(f"       Size: {size:,} bytes ({size_mb:.2f} MB)")
            
            print(f"\n   Total files: {len(files)}")
            print(f"   Total size: {total_size:,} bytes ({total_size/(1024*1024):.2f} MB)")
            
    except Exception as e:
        print(f"   ❌ Error listing objects: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
