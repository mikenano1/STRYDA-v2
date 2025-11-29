"""
STRYDA Intent Router V2 - Configuration
Locked intent definitions and citation policies
"""

from enum import Enum
from typing import List, Dict

class Intent(str, Enum):
    """Locked intent types from training_questions_v2"""
    COMPLIANCE_STRICT = "compliance_strict"
    IMPLICIT_COMPLIANCE = "implicit_compliance"
    GENERAL_HELP = "general_help"
    PRODUCT_INFO = "product_info"
    COUNCIL_PROCESS = "council_process"

def is_compliance_intent(intent: str) -> bool:
    """
    Check if intent is in the compliance bucket (strict or implicit)
    Both get code-heavy retrieval + citations
    """
    return intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]

class IntentPolicy:
    """Citation and retrieval policies for each intent"""
    
    POLICIES = {
        Intent.COMPLIANCE_STRICT: {
            "description": "Explicit code compliance queries requiring precise citations",
            "retrieval_bias": ["code_standards", "technical_docs", "nzs", "nzbc"],
            "citations_default": True,
            "max_citations": 3,
            "require_sources": True,
            "model_preference": "gpt-4o",  # Higher capability for precise answers
            "reasoning": "Heavy code lookup required"
        },
        
        Intent.IMPLICIT_COMPLIANCE: {
            "description": "Code-supported but conversational queries",
            "retrieval_bias": ["code_standards", "practical_guides"],
            "citations_default": False,  # Allow but don't force
            "max_citations": 2,
            "require_sources": False,
            "model_preference": "gpt-4o",
            "reasoning": "Code-aware but flexible"
        },
        
        Intent.GENERAL_HELP: {
            "description": "Practical guidance and tradie experience",
            "retrieval_bias": ["practical_guides", "how_to"],
            "citations_default": False,
            "max_citations": 0,  # No citations unless user explicitly asks
            "require_sources": False,
            "model_preference": "gpt-4o-mini",
            "reasoning": "Experience-based, minimal retrieval"
        },
        
        Intent.PRODUCT_INFO: {
            "description": "Product specifications and manufacturer guidance",
            "retrieval_bias": ["manufacturer_docs", "product_specs"],
            "citations_default": False,
            "max_citations": 1,  # Product reference if needed
            "require_sources": False,
            "model_preference": "gpt-4o-mini",
            "reasoning": "Product-focused, practical"
        },
        
        Intent.COUNCIL_PROCESS: {
            "description": "Council consent and regulatory process queries",
            "retrieval_bias": ["council_docs", "consent_process", "ccc"],
            "citations_default": False,
            "max_citations": 1,
            "require_sources": False,
            "model_preference": "gpt-4o",
            "reasoning": "Process-focused, not code-focused"
        }
    }
    
    @classmethod
    def get_policy(cls, intent: Intent) -> Dict:
        """Get citation policy for a given intent"""
        return cls.POLICIES.get(intent, cls.POLICIES[Intent.GENERAL_HELP])
    
    @classmethod
    def should_show_citations(cls, intent: Intent, has_strong_matches: bool = False) -> bool:
        """Determine if citations should be shown"""
        policy = cls.get_policy(intent)
        
        if policy["citations_default"]:
            return True
        
        # For non-default intents, only show if strong matches
        return has_strong_matches and intent in [Intent.IMPLICIT_COMPLIANCE]

# Trade domain mapping for retrieval routing
TRADE_DOMAINS = {
    "carpentry": {
        "keywords": ["framing", "bracing", "decks", "stairs", "subfloor", "joists", "studs", "nog", "dwang"],
        "primary_sources": ["NZS 3604:2011", "NZ Building Code"],
        "trade_types": ["framing", "bracing", "decks", "subfloor", "stairs", "general_carpentry"]
    },
    "roofing": {
        "keywords": ["roof", "flashing", "longrun", "purlin", "ridge", "valley", "apron"],
        "primary_sources": ["NZ Metal Roofing", "E2/AS1"],
        "trade_types": ["metal_roofing", "flashings", "weathertightness", "roof_framing"]
    },
    "plumbing": {
        "keywords": ["plumbing", "pipe", "tap", "mixer", "drain", "cylinder", "waste", "trap"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["pipework", "fixtures", "drainage", "hot_water", "sanitary"]
    },
    "drainage": {
        "keywords": ["drain", "gully", "stormwater", "sump", "soak pit", "lateral"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["site_drainage", "stormwater", "wastewater", "gullies", "gradients"]
    },
    "concrete_foundations": {
        "keywords": ["concrete", "slab", "foundation", "footing", "rebar", "masonry", "block"],
        "primary_sources": ["NZS 4229:2013", "NZ Building Code"],
        "trade_types": ["slabs", "footings", "piles", "reinforcing", "masonry", "retaining"]
    },
    "passive_fire": {
        "keywords": ["fire", "fire stopping", "penetration", "collar", "mastic", "intumescent"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["penetrations", "fire_wraps", "collars", "intumescent", "c_clauses"]
    },
    "electrical": {
        "keywords": ["electrical", "circuit", "RCD", "breaker", "wiring", "switchboard"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["circuits", "compliance", "earthing", "switchboards", "loads"]
    },
    "cladding": {
        "keywords": ["cladding", "weatherboard", "cavity", "batten", "wrap", "fibre cement"],
        "primary_sources": ["E2/AS1", "NZ Building Code"],
        "trade_types": ["weatherboards", "e2_as1", "cavities", "flashings", "rainscreen"]
    },
    "interior_linings": {
        "keywords": ["GIB", "plasterboard", "lining", "stopping", "fire rated"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["plasterboard", "fire_rating", "frr", "acoustic", "stopping"]
    },
    "joinery": {
        "keywords": ["window", "door", "joinery", "slider", "frame", "glazing", "sill"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["windows", "doors", "flashings", "weathertightness", "thermal"]
    },
    "waterproofing": {
        "keywords": ["waterproof", "membrane", "tanking", "wet area", "shower", "balcony"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["wet_areas", "membranes", "tanking", "e2_compliance"]
    },
    "h1_energy": {
        "keywords": ["H1", "insulation", "r-value", "thermal", "energy"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["insulation", "thermal_performance", "r_values", "energy_efficiency"]
    },
    "hvac_ventilation": {
        "keywords": ["HVAC", "ventilation", "heating", "heat pump", "ducting"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["ventilation", "heating", "heat_pumps", "ductwork", "g4_compliance"]
    },
    "earthworks_stormwater": {
        "keywords": ["earthworks", "stormwater", "site drainage", "retaining"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["site_drainage", "stormwater", "earthworks", "gradients"]
    },
    "council_consent": {
        "keywords": ["council", "consent", "CCC", "inspection", "PS", "producer statement"],
        "primary_sources": ["NZ Building Code"],
        "trade_types": ["ccc", "consents", "inspections", "producer_statements", "rfis"]
    }
}

def get_trade_domain(trade: str) -> Dict:
    """Get domain configuration for a trade"""
    return TRADE_DOMAINS.get(trade, {
        "keywords": [],
        "primary_sources": ["NZ Building Code"],
        "trade_types": []
    })
