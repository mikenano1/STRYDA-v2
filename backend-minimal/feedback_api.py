#!/usr/bin/env python3
"""
STRYDA Protocol V2.0 - Feedback API Module
===========================================
Implements the self-correction loop from Protocol V2.0 Section 11.

Safety-First Thresholds:
- incorrect/misleading: 1 flag = IMMEDIATE deactivation (safety critical)
- duplicate/outdated: 3 flags = auto-deactivation

This ensures building industry answers don't lead to structural failure
or legal liability.

Author: STRYDA Brain Build Team
Version: 2.0
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

import psycopg2
import psycopg2.extras


# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres')


# ============================================================
# FEEDBACK TYPES & THRESHOLDS (SAFETY-FIRST)
# ============================================================

class FeedbackType(Enum):
    """
    Feedback categories from Protocol V2.0.
    Safety-critical types have immediate deactivation.
    """
    INCORRECT = "incorrect"       # SAFETY: 1 flag = immediate deactivation
    MISLEADING = "misleading"     # SAFETY: 1 flag = immediate deactivation
    OUTDATED = "outdated"         # 3 flags = auto-deactivation
    DUPLICATE = "duplicate"       # 3 flags = auto-deactivation


# Safety-first thresholds
FEEDBACK_THRESHOLDS = {
    FeedbackType.INCORRECT.value: 1,    # IMMEDIATE - safety critical
    FeedbackType.MISLEADING.value: 1,   # IMMEDIATE - safety critical
    FeedbackType.OUTDATED.value: 3,     # After 3 reports
    FeedbackType.DUPLICATE.value: 3,    # After 3 reports
}

# Resolution actions
RESOLUTION_ACTIONS = {
    'blacklisted': "Chunk deactivated (is_active = FALSE)",
    'reweighted': "Chunk priority reduced",
    'corrected': "Metadata corrected",
    'dismissed': "Feedback dismissed by moderator",
}


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class FeedbackRecord:
    """A feedback record from the chunk_feedback table."""
    id: str
    chunk_id: str
    user_id: Optional[str]
    feedback_type: str
    feedback_note: Optional[str]
    suggested_correction: Optional[str]
    created_at: datetime
    resolved: bool
    resolution_action: Optional[str]


@dataclass 
class FeedbackResponse:
    """Response from submitting feedback."""
    success: bool
    message: str
    action_taken: Optional[str]
    chunk_status: str
    feedback_count: int


# ============================================================
# CORE FEEDBACK FUNCTIONS
# ============================================================

def submit_feedback(
    chunk_id: str,
    feedback_type: str,
    feedback_note: Optional[str] = None,
    suggested_correction: Optional[str] = None,
    user_id: Optional[str] = None,
) -> FeedbackResponse:
    """
    Submit feedback for a specific chunk.
    
    SAFETY-FIRST LOGIC:
    - If feedback_type is 'incorrect' or 'misleading': IMMEDIATE deactivation
    - If feedback_type is 'outdated' or 'duplicate': Check threshold (3 flags)
    
    Args:
        chunk_id: UUID of the document chunk
        feedback_type: One of 'incorrect', 'outdated', 'misleading', 'duplicate'
        feedback_note: User's description of the issue
        suggested_correction: User's suggested fix (optional)
        user_id: User identifier for tracking (optional)
    
    Returns:
        FeedbackResponse with action taken
    """
    # Validate feedback type
    if feedback_type not in [ft.value for ft in FeedbackType]:
        return FeedbackResponse(
            success=False,
            message=f"Invalid feedback type: {feedback_type}",
            action_taken=None,
            chunk_status="unknown",
            feedback_count=0,
        )
    
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Verify chunk exists
            cur.execute("""
                SELECT id, is_active, feedback_count, blacklist_reason
                FROM documents
                WHERE id = %s;
            """, (chunk_id,))
            
            chunk = cur.fetchone()
            
            if not chunk:
                return FeedbackResponse(
                    success=False,
                    message=f"Chunk not found: {chunk_id}",
                    action_taken=None,
                    chunk_status="not_found",
                    feedback_count=0,
                )
            
            current_is_active = chunk['is_active'] if chunk['is_active'] is not None else True
            current_feedback_count = chunk['feedback_count'] or 0
            
            # Insert feedback record
            feedback_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO chunk_feedback (
                    id, chunk_id, user_id, feedback_type, feedback_note,
                    suggested_correction, created_at, resolved, resolution_action
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), FALSE, NULL)
                RETURNING id;
            """, (
                feedback_id,
                chunk_id,
                user_id,
                feedback_type,
                feedback_note,
                suggested_correction,
            ))
            
            # Increment feedback count on chunk
            new_feedback_count = current_feedback_count + 1
            cur.execute("""
                UPDATE documents
                SET feedback_count = %s
                WHERE id = %s;
            """, (new_feedback_count, chunk_id))
            
            # Determine action based on feedback type and threshold
            threshold = FEEDBACK_THRESHOLDS.get(feedback_type, 3)
            action_taken = None
            chunk_status = "active"
            
            if feedback_type in (FeedbackType.INCORRECT.value, FeedbackType.MISLEADING.value):
                # SAFETY CRITICAL: Immediate deactivation
                blacklist_reason = f"[SAFETY] {feedback_type}: {feedback_note or 'User reported'}"
                
                cur.execute("""
                    UPDATE documents
                    SET is_active = FALSE,
                        blacklist_reason = %s
                    WHERE id = %s;
                """, (blacklist_reason, chunk_id))
                
                # Mark feedback as resolved
                cur.execute("""
                    UPDATE chunk_feedback
                    SET resolved = TRUE,
                        resolution_action = 'blacklisted'
                    WHERE id = %s;
                """, (feedback_id,))
                
                action_taken = "IMMEDIATE_DEACTIVATION"
                chunk_status = "deactivated"
                
                print(f"🚨 SAFETY: Chunk {chunk_id[:8]}... DEACTIVATED - {feedback_type}")
                
            elif new_feedback_count >= threshold:
                # Threshold reached for non-safety types
                blacklist_reason = f"Auto-deactivated: {threshold}+ {feedback_type} flags"
                
                cur.execute("""
                    UPDATE documents
                    SET is_active = FALSE,
                        blacklist_reason = %s
                    WHERE id = %s;
                """, (blacklist_reason, chunk_id))
                
                # Mark all feedback for this chunk as resolved
                cur.execute("""
                    UPDATE chunk_feedback
                    SET resolved = TRUE,
                        resolution_action = 'blacklisted'
                    WHERE chunk_id = %s AND resolved = FALSE;
                """, (chunk_id,))
                
                action_taken = f"AUTO_DEACTIVATION (threshold: {threshold})"
                chunk_status = "deactivated"
                
                print(f"⚠️ Chunk {chunk_id[:8]}... AUTO-DEACTIVATED - {threshold}x {feedback_type}")
                
            else:
                # Under threshold, just log
                action_taken = f"LOGGED (count: {new_feedback_count}/{threshold})"
                chunk_status = "active"
                
                print(f"📝 Feedback logged for {chunk_id[:8]}... ({new_feedback_count}/{threshold})")
            
            conn.commit()
            
            return FeedbackResponse(
                success=True,
                message=f"Feedback submitted successfully",
                action_taken=action_taken,
                chunk_status=chunk_status,
                feedback_count=new_feedback_count,
            )
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Feedback submission failed: {e}")
        return FeedbackResponse(
            success=False,
            message=f"Error: {str(e)}",
            action_taken=None,
            chunk_status="error",
            feedback_count=0,
        )
        
    finally:
        conn.close()


def reweight_chunk(
    chunk_id: str,
    weight_modifier: float,
    reason: str,
    user_id: Optional[str] = None,
) -> FeedbackResponse:
    """
    Re-weight a chunk's priority without fully deactivating it.
    
    Args:
        chunk_id: UUID of the document chunk
        weight_modifier: Float between 0.1 and 1.0 (lower = lower priority)
        reason: Explanation for the re-weighting
        user_id: User identifier for audit trail
    
    Returns:
        FeedbackResponse with action taken
    """
    if not 0.1 <= weight_modifier <= 1.0:
        return FeedbackResponse(
            success=False,
            message="weight_modifier must be between 0.1 and 1.0",
            action_taken=None,
            chunk_status="unchanged",
            feedback_count=0,
        )
    
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        with conn.cursor() as cur:
            # Update chunk priority
            cur.execute("""
                UPDATE documents
                SET priority = COALESCE(priority, 50) * %s
                WHERE id = %s
                RETURNING priority;
            """, (weight_modifier, chunk_id))
            
            result = cur.fetchone()
            
            if not result:
                return FeedbackResponse(
                    success=False,
                    message=f"Chunk not found: {chunk_id}",
                    action_taken=None,
                    chunk_status="not_found",
                    feedback_count=0,
                )
            
            new_priority = result[0]
            
            # Log feedback record
            cur.execute("""
                INSERT INTO chunk_feedback (
                    id, chunk_id, user_id, feedback_type, feedback_note,
                    created_at, resolved, resolution_action
                )
                VALUES (%s, %s, %s, 'misleading', %s, NOW(), TRUE, 'reweighted');
            """, (str(uuid.uuid4()), chunk_id, user_id, reason))
            
            conn.commit()
            
            return FeedbackResponse(
                success=True,
                message=f"Chunk priority adjusted to {new_priority:.1f}",
                action_taken=f"REWEIGHTED ({weight_modifier}x)",
                chunk_status="active",
                feedback_count=0,
            )
            
    except Exception as e:
        conn.rollback()
        return FeedbackResponse(
            success=False,
            message=f"Error: {str(e)}",
            action_taken=None,
            chunk_status="error",
            feedback_count=0,
        )
        
    finally:
        conn.close()


def reactivate_chunk(
    chunk_id: str,
    reason: str,
    user_id: Optional[str] = None,
) -> FeedbackResponse:
    """
    Reactivate a previously deactivated chunk after review.
    
    Args:
        chunk_id: UUID of the document chunk
        reason: Why the chunk is being reactivated
        user_id: Moderator identifier
    
    Returns:
        FeedbackResponse with action taken
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        with conn.cursor() as cur:
            # Reactivate chunk
            cur.execute("""
                UPDATE documents
                SET is_active = TRUE,
                    blacklist_reason = NULL,
                    feedback_count = 0
                WHERE id = %s
                RETURNING source, page;
            """, (chunk_id,))
            
            result = cur.fetchone()
            
            if not result:
                return FeedbackResponse(
                    success=False,
                    message=f"Chunk not found: {chunk_id}",
                    action_taken=None,
                    chunk_status="not_found",
                    feedback_count=0,
                )
            
            # Mark all feedback as dismissed
            cur.execute("""
                UPDATE chunk_feedback
                SET resolved = TRUE,
                    resolution_action = 'dismissed'
                WHERE chunk_id = %s;
            """, (chunk_id,))
            
            # Log reactivation
            cur.execute("""
                INSERT INTO chunk_feedback (
                    id, chunk_id, user_id, feedback_type, feedback_note,
                    created_at, resolved, resolution_action
                )
                VALUES (%s, %s, %s, 'reactivation', %s, NOW(), TRUE, 'corrected');
            """, (str(uuid.uuid4()), chunk_id, user_id, reason))
            
            conn.commit()
            
            print(f"✅ Chunk {chunk_id[:8]}... REACTIVATED: {reason}")
            
            return FeedbackResponse(
                success=True,
                message=f"Chunk reactivated: {result[0]} p.{result[1]}",
                action_taken="REACTIVATED",
                chunk_status="active",
                feedback_count=0,
            )
            
    except Exception as e:
        conn.rollback()
        return FeedbackResponse(
            success=False,
            message=f"Error: {str(e)}",
            action_taken=None,
            chunk_status="error",
            feedback_count=0,
        )
        
    finally:
        conn.close()


# ============================================================
# FEEDBACK DASHBOARD QUERIES
# ============================================================

def get_flagged_chunks(
    limit: int = 50,
    unresolved_only: bool = True,
) -> List[Dict]:
    """
    Get chunks that have been flagged with feedback.
    Useful for moderation dashboard.
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        resolved_filter = "WHERE cf.resolved = FALSE" if unresolved_only else ""
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    d.id as chunk_id,
                    d.source,
                    d.page,
                    d.is_active,
                    d.feedback_count,
                    d.blacklist_reason,
                    ARRAY_AGG(DISTINCT cf.feedback_type) as feedback_types,
                    COUNT(cf.id) as flag_count,
                    MAX(cf.created_at) as latest_flag
                FROM documents d
                JOIN chunk_feedback cf ON d.id = cf.chunk_id
                {resolved_filter}
                GROUP BY d.id, d.source, d.page, d.is_active, d.feedback_count, d.blacklist_reason
                ORDER BY flag_count DESC, latest_flag DESC
                LIMIT %s;
            """, (limit,))
            
            rows = cur.fetchall()
            
            return [dict(row) for row in rows]
            
    finally:
        conn.close()


def get_feedback_stats() -> Dict:
    """
    Get overall feedback statistics for monitoring.
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Overall counts
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved_count,
                    COUNT(*) FILTER (WHERE resolved = TRUE) as resolved_count,
                    COUNT(DISTINCT chunk_id) as unique_chunks_flagged
                FROM chunk_feedback;
            """)
            feedback_stats = dict(cur.fetchone())
            
            # Deactivated chunks
            cur.execute("""
                SELECT COUNT(*) as deactivated_chunks
                FROM documents
                WHERE is_active = FALSE;
            """)
            deactivated = cur.fetchone()[0]
            
            # Feedback by type
            cur.execute("""
                SELECT 
                    feedback_type,
                    COUNT(*) as count
                FROM chunk_feedback
                GROUP BY feedback_type;
            """)
            by_type = {row['feedback_type']: row['count'] for row in cur.fetchall()}
            
            return {
                'unresolved_feedback': feedback_stats['unresolved_count'],
                'resolved_feedback': feedback_stats['resolved_count'],
                'unique_chunks_flagged': feedback_stats['unique_chunks_flagged'],
                'deactivated_chunks': deactivated,
                'feedback_by_type': by_type,
            }
            
    finally:
        conn.close()


# ============================================================
# VALIDATION
# ============================================================

def validate_feedback_system():
    """
    Validate the feedback system is working correctly.
    """
    print("=" * 70)
    print("PROTOCOL V2.0 - FEEDBACK SYSTEM VALIDATION")
    print("=" * 70)
    
    # Check database tables exist
    print("\n1️⃣ Checking database tables...")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    try:
        with conn.cursor() as cur:
            # Check chunk_feedback table
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'chunk_feedback';
            """)
            has_table = cur.fetchone()[0] > 0
            print(f"   chunk_feedback table: {'✅ EXISTS' if has_table else '❌ MISSING'}")
            
            # Check documents columns
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'documents' 
                AND column_name IN ('is_active', 'feedback_count', 'blacklist_reason');
            """)
            columns = [row[0] for row in cur.fetchall()]
            print(f"   documents.is_active: {'✅' if 'is_active' in columns else '❌'}")
            print(f"   documents.feedback_count: {'✅' if 'feedback_count' in columns else '❌'}")
            print(f"   documents.blacklist_reason: {'✅' if 'blacklist_reason' in columns else '❌'}")
    finally:
        conn.close()
    
    # Get stats
    print("\n2️⃣ Feedback statistics...")
    stats = get_feedback_stats()
    print(f"   📊 Unresolved feedback: {stats['unresolved_feedback']}")
    print(f"   📊 Resolved feedback: {stats['resolved_feedback']}")
    print(f"   📊 Unique chunks flagged: {stats['unique_chunks_flagged']}")
    print(f"   📊 Deactivated chunks: {stats['deactivated_chunks']}")
    if stats['feedback_by_type']:
        print(f"   📊 By type: {stats['feedback_by_type']}")
    
    # Test threshold logic
    print("\n3️⃣ Safety threshold configuration...")
    for ft, threshold in FEEDBACK_THRESHOLDS.items():
        safety = "🚨 SAFETY-CRITICAL" if threshold == 1 else "⚠️ Auto-deactivate"
        print(f"   {ft}: {threshold} flag(s) → {safety}")
    
    print("\n" + "=" * 70)
    print("✅ FEEDBACK SYSTEM VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    validate_feedback_system()
