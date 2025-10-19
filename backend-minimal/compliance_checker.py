"""
STRYDA Compliance Checker v2
Structured compliance responses with verdicts and assumptions
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import re

class Verdict(str, Enum):
    YES = "YES"
    NO = "NO"
    COND = "COND"

class ComplianceResponse:
    """Structured compliance response builder"""
    
    @staticmethod
    def extract_numeric_requirements(content: str) -> List[str]:
        """Extract numeric requirements from content"""
        # Pattern for numbers with units
        numeric_pattern = r'\b\d+(?:\.\d+)?\s*(?:mm|m|kPa|kN|°|degrees?|%)\b'
        
        requirements = re.findall(numeric_pattern, content, re.IGNORECASE)
        return list(set(requirements))  # Remove duplicates
    
    @staticmethod
    def identify_table_figure_refs(content: str) -> List[str]:
        """Identify table/figure references in content"""
        # Patterns for tables and figures
        table_pattern = r'Table\s+\d+(?:\.\d+)?'
        figure_pattern = r'Figure\s+\d+(?:\.\d+)?'
        clause_pattern = r'Clause\s+[A-H]?\d+(?:\.\d+)?'
        
        refs = []
        refs.extend(re.findall(table_pattern, content, re.IGNORECASE))
        refs.extend(re.findall(figure_pattern, content, re.IGNORECASE))
        refs.extend(re.findall(clause_pattern, content, re.IGNORECASE))
        
        return refs
    
    @staticmethod
    def build_structured_answer(query: str, docs: List[Dict], intent: str) -> Dict[str, Any]:
        """Build structured compliance answer with verdict"""
        
        if intent != "compliance_strict":
            # Non-compliance intents get simple responses with no citations
            return {
                "answer": "I can help with general building guidance. For specific compliance requirements, ask about particular building code sections.",
                "intent": intent,
                "citations": [],
                "verdict": "COND",
                "assumptions": [],
                "inputs_required": ["Specific building code question"]
            }
        
        if not docs:
            # No retrieval results - ask for clarification
            return {
                "answer": "I need more specific information to provide compliance guidance. Please specify the building element, dimensions, and relevant building standard.",
                "intent": intent,
                "citations": [],
                "verdict": "COND",
                "assumptions": [],
                "inputs_required": ["Building element", "Dimensions", "Relevant standard"]
            }
        
        # Analyze best documents for compliance response
        primary_doc = docs[0]
        primary_content = primary_doc.get('content', '')
        primary_snippet = primary_doc.get('snippet', '')
        
        # Extract key information
        numeric_requirements = ComplianceResponse.extract_numeric_requirements(primary_content + " " + primary_snippet)
        table_refs = ComplianceResponse.identify_table_figure_refs(primary_content)
        
        # Determine verdict based on content analysis
        verdict = "YES"
        if any(word in query.lower() for word in ['can', 'may', 'allowed', 'acceptable']):
            # User asking if something is allowed
            if numeric_requirements and any(word in primary_content.lower() for word in ['minimum', 'maximum', 'limit']):
                verdict = "YES"
            elif any(word in primary_content.lower() for word in ['not', 'prohibited', 'shall not']):
                verdict = "NO"
            else:
                verdict = "COND"
        else:
            # User asking for requirements
            verdict = "YES" if numeric_requirements else "COND"
        
        # Build structured response parts
        rule_part = ""
        if numeric_requirements:
            primary_requirement = numeric_requirements[0]
            source = primary_doc.get('source', 'Unknown')
            page = primary_doc.get('page', 0)
            table_ref = f" {table_refs[0]}" if table_refs else ""
            
            rule_part = f"Requirement: {primary_requirement} — {source}{table_ref}, p.{page}"
        
        applies_when = [
            "Standard building construction",
            "NZ Building Code requirements apply"
        ]
        
        # Add specific context from query
        if 'decking' in query.lower():
            applies_when.append("Solid timber decking")
        if 'joist' in query.lower():
            applies_when.append("Timber floor joists")
        if 'wind' in query.lower():
            applies_when.append("Specific wind zone requirements")
        
        notes = "Consult specific product documentation for additional requirements"
        if verdict == "COND":
            notes = "Additional information needed for specific compliance determination"
        
        # Construct structured answer
        answer_parts = [
            f"VERDICT: {verdict}",
            f"RULE: {rule_part}" if rule_part else "RULE: Refer to building standard requirements",
            f"APPLIES WHEN: {'; '.join(applies_when)}",
            f"NOTES: {notes}"
        ]
        
        structured_answer = "\n".join(answer_parts)
        
        # Build citations (max 3)
        citations = []
        for doc in docs[:3]:
            citation = {
                "source": doc.get("source", "Unknown"),
                "page": doc.get("page", 0),
                "id": table_refs[0] if table_refs else f"p.{doc.get('page', 0)}",
                "snippet": doc.get("snippet", "")[:100] + ("..." if len(doc.get("snippet", "")) > 100 else "")
            }
            citations.append(citation)
        
        return {
            "answer": structured_answer,
            "intent": intent,
            "citations": citations,
            "verdict": verdict,
            "assumptions": applies_when,
            "inputs_required": [] if verdict in ["YES", "NO"] else ["More specific building details"]
        }

# Export for use in main app
def build_compliance_response(query: str, docs: List[Dict], intent: str) -> Dict[str, Any]:
    return ComplianceResponse.build_structured_answer(query, docs, intent)