#!/usr/bin/env python3
"""
STRYDA Big Brain - Full Suite Batch Processor
Downloads, extracts, and ingests all GIB and James Hardie documents
with Vision-enabled diagram captioning
"""

import os
import sys
import json
import subprocess
from datetime import datetime

sys.path.insert(0, '/app/backend-minimal')
sys.path.insert(0, '/app/data/scrapers')
sys.path.insert(0, '/app/data/processing')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')


def run_command(cmd: str, description: str, timeout: int = 300) -> bool:
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.stdout:
            print(result.stdout[-2000:])  # Last 2000 chars
        
        if result.returncode != 0:
            print(f"⚠️ Warning - exit code {result.returncode}")
            if result.stderr:
                print(f"Stderr: {result.stderr[-500:]}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("="*70)
    print("🧠 STRYDA Big Brain - FULL SUITE BATCH PROCESSOR")
    print("="*70)
    print(f"⏰ Started: {datetime.now().isoformat()}")
    
    results = {
        "started_at": datetime.now().isoformat(),
        "steps": []
    }
    
    # Step 1: Fetch James Hardie Full Suite
    print("\n\n" + "🔵"*35)
    print("PHASE 1: JAMES HARDIE FULL SUITE")
    print("🔵"*35)
    
    success = run_command(
        "cd /app/data/scrapers && python3 hardie_connector_v2.py",
        "Downloading James Hardie documents...",
        timeout=300
    )
    results["steps"].append({"name": "hardie_fetch", "success": success})
    
    # Step 2: Fetch GIB Full Suite
    print("\n\n" + "🟢"*35)
    print("PHASE 2: GIB FULL SUITE")
    print("🟢"*35)
    
    success = run_command(
        "cd /app/data/scrapers && python3 gib_connector_v2.py",
        "Downloading GIB documents...",
        timeout=300
    )
    results["steps"].append({"name": "gib_fetch", "success": success})
    
    # Step 3: Process James Hardie with Vision
    print("\n\n" + "👁️"*35)
    print("PHASE 3: VISION PROCESSING - JAMES HARDIE")
    print("👁️"*35)
    
    success = run_command(
        """cd /app/data/processing && python3 pdf_chunker_v2.py \
            --input /app/data/ingestion/B_Enclosure/Wall_Cladding/James_Hardie \
            --output /app/data/processing/hardie_full \
            --manifest /app/data/ingestion/B_Enclosure/Wall_Cladding/James_Hardie/manifest.json""",
        "Vision processing James Hardie PDFs...",
        timeout=600
    )
    results["steps"].append({"name": "hardie_vision", "success": success})
    
    # Step 4: Process GIB with Vision
    print("\n\n" + "👁️"*35)
    print("PHASE 4: VISION PROCESSING - GIB")
    print("👁️"*35)
    
    success = run_command(
        """cd /app/data/processing && python3 pdf_chunker_v2.py \
            --input /app/data/ingestion/C_Interiors/Plasterboard_Linings/GIB \
            --output /app/data/processing/gib_full \
            --manifest /app/data/ingestion/C_Interiors/Plasterboard_Linings/GIB/manifest.json""",
        "Vision processing GIB PDFs...",
        timeout=600
    )
    results["steps"].append({"name": "gib_vision", "success": success})
    
    # Step 5: Ingest James Hardie
    print("\n\n" + "💾"*35)
    print("PHASE 5: INGESTION - JAMES HARDIE")
    print("💾"*35)
    
    success = run_command(
        """cd /app/data/processing && python3 ingestor.py \
            --chunks /app/data/processing/hardie_full/chunks.json \
            --brand "James Hardie" \
            --category "B_Enclosure" \
            --doc-type "Installation_Guide" \
            --product-family "James Hardie Products" \
            --trade "cladding" \
            --source "James Hardie Full Suite" \
            --priority 85""",
        "Ingesting James Hardie chunks...",
        timeout=300
    )
    results["steps"].append({"name": "hardie_ingest", "success": success})
    
    # Step 6: Ingest GIB
    print("\n\n" + "💾"*35)
    print("PHASE 6: INGESTION - GIB")
    print("💾"*35)
    
    success = run_command(
        """cd /app/data/processing && python3 ingestor.py \
            --chunks /app/data/processing/gib_full/chunks.json \
            --brand "GIB" \
            --category "C_Interiors" \
            --doc-type "Installation_Guide" \
            --product-family "GIB Products" \
            --trade "interior_linings" \
            --source "GIB Full Suite" \
            --priority 85""",
        "Ingesting GIB chunks...",
        timeout=300
    )
    results["steps"].append({"name": "gib_ingest", "success": success})
    
    # Summary
    results["completed_at"] = datetime.now().isoformat()
    
    print("\n\n" + "="*70)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*70)
    
    for step in results["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"   {status} {step['name']}")
    
    success_count = sum(1 for s in results["steps"] if s["success"])
    print(f"\n   Total: {success_count}/{len(results['steps'])} successful")
    
    # Save results
    results_file = "/app/data/processing/batch_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved to: {results_file}")
    print(f"⏰ Completed: {datetime.now().isoformat()}")
    
    return all(s["success"] for s in results["steps"])


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
