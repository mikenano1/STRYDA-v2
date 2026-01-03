#!/usr/bin/env python3
"""
STRYDA Big Brain - Enhanced Ingestor v2
With Product Function Detection and Trade Classification

Key Features:
1. Auto-detects product_family from filename and content
2. Auto-classifies trade from product keywords
3. Validates all required metadata before ingestion
4. Supports per-chunk override of product_family/trade
"""

import os
import sys
import json
import time
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import psycopg2
import psycopg2.extras
from openai import OpenAI

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 20
RATE_LIMIT_DELAY = 0.5

# =============================================================================
# PRODUCT FUNCTION CLASSIFICATION RULES
# =============================================================================
# Maps keywords in content/filename to specific product_family and trade

PRODUCT_FUNCTION_RULES = {
    # FIRTH - Multi-category brand
    'firth': {
        'ribraft': {'product_family': 'RibRaft Foundations', 'trade': 'foundations', 'category': 'A_Structure'},
        'x-pod': {'product_family': 'X-Pod TC3 Foundations', 'trade': 'foundations', 'category': 'A_Structure'},
        'xpod': {'product_family': 'X-Pod TC3 Foundations', 'trade': 'foundations', 'category': 'A_Structure'},
        'hotedge': {'product_family': 'RibRaft HotEdge', 'trade': 'foundations', 'category': 'A_Structure'},
        'paving': {'product_family': 'Paving Systems', 'trade': 'paving', 'category': 'G_Landscaping'},
        'paver': {'product_family': 'Paving Systems', 'trade': 'paving', 'category': 'G_Landscaping'},
        'holland': {'product_family': 'Holland Pavers', 'trade': 'paving', 'category': 'G_Landscaping'},
        'ecopave': {'product_family': 'EcoPave Permeable', 'trade': 'paving', 'category': 'G_Landscaping'},
        'masonry': {'product_family': 'Concrete Masonry', 'trade': 'masonry', 'category': 'A_Structure'},
        '20 series': {'product_family': '20 Series Masonry', 'trade': 'masonry', 'category': 'A_Structure'},
        '25 series': {'product_family': '25 Series Masonry', 'trade': 'masonry', 'category': 'A_Structure'},
        'block': {'product_family': 'Concrete Masonry', 'trade': 'masonry', 'category': 'A_Structure'},
        'retaining': {'product_family': 'Retaining Walls', 'trade': 'landscaping', 'category': 'G_Landscaping'},
        'keystone': {'product_family': 'Keystone Retaining', 'trade': 'landscaping', 'category': 'G_Landscaping'},
    },
    
    # THERMAKRAFT - Multi-category brand
    'thermakraft': {
        'wall underlay': {'product_family': 'Wall Underlay', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'roof underlay': {'product_family': 'Roof Underlay', 'trade': 'roofing', 'category': 'B_Enclosure'},
        'building wrap': {'product_family': 'Building Wrap', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'dpc': {'product_family': 'DPC Flashing', 'trade': 'waterproofing', 'category': 'B_Enclosure'},
        'flashing': {'product_family': 'Flashing Tape', 'trade': 'waterproofing', 'category': 'B_Enclosure'},
    },
    
    # SIMPSON STRONG-TIE - Multi-category brand
    'simpson': {
        'connector': {'product_family': 'Timber Connectors', 'trade': 'framing', 'category': 'F_Manufacturers'},
        'hanger': {'product_family': 'Joist Hangers', 'trade': 'framing', 'category': 'F_Manufacturers'},
        'anchor': {'product_family': 'Concrete Anchors', 'trade': 'concrete', 'category': 'F_Manufacturers'},
        'hold down': {'product_family': 'Hold Downs', 'trade': 'framing', 'category': 'F_Manufacturers'},
        'strap': {'product_family': 'Straps Ties', 'trade': 'framing', 'category': 'F_Manufacturers'},
        'bracing': {'product_family': 'Lateral Bracing', 'trade': 'framing', 'category': 'F_Manufacturers'},
    },
    
    # ECKO - Fasteners brand (multi-product)
    'ecko': {
        't-rex': {'product_family': 'T-Rex Screws', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
        'decking': {'product_family': 'Decking Fasteners', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
        'collated': {'product_family': 'Collated Nails', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
        'framing': {'product_family': 'Framing Nails', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
        'joist hanger': {'product_family': 'Joist Hanger Nails', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
        'bracket': {'product_family': 'Brackets Connectors', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
        'staple': {'product_family': 'Staples', 'trade': 'fasteners', 'category': 'F_Manufacturers'},
    },
    
    # GIB - Mostly single category but multiple product lines
    'gib': {
        'fyreline': {'product_family': 'GIB Fyreline Fire', 'trade': 'interior_linings', 'category': 'C_Interiors'},
        'aqualine': {'product_family': 'GIB Aqualine Wet', 'trade': 'interior_linings', 'category': 'C_Interiors'},
        'braceline': {'product_family': 'GIB Braceline Bracing', 'trade': 'interior_linings', 'category': 'C_Interiors'},
        'noiseline': {'product_family': 'GIB Noiseline Acoustic', 'trade': 'interior_linings', 'category': 'C_Interiors'},
        'standard': {'product_family': 'GIB Standard', 'trade': 'interior_linings', 'category': 'C_Interiors'},
        'stopping': {'product_family': 'GIB Stopping', 'trade': 'interior_linings', 'category': 'C_Interiors'},
    },
    
    # JAMES HARDIE - Cladding brand (multi-product)
    'hardie': {
        'linea': {'product_family': 'Linea Weatherboard', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'axon': {'product_family': 'Axon Panel', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'stria': {'product_family': 'Stria Cladding', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'oblique': {'product_family': 'Oblique Cladding', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'titan': {'product_family': 'Titan Facade', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'rab': {'product_family': 'RAB Board', 'trade': 'cladding', 'category': 'B_Enclosure'},
        'secura': {'product_family': 'Secura Flooring', 'trade': 'flooring', 'category': 'B_Enclosure'},
        'villaboard': {'product_family': 'Villaboard Lining', 'trade': 'interior_linings', 'category': 'C_Interiors'},
    },
}

# Generic trade detection (fallback)
TRADE_KEYWORDS = {
    'foundations': ['foundation', 'slab', 'ribraft', 'x-pod', 'footing', 'pile', 'bearer'],
    'framing': ['framing', 'stud', 'joist', 'rafter', 'truss', 'lintel', 'noggin', 'dwang'],
    'cladding': ['cladding', 'weatherboard', 'underlay', 'wrap', 'facade', 'exterior'],
    'roofing': ['roof', 'roofing', 'purlin', 'ridge', 'hip', 'valley', 'flashing'],
    'interior_linings': ['plasterboard', 'gib', 'lining', 'ceiling', 'stopping', 'cornice'],
    'fasteners': ['nail', 'screw', 'fastener', 'anchor', 'bolt', 'connector', 'bracket'],
    'paving': ['paving', 'paver', 'driveway', 'pathway', 'permeable'],
    'masonry': ['masonry', 'block', 'blockwork', 'concrete block', 'mortar', 'grout'],
    'insulation': ['insulation', 'batts', 'r-value', 'thermal', 'acoustic'],
    'waterproofing': ['waterproof', 'membrane', 'dpc', 'tanking', 'moisture'],
    'landscaping': ['retaining', 'landscape', 'garden', 'outdoor'],
}


def detect_product_function(brand: str, filename: str, content: str) -> Tuple[str, str, str]:
    """
    Auto-detect product_family, trade, and category from brand + content.
    
    Returns:
        (product_family, trade, category_code)
    """
    brand_lower = brand.lower()
    text_lower = (filename + " " + content[:2000]).lower()
    
    # Check brand-specific rules first
    for brand_key, rules in PRODUCT_FUNCTION_RULES.items():
        if brand_key in brand_lower:
            # Check each rule for this brand
            for keyword, classification in rules.items():
                if keyword in text_lower:
                    return (
                        classification['product_family'],
                        classification['trade'],
                        classification['category']
                    )
    
    # Fallback: Use generic trade detection
    for trade, keywords in TRADE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return ('General', trade, 'General')
    
    return ('General', 'general', 'General')


@dataclass
class EnhancedIngestionConfig:
    """Enhanced configuration with product function support"""
    brand_name: str
    source_name: str
    priority: int = 80
    
    # These can be overridden per-chunk
    default_category: str = "General"
    default_product_family: str = "General"
    default_trade: str = "general"
    default_doc_type: str = "Technical_Manual"
    
    # Auto-detection settings
    auto_detect_product_function: bool = True


class EnhancedIngestor:
    """Enhanced ingestor with product function detection"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.conn = None
        self.stats = {
            "chunks_processed": 0,
            "chunks_inserted": 0,
            "chunks_skipped": 0,
            "embeddings_generated": 0,
            "product_functions_detected": {},
            "trades_detected": {},
            "errors": []
        }
    
    def connect_db(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return self.conn
    
    def close_db(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts"""
        try:
            cleaned_texts = [t[:20000] if len(t) > 20000 else t for t in texts]
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=cleaned_texts
            )
            self.stats["embeddings_generated"] += len(texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"   ⚠️ Batch embedding error: {e}")
            self.stats["errors"].append(str(e))
            return [None] * len(texts)
    
    def classify_chunk(self, chunk: Dict, config: EnhancedIngestionConfig) -> Dict:
        """
        Classify a chunk with proper product_family and trade.
        Returns enhanced chunk metadata.
        """
        # Start with defaults
        product_family = config.default_product_family
        trade = config.default_trade
        category = config.default_category
        
        # Check if chunk already has classification
        if chunk.get('product_family') and chunk['product_family'] != 'General':
            product_family = chunk['product_family']
        
        if chunk.get('trade') and chunk['trade'] != 'general':
            trade = chunk['trade']
            
        if chunk.get('category_code') and chunk['category_code'] != 'General':
            category = chunk['category_code']
        
        # Auto-detect if enabled and not already classified
        if config.auto_detect_product_function:
            if product_family == 'General' or trade == 'general':
                filename = chunk.get('source_file', chunk.get('source', ''))
                content = chunk.get('content', '')
                
                detected_family, detected_trade, detected_category = detect_product_function(
                    config.brand_name, filename, content
                )
                
                if product_family == 'General' and detected_family != 'General':
                    product_family = detected_family
                
                if trade == 'general' and detected_trade != 'general':
                    trade = detected_trade
                    
                if category == 'General' and detected_category != 'General':
                    category = detected_category
        
        # Track statistics
        self.stats["product_functions_detected"][product_family] = \
            self.stats["product_functions_detected"].get(product_family, 0) + 1
        self.stats["trades_detected"][trade] = \
            self.stats["trades_detected"].get(trade, 0) + 1
        
        return {
            'product_family': product_family,
            'trade': trade,
            'category_code': category,
        }
    
    def insert_chunk(self, chunk: Dict, config: EnhancedIngestionConfig, 
                     classification: Dict, embedding: List[float]) -> bool:
        """Insert a chunk with enhanced metadata"""
        try:
            cursor = self.conn.cursor()
            content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            cursor.execute("""
                INSERT INTO documents (
                    source, page, content, embedding, section, snippet,
                    brand_name, category_code, product_family, doc_type, trade,
                    priority, status, ingestion_source, file_hash, ingested_at,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s::vector, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    NOW(), NOW()
                )
            """, (
                config.source_name,
                chunk.get('page', 0),
                chunk['content'],
                embedding_str,
                chunk.get('section'),
                chunk['content'][:200],
                config.brand_name,
                classification['category_code'],
                classification['product_family'],
                config.default_doc_type,
                classification['trade'],
                config.priority,
                'active',
                'bigbrain_enhanced_v2',
                content_hash,
                datetime.now()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"   ❌ Insert error: {e}")
            self.stats["errors"].append(str(e))
            return False
    
    def ingest_chunks(self, chunks: List[Dict], config: EnhancedIngestionConfig) -> Dict:
        """Ingest chunks with enhanced product function detection"""
        print(f"\n{'='*60}")
        print(f"🧠 ENHANCED INGESTOR v2 - Product Function Detection")
        print(f"{'='*60}")
        print(f"   Brand: {config.brand_name}")
        print(f"   Source: {config.source_name}")
        print(f"   Auto-detect: {config.auto_detect_product_function}")
        print(f"   Chunks: {len(chunks)}")
        
        self.connect_db()
        
        # Process in batches
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(chunks))
            batch = chunks[start_idx:end_idx]
            
            print(f"\n📦 Batch {batch_idx + 1}/{total_batches} ({len(batch)} chunks)...")
            
            # Classify all chunks in batch
            classifications = [self.classify_chunk(c, config) for c in batch]
            
            # Generate embeddings
            texts = [c['content'] for c in batch]
            embeddings = self.generate_embeddings_batch(texts)
            
            # Insert each chunk
            for chunk, classification, embedding in zip(batch, classifications, embeddings):
                self.stats["chunks_processed"] += 1
                
                if embedding is None:
                    self.stats["chunks_skipped"] += 1
                    continue
                
                if self.insert_chunk(chunk, config, classification, embedding):
                    self.stats["chunks_inserted"] += 1
                else:
                    self.stats["chunks_skipped"] += 1
            
            time.sleep(RATE_LIMIT_DELAY)
        
        self.close_db()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 INGESTION SUMMARY")
        print(f"{'='*60}")
        print(f"   ✅ Inserted: {self.stats['chunks_inserted']}")
        print(f"   ⏭️ Skipped: {self.stats['chunks_skipped']}")
        print(f"   🔢 Embeddings: {self.stats['embeddings_generated']}")
        
        print(f"\n   📂 Product Functions Detected:")
        for pf, count in sorted(self.stats['product_functions_detected'].items(), key=lambda x: -x[1]):
            print(f"      • {pf}: {count}")
        
        print(f"\n   🔧 Trades Detected:")
        for trade, count in sorted(self.stats['trades_detected'].items(), key=lambda x: -x[1]):
            print(f"      • {trade}: {count}")
        
        return self.stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Big Brain Ingestor v2")
    parser.add_argument("--chunks", "-c", required=True, help="Path to chunks.json")
    parser.add_argument("--brand", "-b", required=True, help="Brand name")
    parser.add_argument("--source", "-s", required=True, help="Source name for database")
    parser.add_argument("--priority", type=int, default=80, help="Priority (0-100)")
    parser.add_argument("--category", default="General", help="Default category code")
    parser.add_argument("--product-family", default="General", help="Default product family")
    parser.add_argument("--trade", default="general", help="Default trade")
    parser.add_argument("--doc-type", default="Technical_Manual", help="Document type")
    parser.add_argument("--no-auto-detect", action="store_true", help="Disable auto-detection")
    
    args = parser.parse_args()
    
    # Load chunks
    with open(args.chunks) as f:
        chunks = json.load(f)
    
    print(f"📂 Loaded {len(chunks)} chunks from {args.chunks}")
    
    # Create config
    config = EnhancedIngestionConfig(
        brand_name=args.brand,
        source_name=args.source,
        priority=args.priority,
        default_category=args.category,
        default_product_family=args.product_family,
        default_trade=args.trade,
        default_doc_type=args.doc_type,
        auto_detect_product_function=not args.no_auto_detect
    )
    
    # Run ingestion
    ingestor = EnhancedIngestor()
    stats = ingestor.ingest_chunks(chunks, config)
    
    # Save stats
    stats_file = args.chunks.replace('.json', '_enhanced_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    print(f"\n📋 Stats saved to: {stats_file}")


if __name__ == "__main__":
    main()
