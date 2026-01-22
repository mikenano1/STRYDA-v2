#!/usr/bin/env python3
"""EMERGENCY RESUME - Starting from file 440 with unbuffered output"""
import sys
sys.stdout = sys.stderr = open('/app/total_lockdown.log', 'a', buffering=1)  # Line buffered

import os
import json
import re
import csv
import hashlib
import psycopg2
from datetime import datetime
from pathlib import Path
import fitz
import requests

# Load env
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

from supabase import create_client
import openai

DATABASE_URL = os.getenv('DATABASE_URL')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
BUCKET = "product-library"
REGISTER_PATH = "/app/protocols/Compliance_Master_Register.csv"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

START_FROM = 500  # 0-indexed, so file 501

def download_pdf(path):
    try:
        signed = supabase.storage.from_(BUCKET).create_signed_url(path, 300)
        url = signed.get('signedURL')
        if not url: return None
        r = requests.get(url, timeout=60)
        return r.content if r.status_code == 200 else None
    except: return None

def extract_text(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "".join(p.get_text() for p in doc)
        pages = len(doc)
        doc.close()
        # Remove NUL characters
        text = text.replace('\x00', '')
        return text, pages
    except: return "", 0

def get_embedding(text):
    try:
        r = openai_client.embeddings.create(model="text-embedding-3-small", input=text[:8000], dimensions=1536)
        return r.data[0].embedding
    except: return None

def detect_sector(path):
    p = path.lower()
    if 'roofing' in p or 'roof' in p: return 'roofing'
    if 'window' in p or 'joinery' in p: return 'windows'
    if 'fastener' in p or 'screw' in p: return 'fasteners'
    if 'membrane' in p or 'wrap' in p: return 'membranes'
    if 'timber' in p or 'wood' in p: return 'timber'
    if 'insulation' in p or 'batts' in p: return 'insulation'
    if 'cladding' in p: return 'cladding'
    if 'compliance' in p or 'nzbc' in p: return 'compliance'
    return 'general'

def detect_compliance(text, fname):
    has_bpir = 'bpir' in text.lower() or 'building product information' in text.lower()
    has_codemark = bool(re.search(r'codemark|CM[\s\-]?\d{5}', text, re.I))
    has_branz = bool(re.search(r'branz\s+appraisal|appraisal\s+\d{3,4}', text, re.I))
    if has_codemark or has_branz: return 'CERTIFIED', has_bpir
    if has_bpir: return 'BPIR_ONLY', has_bpir
    return 'MISSING', has_bpir

print(f"\n{'='*70}", flush=True)
print(f"⚔️ EMERGENCY RESUME - Starting from file {START_FROM+1}", flush=True)
print(f"Time: {datetime.now().isoformat()}", flush=True)
print(f"{'='*70}\n", flush=True)

with open('/app/full_library_audit_files.json') as f:
    all_files = json.load(f)

register = []
processed = set()
stats = {'ingested': 0, 'chunks': 0, 'missing': 0, 'errors': 0}

for i, finfo in enumerate(all_files[START_FROM:], START_FROM+1):
    fname = finfo['name']
    path = finfo['path']
    brand = path.split('/')[1].replace('_', ' ') if len(path.split('/')) > 1 else 'Unknown'
    
    print(f"[{i}/4184] {fname[:55]}...", flush=True)
    
    pdf = download_pdf(path)
    if not pdf:
        print(f"      ⏭️ Skip (download failed)", flush=True)
        continue
    
    text, pages = extract_text(pdf)
    if not text:
        print(f"      ⏭️ Skip (no text)", flush=True)
        continue
    
    h = hashlib.sha256(text.encode()).hexdigest()[:16]
    if h in processed:
        print(f"      ⏭️ Skip (duplicate)", flush=True)
        continue
    processed.add(h)
    
    sector = detect_sector(path)
    status, has_bpir = detect_compliance(text, fname)
    
    register.append({'brand': brand, 'product': fname[:100], 'sector': sector, 'status': status})
    
    if status == 'MISSING':
        stats['missing'] += 1
        print(f"      ⚠️ MISSING_DOCS: {brand[:20]} - {fname[:30]}", flush=True)
    
    # Chunk and ingest
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{h}%",))
        if cur.fetchone():
            conn.close()
            continue
        
        chunks = [text[j:j+1500] for j in range(0, len(text), 1300)]
        inserted = 0
        
        for ci, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            if not emb: continue
            
            cur.execute("""
                INSERT INTO documents (content, source, page, embedding, page_hash, trade, priority, is_active, doc_type)
                VALUES (%s, %s, %s, %s::vector, %s, %s, 80, true, 'Product_Document')
            """, (chunk, f"{brand} - {fname.replace('.pdf','')}", ci+1, emb, f"{h}_{ci}", sector))
            inserted += 1
        
        if inserted:
            conn.commit()
            stats['ingested'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks", flush=True)
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}", flush=True)
        stats['errors'] += 1
        conn.rollback()
    finally:
        conn.close()
    
    if i % 100 == 0:
        print(f"\n   📊 CHECKPOINT: {i}/4184 | Chunks: {stats['chunks']} | Missing: {stats['missing']}\n", flush=True)

# Write register
print(f"\n{'='*70}", flush=True)
print(f"📋 Writing Compliance Register...", flush=True)
with open(REGISTER_PATH, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['brand','product','sector','status'])
    w.writeheader()
    w.writerows(register)

print(f"✅ COMPLETE: {stats['ingested']} files, {stats['chunks']} chunks, {stats['missing']} MISSING_DOCS", flush=True)
print(f"{'='*70}", flush=True)
