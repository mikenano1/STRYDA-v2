"""
STRYDA Context Session Manager
Lightweight session state for multi-turn context gathering
"""

import time
from typing import Dict, Optional, List

# In-memory session storage (key: session_id)
_context_sessions = {}

# Session expiry time (5 minutes)
SESSION_TIMEOUT = 300


class ContextSession:
    """Represents an active context-gathering session"""
    
    def __init__(self, session_id: str, original_question: str, category: str, required_fields: List[str]):
        self.session_id = session_id
        self.original_question = original_question
        self.category = category
        self.required_fields = required_fields
        self.filled_fields = {}
        self.last_updated = time.time()
        self.has_pending_context = True
    
    def update(self, new_fields: Dict[str, str]):
        """Update filled fields with new context"""
        self.filled_fields.update(new_fields)
        self.last_updated = time.time()
    
    def get_missing_fields(self) -> List[str]:
        """Get list of fields still missing"""
        return [f for f in self.required_fields if f not in self.filled_fields]
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled"""
        return len(self.get_missing_fields()) == 0
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return (time.time() - self.last_updated) > SESSION_TIMEOUT
    
    def build_synthetic_query(self) -> str:
        """
        Build a synthetic full query combining original question + context
        
        Example output:
        "Do I need consent for a 25m² shed?
        
        Details:
        - Building type: shed
        - Floor area: 25m²
        - Height: 2.7m
        - Storeys: single-storey
        - Plumbing: shower, toilet, vanity"
        """
        context_lines = []
        for field, value in self.filled_fields.items():
            # Convert field key to readable label
            field_labels = {
                "building_type": "Building type",
                "floor_area_m2": "Floor area",
                "height_or_fall": "Height",
                "storeys": "Storeys",
                "plumbing_sanitary": "Plumbing",
                "timber_grade": "Timber grade",
                "joist_spacing": "Spacing",
                "use_case": "Use",
                "climate_zone": "Climate zone",
                "wind_zone": "Wind zone",
                "roof_type": "Roof type",
                "pitch": "Pitch",
                "fixture_type": "Fixture",
                "location": "Location",
                "work_type": "Work type",
                "load": "Load",
            }
            
            label = field_labels.get(field, field)
            context_lines.append(f"- {label}: {value}")
        
        context_block = "\n".join(context_lines)
        
        return f"{self.original_question}\n\nDetails:\n{context_block}"


def create_session(session_id: str, original_question: str, category: str, required_fields: List[str], initial_fields: Dict = None) -> ContextSession:
    """Create a new context session"""
    session = ContextSession(session_id, original_question, category, required_fields)
    
    if initial_fields:
        session.update(initial_fields)
    
    _context_sessions[session_id] = session
    print(f"📝 Created context session: {category} for session {session_id[:8]}...")
    
    return session


def get_session(session_id: str) -> Optional[ContextSession]:
    """Get existing context session"""
    session = _context_sessions.get(session_id)
    
    if session and session.is_expired():
        # Clean up expired session
        print(f"⏰ Context session expired for {session_id[:8]}...")
        del _context_sessions[session_id]
        return None
    
    return session


def clear_session(session_id: str):
    """Clear context session"""
    if session_id in _context_sessions:
        category = _context_sessions[session_id].category
        print(f"🧹 Cleared context session: {category} for {session_id[:8]}...")
        del _context_sessions[session_id]


def has_active_session(session_id: str) -> bool:
    """Check if there's an active context session"""
    session = get_session(session_id)
    return session is not None and session.has_pending_context
