#!/usr/bin/env python3
"""
Update existing Firth documents with granular trade tags.
This script updates the trade and product_family fields based on content analysis.
"""

import psycopg2
import psycopg2.extras
import re
import sys
from dotenv import load_dotenv

load_dotenv('/app/backend-minimal/.env')

DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'

# Trade detection rules for Firth products
FIRTH_TRADE_RULES = {
    'foundations': {
        'keywords': ['ribraft', 'rib raft', 'x-pod', 'xpod', 'hotedge', 'hot edge', 
                     'foundation', 'slab', 'tc3', 'canterbury', 'ground beam', 
                     'pile', 'footing', 'bearer', 'edge beam', 'thickening'],
        'product_families': {
            'ribraft': 'RibRaft Foundations',
            'rib raft': 'RibRaft Foundations',
            'x-pod': 'X-Pod TC3 Foundations',
            'xpod': 'X-Pod TC3 Foundations',
            'hotedge': 'RibRaft HotEdge',
            'hot edge': 'RibRaft HotEdge',
            'tc3': 'X-Pod TC3 Foundations',
            'canterbury': 'X-Pod TC3 Foundations',
        }
    },
    'paving': {
        'keywords': ['paving', 'paver', 'pavers', 'holland', 'ecopave', 'eco pave',
                     'driveway', 'pathway', 'permeable', 'cobble', 'permapave',
                     'pedestrian', 'vehicle', 'laying pattern', 'sand bedding'],
        'product_families': {
            'holland': 'Holland Pavers',
            'ecopave': 'EcoPave Permeable',
            'eco pave': 'EcoPave Permeable',
            'permapave': 'EcoPave Permeable',
            'permeable': 'EcoPave Permeable',
            'cobble': 'Paving Systems',
        }
    },
    'masonry': {
        'keywords': ['masonry', 'block', 'blockwork', '20 series', '25 series',
                     '15 series', 'bond beam', 'grout', 'mortar', 'blocklayer',
                     'concrete block', 'hollow core', 'filled block', 'lintel block',
                     'knockout', 'masonry veneer', 'h block', 'solid block'],
        'product_families': {
            '20 series': '20 Series Masonry',
            '25 series': '25 Series Masonry',
            '15 series': '15 Series Masonry',
            'bond beam': 'Concrete Masonry',
            'lintel block': 'Concrete Masonry',
        }
    },
    'retaining': {
        'keywords': ['retaining', 'keystone', 'garden wall', 'landscape wall',
                     'gravity wall', 'geogrid', 'tieback'],
        'product_families': {
            'keystone': 'Keystone Retaining',
            'retaining': 'Retaining Walls',
        }
    },
}


def detect_firth_trade(content: str, source: str = '') -> tuple:
    """
    Detect the specific trade and product_family for a Firth chunk.
    Returns (trade, product_family)
    """
    text_lower = (content + ' ' + source).lower()
    
    # Score each trade
    trade_scores = {}
    best_product_family = 'Firth General'
    
    for trade, rules in FIRTH_TRADE_RULES.items():
        score = 0
        keywords = rules['keywords']
        product_families = rules['product_families']
        
        for kw in keywords:
            if kw in text_lower:
                score += 1
                # Check if this keyword has a specific product family
                if kw in product_families:
                    best_product_family = product_families[kw]
        
        if score > 0:
            trade_scores[trade] = score
    
    if trade_scores:
        best_trade = max(trade_scores, key=trade_scores.get)
        
        # If we haven't found a specific product family, use a default based on trade
        if best_product_family == 'Firth General':
            defaults = {
                'foundations': 'Foundations Systems',
                'paving': 'Paving Systems',
                'masonry': 'Concrete Masonry',
                'retaining': 'Retaining Walls',
            }
            best_product_family = defaults.get(best_trade, 'Firth General')
        
        return best_trade, best_product_family
    
    # Default fallback - look for any Firth indicator
    return 'general', 'Firth General'


def update_firth_documents():
    """Update all Firth documents with correct trade tags"""
    print("\n" + "="*60)
    print("🔄 UPDATING FIRTH DOCUMENTS WITH GRANULAR TRADE TAGS")
    print("="*60)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Fetch all Firth documents
    cur.execute("""
        SELECT id, content, source, trade, product_family
        FROM documents
        WHERE brand_name ILIKE '%firth%' OR source ILIKE '%firth%'
    """)
    
    documents = cur.fetchall()
    print(f"\n📄 Found {len(documents)} Firth documents to process")
    
    # Track statistics
    stats = {
        'total': len(documents),
        'updated': 0,
        'unchanged': 0,
        'trades': {},
        'product_families': {},
    }
    
    # Process each document
    for doc in documents:
        doc_id = doc['id']
        content = doc['content']
        source = doc['source']
        current_trade = doc['trade']
        current_pf = doc['product_family']
        
        # Detect new trade and product_family
        new_trade, new_pf = detect_firth_trade(content, source)
        
        # Track stats
        stats['trades'][new_trade] = stats['trades'].get(new_trade, 0) + 1
        stats['product_families'][new_pf] = stats['product_families'].get(new_pf, 0) + 1
        
        # Update if different
        if new_trade != current_trade or new_pf != current_pf:
            cur.execute("""
                UPDATE documents
                SET trade = %s, product_family = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_trade, new_pf, doc_id))
            stats['updated'] += 1
        else:
            stats['unchanged'] += 1
    
    conn.commit()
    conn.close()
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 UPDATE SUMMARY")
    print(f"{'='*60}")
    print(f"   Total documents: {stats['total']}")
    print(f"   ✅ Updated: {stats['updated']}")
    print(f"   ⏭️ Unchanged: {stats['unchanged']}")
    
    print(f"\n   📂 Trade Distribution:")
    for trade, count in sorted(stats['trades'].items(), key=lambda x: -x[1]):
        print(f"      • {trade}: {count}")
    
    print(f"\n   📦 Product Family Distribution:")
    for pf, count in sorted(stats['product_families'].items(), key=lambda x: -x[1]):
        print(f"      • {pf}: {count}")
    
    return stats


if __name__ == "__main__":
    update_firth_documents()
