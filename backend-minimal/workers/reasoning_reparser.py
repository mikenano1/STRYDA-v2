#!/usr/bin/env python3
"""
GPT-5 Reasoning Trace Re-parser Worker

Periodically checks reasoning_responses table for GPT-5 traces with empty final_answer
and attempts to extract usable output when possible.

This allows STRYDA to automatically populate answers once GPT-5 models start returning
output fields or when new extraction patterns are discovered.
"""

import os
import json
import time
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BATCH_LIMIT = 10
WORKER_INTERVAL_SECONDS = 300  # 5 minutes

print(f"🔁 GPT-5 Reasoning Re-parser Worker Starting...")
print(f"   Database: {'✅ Configured' if DATABASE_URL else '❌ Missing'}")
print(f"   Batch size: {BATCH_LIMIT}")
print(f"   Interval: {WORKER_INTERVAL_SECONDS}s")

def extract_text_from_trace(trace: Dict[Any, Any]) -> str:
    """
    Try multiple known GPT-5/o1 output paths to extract final answer text.
    
    Args:
        trace: Full response.model_dump() JSON from GPT-5
        
    Returns:
        Extracted text string, or empty string if none found
    """
    if not trace or not isinstance(trace, dict):
        return ""
    
    try:
        # 1️⃣ GPT-5/o1 reasoning model output path (new style)
        if "output" in trace and trace["output"]:
            output_list = trace["output"]
            if isinstance(output_list, list) and output_list:
                parts = output_list[0].get("content", [])
                for part in parts:
                    if isinstance(part, dict):
                        part_type = part.get("type", "")
                        # Skip reasoning, extract only output
                        if part_type in ("reasoning", "thoughts"):
                            continue
                        if part_type in ("output_text", "text"):
                            text = part.get("text") or part.get("value") or ""
                            if text and text.strip():
                                return text.strip()
        
        # 2️⃣ Responses API compatibility (output_text field)
        if "output_text" in trace and trace["output_text"]:
            return str(trace["output_text"]).strip()
        
        # 3️⃣ Legacy standard path (choices[0].message.content)
        if "choices" in trace and trace["choices"]:
            choices = trace["choices"]
            if isinstance(choices, list) and choices:
                msg = choices[0].get("message", {})
                content = msg.get("content", "")
                
                # String content
                if isinstance(content, str) and content.strip():
                    return content.strip()
                
                # Array content
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict):
                            part_type = part.get("type", "")
                            if part_type in ("reasoning", "thoughts"):
                                continue
                            if part_type in ("text", "output_text") and "text" in part:
                                text_parts.append(part["text"])
                    
                    if text_parts:
                        return " ".join(text_parts).strip()
    
    except Exception as e:
        print(f"   ⚠️ extract_text_from_trace error: {e}")
    
    return ""

def reparse_pending_traces():
    """
    Query database for GPT-5 traces with NULL or empty final_answer,
    attempt to extract text, and update the database.
    """
    try:
        print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] Checking for pending GPT-5 traces...")
        
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Query for GPT-5 traces with empty final_answer
        cur.execute("""
            SELECT id, query, intent, model, reasoning_trace, final_answer, metadata
            FROM reasoning_responses
            WHERE model LIKE '%gpt-5%'
              AND (final_answer IS NULL OR final_answer = '')
            ORDER BY created_at DESC
            LIMIT %s;
        """, (BATCH_LIMIT,))
        
        rows = cur.fetchall()
        total_pending = len(rows)
        
        if total_pending == 0:
            print(f"   ✅ No pending traces to parse")
            cur.close()
            conn.close()
            return
        
        print(f"   📊 Found {total_pending} pending traces to parse")
        
        parsed_count = 0
        still_empty_count = 0
        
        for row in rows:
            row_id = row['id']
            trace = row['reasoning_trace']
            
            # Try to extract text from trace
            extracted_text = extract_text_from_trace(trace)
            
            if extracted_text and len(extracted_text) > 10:  # Minimum 10 chars to be valid
                # Update database with extracted text
                update_cur = conn.cursor()
                update_cur.execute("""
                    UPDATE reasoning_responses
                    SET final_answer = %s,
                        metadata = jsonb_set(
                            COALESCE(metadata, '{}'::jsonb),
                            '{reparsed_at}',
                            to_jsonb(NOW()::text)
                        )
                    WHERE id = %s;
                """, (extracted_text[:10000], row_id))  # Limit to 10k chars
                conn.commit()
                update_cur.close()
                
                parsed_count += 1
                print(f"   ✅ Parsed id={row_id}: {len(extracted_text)} chars extracted")
            else:
                still_empty_count += 1
                print(f"   ⚠️ Still no output for id={row_id} (model={row.get('model', 'unknown')})")
        
        cur.close()
        conn.close()
        
        # Summary
        print(f"\n   📈 Batch Summary:")
        print(f"      Parsed successfully: {parsed_count}")
        print(f"      Still empty: {still_empty_count}")
        print(f"      Total processed: {total_pending}")
        
    except Exception as e:
        print(f"   ❌ Re-parser error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """
    Main worker loop - runs continuously and re-parses traces every interval.
    """
    print(f"\n🚀 Worker started at {datetime.now()}")
    print(f"   Will check every {WORKER_INTERVAL_SECONDS} seconds\n")
    
    run_count = 0
    
    try:
        while True:
            run_count += 1
            print(f"{'='*60}")
            print(f"Run #{run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            reparse_pending_traces()
            
            print(f"\n💤 Sleeping for {WORKER_INTERVAL_SECONDS}s until next run...")
            time.sleep(WORKER_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Worker stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Worker crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Validate required environment variables
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not set (extraction patterns only, no AI assistance)")
    
    main()
