"""
STRYDA Simple Conversation Store (Task 2D Spike)
Minimal in-memory storage for unified conversation model
"""

import time
import uuid
from typing import Dict, Optional

# In-memory conversation storage (key: conversation_id)
_conversations = {}

# Conversation expiry (30 minutes)
CONVERSATION_TIMEOUT = 1800


class SimpleConversation:
    """Unified conversation object for SIMPLE_SESSION_MODE"""
    
    def __init__(self, conversation_id: str, original_question: str, intent_locked: str):
        self.conversation_id = conversation_id
        self.intent_locked = intent_locked
        self.intent_locked_at_turn = 1
        self.conversation_state = "normal"  # normal | gathering_context | answered
        self.original_question = original_question
        self.context_collected = {}
        self.pending_gate = None  # For required-inputs gate
        self.turn_number = 1
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def increment_turn(self):
        """Increment turn counter"""
        self.turn_number += 1
        self.updated_at = time.time()
    
    def set_state(self, state: str):
        """Update conversation state"""
        self.conversation_state = state
        self.updated_at = time.time()
    
    def update_context(self, new_context: Dict):
        """Update collected context"""
        self.context_collected.update(new_context)
        self.updated_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if conversation has expired"""
        return (time.time() - self.updated_at) > CONVERSATION_TIMEOUT
    
    def to_dict(self) -> Dict:
        """Export as dict for logging"""
        return {
            "conversation_id": self.conversation_id,
            "intent_locked": self.intent_locked,
            "intent_locked_at_turn": self.intent_locked_at_turn,
            "conversation_state": self.conversation_state,
            "original_question": self.original_question,
            "context_collected": self.context_collected,
            "turn_number": self.turn_number,
            "age_seconds": int(time.time() - self.created_at)
        }


def bootstrap_conversation(session_id: str, original_question: str, intent_locked: str) -> SimpleConversation:
    """
    Create new conversation on Turn 1
    
    Args:
        session_id: Session ID from request (used as conversation_id)
        original_question: User's first message
        intent_locked: Intent classification result (locked for conversation)
    
    Returns:
        SimpleConversation object
    """
    # Use session_id as conversation_id (simpler for spike)
    conversation_id = session_id
    
    conversation = SimpleConversation(conversation_id, original_question, intent_locked)
    _conversations[conversation_id] = conversation
    
    print(f"[conversation_bootstrap] id={conversation_id[:12]} intent={intent_locked} state={conversation.conversation_state} simple_session=true")
    
    return conversation


def get_conversation(conversation_id: str) -> Optional[SimpleConversation]:
    """Get existing conversation"""
    conversation = _conversations.get(conversation_id)
    
    if conversation and conversation.is_expired():
        # Clean up expired
        print(f"⏰ Conversation expired: {conversation_id[:12]}")
        del _conversations[conversation_id]
        return None
    
    return conversation


def clear_conversation(conversation_id: str):
    """Clear conversation"""
    if conversation_id in _conversations:
        print(f"🧹 Cleared conversation: {conversation_id[:12]}")
        del _conversations[conversation_id]




def set_pending_gate(conversation_id: str, gate_payload: Dict, original_question: str):
    """Set pending gate state for conversation"""
    conv = get_conversation(conversation_id)
    if conv:
        conv.pending_gate = {
            "question_key": gate_payload.get("question_key"),
            "required_fields": gate_payload.get("required_fields", []),
            "collected_fields": {},
            "started_at": time.time()
        }
        if not conv.original_question:
            conv.original_question = original_question
        conv.updated_at = time.time()


def update_pending_gate(conversation_id: str, field_updates: Dict):
    """Update collected fields"""
    conv = get_conversation(conversation_id)
    if conv and conv.pending_gate:
        conv.pending_gate["collected_fields"].update(field_updates)
        conv.updated_at = time.time()


def get_pending_gate(conversation_id: str) -> Optional[Dict]:
    """Get pending gate"""
    conv = get_conversation(conversation_id)
    return conv.pending_gate if conv else None


def clear_pending_gate(conversation_id: str):
    """Clear gate"""
    conv = get_conversation(conversation_id)
    if conv:
        conv.pending_gate = None
        conv.updated_at = time.time()

def has_conversation(conversation_id: str) -> bool:
    """Check if conversation exists"""
    conv = get_conversation(conversation_id)
    return conv is not None
