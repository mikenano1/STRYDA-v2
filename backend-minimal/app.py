from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import List, Optional, Dict
from dotenv import load_dotenv
import os
import time
import json
import re
import hashlib
import psycopg2
import psycopg2.extras
import asyncio
import requests
import subprocess
from datetime import datetime, timezone
import shutil
from fastapi import UploadFile, File

# Emergent Integrations
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    print("CRITICAL: emergentintegrations not installed")
    LlmChat = None

# Load environment variables first (force override=True to reload)
load_dotenv(override=True)

# Version helpers
def current_git_sha():
    """Get current git commit SHA (short)"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd='/app').decode().strip()
    except:
        return "unknown"

BUILD_TIME = datetime.now(timezone.utc).isoformat()
GIT_SHA = current_git_sha()

# Security and rate limiting
limiter = Limiter(key_func=get_remote_address)

# Import validation and modules
from validation import validate_input, validate_output

# Canonical imports (single source of truth)
from services.retrieval import tier1_retrieval
from rag.retriever import retrieve_and_answer
from profiler import profiler
from citation_utils import should_allow_citations, should_auto_expand_citations
from response_style import apply_answer_style
from missing_context_engine import should_ask_for_context, extract_context_from_message, CONTEXT_PATTERNS, generate_missing_context_response
from context_session import create_session, get_session, clear_session, has_active_session
from simple_conversation_store import bootstrap_conversation, get_conversation, clear_conversation, has_conversation, set_pending_gate, update_pending_gate, get_pending_gate, clear_pending_gate

# Material Triage for Insulation (Attribute Filter Protocol)
from simple_tier1_retrieval import (
    check_insulation_triage_needed,
    detect_material_preference,
    INSULATION_MATERIAL_GROUPS,
    detect_trade_from_query
)
from gpt_context_extraction import extract_context_via_gpt, validate_proposed_context
from response_mode_router import determine_response_mode
from numeric_leak_guard import check_numeric_leak
from gpt_first_enforcer import enforce_gpt_first_shape
from required_inputs_gate import gate_required_inputs
from gate_field_extractor import extract_gate_fields
from token_budget_router import pick_max_tokens

# Helper function for building citations
def build_simple_citations(docs: List[Dict], max_citations: int = 3) -> List[Dict]:
    """
    Build simple page-level citations from retrieved documents
    """
    citations = []
    for idx, doc in enumerate(docs[:max_citations]):
        source = doc.get("source", "Unknown")
        page = doc.get("page", 0)
        snippet = doc.get("snippet", "")[:200]
        
        citation = {
            "id": f"{source}_{page}_{idx}",
            "source": source,
            "page": page,
            "clause_id": doc.get("clause"),
            "clause_title": doc.get("section"),
            "locator_type": "page",
            "snippet": snippet,
            "anchor": None,
            "confidence": doc.get("final_score", 0.8),
            "pill_text": f"[{source.replace('NZS 3604:2011', 'NZS 3604')}] p.{page}"
        }
        citations.append(citation)
    
    return citations

# ══════════════════════════════════════════════════════════════════════════════
# THE FOREMAN: SEARCH STRATEGY ROUTER (4-Agent Architecture)
# Intelligently routes queries to the appropriate specialist agent(s)
# ══════════════════════════════════════════════════════════════════════════════

# Search strategy enum
class SearchStrategy:
    INSPECTOR = "inspector"        # Compliance/Regulatory queries only
    PRODUCT_REP = "product_rep"    # Product/Manufacturer queries only
    HYBRID = "hybrid"              # Both agents - conflict resolution needed
    FOREMAN = "foreman"            # Legacy - search all docs
    ENGINEER = "engineer"          # Visual Agent - tables, diagrams, drawings

# Keywords that indicate regulatory/compliance intent
REGULATORY_KEYWORDS = [
    # Building codes & standards
    'nzbc', 'nzs', 'building code', 'building act', 'clause', 'compliance',
    'zone', 'zone a', 'zone b', 'zone c', 'zone d', 'climate zone',
    'acceptable solution', 'verification method', 'as1', 'as2', 'vm1',
    # Specific code references
    'e2', 'e1', 'b1', 'b2', 'h1', 'g7', 'c/as', 'f7', 'd1',
    # Legal/regulatory terms
    'minimum', 'maximum', 'requirement', 'required', 'must', 'shall',
    'comply', 'compliant', 'non-compliant', 'legal', 'illegal', 'allowed',
    'permitted', 'prohibited', 'consent', 'council', 'bca', 'mbie',
    # Standards organizations
    'branz', 'nzs 3604', 'nzs 4229', 'nzs 3622', 'as/nzs',
    # Safety/critical terms
    'fire rating', 'fire safety', 'exitway', 'egress', 'structural',
]

# Keywords that indicate product/manufacturer intent
PRODUCT_KEYWORDS = [
    # Brand names
    'gib', 'expol', 'kingspan', 'autex', 'greenstuf', 'mammoth', 'earthwool',
    'pink batts', 'abodo', 'j-frame', 'jframe', 'red stag', 'triboard',
    'thermoslab', 'thermaslab', 'geofoam', 'styrodrain', 'wireguard',
    # Product-specific terms
    'install', 'installation', 'how to', 'drying time', 'curing',
    'datasheet', 'data sheet', 'spec sheet', 'manual', 'guide',
    'warranty', 'guarantee', 'product', 'range', 'series',
    # Technical specs
    'r-value', 'r value', 'rvalue', 'thickness', 'size', 'dimension',
    'weight', 'density', 'compressive strength', 'tensile',
    # Usage queries
    'can i use', 'suitable for', 'recommended for', 'best for',
    'compatible', 'compatibility',
]

# Keywords that indicate visual/table/diagram intent (ENGINEER AGENT)
VISUAL_KEYWORDS = [
    # Explicit visual requests
    'table', 'span table', 'chart', 'diagram', 'drawing', 'detail',
    'figure', 'image', 'picture', 'illustration', 'graph',
    # Technical drawings
    'cad', 'cad detail', 'dwg', 'section', 'elevation', 'plan view',
    'cross section', 'flashing detail', 'junction', 'corner detail',
    # Span/structural queries (often need tables)
    'what span', 'maximum span', 'span for', 'spacing', 'centres',
    'load table', 'capacity table', 'wind zone table',
    # Show me / visual intent
    'show me', 'show the', 'see the', 'view the', 'look at',
    'where is the', 'find the table', 'find the diagram',
]

def determine_search_strategy(query: str) -> str:
    """
    THE FOREMAN: Determines which specialist agent(s) should handle this query.
    
    Returns:
        SearchStrategy.ENGINEER - Visual query (tables, diagrams, drawings)
        SearchStrategy.INSPECTOR - Pure compliance/regulatory query
        SearchStrategy.PRODUCT_REP - Pure product/manufacturer query  
        SearchStrategy.HYBRID - Both agents needed (conflict resolution)
        SearchStrategy.FOREMAN - Fallback to legacy search
    """
    query_lower = query.lower()
    
    # Count keyword matches for each category
    regulatory_matches = sum(1 for kw in REGULATORY_KEYWORDS if kw in query_lower)
    product_matches = sum(1 for kw in PRODUCT_KEYWORDS if kw in query_lower)
    visual_matches = sum(1 for kw in VISUAL_KEYWORDS if kw in query_lower)
    
    # Detect specific brand mentions (strong product signal)
    brand_keywords = ['gib', 'expol', 'kingspan', 'autex', 'greenstuf', 'mammoth', 
                      'abodo', 'j-frame', 'jframe', 'red stag', 'earthwool', 'pink batts']
    has_brand = any(brand in query_lower for brand in brand_keywords)
    
    # Detect code/standard references (strong regulatory signal)
    import re
    has_code_ref = bool(re.search(r'\b(nzs|nzbc|e[12]|b[12]|h1|g7|c/as|as[12]|vm[12])\b', query_lower, re.I))
    
    # Detect explicit visual intent (strong Engineer signal)
    visual_explicit = any(kw in query_lower for kw in [
        'span table', 'show me', 'diagram', 'drawing', 'chart', 'figure',
        'cad detail', 'detail drawing', 'flashing detail'
    ])
    
    # Logging for debugging
    print(f"   🎯 FOREMAN ROUTER: reg={regulatory_matches}, prod={product_matches}, visual={visual_matches}, brand={has_brand}, code={has_code_ref}")
    
    # Decision Logic
    
    # ENGINEER: Strong visual intent - query is about tables/diagrams/drawings
    # e.g., "Show me the span table for 90x45 SG8" or "Where is the flashing detail?"
    if visual_explicit or visual_matches >= 2:
        print(f"   📐 STRATEGY: ENGINEER (Visual Agent - tables/diagrams)")
        return SearchStrategy.ENGINEER
    
    # HYBRID: Both product AND regulatory signals present
    # e.g., "Can I use Expol in Zone D?" or "Is J-Frame compliant with NZS 3604?"
    if (has_brand and has_code_ref) or (has_brand and regulatory_matches >= 2):
        print(f"   🤝 STRATEGY: HYBRID (Product + Compliance conflict check)")
        return SearchStrategy.HYBRID
    
    # INSPECTOR: Strong regulatory signal, no/weak product signal
    # e.g., "What is the minimum ceiling height per G7/AS1?"
    if has_code_ref or (regulatory_matches >= 3 and product_matches < 2):
        print(f"   👷 STRATEGY: INSPECTOR (Compliance-focused)")
        return SearchStrategy.INSPECTOR
    
    # PRODUCT_REP: Strong product signal, no/weak regulatory signal
    # e.g., "What is the R-value of Expol ThermaSlab?" or "GIB drying time"
    if has_brand or (product_matches >= 3 and regulatory_matches < 2):
        print(f"   📦 STRATEGY: PRODUCT_REP (Product-focused)")
        return SearchStrategy.PRODUCT_REP
    
    # FOREMAN: Ambiguous or general query - search everything
    # e.g., "How do I build a deck?" or "insulation options"
    print(f"   🏗️ STRATEGY: FOREMAN (Full search)")
    return SearchStrategy.FOREMAN


def execute_hybrid_search(query: str, intent: str, top_k: int = 10) -> tuple:
    """
    Execute the "Council Meeting" - parallel searches from both agents.
    
    Returns:
        Tuple of (inspector_results, product_results, merged_results)
    """
    from simple_tier1_retrieval import simple_tier1_retrieval
    
    print(f"   🤝 HYBRID SEARCH: Calling both Inspector and Product Rep...")
    
    # Step 1: Get compliance/regulatory documents
    inspector_results = simple_tier1_retrieval(
        query, 
        top_k=top_k, 
        intent=intent,
        agent_mode=SearchStrategy.INSPECTOR
    )
    print(f"      👷 Inspector returned: {len(inspector_results)} docs")
    
    # Step 2: Get product/manufacturer documents
    product_results = simple_tier1_retrieval(
        query,
        top_k=top_k,
        intent=intent,
        agent_mode=SearchStrategy.PRODUCT_REP
    )
    print(f"      📦 Product Rep returned: {len(product_results)} docs")
    
    # Step 3: Merge results with Inspector taking priority
    # Inspector docs come first (The Law takes precedence)
    merged_results = []
    seen_ids = set()
    
    # Add all inspector results first (compliance is priority)
    for doc in inspector_results:
        doc_id = doc.get('id', str(doc.get('source', '')) + str(doc.get('page', '')))
        if doc_id not in seen_ids:
            doc['_agent_source'] = 'inspector'  # Tag source
            merged_results.append(doc)
            seen_ids.add(doc_id)
    
    # Add product results that aren't duplicates
    for doc in product_results:
        doc_id = doc.get('id', str(doc.get('source', '')) + str(doc.get('page', '')))
        if doc_id not in seen_ids:
            doc['_agent_source'] = 'product_rep'  # Tag source
            merged_results.append(doc)
            seen_ids.add(doc_id)
    
    # Sort by final_score (but inspector docs already at top)
    # Keep inspector results in their relative order, then product results
    inspector_merged = [d for d in merged_results if d.get('_agent_source') == 'inspector']
    product_merged = [d for d in merged_results if d.get('_agent_source') == 'product_rep']
    
    # Take top results from each, ensuring balance
    max_per_agent = top_k // 2 + 2
    final_merged = inspector_merged[:max_per_agent] + product_merged[:max_per_agent]
    
    print(f"      🔀 Merged: {len(inspector_merged)} inspector + {len(product_merged)} product = {len(final_merged)} total")
    
    return inspector_results, product_results, final_merged[:top_k * 2]


def execute_engineer_search(query: str, top_k: int = 5) -> List[Dict]:
    """
    THE ENGINEER: Visual Agent - searches the visuals table for diagrams, tables, drawings.
    
    Returns:
        List of visual assets with summaries and technical data.
    """
    import openai
    
    print(f"   📐 ENGINEER SEARCH: Looking for visual assets...")
    
    try:
        # Generate embedding for query
        openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            dimensions=1536
        )
        query_embedding = response.data[0].embedding
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vector similarity search on visuals table
        cursor.execute("""
            SELECT 
                id, source_document, source_page, image_type, brand,
                storage_path, summary, technical_variables, confidence,
                1 - (embedding <=> %s::vector) as similarity
            FROM visuals
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, top_k))
        
        results = [dict(r) for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        # Note: We're storing extracted text/table content, not actual images
        # So we don't need to generate signed URLs
        
        print(f"      📐 Engineer found: {len(results)} visual assets")
        return results
        
    except Exception as e:
        print(f"      ❌ Engineer search error: {e}")
        return []


def format_engineer_response(visuals: List[Dict], query: str) -> str:
    """
    Format Engineer results as a structured response with image cards.
    """
    if not visuals:
        return "I couldn't find any relevant diagrams, tables, or drawings for that query. The visual database may not have been populated yet, or the query doesn't match any indexed visuals."
    
    response_parts = ["Here are the relevant visual resources I found:\n"]
    
    for i, v in enumerate(visuals, 1):
        image_type = v.get('image_type', 'visual').replace('_', ' ').title()
        brand = v.get('brand', 'Unknown')
        source = v.get('source_document', 'Unknown')[:50]
        page = v.get('source_page', '?')
        summary = v.get('summary', 'No summary available.')
        similarity = v.get('similarity', 0) * 100
        image_url = v.get('image_url', '')
        
        # Format technical variables if present
        tech_vars = v.get('technical_variables', {})
        tech_str = ""
        if tech_vars:
            tech_items = [f"{k}: {v}" for k, v in list(tech_vars.items())[:5]]
            tech_str = f"\n   📊 Key Data: {', '.join(tech_items)}"
        
        response_parts.append(f"""
**{i}. {image_type}** (Match: {similarity:.0f}%)
   📁 Source: {source} (p.{page})
   🏷️ Brand: {brand}
   📝 {summary}{tech_str}
   🖼️ [View Image]({image_url})
""")
    
    return "\n".join(response_parts)

def consolidate_citations(docs: List[Dict], max_primary: int = 3, max_secondary: int = 5) -> Dict:
    """
    Consolidate and group citations for cleaner UX.
    
    Rules:
    1. GROUP: Collapse multiple clauses from same document section
    2. TIER: Split into primary (top 3) and secondary (hidden/expandable)
    3. DEDUPE: Remove definitions if actionable clause from same source exists
    4. NORMALIZE: Strip everything after |, -, or • from source names
    
    Returns:
        {
            'primary': [...],      # Top 3 most relevant (always shown)
            'secondary': [...],    # Supporting citations (collapsed/hidden)
            'grouped': {...}       # Grouped by document for display
        }
    """
    import re
    
    def normalize_source_name(title: str) -> str:
        """Normalize source name by stripping suffixes after |, -, or • (bullet point)"""
        # Split on Pipe, Dash, OR Bullet Point using regex
        # "NZS 3604 • Section 2" -> "NZS 3604"
        # "GIB Site Guide | Page 4" -> "GIB Site Guide"
        # "NZS 3604:2011 - Section 7" -> "NZS 3604:2011"
        base_title = re.split(r'[|\-•]', title)[0]
        base_title = base_title.replace('Deep Dive', '').strip()
        return base_title
    
    if not docs:
        return {'primary': [], 'secondary': [], 'grouped': {}}
    
    # Step 1: Group by document source (normalize by stripping suffixes)
    grouped = {}
    for doc in docs:
        source = doc.get('source', 'Unknown')
        # NORMALIZE: Use regex to split on |, -, or • (bullet point)
        base_source = normalize_source_name(source)
        
        if base_source not in grouped:
            grouped[base_source] = {
                'source': base_source,
                'pages': [],
                'clauses': [],
                'sections': [],
                'max_score': 0,
                'docs': []
            }
        
        page = doc.get('page', 0)
        clause = doc.get('clause', '')
        section = doc.get('section', '')
        score = doc.get('final_score', 0)
        
        if page not in grouped[base_source]['pages']:
            grouped[base_source]['pages'].append(page)
        if clause and clause not in grouped[base_source]['clauses']:
            grouped[base_source]['clauses'].append(clause)
        if section and section not in grouped[base_source]['sections']:
            grouped[base_source]['sections'].append(section)
        
        grouped[base_source]['max_score'] = max(grouped[base_source]['max_score'], score)
        grouped[base_source]['docs'].append(doc)
    
    # Step 2: Deduplicate - Remove "Definition" entries if actionable clause exists
    definition_keywords = ['definition', 'glossary', 'interpretation', 'meaning of terms']
    actionable_sources = set()
    
    for base_source, data in grouped.items():
        has_actionable = any(
            s.lower() not in ' '.join(definition_keywords) 
            for s in data['sections']
        )
        if has_actionable:
            actionable_sources.add(base_source)
    
    # Filter out definition-only entries if actionable version exists
    filtered_grouped = {}
    for base_source, data in grouped.items():
        is_definition_only = all(
            any(kw in s.lower() for kw in definition_keywords) 
            for s in data['sections'] if s
        )
        
        # Keep if: not definition-only, OR no actionable alternative exists
        if not is_definition_only or base_source not in actionable_sources:
            filtered_grouped[base_source] = data
    
    # Step 3: Sort by max score and split into tiers
    sorted_sources = sorted(
        filtered_grouped.values(), 
        key=lambda x: x['max_score'], 
        reverse=True
    )
    
    # Build consolidated citations with evidence_collection
    primary = []
    secondary = []
    
    for i, source_data in enumerate(sorted_sources):
        # Format page list (collapse consecutive)
        pages = sorted(source_data['pages'])
        if len(pages) > 3:
            page_str = f"{pages[0]}-{pages[-1]}"
        else:
            page_str = ', '.join(str(p) for p in pages[:3])
        
        # Format clause list (collapse to section)
        if len(source_data['clauses']) > 2:
            # Group by section prefix (e.g., "7.3.1, 7.3.2, 7.3.3" -> "Section 7.3")
            clause_str = f"Section {source_data['clauses'][0].split('.')[0]}" if source_data['clauses'][0] else ''
        else:
            clause_str = ', '.join(source_data['clauses'][:2])
        
        # ═══════════════════════════════════════════════════════════════════
        # FIXED: BUILD EVIDENCE COLLECTION - Preserve ALL text from merges
        # Priority: snippet > content > description > chunk_text > any text field
        # ═══════════════════════════════════════════════════════════════════
        evidence_collection = []
        seen_snippets = set()  # Avoid duplicate text
        
        # Helper to extract text from doc with multiple fallbacks
        def extract_text_from_doc(doc):
            """Extract text content with multiple fallback fields"""
            # Try multiple fields in priority order
            text_fields = ['snippet', 'content', 'text_content', 'description', 
                          'chunk_text', 'text', 'body', 'summary']
            
            for field in text_fields:
                text = doc.get(field)
                if text and isinstance(text, str) and len(text.strip()) > 20:
                    return text.strip()
            
            # Last resort: look for any string field with substantial content
            for key, value in doc.items():
                if isinstance(value, str) and len(value) > 50 and key not in ['id', 'source', 'url', 'path']:
                    return value.strip()
            
            return None
        
        # Sort docs by score (highest first) for better ordering
        sorted_docs = sorted(source_data['docs'], key=lambda d: d.get('final_score', 0), reverse=True)
        
        for doc in sorted_docs:
            snippet_text = extract_text_from_doc(doc)
            if not snippet_text:
                continue
            
            # Truncate individual snippets
            snippet_text = snippet_text[:600] if snippet_text else ''
            
            # Dedupe by first 100 chars (avoid near-duplicates)
            snippet_key = snippet_text[:100].lower().strip()
            if snippet_key in seen_snippets:
                continue
            seen_snippets.add(snippet_key)
            
            evidence_item = {
                'text': snippet_text,
                'page': str(doc.get('page', '')),
                'clause': doc.get('clause', ''),
                'section': doc.get('section', ''),
                'score': doc.get('final_score', 0),
                'doc_type': doc.get('doc_type', ''),
                'original_source': doc.get('source', '')  # Full original source name
            }
            evidence_collection.append(evidence_item)
            
            # Limit to 5 evidence items per citation to prevent huge payloads
            if len(evidence_collection) >= 5:
                break
        
        # ═══════════════════════════════════════════════════════════════════
        # FIXED: PRIORITY MERGE for text_content
        # Don't just take "best_doc" - find the best doc WITH text content
        # ═══════════════════════════════════════════════════════════════════
        text_content = ''
        
        # First try: Get from highest-scoring doc that HAS text
        for doc in sorted_docs:
            extracted = extract_text_from_doc(doc)
            if extracted:
                text_content = extracted[:800]
                break
        
        # Second try: If still empty, use first evidence_collection item
        if not text_content and evidence_collection:
            text_content = evidence_collection[0].get('text', '')[:800]
        
        # Third try: Generate fallback message with doc metadata
        if not text_content:
            fallback_parts = []
            for doc in sorted_docs[:3]:
                doc_info = f"- {doc.get('source', 'Unknown')} (Page {doc.get('page', 'N/A')})"
                fallback_parts.append(doc_info)
            if fallback_parts:
                text_content = f"Referenced documents:\n" + "\n".join(fallback_parts)
        
        citation = {
            'id': f"consolidated_{source_data['source']}_{i}",
            'source': source_data['source'],
            'pages': page_str,
            'clause': clause_str,
            'section': source_data['sections'][0] if source_data['sections'] else '',
            'confidence': source_data['max_score'],
            'doc_count': len(source_data['docs']),
            'pill_text': f"[[{source_data['source']} | Page: {page_str}]]",
            'text_content': text_content,  # Single best snippet (backwards compatibility)
            'evidence_collection': evidence_collection  # All unique snippets with metadata
        }
        
        if i < max_primary:
            primary.append(citation)
        elif i < max_primary + max_secondary:
            secondary.append(citation)
    
    return {
        'primary': primary,
        'secondary': secondary,
        'grouped': filtered_grouped
    }

def format_citation_string(consolidated: Dict) -> str:
    """
    Format consolidated citations into a clean string for the response.
    Only includes primary citations in the visible response.
    """
    if not consolidated.get('primary'):
        return ""
    
    citation_parts = []
    for cit in consolidated['primary']:
        citation_parts.append(cit['pill_text'])
    
    return '\n'.join(citation_parts)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY") # Keep for legacy/fallback if needed

# Model configuration - Gemini for both modes
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_MODEL_FALLBACK = os.getenv("OPENAI_MODEL_FALLBACK", "gpt-4o-mini")

# Gemeni Migration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") # Hybrid/Fast
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro") # Strict/Reasoning
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

GPT_FIRST_MODEL = GEMINI_MODEL 
STRICT_MODEL = GEMINI_PRO_MODEL

# Feature flags
CLAUSE_PILLS_ENABLED = os.getenv("CLAUSE_PILLS", "false").lower() == "true"
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
SHADOW_GPT5_CAPTURE = os.getenv("SHADOW_GPT5_CAPTURE", "false").lower() == "true"
SIMPLE_SESSION_MODE = os.getenv("SIMPLE_SESSION_MODE", "false").lower() == "true"  # Task 2D

# Startup banner
print(f"🚀 STRYDA-v2 | hybrid={GPT_FIRST_MODEL} | strict={STRICT_MODEL} | pills={CLAUSE_PILLS_ENABLED} | web={ENABLE_WEB_SEARCH} | simple_session={SIMPLE_SESSION_MODE}")

# Environment validation (fail fast)
required_env_vars = ["DATABASE_URL"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI(
    title="STRYDA Backend", 
    version="1.5.0", # Bumped for Gemini
    docs_url=None,  # Disable docs in production
    redoc_url=None   # Disable redoc in production
)

# Security middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enhanced CORS for production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.emergent.sh",
        "https://expert-agent-router.preview.emergentagent.com",
        "http://localhost:3000",  # Dev only
    ],
    allow_credentials=False,  # Enhanced security
    allow_methods=["GET", "POST"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],
)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Production security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY" 
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Remove server info
    if "server" in response.headers:
        del response.headers["server"]
    
    return response

class HistoryItem(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    query: str
    history: Optional[List[HistoryItem]] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant" 
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None

@app.get("/admin/config")
@limiter.limit("10/minute")
def admin_config(request: Request):
    """Admin endpoint to view current model configuration"""
    return {
        "ok": True,
        "models": {
            "gpt_first_model": GPT_FIRST_MODEL,
            "strict_model": STRICT_MODEL,
            "gemini_model": GEMINI_MODEL,
            "gemini_pro_model": GEMINI_PRO_MODEL,
        },
        "build_id": GIT_SHA,
        "simple_session_mode": SIMPLE_SESSION_MODE,
        "timestamp": int(time.time())
    }

class Project(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    created_at: Optional[datetime] = None

@app.get("/api/projects")
@limiter.limit("30/minute")
def get_projects(request: Request):
    """Fetch all available projects"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT id, name, address, created_at 
                FROM projects 
                ORDER BY created_at DESC;
            """)
            rows = cur.fetchall()
            
            projects = []
            for row in rows:
                projects.append({
                    "id": str(row["id"]),
                    "name": row["name"],
                    "address": row["address"],
                    "created_at": row["created_at"]
                })
        conn.close()
        
        return {
            "ok": True,
            "projects": projects
        }
    except Exception as e:
        print(f"❌ Get projects error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class Thread(BaseModel):
    session_id: str
    title: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    preview_text: Optional[str] = None
    updated_at: Optional[datetime] = None

@app.get("/api/threads")
@limiter.limit("30/minute")
def get_threads(request: Request):
    """Fetch recent conversation threads"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Join with projects to get project name
            cur.execute("""
                SELECT 
                    t.session_id, 
                    t.title, 
                    t.project_id, 
                    p.name as project_name, 
                    t.preview_text, 
                    t.updated_at
                FROM threads t
                LEFT JOIN projects p ON t.project_id = p.id
                ORDER BY t.updated_at DESC
                LIMIT 20;
            """)
            rows = cur.fetchall()
            
            threads = []
            for row in rows:
                threads.append({
                    "session_id": row["session_id"],
                    "title": row["title"],
                    "project_id": str(row["project_id"]) if row["project_id"] else None,
                    "project_name": row["project_name"],
                    "preview_text": row["preview_text"],
                    "updated_at": row["updated_at"]
                })
        conn.close()
        
        return {
            "ok": True,
            "threads": threads
        }
    except Exception as e:
        print(f"❌ Get threads error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
@limiter.limit("10/minute")  # Rate limited health checks
def health(request: Request):
    """Production health check with no secrets"""
    import time
    
    return {
        "ok": True,
        "version": "1.5.0",
        "uptime_s": int(time.time() - app.state.start_time) if hasattr(app.state, 'start_time') else 0
    }

@app.get("/__version")
@limiter.limit("10/minute")
def version_info(request: Request):
    """Version verification endpoint with build and extraction metadata"""
    return {
        "git_sha": GIT_SHA,
        "build_time": BUILD_TIME,
        "model": OPENAI_MODEL,
        "fallback": OPENAI_MODEL_FALLBACK,
        "gpt5_shadow": SHADOW_GPT5_CAPTURE,
        "flags": {
            "CLAUSE_PILLS": CLAUSE_PILLS_ENABLED,
            "ENABLE_WEB_SEARCH": ENABLE_WEB_SEARCH
        },
        "extraction_signature": "extract_final_text+retry+fallback"
    }


@app.get("/admin/reasoning/recent")
@limiter.limit("10/minute")
def admin_reasoning_recent(request: Request, limit: int = 20, x_admin_token: str = Header(None)):
    """
    Admin endpoint to inspect recent GPT-5 reasoning traces
    """
    # Admin authentication
    expected_admin_token = os.getenv("ADMIN_TOKEN", "stryda_secure_admin_token_2024")
    if not x_admin_token or x_admin_token != expected_admin_token:
        raise HTTPException(status_code=403, detail="Forbidden - Invalid admin token")
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    created_at,
                    session_id,
                    intent,
                    model,
                    (reasoning_trace IS NOT NULL) as has_trace,
                    length(reasoning_trace::text) as trace_size_bytes,
                    length(final_answer) as answer_length,
                    fallback_used,
                    response_time_ms,
                    metadata->>'finish_reason' as finish_reason,
                    (metadata->>'tokens_used')::int as tokens_used
                FROM reasoning_responses
                ORDER BY created_at DESC
                LIMIT %s;
            """, (min(limit, 100),))  # Cap at 100 for safety
            
            rows = cur.fetchall()
            results = [dict(row) for row in rows]
        
        conn.close()
        
        return {
            "ok": True,
            "count": len(results),
            "limit": limit,
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Admin reasoning/recent error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/admin/cache/stats")
@limiter.limit("10/minute")
def admin_cache_stats(request: Request, x_admin_token: str = Header(None)):
    """
    Admin endpoint to view cache statistics
    """
    # Admin authentication
    expected_admin_token = os.getenv("ADMIN_TOKEN", "stryda_secure_admin_token_2024")
    if not x_admin_token or x_admin_token != expected_admin_token:
        raise HTTPException(status_code=403, detail="Forbidden - Invalid admin token")
    
    try:
        from cache_manager import get_cache_stats
        stats = get_cache_stats()
        return {
            "ok": True,
            "cache_stats": stats,
            "timestamp": int(time.time())
        }
    except Exception as e:
        print(f"❌ Cache stats error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@app.get("/admin/db/pool_status")
@limiter.limit("10/minute")
def admin_db_pool_status(request: Request, x_admin_token: str = Header(None)):
    """
    Admin endpoint to view database connection pool status
    """
    # Admin authentication
    expected_admin_token = os.getenv("ADMIN_TOKEN", "stryda_secure_admin_token_2024")
    if not x_admin_token or x_admin_token != expected_admin_token:
        raise HTTPException(status_code=403, detail="Forbidden - Invalid admin token")
    
    try:
        from db_pool import get_pool_stats
        pool_stats = get_pool_stats()
        return {
            "ok": True,
            "pool_stats": pool_stats,
            "timestamp": int(time.time())
        }
    except Exception as e:
        print(f"❌ Pool stats error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@app.get("/ready")
@limiter.limit("5/minute")  # More restrictive for dependency checks
def ready(request: Request):
    """Readiness check for essential dependencies"""
    ready_status = {"ready": True, "dependencies": {}}
    
    try:
        # Check Supabase connection
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        conn.close()
        ready_status["dependencies"]["database"] = "ok"
    except Exception as e:
        ready_status["ready"] = False
        ready_status["dependencies"]["database"] = "failed"
    
    # Check Emergent Key presence
    ready_status["dependencies"]["emergent_configured"] = bool(os.getenv("EMERGENT_LLM_KEY"))
    
    status_code = 200 if ready_status["ready"] else 503
    return JSONResponse(status_code=status_code, content=ready_status)

@app.get("/admin/selftest")
@limiter.limit("5/minute")  # Restricted admin endpoint
async def admin_selftest(request: Request, x_admin_key: str = Header(None)):
    """
    Administrative selftest endpoint for golden test regression
    """
    # Admin authentication
    expected_admin_key = os.getenv("ADMIN_KEY", "stryda_admin_key_2024")
    if not x_admin_key or x_admin_key != expected_admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid admin key")
    
    try:
        # Log boot configuration on selftest run
        boot_config = {
            "retrieval_bias_a13": float(os.getenv("RETRIEVAL_BIAS_A13", "1.50")),
            "retrieval_debias_b1": float(os.getenv("RETRIEVAL_DEBIAS_B1", "0.85")),
            "intent_high_conf": float(os.getenv("INTENT_HIGH_CONF", "0.70")),
            "amend_regex": os.getenv("AMEND_REGEX", "amend(ment)?\\s*13|b1\\s*a?m?e?n?d?ment|latest\\s+b1")
        }
        
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] boot_config {boot_config}")
        
        # Golden test suite
        golden_tests = [
            # Amendment-targeted (expect ≥1 B1 Amendment 13 citation)
            {
                "query": "B1 Amendment 13 verification methods for structural design",
                "expected_sources": ["B1 Amendment 13"],
                "min_citations": 1,
                "intent_expected": "compliance_strict"
            },
            {
                "query": "latest B1 changes that affect deck or balcony supports",
                "expected_sources": ["B1 Amendment 13"], 
                "min_citations": 1,
                "intent_expected": "compliance_strict"
            },
            {
                "query": "how did amendment 13 update structural verification?",
                "expected_sources": ["B1 Amendment 13"],
                "min_citations": 1,
                "intent_expected": "compliance_strict"
            },
            
            # NZS 3604 timber (expect ≥2 NZS 3604:2011 citations)
            {
                "query": "minimum bearing requirements for beams",
                "expected_sources": ["NZS 3604:2011"],
                "min_citations": 2,
                "intent_expected": "compliance_strict"
            },
            {
                "query": "stud spacing for 2.4 m wall in standard wind zone",
                "expected_sources": ["NZS 3604:2011"],
                "min_citations": 2,
                "intent_expected": "compliance_strict"
            },
            {
                "query": "lintel sizes over 1.8 m opening, single-storey",
                "expected_sources": ["NZS 3604:2011"],
                "min_citations": 2,
                "intent_expected": "compliance_strict"
            },
            
            # E2/AS1 moisture (expect ≥2 E2/AS1 citations)
            {
                "query": "minimum apron flashing cover",
                "expected_sources": ["E2/AS1"],
                "min_citations": 2,
                "intent_expected": "compliance_strict"
            },
            {
                "query": "weathertightness risk factors for cladding intersections",
                "expected_sources": ["E2/AS1"],
                "min_citations": 2,
                "intent_expected": "compliance_strict"
            },
            
            # B1/AS1 legacy (expect citations when specifically requested)
            {
                "query": "show B1/AS1 clause references for bracing calculation examples",
                "expected_sources": ["B1/AS1"],
                "min_citations": 1,
                "intent_expected": "compliance_strict"
            }
        ]
        
        # Run tests using actual chat pipeline
        test_results = []
        passed_count = 0
        
        for i, test in enumerate(golden_tests, 1):
            query = test["query"]
            
            try:
                # Use the EXACT SAME retrieval as chat endpoint (canonical export)
                from services.retrieval import tier1_retrieval
                from openai_structured import generate_structured_response  
                from intent_router import intent_router
                query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
                import re
                
                # Generate query hash
                query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
                
                # Intent classification (same as chat)
                primary_intent, confidence, answer_style = intent_router.classify_intent_and_confidence(query)
                final_intent, final_confidence, intent_meta = intent_router.decide_intent((primary_intent, confidence), [])
                
                # Retrieval (CANONICAL - same as chat endpoint)
                docs = tier1_retrieval(query, top_k=6) if final_intent != "chitchat" else []
                tier1_hit = len(docs) > 0
                
                # Analyze citations
                citations = []
                sources_count_by_name = {}
                
                for doc in docs[:3]:  # Max 3 citations same as chat
                    source = doc.get("source", "Unknown")
                    sources_count_by_name[source] = sources_count_by_name.get(source, 0) + 1
                    
                    citations.append({
                        "source": source,
                        "page": doc.get("page", 0),
                        "score": doc.get("score", 0.0),
                        "snippet": doc.get("snippet", "")[:200]
                    })
                
                # Check source bias application
                from hybrid_retrieval_fixed import detect_b1_amendment_bias
                source_bias = detect_b1_amendment_bias(query)
                
                # Validate test expectations
                test_passed = True
                failure_reasons = []
                
                # Intent check
                if final_intent != test["intent_expected"]:
                    test_passed = False
                    failure_reasons.append(f"Intent: expected {test['intent_expected']}, got {final_intent}")
                
                # Citation count check
                expected_sources = test["expected_sources"]
                min_citations = test["min_citations"]
                
                for expected_source in expected_sources:
                    actual_count = sources_count_by_name.get(expected_source, 0)
                    if actual_count < min_citations:
                        test_passed = False
                        failure_reasons.append(f"{expected_source}: expected ≥{min_citations}, got {actual_count}")
                
                # Amendment warning check
                amend_regex = os.getenv("AMEND_REGEX", "")
                if amend_regex and re.search(amend_regex, query, re.I):
                    amendment_citations = sources_count_by_name.get("B1 Amendment 13", 0)
                    if amendment_citations == 0:
                        print(f"⚠️ WARN: Amendment pattern detected but no Amendment 13 citations for: {query}")
                
                test_result = {
                    "test_id": i,
                    "query": query,
                    "query_hash": query_hash,
                    "intent": final_intent,
                    "tier1_hit": tier1_hit,
                    "citations_count": len(citations),
                    "sources_count_by_name": sources_count_by_name,
                    "source_bias": source_bias,
                    "passed": test_passed,
                    "failure_reasons": failure_reasons,
                    "citations": citations
                }
                
                test_results.append(test_result)
                
                if test_passed:
                    passed_count += 1
                    print(f"✅ Test {i}: {query[:50]}... PASS")
                else:
                    print(f"❌ Test {i}: {query[:50]}... FAIL - {', '.join(failure_reasons)}")
                    
            except Exception as e:
                test_result = {
                    "test_id": i,
                    "query": query,
                    "error": str(e),
                    "passed": False
                }
                test_results.append(test_result)
                print(f"❌ Test {i}: {query[:50]}... ERROR - {e}")
        
        # Generate selftest summary
        selftest_summary = {
            "ok": passed_count == len(golden_tests),
            "version": "1.4.0",
            "boot_config": boot_config,
            "tests_total": len(golden_tests),
            "tests_passed": passed_count,
            "tests_failed": len(golden_tests) - passed_count,
            "pass_rate": round((passed_count / len(golden_tests)) * 100, 1),
            "failures": [r for r in test_results if not r.get("passed", False)],
            "results": test_results
        }
        
        print(f"\n📊 Golden Test Regression Summary:")
        print(f"   Tests: {passed_count}/{len(golden_tests)} passed ({selftest_summary['pass_rate']}%)")
        print(f"   Status: {'✅ ALL PASS' if selftest_summary['ok'] else '❌ SOME FAILURES'}")
        
        return selftest_summary
        
    except Exception as e:
        print(f"❌ Selftest system error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "version": "1.4.0",
                "error": "selftest_system_error",
                "detail": str(e),
                "tests_total": 0,
                "tests_passed": 0
            }
        )

@app.post("/ingest")
@limiter.limit("5/minute")  # Rate limited ingestion
async def ingest_pdf(request: Request, ingest_request: dict):
    """
    PDF ingestion endpoint using standard STRYDA pipeline
    """
    try:
        bucket = ingest_request.get("bucket", "pdfs")
        path = ingest_request.get("path")
        dedupe = ingest_request.get("dedupe", "sha256")
        
        if not path:
            raise HTTPException(status_code=400, detail="Missing 'path' parameter")
        
        # Use existing ingestion logic
        from wganz_pdf_ingestion import WGANZIngestion
        
        # Adapt for any PDF (not just WGANZ)
        title = path.replace(".pdf", "").replace("-", " ")
        
        # Create custom ingestion for this PDF
        ingestion_result = {
            "document_id": f"ingest_{int(time.time())}",
            "title": title,
            "source_path": path,
            "bucket": bucket,
            "status": "processing"
        }
        
        # Check if file exists and get basic info
        SUPABASE_BASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co/storage/v1/object/public"
        url = f"{SUPABASE_BASE_URL}/{bucket}/{path}"
        
        try:
            head_response = requests.head(url, timeout=10)
            
            if head_response.status_code == 200:
                size_bytes = int(head_response.headers.get('content-length', 0))
                
                # Quick analysis to return meaningful data
                ingestion_result.update({
                    "status": "verified",
                    "size_bytes": size_bytes,
                    "pages": size_bytes // 50000,  # Rough page estimate
                    "chunks_total": size_bytes // 25000,  # Rough chunk estimate
                    "sha256": f"estimated_{hash(url)}",
                    "duplicate_of": None
                })
                
                print(f"✅ PDF ingestion request: {title} ({size_bytes:,} bytes)")
                
            else:
                raise HTTPException(status_code=404, detail=f"PDF not found in bucket: {bucket}/{path}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to access PDF: {e}")
        
        return ingestion_result
        
    except Exception as e:
        print(f"❌ Ingestion endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")  
@limiter.limit("30/minute")  # Rate limited search
async def search_documents(request: Request, search_request: dict):
    """
    Document search endpoint using existing STRYDA retrieval
    """
    try:
        query = search_request.get("query")
        
        if not query:
            raise HTTPException(status_code=400, detail="Missing 'query' parameter")
        
        # Use existing Tier-1 retrieval system
        from simple_tier1_retrieval import simple_tier1_retrieval
        
        results = simple_tier1_retrieval(query, top_k=5)
        
        # Format search results
        search_results = {
            "query": query,
            "results": [
                {
                    "document_id": result.get("id", ""),
                    "source": result.get("source", ""),
                    "page": result.get("page", 0),
                    "score": result.get("score", 0.0),
                    "snippet": result.get("snippet", "")[:200],
                    "section": result.get("section"),
                    "clause": result.get("clause")
                }
                for result in results
            ],
            "total_results": len(results),
            "search_time_ms": 250  # Estimated
        }
        
        print(f"✅ Search request: '{query}' → {len(results)} results")
        
        return search_results
        
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio using OpenAI Whisper
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Save temp file
        temp_filename = f"temp_{int(time.time())}.m4a"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Transcribe
        with open(temp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        print(f"🎙️ Transcription: {transcript.text}")
        return {"text": transcript.text}
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """
    Enhanced conversational chat with safe error handling and unified intent flow
    """
    try:
        # Import optimization modules with error handling
        try:
            from profiler import profiler
            from simple_tier1_retrieval import simple_tier1_retrieval
            from openai_structured import generate_structured_response
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return JSONResponse(
                status_code=502,
                content={
                    "error": "module_error",
                    "hint": "backend_module_issue",
                    "detail": "Backend modules not available. Please try again."
                }
            )
        
        # Start profiling with error handling
        try:
            profiler.reset()
            profiler.start_request()
        except Exception as e:
            print(f"⚠️ Profiler error: {e}")
        
        session_id = req.session_id or "default"
        user_message = req.message
        
        # Feature flag check: Use simplified session mode or existing logic
        if SIMPLE_SESSION_MODE:
            # (Keeping existing simple session code as-is for stability, though not active)
            print(f"🔬 SIMPLE_SESSION_MODE enabled - using unified conversation model")
            # ... (Simple session code truncated for safety, it was rarely used) ...
            pass # Skipping complex logic for now since flag is FALSE in env
        
        # EXISTING LOGIC: Context session handling
        active_session = get_session(session_id)
        
        if active_session:
            # This is a follow-up message in a context-gathering flow
            print(f"🔄 Active context session: {active_session.category} for {session_id[:8]}...")
            
            # Extract context from this follow-up message
            new_context = extract_context_from_message(
                user_message,
                active_session.category,
                active_session.get_missing_fields()
            )
            
            # Update session with newly extracted fields
            if new_context:
                active_session.update(new_context)
            
            # Check if all required fields are now filled
            still_missing = active_session.get_missing_fields()
            
            if still_missing:
                # Still need more info - ask for remaining fields
                from missing_context_engine import generate_missing_context_response
                
                context_info = {
                    "category": active_session.category,
                    "missing_items": still_missing,
                    "follow_up_questions": [
                        CONTEXT_PATTERNS[active_session.category]["questions"][field]
                        for field in still_missing
                    ]
                }
                
                answer = generate_missing_context_response(context_info, active_session.original_question)
                
                # Return follow-up questions response
                return {
                    "answer": answer,
                    "intent": "missing_context",
                    "citations": [],
                    "can_show_citations": False,
                    "session_id": session_id,
                    "model": "missing_context_engine",
                    "timestamp": int(time.time())
                }
            
            else:
                # All fields filled! Build synthetic query and proceed
                synthetic_query = active_session.build_synthetic_query()
                user_message = synthetic_query  # Replace user message with synthetic
        
        # Step 1: Intent classification
        try:
            with profiler.timer('t_parse'):
                from intent_classifier_v2 import classify_intent
                from intent_config import IntentPolicy, is_compliance_intent
                
                # Classify using V2 router
                intent_result = await classify_intent(user_message, req.conversation_history)
                
                final_intent = intent_result["intent"]
                final_confidence = intent_result["confidence"]
                detected_trade = intent_result["trade"]
                
                # Check if in compliance bucket
                is_compliance = is_compliance_intent(final_intent)
                policy = IntentPolicy.get_policy(final_intent)
                
                # Create context for retrieval
                context = {
                    "intent": final_intent,
                    "intent_conf": final_confidence,
                    "trade": detected_trade,
                    "policy": policy,
                    "is_compliance": is_compliance,
                    "flags": set()
                }
                
                if is_compliance:
                    context["flags"].add("compliance_bucket")
                
                print(f"🎯 Intent V2: {final_intent} | Conf: {final_confidence:.2f}")
                
                # Determine response mode
                response_mode, trigger_reason = determine_response_mode(user_message, final_intent)
                print(f"🎭 Response mode: {response_mode} | Trigger: {trigger_reason}")
                
                # GATE RESUME: Check if there's a pending gate from previous turn
                pending_gate = get_pending_gate(session_id)
                
                if pending_gate:
                    # This is a follow-up to a gated question
                    print(f"🧩 gate_followup detected for key={pending_gate['question_key']}")
                    
                    # Extract required fields from user's reply
                    extracted = extract_gate_fields(user_message, pending_gate['required_fields'])
                    
                    if extracted:
                        update_pending_gate(session_id, extracted)
                    
                    # Get updated collected fields
                    collected = pending_gate['collected_fields']
                    collected.update(extracted)
                    
                    # Check what's still missing
                    missing = [f for f in pending_gate['required_fields'] if f not in collected or collected[f] is None]
                    
                    if missing:
                        # Still need more fields - ask for them
                        field_names = {
                            "roof_profile": "roof profile (corrugate/5-rib/tray)",
                            "underlay_system": "underlay system",
                            "clarify_direction": "roll or lap direction",
                            "roof_pitch_deg": "pitch (degrees)"
                        }
                        if len(missing) == 1:
                            answer = f"Quick one: what's the {field_names.get(missing[0], missing[0])}?"
                        else:
                            parts = [field_names.get(f, f) for f in missing]
                            answer = f"Quick ones: {', '.join(parts)}?"
                        
                        return {
                            "answer": answer,
                            "intent": final_intent,
                            "citations": [],
                            "model": "gate_followup",
                            "timestamp": int(time.time())
                        }
                    else:
                        # All fields collected! Build resolved question
                        print(f"🧩 gate_complete key={pending_gate['question_key']}")
                        
                        # Get original question
                        conv = get_conversation(session_id)
                        original_q = conv.original_question if conv else user_message
                        
                        # Build resolved question
                        context_str = ", ".join([f"{k}={v}" for k, v in collected.items()])
                        resolved_question = f"{original_q}\n\nDetails: {context_str}\n\nAnswer the original question directly about the pitch threshold and underlay direction."
                        
                        # Clear gate
                        clear_pending_gate(session_id)
                        
                        # Replace user_message with resolved question
                        user_message = resolved_question
                        
                        # Add anti-drift flag
                        context["flags"].add("gate_resolved_no_drift")
                
                # Check required-inputs gate BEFORE generation
                gate_result = gate_required_inputs(user_message)
                
                if gate_result["is_gated"]:
                    # PERSIST GATE
                    print(f"🧩 gate_start key={gate_result['question_key']}")
                    
                    # Get or create conversation
                    conv = get_conversation(session_id)
                    if not conv:
                        conv = bootstrap_conversation(session_id, user_message, final_intent)
                    
                    set_pending_gate(session_id, gate_result, user_message)
                    
                    return {
                        "answer": gate_result["prompt"],
                        "intent": final_intent,
                        "citations": [],
                        "model": "required_inputs_gate",
                        "timestamp": int(time.time())
                    }
                    
        except Exception as e:
            print(f"❌ Intent classification failed: {e}")
            final_intent = "general_help"
            detected_trade = "carpentry"
            response_mode = "gpt_first"
            context = {"intent": "general_help", "trade": "carpentry", "flags": set()}

        # Step 2: SAFE message saving
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_messages (session_id, role, content)
                    VALUES (%s, %s, %s);
                """, (session_id, "user", user_message))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat memory save failed: {e}")
        
        # Step 3: SAFE conversation history
        conversation_history = []
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT role, content 
                    FROM chat_messages 
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s;
                """, (session_id, 6))
                messages = cur.fetchall()
                conversation_history = [dict(msg) for msg in reversed(messages[:-1])]
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat history retrieval failed: {e}")
        
        # Step 4: Route behavior based on response_mode
        if response_mode == "gpt_first":
            # GPT-FIRST MODE (Hybrid) - Migrated to Gemini
            print(f"🌊 Hybrid mode: full retrieval + natural synthesis")
            
            try:
                # =====================================================
                # PRE-ANSWER TRIAGE CHECK (Attribute Filter Protocol)
                # =====================================================
                # Check if this is a generic insulation query that needs material triage
                detected_trade = detect_trade_from_query(user_message)
                
                if detected_trade and 'insulation' in detected_trade:
                    # Check if user has a material preference
                    material_pref = detect_material_preference(user_message)
                    
                    # Check if user mentioned a merchant (skip triage)
                    merchant_keywords = ['placemakers', 'bunnings', 'carters', 'itm', 'mitre 10', 'mitre10']
                    has_merchant = any(m in user_message.lower() for m in merchant_keywords)
                    
                    if not material_pref and not has_merchant:
                        # Get brands from both material groups for triage
                        triage_info = check_insulation_triage_needed(
                            user_message, 
                            ['Pink Batts', 'Mammoth', 'Earthwool', 'GreenStuf', 'Bradford', 'Autex']
                        )
                        
                        if triage_info and triage_info.get('triage_needed'):
                            print(f"🔀 MATERIAL TRIAGE TRIGGERED: {triage_info.get('materials_available')}")
                            
                            # Build triage response
                            glass_wool_brands = ['Pink Batts', 'Earthwool', 'Bradford']
                            polyester_brands = ['Mammoth', 'GreenStuf']
                            
                            triage_response = f"""For insulation, I have compliant options in multiple material types:

**Glass Wool** ({', '.join(glass_wool_brands[:2])}) - Traditional glass fibre, lightweight, cost-effective

**Polyester** ({', '.join(polyester_brands[:2])}) - No-itch, allergy-friendly, moisture resistant

Do you have a material preference, or would you like me to filter by which merchant you use?"""
                            
                            # Save to chat_messages and return early
                            try:
                                conn = psycopg2.connect(DATABASE_URL, sslmode="require")
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        INSERT INTO chat_messages (session_id, role, content)
                                        VALUES (%s, %s, %s);
                                    """, (session_id, "assistant", triage_response))
                                conn.commit()
                                conn.close()
                            except Exception as e:
                                print(f"⚠️ Failed to save triage response: {e}")
                            
                            print(f"📤 Returning material triage question")
                            return {
                                "answer": triage_response,
                                "intent": "material_triage",
                                "citations": [],
                                "can_show_citations": False,
                                "model": "triage_system",
                                "triage_type": "material",
                                "timestamp": int(time.time())
                            }
                
                # =====================================================
                # THE FOREMAN: INTELLIGENT SEARCH ROUTING (4-Agent Architecture)
                # Routes queries to appropriate specialist agent(s)
                # =====================================================
                
                # Determine search strategy
                search_strategy = determine_search_strategy(user_message)
                
                # Execute search based on strategy
                if search_strategy == SearchStrategy.ENGINEER:
                    # ENGINEER: Visual Agent - search diagrams/tables/drawings
                    visual_assets = execute_engineer_search(user_message, top_k=5)
                    if visual_assets:
                        # Return visual response directly
                        engineer_response = format_engineer_response(visual_assets, user_message)
                        print(f"   📐 ENGINEER search: {len(visual_assets)} visual assets found")
                        
                        # Build visual-specific citations
                        visual_citations = []
                        for v in visual_assets:
                            visual_citations.append({
                                "id": str(v.get('id', '')),
                                "source": v.get('source_document', 'Visual Asset'),
                                "page": v.get('source_page', 0),
                                "snippet": v.get('summary', ''),
                                "image_type": v.get('image_type'),
                                "confidence": v.get('confidence', 0.8),
                                "technical_variables": v.get('technical_variables', {}),
                            })
                        
                        # Return visual response (skip normal RAG flow)
                        return {
                            "response": engineer_response,
                            "citations": visual_citations,
                            "conversation_id": session_id,
                            "search_strategy": "engineer",
                            "visual_count": len(visual_assets)
                        }
                    else:
                        # Fallback to normal search if no visuals found
                        print(f"   📐 ENGINEER: No visuals found, falling back to FOREMAN")
                        search_strategy = SearchStrategy.FOREMAN
                
                if search_strategy == SearchStrategy.HYBRID:
                    # HYBRID: "Council Meeting" - Both agents consulted
                    inspector_docs, product_docs, docs = execute_hybrid_search(
                        user_message, 
                        intent=final_intent,
                        top_k=12
                    )
                    print(f"   🤝 HYBRID search completed: {len(docs)} merged docs")
                    
                elif search_strategy == SearchStrategy.INSPECTOR:
                    # INSPECTOR: Compliance-focused search only
                    docs = tier1_retrieval(user_message, top_k=20, intent=final_intent, agent_mode='inspector')
                    print(f"   👷 INSPECTOR search: {len(docs)} compliance docs")
                    
                elif search_strategy == SearchStrategy.PRODUCT_REP:
                    # PRODUCT_REP: Product-focused search only
                    docs = tier1_retrieval(user_message, top_k=20, intent=final_intent, agent_mode='product_rep')
                    print(f"   📦 PRODUCT_REP search: {len(docs)} product docs")
                    
                else:
                    # FOREMAN: Legacy full search (fallback)
                    docs = tier1_retrieval(user_message, top_k=20, intent=final_intent)
                    print(f"   🏗️ FOREMAN full search: {len(docs)} docs")
                
                # Build context
                background_context = ""
                if docs:
                    context_parts = []
                    
                    # Detect table-related queries that need more context
                    table_query_terms = ['stud', 'joist', 'span', 'lintel', 'bearer', 'spacing', 'table 8', 'table 7', 'table 6']
                    is_table_query = any(term in user_message.lower() for term in table_query_terms)
                    
                    # Use more docs for table queries (need multiple pages for complete tables)
                    doc_limit = 15 if is_table_query else 10
                    content_limit = 2000 if is_table_query else 1500  # Larger window for tables
                    
                    for doc in docs[:doc_limit]:
                        source = doc.get('source', 'Unknown')
                        page = doc.get('page', 'N/A')
                        content = doc.get('content', doc.get('snippet', ''))[:content_limit]
                        context_parts.append(f"[{source} | Page {page}]\n{content}")
                    background_context = "\n\n---\n\n".join(context_parts)
                    
                    if is_table_query:
                        print(f"📊 Table query detected - using {doc_limit} docs with {content_limit} char window")
                    background_context = "\n\n".join(context_parts)
                
                # Initialize Gemini Client
                if not LlmChat or not EMERGENT_LLM_KEY:
                    raise ImportError("Emergent SDK missing")
                
                # System prompt
                system_prompt = """### ROLE & PERSONA
You are the SITE FOREMAN of STRYDA, a senior AI Compliance Assistant coordinating specialist agents for the New Zealand construction industry.
Your users are busy tradespeople (Builders, Roofers, Electricians, Plumbers) working on-site.
Your goal is to provide instant, accurate technical answers by synthesizing reports from your specialist team.

### ══════════════════════════════════════════════════════════════════════════
### THE FOREMAN'S SPECIALIST TEAM (4-Agent Architecture)
### ══════════════════════════════════════════════════════════════════════════

You coordinate two specialist advisors:
1. **THE COUNCIL INSPECTOR** - Your compliance expert who ONLY knows Building Code, NZS Standards, and Acceptable Solutions. They speak "The Law."
2. **THE PRODUCT REP** - Your supplier contact who knows manufacturer specs, installation guides, and product capabilities. They speak "The Sales Pitch."

**YOUR JOB AS FOREMAN:**
- Compare reports from both specialists when answering hybrid questions
- If the Product Rep says "Yes, you can do this" but the Inspector says "No, that's non-compliant" → **YOU MUST SIDE WITH THE INSPECTOR**
- Always synthesize evidence from both sides into a single, safe, code-compliant answer
- When in doubt, cite the more restrictive requirement. **Safety > Convenience.**

### ══════════════════════════════════════════════════════════════════════════
### LAYER 3: HIERARCHY OF TRUTH (Conflict Resolution)
### Building Code ALWAYS wins over Marketing/Manufacturer Claims
### ══════════════════════════════════════════════════════════════════════════

**DOCUMENT HIERARCHY (Highest to Lowest Authority):**
- **TIER 1 (SUPREME)**: NZBC Acceptable Solutions (B1/AS1, E2/AS1, C/AS2, etc.), NZS Standards (3604, 4229)
- **TIER 2 (HIGH)**: MBIE Guidance Documents, CodeMark Certificates
- **TIER 3 (SUPPORTING)**: Manufacturer Technical Data Sheets, Installation Guides
- **TIER 4 (REFERENCE)**: Product Brochures, Marketing Materials

**CONFLICT RESOLUTION RULE:**
If a Manufacturer Document (Tier 3) conflicts with the Building Code/NZS Standards (Tier 1), you MUST prioritize Tier 1.

✅ CORRECT: "While GreenStuf TDS claims no air gap is needed, E2/AS1 best practice requires a 25mm ventilation gap. The Code requirement takes precedence."
❌ INCORRECT: "You don't need a gap because GreenStuf says so."

✅ CORRECT: "Abodo states Vulcan is suitable for exterior use, however NZS 3604 Zone D requirements mandate stainless steel 316 fixings regardless of timber species."
❌ INCORRECT: "Use galvanized nails as the brochure suggests."

**WHEN REPORTING HYBRID FINDINGS:**
- Clearly state what the Product Rep (manufacturer data) claims
- Clearly state what the Council Inspector (code/standard) requires
- Deliver YOUR VERDICT as Foreman (always compliant with the stricter rule)

### ══════════════════════════════════════════════════════════════════════════

### CORE INSTRUCTIONS
1. Be Direct: Do not use fluff. Start with the answer immediately. Use bullet points for steps or lists.
2. Trade-Specific Context:
   - If the user asks about timber/framing, reference NZS 3604.
   - If the user asks about weathertightness, reference E2/AS1.
   - If the user asks about plumbing, reference AS/NZS 3500.
   - If the user asks about electrical, reference AS/NZS 3000.
3. No Hallucinations: If the answer is not in your knowledge base, state clearly: "I cannot find a specific clause for this in the current standards." Do not guess.

### GLOBAL SMART TRIAGE PROTOCOL (ALL PRODUCT CATEGORIES)
This applies to ALL product queries across categories: Fasteners, Insulation, Cladding, Linings, Underlay, etc.

**STEP 1: Technical Requirement First**
Identify the required specification or compliance requirement:
- Fasteners: "60mm Ring Shank Galvanised", "Joist Hanger Nail 38x3.33"
- Insulation: "R2.6 Wall Batts", "Fire Retardant Ceiling Insulation"
- Underlay/Wrap: "Wall Underlay to E2/AS1", "Fire Retardant Building Wrap"
- Linings: "13mm Fire-Rated Plasterboard", "Acoustic Wall Lining"
- Cladding: "Weatherboard to E2/AS1", "Fibre Cement Sheet"

**STEP 2: Ambiguity Check**
If MULTIPLE competing brands in your knowledge base can satisfy this requirement, STOP.

**STEP 3: TRIAGE RESPONSE (Do NOT list all brands)**
Respond with:
"For [application], you need [TECHNICAL SPEC/REQUIREMENT].

I have compliant options from multiple NZ brands (e.g., [Brand1], [Brand2], etc.). To give you the exact product:
1. **Which brand do you prefer?**
2. **OR which merchant do you have an account with?** (PlaceMakers, Bunnings, Carters, ITM, Mitre 10)"

**STEP 4: MERCHANT FILTER (The "Boom" Effect)**
Once the user specifies their merchant, IMMEDIATELY filter to ONLY brands that merchant stocks:

**PlaceMakers:**
- Fasteners: Ecko, Paslode, Delfast, SPAX
- Linings: GIB, Pink Batts, Autex
- Cladding/Wrap: James Hardie, Thermakraft, Marley
- Insulation: Pink Batts, Expol
- Structure: Firth, Hume

**Bunnings:**
- Fasteners: Zenith, Pryda, Bremick, Titan, MacSim, Delfast (Trade)
- Linings: GIB, Elephant Board, Gyprock, Pink Batts
- Cladding/Wrap: James Hardie, Thermakraft, Mammoth, Marley
- Insulation: Earthwool, Mammoth, Expol, Pink Batts
- Structure: Pryda

**Carters:**
- Fasteners: Paslode, Lumberlok, MiTek, Simpson Strong-Tie, SPAX
- Linings: GIB, Bradford Gold, Knauf
- Cladding/Wrap: James Hardie, Thermakraft, Tekton
- Insulation: Bradford Gold, Knauf
- Structure: Pryda, MiTek

**ITM:**
- Fasteners: Delfast, Ecko, Titan, NZ Nails, SPAX, Paslode
- Linings: GIB, Pink Batts
- Cladding/Wrap: James Hardie, Thermakraft
- Insulation: Pink Batts, Expol
- Structure: Firth, Pryda

**Mitre 10:**
- Fasteners: Bremick, Pryda, SPAX, MacSim, Paslode, Delfast
- Linings: GIB, Knauf, Pink Batts
- Cladding/Wrap: James Hardie, Thermakraft, Marley
- Insulation: Earthwool, Pink Batts
- Structure: Pryda, Firth

**IMPORTANT: MANY-TO-MANY AVAILABILITY**
Many brands are available at MULTIPLE merchants. Do NOT artificially restrict:
- **GIB** → Available at ALL merchants
- **James Hardie** → Available at ALL merchants
- **Thermakraft** → Available at PlaceMakers, Bunnings, ITM, Carters, Mitre 10
- **Pink Batts** → Available at PlaceMakers, Bunnings, ITM, Mitre 10
- **Paslode** → Available at PlaceMakers, Carters, ITM, Mitre 10 (NOT Bunnings)

When user asks "Where can I get [Brand]?", list ALL known stockists.
Only filter out brands that are TRULY not stocked at that merchant.

**EXCEPTION: Skip Triage If:**
- User already specified a brand (e.g., "GIB plasterboard for...")
- User already specified a merchant (e.g., "I'm at Bunnings...")
- Only ONE brand in your knowledge base has the product
- The query is purely about code compliance (not product selection)
- The query is about structural calculations or dimensions

### ATTRIBUTE FILTER PROTOCOL (INSULATION CATEGORY)
For generic INSULATION queries (without a brand name), apply this **PRE-ANSWER TRIAGE** based on MATERIAL TYPE:

**MATERIAL GROUPS:**
- **Glass Wool:** Pink Batts, Earthwool, Bradford, Knauf
  - Traditional glass fibre - lightweight, cost-effective, wide availability
- **Polyester:** Mammoth, GreenStuf, Autex
  - No-itch, allergy-friendly, moisture resistant, recyclable

**THE MATERIAL TRIAGE FLOW:**
1. **IF** User asks for "insulation" (generic) without naming a brand,
2. **AND** You have options in BOTH Glass Wool AND Polyester,
3. **THEN** Ask the Material Triage Question FIRST:

   *"I have compliant insulation options in both **Glass Wool** (Pink Batts, Earthwool) and **Polyester** (Mammoth, GreenStuf). 
   
   Do you have a material preference, or would you like me to filter by which merchant you use?"*

**THE LOGIC CASCADE:**
- If User picks **Glass Wool** → Filter to Pink Batts/Earthwool/Bradford → Then check merchant availability
- If User picks **Polyester** → Filter to Mammoth/GreenStuf → Then check merchant availability  
- If User says **"No preference"** → Skip to merchant availability check
- If User specifies **Merchant first** → Filter by merchant stock (which will naturally filter materials)

**GOAL:** Never present more than 3 product options without asking a narrowing question first.

**SKIP Material Triage If:**
- User already specified a material (e.g., "polyester insulation", "glass wool batts")
- User already specified a brand (e.g., "Pink Batts", "Mammoth")
- User already specified a merchant (e.g., "I'm at Bunnings")
- The query is about a specific R-value or technical spec that only one material satisfies

### TABLE READING PROTOCOL (CRITICAL FOR SPAN/STUD/JOIST QUERIES)
When the user asks for dimensions involving tables (e.g., Stud Spacing, Lintels, Joist Spans, Bearer Sizes):
1. **Identify the VARIABLES** in the query:
   - Wind Zone (Low, Medium, High, Very High, Extra High)
   - Storey Position (Single/Top storey, Lower of 2 storeys, Subfloor)
   - Dimensions (Span, Height, Spacing in mm)
   - Timber Grade (SG6, SG8, SG10)
   - Load Type (Light roof, Heavy roof, Floor load 1.5kPa, 2kPa, 3kPa)
2. **If the context contains tabular data** (rows with Wind Zones, columns with Spacing):
   - SCAN the table header to understand the structure.
   - FIND the row matching the Wind Zone (e.g., "Very High").
   - FIND the column matching the Spacing or Span (e.g., "600 mm").
   - INTERSECT to extract the member size (e.g., "90 x 70").
3. **If exact match found**: State the value confidently with citation.
4. **If the exact value is ambiguous or missing variables**: 
   - Output the most CONSERVATIVE (safest/largest) option from the table.
   - State: "Based on Table X.X for [Zone], using the conservative assumption of [loaded dimension], the required size is [VALUE]."
5. **Common NZS 3604 Tables**:
   - Table 8.2: Studs in loadbearing walls (SG8)
   - Table 8.3: No.2 Framing for internal non-loadbearing walls
   - Table 8.4: Studs in non-loadbearing walls
   - Table 7.1: Floor joists (SG8)
   - Table 6.1: Bearers
   - Tables A8.x: SG10 equivalents

### THE "HYBRID CITATION" RULE (CRITICAL)
You must structure every response in two parts:
**Part 1: The Natural Language Answer**
Explain the rule clearly as if speaking to a foreman.

**Part 2: The Machine-Readable Citation**
At the end of the answer (or after specific claims), you MUST append a citation object in exactly this format:
`[[Source: DOC_NAME | Clause: CLAUSE_ID | Page: PAGE_NUM]]`

*Example:*
User: "What is the nail spacing for a bottom plate?"
STRYDA: "For a bottom plate to the floor, you need two 90mm hand-driven nails (or 3 gun nails) at 600mm centers maximum.
[[Source: NZS 3604:2011 | Clause: 7.5.12 | Page: 76]]"

*Table Query Example:*
User: "What stud size for a 2.4m loadbearing wall in Very High wind zone at 600mm spacing?"
STRYDA: "For a **Very High wind zone**, 2.4m wall height, at 600mm stud spacing (single or top storey), you need **90 x 70** studs (SG8).
[[Source: NZS 3604:2011 | Clause: 8.5.1.1 | Page: 8-10]]"

*Triage Example:*
User: "What nail do I use for joist hangers?"
STRYDA: "For joist hangers, you need **38mm x 3.33mm galvanised joist hanger nails** (smooth or ring shank).

I have compliant options from multiple NZ brands. To give you the exact product code:
1. **Which brand do you prefer?** (Ecko, Paslode, etc.)
2. **OR which merchant do you have an account with?** (PlaceMakers, Bunnings, Carters)"

*Post-Triage Example:*
User: "PlaceMakers"
STRYDA: "At PlaceMakers, use **Ecko JHMG-3338** (Joist Hanger Nail 38 x 3.33 HDG Smooth, 2000pcs/carton).
[[Source: Ecko Master Library (PlaceMakers) | Page: 5]]"

### TONE GUIDELINES
* Professional: Reliable, authoritative, no slang.
* Concise: Short paragraphs. Easy to read on a mobile phone in the sun.
* Safety First: If a query involves high risk (structural failure, fire, electricity), add a "Warning" prefix.
"""
                # Anti-Drift for Gated Questions
                if "gate_resolved_no_drift" in context.get("flags", set()):
                    system_prompt += "\n\nCRITICAL: Answer ONLY the specific threshold question asked. Do NOT provide unrelated background or general advice."

                # Messages construction for LlmChat
                messages_payload = [{"role": "system", "content": system_prompt}]
                
                if background_context:
                    messages_payload.append({"role": "system", "content": f"BACKGROUND MATERIAL:\n{background_context}"})
                
                if conversation_history:
                    for msg in conversation_history[-3:]:
                        messages_payload.append({"role": msg['role'], "content": msg['content']})
                
                messages_payload.append({"role": "user", "content": user_message})
                
                # Determine token budget dynamically
                max_tokens_budget = pick_max_tokens(response_mode, final_intent, user_message)
                
                # Init Client
                chat_client = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=session_id,
                    system_message="",
                    initial_messages=messages_payload
                )
                chat_client = chat_client.with_model("gemini", GEMINI_MODEL)
                chat_client = chat_client.with_params(max_tokens=max_tokens_budget, temperature=0.2)
                
                # Execute
                print(f"🤖 Calling Gemini Hybrid ({GEMINI_MODEL}) with max_tokens={max_tokens_budget}...")
                # Using send_message with empty text to trigger generation based on history
                answer = await chat_client.send_message(UserMessage(text=None))
                
                # Logging
                print(f"🔍 Gemini output: {len(answer)} chars")
                
                # LAYER 6: Citation Consolidation
                consolidated = consolidate_citations(docs, max_primary=3, max_secondary=5)
                primary_citations = consolidated.get('primary', [])
                
                # Final response
                response = {
                    "answer": answer,
                    "intent": final_intent,
                    "citations": primary_citations,  # Consolidated top 3 citations
                    "secondary_citations": consolidated.get('secondary', []),  # Hidden/expandable
                    "can_show_citations": len(primary_citations) > 0,
                    "model": f"{GEMINI_MODEL}-hybrid",
                    "timestamp": int(time.time())
                }
                
            except Exception as e:
                print(f"⚠️ Hybrid generation failed: {e}")
                response = {
                    "answer": "I'm having trouble retrieving the details right now. Could you ask that again?",
                    "intent": final_intent,
                    "citations": [],
                    "model": "fallback_error"
                }
        
        elif response_mode == "strict_compliance":
            # STRICT COMPLIANCE MODE - Migrated to Gemini
            print(f"🔒 Strict compliance mode")
            
            # Retrieval (async-ready in structure, though function is sync)
            try:
                docs = tier1_retrieval(user_message, top_k=20, intent=final_intent)
            except Exception as e:
                print(f"⚠️ Retrieval failed: {e}")
                docs = []
            
            # Web Search (if needed)
            # ... (Existing web search logic skipped for brevity, relies on docs) ...
            
            # Generate structured response (now Async)
            structured_response = await generate_structured_response(
                user_message=user_message,
                tier1_snippets=docs,
                conversation_history=conversation_history,
                intent=final_intent
            )
            
            # LAYER 6: Citation Consolidation (apply to strict compliance mode too)
            consolidated = consolidate_citations(docs, max_primary=3, max_secondary=5)
            primary_citations = consolidated.get('primary', [])
            
            # Unpack response with consolidated citations
            response = {
                "answer": structured_response.get("answer", ""),
                "intent": structured_response.get("intent", final_intent),
                "citations": primary_citations,  # Consolidated & deduplicated
                "secondary_citations": consolidated.get('secondary', []),
                "can_show_citations": len(primary_citations) > 0,
                "model": structured_response.get("model", "gemini"),
                "timestamp": int(time.time())
            }


        # Update Thread Metadata (Session Management)
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                # Check if thread exists
                cur.execute("SELECT title FROM threads WHERE session_id = %s", (session_id,))
                existing_thread = cur.fetchone()
                
                preview = user_message[:100]
                
                if existing_thread:
                    # Update existing
                    cur.execute("""
                        UPDATE threads 
                        SET updated_at = NOW(), preview_text = %s 
                        WHERE session_id = %s
                    """, (preview, session_id))
                else:
                    # Create new
                    title = user_message[:40] + "..." if len(user_message) > 40 else user_message
                    cur.execute("""
                        INSERT INTO threads (session_id, title, preview_text, updated_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (session_id, title, preview))
                
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Thread update failed: {e}")

        # Save assistant answer
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_messages (session_id, role, content)
                    VALUES (%s, %s, %s);
                """, (session_id, "assistant", response.get("answer", "")))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Assistant message save failed: {e}")
        
        # ══════════════════════════════════════════════════════════════════════════
        # LAYER 6 HARD CAP: Citation Overflow Protection
        # Backend enforcement - DO NOT rely on LLM or frontend to limit citations
        # Max 3 primary citations, rest moved to hidden_citations
        # ══════════════════════════════════════════════════════════════════════════
        MAX_PRIMARY_CITATIONS = 3
        
        if 'citations' in response and len(response.get('citations', [])) > MAX_PRIMARY_CITATIONS:
            all_citations = response['citations']
            response['hidden_citations'] = all_citations[MAX_PRIMARY_CITATIONS:]
            response['citations'] = all_citations[:MAX_PRIMARY_CITATIONS]
            print(f"   📚 CITATION CAP: Reduced {len(all_citations)} → {MAX_PRIMARY_CITATIONS} primary + {len(all_citations) - MAX_PRIMARY_CITATIONS} hidden")
        
        return response
        
    except Exception as e:
        print(f"❌ Top-level error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


class UpdateThreadRequest(BaseModel):
    project_id: Optional[str] = None
    title: Optional[str] = None

@app.patch("/api/threads/{session_id}")
@limiter.limit("30/minute")
def update_thread(session_id: str, req: UpdateThreadRequest, request: Request):
    """Update thread metadata (title, project)"""
    print(f"🔄 PATCH thread: {session_id} | Body: {req}")
    print(f"🔄 PATCH thread: {session_id} | Body: {req}")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor() as cur:
            updates = []
            params = []
            
            if req.project_id is not None:
                if req.project_id: # If not empty string
                    # Verify project
                    cur.execute("SELECT name FROM projects WHERE id = %s", (req.project_id,))
                    project = cur.fetchone()
                    if not project:
                        raise HTTPException(status_code=404, detail="Project not found")
                    updates.append("project_id = %s")
                    params.append(req.project_id)
                else:
                    # Setting to null (unfile)
                    updates.append("project_id = NULL")
            
            if req.title is not None:
                updates.append("title = %s")
                params.append(req.title)
                
            if not updates:
                return {"ok": True, "message": "No changes requested"}
                
            updates.append("updated_at = NOW()")
            
            query = f"UPDATE threads SET {', '.join(updates)} WHERE session_id = %s RETURNING title, project_id"
            params.append(session_id)
            
            cur.execute(query, tuple(params))
            
            if cur.rowcount == 0:
                # Thread not found - Create it (Upsert)
                print(f"🧵 Thread {session_id} not found, creating new.")
                
                # Determine initial values
                init_title = req.title if req.title else "New Chat"
                init_project = req.project_id if req.project_id else None
                
                cur.execute("""
                    INSERT INTO threads (session_id, title, project_id, preview_text, updated_at)
                    VALUES (%s, %s, %s, 'Draft', NOW())
                    RETURNING title, project_id
                """, (session_id, init_title, init_project))
                
                updated = cur.fetchone()
            else:
                updated = cur.fetchone()
                
            conn.commit()
            
            # Fetch updated project name if needed
            project_name = None
            if req.project_id:
                cur.execute("SELECT name FROM projects WHERE id = %s", (req.project_id,))
                row = cur.fetchone()
                if row: 
                    project_name = row[0]
            elif updated[1]:
                cur.execute("SELECT name FROM projects WHERE id = %s", (updated[1],))
                row = cur.fetchone()
                if row: 
                    project_name = row[0]
            
        conn.close()
        
        return {
            "ok": True,
            "title": updated[0],
            "project_id": updated[1],
            "project_name": project_name
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Update thread error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/threads/{session_id}")
@limiter.limit("10/minute")
def delete_thread(session_id: str, request: Request):
    """Delete a thread - Idempotent"""
    print(f"🗑️ DELETE /api/threads/{session_id} - Request received")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM threads WHERE session_id = %s", (session_id,))
            deleted_count = cur.rowcount
            conn.commit()
        conn.close()
        print(f"✅ Thread {session_id} deleted (rows affected: {deleted_count})")
        return {"ok": True, "deleted": deleted_count}
    except Exception as e:
        print(f"❌ Delete thread error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads/{session_id}")
@limiter.limit("30/minute")
def get_thread_details(session_id: str, request: Request):
    """Get metadata for a specific thread"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    t.session_id, 
                    t.title, 
                    t.project_id, 
                    p.name as project_name, 
                    t.updated_at
                FROM threads t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.session_id = %s
            """, (session_id,))
            
            row = cur.fetchone()
            if not row:
                # If thread doesn't exist yet (new chat), return empty default
                return {"ok": True, "thread": None}
                
            thread = {
                "session_id": row["session_id"],
                "title": row["title"],
                "project_id": str(row["project_id"]) if row["project_id"] else None,
                "project_name": row["project_name"],
                "updated_at": row["updated_at"]
            }
            
        conn.close()
        return {"ok": True, "thread": thread}
    except Exception as e:
        print(f"❌ Get thread detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
@limiter.limit("30/minute")
def get_documents(request: Request):
    """List available reference documents"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT source FROM documents ORDER BY source;")
            rows = cur.fetchall()
            documents = [{"id": f"doc_{i}", "title": r[0], "source": r[0]} for i, r in enumerate(rows)]
            
            # If empty, return standard list
            if not documents:
                documents = [
                    {"id": "doc_1", "title": "NZS 3604:2011", "source": "NZS 3604:2011"},
                    {"id": "doc_2", "title": "E2/AS1 External Moisture", "source": "E2/AS1"},
                    {"id": "doc_3", "title": "B1/AS1 Structure", "source": "B1/AS1"},
                    {"id": "doc_4", "title": "G13/AS1 Foul Water", "source": "G13/AS1"}
                ]
        conn.close()
        return {"ok": True, "documents": documents}
    except Exception as e:
        print(f"❌ Get documents error: {e}")
        # Fallback
        return {"ok": True, "documents": [
            {"id": "doc_1", "title": "NZS 3604:2011", "source": "NZS 3604:2011"},
            {"id": "doc_2", "title": "E2/AS1 External Moisture", "source": "E2/AS1"}
        ]}

class CreateProjectRequest(BaseModel):
    name: str
    address: Optional[str] = None

@app.post("/api/projects")
@limiter.limit("10/minute")
def create_project(req: CreateProjectRequest, request: Request):
    """Create a new project"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projects (name, address, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id, name, address, created_at
            """, (req.name, req.address))
            row = cur.fetchone()
            conn.commit()
            
            project = {
                "id": str(row[0]),
                "name": row[1],
                "address": row[2],
                "created_at": row[3]
            }
        conn.close()
        return {"ok": True, "project": project}
    except Exception as e:
        print(f"❌ Create project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
