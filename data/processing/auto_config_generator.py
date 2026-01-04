#!/usr/bin/env python3
"""
STRYDA Auto-Config Generator + Low Confidence Report
=====================================================

Automatically generates brand detection rules from database metadata
and produces a quality report flagging brands that need manual review.

Features:
- Scans all brand_name, trade, product_family data from documents table
- Generates detection keywords from product family names
- Produces confidence scores with specialist brand logic
- Outputs actionable Low Confidence Report
- Generates ready-to-use config for simple_tier1_retrieval.py

Usage:
    python3 auto_config_generator.py           # Generate report + config
    python3 auto_config_generator.py --apply   # Apply config to retrieval file
"""

import os
import sys
import re
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')
OUTPUT_DIR = '/app/data/processing/auto_config_output'
RETRIEVAL_FILE = '/app/backend-minimal/simple_tier1_retrieval.py'

# =============================================================================
# CONFIDENCE SCORING THRESHOLDS
# =============================================================================

THRESHOLDS = {
    'min_chunks_normal': 50,        # Minimum chunks for normal brands
    'min_chunks_specialist': 15,    # Minimum for specialist brands (if clean)
    'min_trades': 2,                # Minimum distinct trades for HIGH
    'min_product_families': 2,      # Minimum product families for HIGH
    'max_general_pct_high': 30,     # Max % "general" tags for HIGH confidence
    'max_general_pct_medium': 60,   # Max % "general" tags for MEDIUM
    'specialist_clean_threshold': 10,  # Max % "general" for specialist HIGH
}

# Known "general" trade patterns that indicate poor classification
GENERAL_TRADE_PATTERNS = [
    '_general', 'general', 'unknown', 'other', 'misc', 'brand_wide', 'brand-wide'
]

# =============================================================================
# DATABASE SCANNING
# =============================================================================

def scan_database() -> Dict:
    """Scan database for all brand metadata"""
    print("\n📊 Scanning database for brand metadata...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get all brands with their statistics
    cur.execute('''
        SELECT 
            brand_name,
            COUNT(*) as chunk_count,
            COUNT(DISTINCT trade) as trade_count,
            COUNT(DISTINCT product_family) as family_count,
            COUNT(DISTINCT doc_type) as doc_type_count,
            COUNT(DISTINCT category_code) as category_count,
            ARRAY_AGG(DISTINCT trade) as trades,
            ARRAY_AGG(DISTINCT product_family) as families,
            ARRAY_AGG(DISTINCT doc_type) as doc_types,
            ARRAY_AGG(DISTINCT category_code) as categories
        FROM documents 
        WHERE brand_name IS NOT NULL 
          AND brand_name != ''
          AND embedding IS NOT NULL
        GROUP BY brand_name
        ORDER BY chunk_count DESC
    ''')
    
    brands = {}
    for row in cur.fetchall():
        brand_name = row[0]
        
        # Clean up arrays (remove None values)
        trades = [t for t in (row[6] or []) if t]
        families = [f for f in (row[7] or []) if f]
        doc_types = [d for d in (row[8] or []) if d]
        categories = [c for c in (row[9] or []) if c]
        
        brands[brand_name] = {
            'chunk_count': row[1],
            'trade_count': row[2],
            'family_count': row[3],
            'doc_type_count': row[4],
            'category_count': row[5],
            'trades': trades,
            'product_families': families,
            'doc_types': doc_types,
            'categories': categories,
        }
    
    # Get general tag percentages for each brand
    for brand_name in brands:
        cur.execute('''
            SELECT trade, COUNT(*) 
            FROM documents 
            WHERE brand_name = %s AND embedding IS NOT NULL
            GROUP BY trade
        ''', (brand_name,))
        
        trade_counts = {row[0]: row[1] for row in cur.fetchall()}
        total = sum(trade_counts.values())
        
        # Calculate percentage of "general" tagged content
        general_count = sum(
            count for trade, count in trade_counts.items()
            if trade and any(pattern in trade.lower() for pattern in GENERAL_TRADE_PATTERNS)
        )
        
        brands[brand_name]['general_pct'] = (general_count / total * 100) if total > 0 else 0
        brands[brand_name]['trade_distribution'] = trade_counts
    
    cur.close()
    conn.close()
    
    print(f"   Found {len(brands)} brands in database")
    return brands


# =============================================================================
# CONFIDENCE SCORING
# =============================================================================

def calculate_confidence(brand_name: str, data: Dict) -> Tuple[str, List[str]]:
    """
    Calculate confidence score for a brand.
    
    Returns: (confidence_level, list_of_issues)
    
    Logic:
    - HIGH: Good coverage, clear tagging, diverse trades
    - MEDIUM: Some issues but usable
    - LOW: Needs manual review
    
    SPECIALIST BRAND LOGIC:
    - Low chunk count BUT clean tagging (< 10% general) = HIGH confidence
    """
    issues = []
    
    chunk_count = data['chunk_count']
    trade_count = data['trade_count']
    family_count = data['family_count']
    general_pct = data['general_pct']
    doc_types = data['doc_types']
    
    # Check for Technical Data Sheets
    has_tds = any('technical' in dt.lower() or 'data_sheet' in dt.lower() or 'datasheet' in dt.lower() 
                  for dt in doc_types if dt)
    
    # ===========================================
    # SPECIALIST BRAND CHECK (Low volume, clean data)
    # ===========================================
    is_specialist = chunk_count < THRESHOLDS['min_chunks_normal']
    is_clean = general_pct <= THRESHOLDS['specialist_clean_threshold']
    
    if is_specialist and is_clean and chunk_count >= THRESHOLDS['min_chunks_specialist']:
        # Specialist brand with clean tagging = HIGH confidence
        return 'HIGH', [f"Specialist brand ({chunk_count} chunks, {general_pct:.0f}% general - CLEAN)"]
    
    # ===========================================
    # STANDARD SCORING
    # ===========================================
    
    # Check chunk count
    if chunk_count < THRESHOLDS['min_chunks_specialist']:
        issues.append(f"Very low chunk count: {chunk_count}")
    elif chunk_count < THRESHOLDS['min_chunks_normal']:
        issues.append(f"Low chunk count: {chunk_count} (may be specialist brand)")
    
    # Check trade diversity
    if trade_count < THRESHOLDS['min_trades']:
        issues.append(f"Limited trade diversity: {trade_count} trade(s)")
    
    # Check product family coverage
    if family_count < THRESHOLDS['min_product_families']:
        issues.append(f"Few product families detected: {family_count}")
    
    # Check general tag percentage
    if general_pct > THRESHOLDS['max_general_pct_medium']:
        issues.append(f"High generic tagging: {general_pct:.0f}% tagged as 'general'")
    elif general_pct > THRESHOLDS['max_general_pct_high']:
        issues.append(f"Moderate generic tagging: {general_pct:.0f}% tagged as 'general'")
    
    # Check for Technical Data Sheets
    if not has_tds:
        issues.append("No Technical Data Sheets detected")
    
    # ===========================================
    # DETERMINE CONFIDENCE LEVEL
    # ===========================================
    
    critical_issues = [i for i in issues if 'Very low' in i or 'High generic' in i or 'Few product families' in i]
    moderate_issues = [i for i in issues if i not in critical_issues]
    
    if len(critical_issues) >= 2:
        return 'LOW', issues
    elif len(critical_issues) == 1 or len(moderate_issues) >= 3:
        return 'MEDIUM', issues
    elif len(issues) <= 1:
        return 'HIGH', issues if issues else ['All quality checks passed']
    else:
        return 'MEDIUM', issues


# =============================================================================
# KEYWORD EXTRACTION
# =============================================================================

def extract_keywords_from_family(product_family: str) -> List[str]:
    """Extract searchable keywords from a product family name"""
    if not product_family:
        return []
    
    # Normalize
    text = product_family.lower().strip()
    
    # Remove common brand prefixes we'll handle separately
    common_prefixes = ['kingspan', 'expol', 'autex', 'pink batts', 'bradford', 
                       'earthwool', 'mammoth', 'greenstuf', 'firth', 'james hardie']
    for prefix in common_prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Extract meaningful parts
    keywords = []
    
    # Add the full cleaned name
    if len(text) > 2:
        keywords.append(text)
    
    # Extract product codes (e.g., K12, TR28, K10)
    codes = re.findall(r'\b[A-Z]{1,3}\d{1,3}[A-Z]?\b', product_family, re.IGNORECASE)
    keywords.extend([c.lower() for c in codes])
    
    # Extract key product words
    product_words = re.findall(r'\b(panel|board|batt|blanket|wrap|membrane|tile|screen|ceiling|wall|roof|floor|soffit|facade|drain|pod)\b', text, re.IGNORECASE)
    keywords.extend([w.lower() for w in product_words])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen and len(kw) > 1:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords


def generate_brand_keywords(brand_name: str, data: Dict) -> Dict:
    """Generate all detection keywords for a brand"""
    keywords = {
        'brand_name': brand_name,
        'brand_keywords': [brand_name.lower()],
        'product_keywords': [],
        'trade_keywords': [],
    }
    
    # Add brand name variations
    brand_lower = brand_name.lower()
    keywords['brand_keywords'].append(brand_lower)
    
    # Handle hyphenated/spaced variations
    if ' ' in brand_name:
        keywords['brand_keywords'].append(brand_name.lower().replace(' ', ''))
        keywords['brand_keywords'].append(brand_name.lower().replace(' ', '-'))
    if '-' in brand_name:
        keywords['brand_keywords'].append(brand_name.lower().replace('-', ' '))
        keywords['brand_keywords'].append(brand_name.lower().replace('-', ''))
    
    # Extract product keywords from families
    for family in data['product_families']:
        kws = extract_keywords_from_family(family)
        keywords['product_keywords'].extend(kws)
    
    # Add trade keywords
    for trade in data['trades']:
        if trade and not any(p in trade.lower() for p in GENERAL_TRADE_PATTERNS):
            # Convert trade to searchable keywords
            trade_words = trade.replace('_', ' ').split()
            keywords['trade_keywords'].extend(trade_words)
    
    # Deduplicate
    keywords['brand_keywords'] = list(set(keywords['brand_keywords']))
    keywords['product_keywords'] = list(set(keywords['product_keywords']))
    keywords['trade_keywords'] = list(set(keywords['trade_keywords']))
    
    return keywords


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(brands: Dict) -> str:
    """Generate the Low Confidence Report"""
    
    # Calculate confidence for all brands
    results = {
        'HIGH': [],
        'MEDIUM': [],
        'LOW': [],
    }
    
    for brand_name, data in brands.items():
        confidence, issues = calculate_confidence(brand_name, data)
        results[confidence].append({
            'brand': brand_name,
            'chunks': data['chunk_count'],
            'trades': data['trade_count'],
            'families': data['family_count'],
            'general_pct': data['general_pct'],
            'issues': issues,
            'categories': data['categories'],
        })
    
    # Sort each category by chunk count
    for level in results:
        results[level].sort(key=lambda x: x['chunks'], reverse=True)
    
    # Generate report
    report = []
    report.append("=" * 70)
    report.append("       STRYDA AUTO-CONFIG - LOW CONFIDENCE REPORT")
    report.append(f"       Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)
    
    # Summary
    total_brands = len(brands)
    total_chunks = sum(b['chunk_count'] for b in brands.values())
    report.append(f"\n📊 SUMMARY: {total_brands} brands | {total_chunks:,} total chunks\n")
    
    # HIGH Confidence
    report.append("=" * 70)
    report.append(f"✅ HIGH CONFIDENCE ({len(results['HIGH'])} brands) - Ready for Production")
    report.append("=" * 70)
    for item in results['HIGH']:
        cats = ', '.join(item['categories']) if item['categories'] else 'Unknown'
        report.append(f"   • {item['brand']}: {item['chunks']:,} chunks | {item['trades']} trades | {item['families']} families")
        report.append(f"     Categories: {cats}")
        if item['issues'] and item['issues'][0] != 'All quality checks passed':
            report.append(f"     Note: {item['issues'][0]}")
    
    # MEDIUM Confidence
    report.append("\n" + "=" * 70)
    report.append(f"⚠️  MEDIUM CONFIDENCE ({len(results['MEDIUM'])} brands) - Review Recommended")
    report.append("=" * 70)
    for item in results['MEDIUM']:
        report.append(f"   • {item['brand']}: {item['chunks']:,} chunks | {item['general_pct']:.0f}% general tags")
        for issue in item['issues']:
            report.append(f"     → {issue}")
        report.append(f"     Action: Review PDFs for clearer product segmentation")
    
    # LOW Confidence
    report.append("\n" + "=" * 70)
    report.append(f"❌ LOW CONFIDENCE ({len(results['LOW'])} brands) - Manual Review Required")
    report.append("=" * 70)
    if results['LOW']:
        for item in results['LOW']:
            report.append(f"   • {item['brand']}: {item['chunks']:,} chunks | {item['general_pct']:.0f}% general tags")
            for issue in item['issues']:
                report.append(f"     → {issue}")
            report.append(f"     Action: Check PDF quality, may need manual tagging or re-ingestion")
    else:
        report.append("   None! All brands meet quality thresholds.")
    
    # Recommendations
    report.append("\n" + "=" * 70)
    report.append("📋 RECOMMENDATIONS")
    report.append("=" * 70)
    
    if results['LOW']:
        report.append(f"   1. Review {len(results['LOW'])} LOW confidence brand(s) before production use")
    if results['MEDIUM']:
        report.append(f"   2. Consider re-ingesting {len(results['MEDIUM'])} MEDIUM confidence brand(s) with better folder structure")
    report.append(f"   3. {len(results['HIGH'])} brand(s) are ready for production use")
    
    report.append("\n" + "=" * 70)
    
    return '\n'.join(report), results


def generate_config(brands: Dict, confidence_results: Dict) -> Dict:
    """Generate the auto-config for simple_tier1_retrieval.py"""
    
    config = {
        'brand_priority': [],  # For brand detection
        'source_detection': {},  # Brand -> keywords for source detection
        'brand_retailer_map': {},  # Placeholder - needs manual input
        'generated_at': datetime.now().isoformat(),
    }
    
    # Only include HIGH and MEDIUM confidence brands
    included_brands = confidence_results['HIGH'] + confidence_results['MEDIUM']
    
    for item in included_brands:
        brand_name = item['brand']
        data = brands[brand_name]
        
        # Generate keywords
        keywords = generate_brand_keywords(brand_name, data)
        
        # Add to brand_priority list
        for kw in keywords['brand_keywords']:
            if kw and len(kw) > 1:
                config['brand_priority'].append((kw, brand_name))
        
        # Add significant product keywords to brand priority
        for kw in keywords['product_keywords'][:5]:  # Top 5 product keywords
            if kw and len(kw) > 2:
                config['brand_priority'].append((kw, brand_name))
        
        # Source detection keywords
        all_keywords = keywords['brand_keywords'] + keywords['product_keywords'][:10]
        config['source_detection'][brand_name] = {
            'keywords': list(set(all_keywords)),
            'source_name': f"{brand_name} Deep Dive",
            'trades': data['trades'],
            'categories': data['categories'],
        }
        
        # Retailer map placeholder
        config['brand_retailer_map'][brand_name] = ['PlaceMakers', 'ITM', 'Bunnings']  # Default, needs manual update
    
    return config


# =============================================================================
# CODE GENERATION
# =============================================================================

def generate_retrieval_code(config: Dict) -> str:
    """Generate Python code snippet for simple_tier1_retrieval.py"""
    
    code = []
    code.append("# " + "=" * 70)
    code.append("# AUTO-GENERATED BRAND DETECTION (from auto_config_generator.py)")
    code.append(f"# Generated: {config['generated_at']}")
    code.append("# " + "=" * 70)
    code.append("")
    
    # Brand Priority List
    code.append("# Add these to brand_priority list in simple_tier1_retrieval.py:")
    code.append("AUTO_BRAND_PRIORITY = [")
    for keyword, brand in sorted(set(config['brand_priority']), key=lambda x: x[1]):
        code.append(f"    ('{keyword}', '{brand}'),")
    code.append("]")
    code.append("")
    
    # Source Detection
    code.append("# Add these to source detection in get_relevant_sources():")
    code.append("AUTO_SOURCE_DETECTION = {")
    for brand_name, data in config['source_detection'].items():
        keywords_str = ', '.join(f"'{kw}'" for kw in data['keywords'][:15])
        code.append(f"    '{brand_name}': {{")
        code.append(f"        'keywords': [{keywords_str}],")
        code.append(f"        'source_name': '{data['source_name']}',")
        code.append(f"    }},")
    code.append("}")
    code.append("")
    
    return '\n'.join(code)


# =============================================================================
# MAIN
# =============================================================================

def main(apply_config: bool = False):
    print("\n" + "=" * 70)
    print("🤖 STRYDA AUTO-CONFIG GENERATOR")
    print("   Scanning database and generating brand detection rules...")
    print("=" * 70)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Scan database
    brands = scan_database()
    
    if not brands:
        print("❌ No brands found in database!")
        return
    
    # Generate report
    print("\n📋 Generating Low Confidence Report...")
    report_text, confidence_results = generate_report(brands)
    
    # Print report
    print("\n" + report_text)
    
    # Save report
    report_file = os.path.join(OUTPUT_DIR, f'confidence_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    with open(report_file, 'w') as f:
        f.write(report_text)
    print(f"\n💾 Report saved to: {report_file}")
    
    # Generate config
    print("\n⚙️  Generating auto-config...")
    config = generate_config(brands, confidence_results)
    
    # Save config as JSON
    config_file = os.path.join(OUTPUT_DIR, 'auto_config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2, default=str)
    print(f"💾 Config saved to: {config_file}")
    
    # Generate code snippet
    code_snippet = generate_retrieval_code(config)
    code_file = os.path.join(OUTPUT_DIR, 'retrieval_code_snippet.py')
    with open(code_file, 'w') as f:
        f.write(code_snippet)
    print(f"💾 Code snippet saved to: {code_file}")
    
    # Summary
    high_count = len(confidence_results['HIGH'])
    medium_count = len(confidence_results['MEDIUM'])
    low_count = len(confidence_results['LOW'])
    
    print("\n" + "=" * 70)
    print("✅ AUTO-CONFIG GENERATION COMPLETE")
    print("=" * 70)
    print(f"   HIGH Confidence:   {high_count} brands (ready for production)")
    print(f"   MEDIUM Confidence: {medium_count} brands (review recommended)")
    print(f"   LOW Confidence:    {low_count} brands (manual review required)")
    print(f"\n   Output files in: {OUTPUT_DIR}")
    print("=" * 70)
    
    if apply_config:
        print("\n🔧 Applying config to retrieval file...")
        # TODO: Implement auto-apply logic
        print("   Auto-apply not yet implemented. Please manually review and apply.")
    
    return config, confidence_results


if __name__ == "__main__":
    apply_flag = '--apply' in sys.argv
    main(apply_config=apply_flag)
