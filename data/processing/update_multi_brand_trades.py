#!/usr/bin/env python3
"""
Update Multi-Category Brands with Granular Trade Tags
Re-tags fastener brands and other multi-category brands with specific product functions
"""

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import re

load_dotenv('/app/backend-minimal/.env')

DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'

# =============================================================================
# BRAND-SPECIFIC TRADE DETECTION RULES
# =============================================================================

BRAND_TRADE_RULES = {
    # =========================================================================
    # SIMPSON STRONG-TIE - Structural Connectors & Fasteners
    # =========================================================================
    'simpson': {
        'framing': {
            'keywords': ['joist hanger', 'hanger', 'lus', 'hu', 'face mount', 
                         'top flange', 'connector', 'angle bracket', 'rafter',
                         'purlin', 'ridge', 'hip', 'valley', 'stringer'],
            'product_families': {
                'joist hanger': 'Joist Hangers',
                'hanger': 'Joist Hangers',
                'angle': 'Angle Brackets',
                'rafter': 'Rafter Connectors',
                'purlin': 'Purlin Clips',
            }
        },
        'bracing': {
            'keywords': ['brace', 'bracing', 'hold down', 'hold-down', 'holddown',
                         'strap', 'tie', 'tension', 'shear', 'lateral'],
            'product_families': {
                'hold down': 'Hold Downs',
                'hold-down': 'Hold Downs',
                'strap': 'Straps & Ties',
                'brace': 'Bracing Systems',
            }
        },
        'anchoring': {
            'keywords': ['anchor', 'post base', 'post anchor', 'column base',
                         'concrete', 'masonry', 'retrofit', 'epoxy', 'chemical'],
            'product_families': {
                'post base': 'Post Bases',
                'post anchor': 'Post Anchors',
                'concrete': 'Concrete Anchors',
                'epoxy': 'Chemical Anchors',
            }
        },
        'nailplates': {
            'keywords': ['nail plate', 'nailplate', 'mending plate', 'tie plate',
                         'gang nail', 'truss', 'plate'],
            'product_families': {
                'nail plate': 'Nail Plates',
                'truss': 'Truss Plates',
            }
        },
    },
    
    # =========================================================================
    # PRYDA - Structural Connectors & Bracing
    # =========================================================================
    'pryda': {
        'framing': {
            'keywords': ['joist hanger', 'hanger', 'bracket', 'connector', 
                         'post support', 'beam'],
            'product_families': {
                'joist hanger': 'Joist Hangers',
                'hanger': 'Joist Hangers',
                'bracket': 'Framing Brackets',
            }
        },
        'bracing': {
            'keywords': ['brace', 'bracing', 'hold down', 'strap', 'tension',
                         'speed brace', 'wall brace'],
            'product_families': {
                'speed brace': 'Speed Bracing',
                'hold down': 'Hold Downs',
                'strap': 'Straps',
            }
        },
        'nailplates': {
            'keywords': ['nail plate', 'nailplate', 'gang plate', 'truss',
                         'mending', 'splice'],
            'product_families': {
                'nail plate': 'Nail Plates',
                'truss': 'Truss Connectors',
            }
        },
        'anchoring': {
            'keywords': ['anchor', 'concrete', 'masonry', 'foundation', 'post base'],
            'product_families': {
                'anchor': 'Anchors',
                'post base': 'Post Bases',
            }
        },
    },
    
    # =========================================================================
    # ECKO - Fasteners (Nails, Screws, Collated)
    # =========================================================================
    'ecko': {
        'framing_nails': {
            'keywords': ['framing nail', 'framing', 'gun nail', 'collated', 
                         'coil', 'strip', 'clipped head', 'full head'],
            'product_families': {
                'framing': 'Framing Nails',
                'collated': 'Collated Nails',
                'coil': 'Coil Nails',
            }
        },
        'joist_hanger_nails': {
            'keywords': ['joist hanger', 'hanger nail', 'connector nail', 
                         'jhn', 'structural'],
            'product_families': {
                'joist hanger': 'Joist Hanger Nails',
                'connector': 'Connector Nails',
            }
        },
        'decking': {
            'keywords': ['deck', 'decking', 't-rex', 'trex', 'outdoor', 
                         'stainless', 'treated'],
            'product_families': {
                't-rex': 'T-Rex Decking Screws',
                'deck': 'Decking Fasteners',
            }
        },
        'roofing': {
            'keywords': ['roof', 'roofing', 'purlin', 'batten', 'cladding'],
            'product_families': {
                'roof': 'Roofing Nails',
                'purlin': 'Purlin Nails',
            }
        },
        'staples': {
            'keywords': ['staple', 'staples', 'air staple', 'pneumatic'],
            'product_families': {
                'staple': 'Staples',
            }
        },
    },
    
    # =========================================================================
    # ZENITH - Hardware & Fasteners
    # =========================================================================
    'zenith': {
        'screws': {
            'keywords': ['screw', 'self drill', 'self-drill', 'timber screw',
                         'metal screw', 'tek', 'bugle'],
            'product_families': {
                'timber screw': 'Timber Screws',
                'self drill': 'Self-Drilling Screws',
                'bugle': 'Bugle Screws',
            }
        },
        'bolts': {
            'keywords': ['bolt', 'coach', 'hex', 'carriage', 'cup head', 'cuphead'],
            'product_families': {
                'coach': 'Coach Bolts',
                'hex': 'Hex Bolts',
                'carriage': 'Carriage Bolts',
            }
        },
        'anchoring': {
            'keywords': ['anchor', 'dynabolt', 'sleeve', 'wedge', 'drop-in',
                         'chemical', 'concrete', 'masonry'],
            'product_families': {
                'dynabolt': 'Dynabolts',
                'wedge': 'Wedge Anchors',
                'drop-in': 'Drop-In Anchors',
                'chemical': 'Chemical Anchors',
            }
        },
        'hardware': {
            'keywords': ['hinge', 'latch', 'hasp', 'lock', 'handle', 'hook',
                         'bracket', 'corner', 'shelf'],
            'product_families': {
                'hinge': 'Hinges',
                'latch': 'Latches',
                'bracket': 'Brackets',
            }
        },
        'nails': {
            'keywords': ['nail', 'brad', 'finishing', 'clout', 'flat head'],
            'product_families': {
                'brad': 'Brad Nails',
                'clout': 'Clout Nails',
            }
        },
    },
    
    # =========================================================================
    # MACSIM - Fasteners & Anchors
    # =========================================================================
    'macsim': {
        'screws': {
            'keywords': screw', 'timber', 'decking', 'bugle', 'countersunk',
                         'wafer', 'hex', 'self-drill'],
            'product_families': {
                'timber': 'Timber Screws',
                'decking': 'Decking Screws',
                'bugle': 'Bugle Screws',
            }
        },
        'anchoring': {
            'keywords': ['anchor', 'dynabolt', 'through bolt', 'sleeve',
                         'concrete', 'masonry', 'chemical', 'epoxy'],
            'product_families': {
                'dynabolt': 'Dynabolts',
                'through bolt': 'Through Bolts',
                'chemical': 'Chemical Anchors',
            }
        },
        'nails': {
            'keywords': ['nail', 'gun nail', 'collated', 'framing', 'brad'],
            'product_families': {
                'framing': 'Framing Nails',
                'collated': 'Collated Nails',
            }
        },
        'bolts': {
            'keywords': ['bolt', 'coach', 'hex', 'set screw', 'stud'],
            'product_families': {
                'coach': 'Coach Bolts',
                'hex': 'Hex Bolts',
            }
        },
    },
    
    # =========================================================================
    # BREMICK - Industrial Fasteners
    # =========================================================================
    'bremick': {
        'screws': {
            'keywords': ['screw', 'self drill', 'roofing screw', 'cladding',
                         'timber', 'metal', 'tek'],
            'product_families': {
                'self drill': 'Self-Drilling Screws',
                'roofing': 'Roofing Screws',
                'timber': 'Timber Screws',
            }
        },
        'anchoring': {
            'keywords': ['anchor', 'bremfix', 'chemical', 'injection', 'masonry',
                         'concrete', 'wedge', 'sleeve'],
            'product_families': {
                'bremfix': 'Bremfix Anchors',
                'chemical': 'Chemical Anchors',
                'wedge': 'Wedge Anchors',
            }
        },
        'bolts': {
            'keywords': ['bolt', 'structural', 'high tensile', 'hex', 'cup head'],
            'product_families': {
                'structural': 'Structural Bolts',
                'hex': 'Hex Bolts',
            }
        },
        'rivets': {
            'keywords': ['rivet', 'blind rivet', 'pop rivet', 'structural rivet'],
            'product_families': {
                'rivet': 'Rivets',
                'blind': 'Blind Rivets',
            }
        },
    },
    
    # =========================================================================
    # SPAX - Premium Screws
    # =========================================================================
    'spax': {
        'timber_screws': {
            'keywords': ['timber', 'wood', 'construction', 'structural', 'power lag'],
            'product_families': {
                'construction': 'Construction Screws',
                'structural': 'Structural Screws',
                'power lag': 'Power Lag Screws',
            }
        },
        'decking': {
            'keywords': ['deck', 'decking', 'outdoor', 'exterior', 't-star'],
            'product_families': {
                'deck': 'Decking Screws',
            }
        },
        'facades': {
            'keywords': ['facade', 'cladding', 'panel', 'flat head'],
            'product_families': {
                'facade': 'Facade Screws',
            }
        },
    },
}

# Generic trade keywords fallback
GENERIC_TRADE_KEYWORDS = {
    'framing': ['hanger', 'joist', 'rafter', 'purlin', 'connector', 'bracket'],
    'bracing': ['brace', 'bracing', 'hold down', 'strap', 'tension', 'lateral'],
    'anchoring': ['anchor', 'concrete anchor', 'masonry', 'dynabolt', 'chemical'],
    'screws': ['screw', 'timber screw', 'decking screw', 'self drill'],
    'nails': ['nail', 'framing nail', 'gun nail', 'collated', 'brad'],
    'bolts': ['bolt', 'coach bolt', 'hex bolt', 'carriage'],
    'roofing': ['roof', 'roofing', 'purlin', 'cladding screw'],
    'decking': ['deck', 'decking', 'outdoor', 'stainless'],
}


def detect_trade_for_brand(brand: str, content: str, source: str = '') -> tuple:
    """
    Detect specific trade and product_family for a given brand.
    Returns (trade, product_family)
    """
    brand_lower = brand.lower() if brand else ''
    text_lower = (content + ' ' + source).lower()
    
    # Find matching brand rules
    matching_rules = None
    for brand_key, rules in BRAND_TRADE_RULES.items():
        if brand_key in brand_lower:
            matching_rules = rules
            break
    
    if matching_rules:
        # Score each trade category
        trade_scores = {}
        best_product_family = 'General'
        
        for trade, trade_info in matching_rules.items():
            keywords = trade_info['keywords']
            product_families = trade_info['product_families']
            score = 0
            
            for kw in keywords:
                if kw in text_lower:
                    score += 1
                    if kw in product_families and best_product_family == 'General':
                        best_product_family = product_families[kw]
            
            if score > 0:
                trade_scores[trade] = score
        
        if trade_scores:
            best_trade = max(trade_scores, key=trade_scores.get)
            return best_trade, best_product_family
    
    # Fallback to generic detection
    for trade, keywords in GENERIC_TRADE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return trade, 'General'
    
    return 'fasteners', 'General'


def update_brand_documents(brand_filter: str, dry_run: bool = False):
    """Update documents for a specific brand with granular trade tags"""
    print(f"\n{'='*60}")
    print(f"🔄 UPDATING: {brand_filter}")
    print(f"{'='*60}")
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Fetch documents for this brand
    cur.execute("""
        SELECT id, content, source, brand_name, trade, product_family
        FROM documents
        WHERE LOWER(brand_name) LIKE %s
    """, (f'%{brand_filter.lower()}%',))
    
    documents = cur.fetchall()
    print(f"   📄 Found {len(documents)} documents")
    
    if len(documents) == 0:
        conn.close()
        return {'total': 0, 'updated': 0, 'unchanged': 0, 'trades': {}}
    
    stats = {
        'total': len(documents),
        'updated': 0,
        'unchanged': 0,
        'trades': {},
        'product_families': {},
    }
    
    for doc in documents:
        doc_id = doc['id']
        content = doc['content']
        source = doc['source']
        brand_name = doc['brand_name']
        current_trade = doc['trade']
        current_pf = doc['product_family']
        
        new_trade, new_pf = detect_trade_for_brand(brand_name, content, source)
        
        # Track stats
        stats['trades'][new_trade] = stats['trades'].get(new_trade, 0) + 1
        stats['product_families'][new_pf] = stats['product_families'].get(new_pf, 0) + 1
        
        # Update if different and not dry run
        if (new_trade != current_trade or new_pf != current_pf):
            if not dry_run:
                cur.execute("""
                    UPDATE documents
                    SET trade = %s, product_family = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_trade, new_pf, doc_id))
            stats['updated'] += 1
        else:
            stats['unchanged'] += 1
    
    if not dry_run:
        conn.commit()
    conn.close()
    
    # Print summary
    print(f"   ✅ Updated: {stats['updated']}")
    print(f"   ⏭️ Unchanged: {stats['unchanged']}")
    print(f"   📂 Trade Distribution:")
    for trade, count in sorted(stats['trades'].items(), key=lambda x: -x[1]):
        print(f"      • {trade}: {count}")
    
    return stats


def main():
    """Update all multi-category brands"""
    print("\n" + "="*70)
    print("🔄 MULTI-CATEGORY BRAND RE-TAGGING")
    print("="*70)
    
    # Brands to update (prioritized by importance)
    brands_to_update = [
        'Simpson',      # 591 chunks - structural connectors
        'Pryda',        # 533 chunks - bracing & connectors
        'Ecko',         # 189 chunks - various fasteners
        'Zenith',       # 2735 chunks - hardware & fasteners
        'MacSim',       # 3938 chunks - general fasteners
        'Bremick',      # 732 chunks - industrial fasteners
        'SPAX',         # 226 chunks - premium screws
    ]
    
    all_stats = {}
    
    for brand in brands_to_update:
        stats = update_brand_documents(brand, dry_run=False)
        all_stats[brand] = stats
    
    # Final summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY - ALL BRANDS")
    print("="*70)
    
    total_updated = 0
    total_docs = 0
    
    for brand, stats in all_stats.items():
        total_docs += stats['total']
        total_updated += stats['updated']
        print(f"\n{brand}:")
        print(f"   Total: {stats['total']}, Updated: {stats['updated']}")
        if stats['trades']:
            top_trades = sorted(stats['trades'].items(), key=lambda x: -x[1])[:3]
            print(f"   Top trades: {', '.join(f'{t[0]}({t[1]})' for t in top_trades)}")
    
    print(f"\n{'='*70}")
    print(f"✅ COMPLETE: {total_updated}/{total_docs} documents updated")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
