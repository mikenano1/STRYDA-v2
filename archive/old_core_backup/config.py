#!/usr/bin/env python3
"""
⚡ STRYDA CORE CONFIGURATION
===========================
Hardwired system dependencies and vision engine configuration.

Version: 3.0 PLATINUM
Last Updated: 2026-01-25
"""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/app/backend-minimal/.env')

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
DATABASE_URL = os.getenv('DATABASE_URL')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# ==============================================================================
# LLM CONFIGURATION
# ==============================================================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')

# Vision Model Configuration (Emergent Integrations)
VISION_MODEL_PROVIDER = 'gemini'
VISION_MODEL_NAME = 'gemini-2.5-flash'
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 1536

# ==============================================================================
# PDF PROCESSING CONFIGURATION
# ==============================================================================
PDF_DPI_STANDARD = 200
PDF_DPI_HIGH_COMPLEXITY = 250
MAX_PAGES_STANDARD = 10
MAX_PAGES_HIGH_COMPLEXITY = 15
JPEG_QUALITY = 85

# Poppler Configuration (System Dependency)
# Installed via: apt-get install poppler-utils
POPPLER_INSTALLED = True

# ==============================================================================
# SEGMENT CONFIGURATIONS
# ==============================================================================
SEGMENT_CONFIGS = {
    'bremick': {
        'name': 'Bremick Fasteners',
        'source_pattern': 'Bremick%',
        'storage_path': 'F_Manufacturers/Fasteners/Bremick',
        'trade': 'fasteners',
        'primary_unit': 'lbf',
        'secondary_unit': 'N',
        'status': 'PLATINUM',
        'chunks': 8361,
        'audit_pass_rate': 90.0
    },
    'pryda': {
        'name': 'Pryda Structural Connectors',
        'source_pattern': 'Pryda%',
        'storage_path': 'F_Manufacturers/Fasteners/Pryda',
        'trade': 'structural_connectors',
        'primary_unit': 'kN',
        'timber_grades': ['SG8', 'SG10', 'SG12', 'MSG8', 'MSG10'],
        'joint_groups': ['JD4', 'JD5', 'J2', 'J3', 'J4', 'J5'],
        'status': 'PLATINUM',
        'chunks': 326,
        'audit_pass_rate': None  # Pending V4 audit
    }
}

# ==============================================================================
# HALLUCINATION KEYWORDS (Cross-Domain Leakage)
# ==============================================================================
HALLUCINATION_KEYWORDS = [
    # Timber framing (wrong domain for fastener queries)
    'nzs 3604', 'nzs3604', 'timber span', 'rafter span', 'joist span',
    'bearer span', 'purlin span', 'roof span', 'floor span', 'ceiling span',
    '90x45', '140x45', '190x45', '240x45',
    # Generic evasions
    'consult the manual', 'refer to documentation', 'contact manufacturer',
    'beyond scope', 'cannot determine'
]

# ==============================================================================
# ANTI-HALLUCINATION LOCK - STRICT EXCLUSION LIST
# ==============================================================================
PRYDA_STRICT_EXCLUSIONS = [
    'nzs 3604', 'nzs3604', 'nzs-3604',
    'timber span', 'rafter span', 'joist span', 'bearer span',
    'floor span', 'roof span', 'ceiling span', 'purlin span',
    'span table', 'span calculation',
    'wind zone calculation', 'bracing calculation'
]

PRYDA_EXCLUSION_RESPONSE = """Data not in Pryda Spec. Referring to Manufacturer Loadings only.

Pryda connector capacities are based on:
- Timber joint group (J2, J3, JD4, JD5)
- Nail/screw fixing pattern
- Characteristic load (kN)

For structural design calculations, spans, or NZS 3604 compliance, please consult a qualified engineer."""

def check_pryda_exclusion(query):
    """
    Check if query contains Pryda-excluded terms.
    Returns exclusion response if triggered, None otherwise.
    """
    query_lower = query.lower()
    for term in PRYDA_STRICT_EXCLUSIONS:
        if term in query_lower:
            return PRYDA_EXCLUSION_RESPONSE
    return None

# ==============================================================================
# PRYDA UNIT LAW
# ==============================================================================
PRYDA_UNIT_LAW = """
PRYDA UNIT LAW (MANDATORY):
- Primary force unit: kN (kilonewtons)
- Timber grades: SG8, SG10, SG12, MSG8, MSG10
- Nailing patterns: 4/3.15, 6/3.15, 8/3.15 (count/diameter mm)
- Joint groups: JD4, JD5, J2, J3, J4, J5
- Cyclonic regions: C1, C2, C3, C4
- Wind zones: Low, Medium, High, Very High, Extra High
"""

JOINT_GROUP_DEFINITIONS = {
    'JD4': 'Joint Group JD4 - High density hardwood',
    'JD5': 'Joint Group JD5 - Medium density hardwood',
    'J2': 'Joint Group J2 - Radiata Pine (dry)',
    'J3': 'Joint Group J3 - Radiata Pine (green)',
    'J4': 'Joint Group J4 - Softwood dry',
    'J5': 'Joint Group J5 - Softwood green'
}

# ==============================================================================
# V4 AUDIT CONFIGURATION
# ==============================================================================
AUDIT_CONFIG = {
    'min_questions': 50,
    'platinum_threshold': 90.0,
    'gold_threshold': 75.0,
    'silver_threshold': 50.0,
    'hallucination_tolerance': 0.0,
    'nightly_schedule': '0 2 * * *'  # 2:00 AM daily
}
