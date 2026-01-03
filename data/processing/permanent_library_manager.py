#!/usr/bin/env python3
"""
STRYDA Big Brain - Permanent PDF Library Manager
Manages PDF storage in Supabase Storage for persistence across container restarts.

Storage Structure:
  product-library/
  ├── A_Structure/
  ├── B_Enclosure/
  │   └── James_Hardie/
  ├── C_Interiors/
  │   └── GIB/
  ├── F_Manufacturers/
  │   └── Fasteners/
  │       ├── Ecko/
  │       ├── Pryda/
  │       ├── Zenith/
  │       └── ...
  └── Standards/
      └── NZS_3604/
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client, Client

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = "product-library"
LOCAL_INGESTION_PATH = "/app/data/ingestion"


class PermanentLibraryManager:
    """Manages permanent PDF storage in Supabase"""
    
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.bucket = self.supabase.storage.from_(BUCKET_NAME)
    
    def upload_pdf(self, local_path: str, remote_path: str) -> Dict:
        """
        Upload a single PDF to permanent storage.
        
        Args:
            local_path: Local file path (e.g., /app/data/ingestion/F_Manufacturers/Fasteners/Ecko/catalogue.pdf)
            remote_path: Storage path (e.g., F_Manufacturers/Fasteners/Ecko/catalogue.pdf)
        
        Returns:
            Dict with upload result
        """
        try:
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase Storage
            result = self.bucket.upload(
                path=remote_path,
                file=file_data,
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            
            file_size = len(file_data) / 1024 / 1024  # MB
            print(f"   ✅ Uploaded: {remote_path} ({file_size:.1f} MB)")
            
            return {
                "success": True,
                "path": remote_path,
                "size_mb": file_size
            }
            
        except Exception as e:
            print(f"   ❌ Failed: {remote_path} - {e}")
            return {
                "success": False,
                "path": remote_path,
                "error": str(e)
            }
    
    def upload_directory(self, local_dir: str, remote_prefix: str = "") -> Dict:
        """
        Upload all PDFs from a local directory to permanent storage.
        Preserves folder structure.
        """
        results = {
            "uploaded": 0,
            "failed": 0,
            "total_size_mb": 0,
            "files": []
        }
        
        local_path = Path(local_dir)
        
        for pdf_file in local_path.rglob("*.pdf"):
            # Calculate remote path preserving structure
            relative_path = pdf_file.relative_to(local_path)
            remote_path = f"{remote_prefix}/{relative_path}" if remote_prefix else str(relative_path)
            remote_path = remote_path.replace("\\", "/")  # Windows compatibility
            
            result = self.upload_pdf(str(pdf_file), remote_path)
            results["files"].append(result)
            
            if result["success"]:
                results["uploaded"] += 1
                results["total_size_mb"] += result.get("size_mb", 0)
            else:
                results["failed"] += 1
        
        return results
    
    def list_files(self, path: str = "") -> List[Dict]:
        """List all files in a storage path"""
        try:
            files = self.bucket.list(path)
            return files
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def download_pdf(self, remote_path: str, local_path: str) -> bool:
        """Download a PDF from permanent storage"""
        try:
            data = self.bucket.download(remote_path)
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(data)
            
            print(f"   ✅ Downloaded: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            return False
    
    def get_public_url(self, remote_path: str) -> str:
        """Get a signed URL for a file (valid for 1 hour)"""
        try:
            result = self.bucket.create_signed_url(remote_path, 3600)
            return result.get("signedURL", "")
        except Exception as e:
            print(f"Error getting URL: {e}")
            return ""


def migrate_existing_library():
    """Migrate all existing PDFs to permanent storage"""
    
    print("=" * 60)
    print("🚀 MIGRATING EXISTING PDFs TO PERMANENT STORAGE")
    print("=" * 60)
    print(f"   Source: {LOCAL_INGESTION_PATH}")
    print(f"   Destination: Supabase Storage ({BUCKET_NAME})")
    print()
    
    manager = PermanentLibraryManager()
    
    # Categories to migrate
    categories = [
        "A_Structure",
        "B_Enclosure", 
        "C_Interiors",
        "D_Landscaping",
        "E_Specialty",
        "F_Manufacturers",
        "G_Merchants",
    ]
    
    total_uploaded = 0
    total_failed = 0
    total_size = 0
    
    for category in categories:
        category_path = os.path.join(LOCAL_INGESTION_PATH, category)
        if not os.path.exists(category_path):
            continue
        
        # Count PDFs
        pdf_count = sum(1 for _ in Path(category_path).rglob("*.pdf"))
        if pdf_count == 0:
            continue
        
        print(f"\n📁 {category}: {pdf_count} PDFs")
        print("-" * 40)
        
        results = manager.upload_directory(category_path, category)
        
        total_uploaded += results["uploaded"]
        total_failed += results["failed"]
        total_size += results["total_size_mb"]
    
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"   ✅ Uploaded: {total_uploaded} files")
    print(f"   ❌ Failed: {total_failed} files")
    print(f"   💾 Total size: {total_size:.1f} MB")
    print(f"\n   🗄️ Permanent Storage: {SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/")
    
    return total_failed == 0


def upload_manual_files(local_dir: str, brand: str, category: str = "F_Manufacturers/Fasteners"):
    """Upload manually provided files with proper categorization"""
    
    print("=" * 60)
    print(f"📤 UPLOADING MANUAL FILES: {brand}")
    print("=" * 60)
    
    manager = PermanentLibraryManager()
    remote_prefix = f"{category}/{brand}"
    
    results = manager.upload_directory(local_dir, remote_prefix)
    
    print(f"\n✅ Uploaded {results['uploaded']} files to: {remote_prefix}/")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Permanent PDF Library Manager")
    parser.add_argument("--migrate", action="store_true", help="Migrate all existing PDFs")
    parser.add_argument("--upload", type=str, help="Upload a directory")
    parser.add_argument("--brand", type=str, help="Brand name for upload")
    parser.add_argument("--list", type=str, nargs="?", const="", help="List files in path")
    
    args = parser.parse_args()
    
    if args.migrate:
        migrate_existing_library()
    elif args.upload and args.brand:
        upload_manual_files(args.upload, args.brand)
    elif args.list is not None:
        manager = PermanentLibraryManager()
        files = manager.list_files(args.list)
        print(f"Files in '{args.list or 'root'}':")
        for f in files:
            print(f"   • {f.get('name', f)}")
    else:
        print("Usage:")
        print("  --migrate           Migrate all existing PDFs to permanent storage")
        print("  --upload DIR --brand NAME   Upload a directory with brand tag")
        print("  --list [PATH]       List files in storage")
