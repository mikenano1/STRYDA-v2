"""
STRYDA.ai Compliance Alternatives Engine
Provides compliant alternatives for common building code fail cases
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ComplianceIssue:
    """Represents a potential compliance issue"""
    issue_type: str
    description: str
    severity: str  # 'critical', 'major', 'minor'
    code_reference: str
    alternatives: List[Dict[str, Any]]

@dataclass  
class ComplianceAlternative:
    """Represents a compliant alternative solution"""
    solution_id: str
    title: str
    description: str
    requirements: List[str]
    cost_impact: str  # 'none', 'low', 'medium', 'high'
    difficulty: str  # 'easy', 'moderate', 'complex'
    code_references: List[str]

class ComplianceAlternativesEngine:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.fail_case_patterns = self._load_fail_case_patterns()
        
    def _load_fail_case_patterns(self) -> Dict[str, Any]:
        """Load common fail case patterns and their alternatives"""
        
        return {
            # Hearth and Fireplace Issues
            "hearth_clearances": {
                "patterns": [
                    r"hearth.*clearance.*insufficient",
                    r"fireplace.*too.*close",
                    r"combustible.*material.*near.*fire",
                    r"metrofires.*clearance.*fail"
                ],
                "alternatives": [
                    {
                        "id": "extended_hearth",
                        "title": "Extended Non-Combustible Hearth",
                        "description": "Increase hearth size to meet minimum clearances",
                        "requirements": [
                            "Extend hearth to minimum 400mm front, 200mm sides from fireplace opening",
                            "Use non-combustible materials: concrete, stone, or ceramic tiles on concrete substrate",
                            "Minimum 100mm thickness for concrete hearths, 20mm for stone on concrete base"
                        ],
                        "cost_impact": "low",
                        "difficulty": "easy",
                        "code_references": ["NZBC G5.3.2", "Metrofires Installation Manual"]
                    },
                    {
                        "id": "fireproof_wall_lining",
                        "title": "Fire-Resistant Wall Lining",
                        "description": "Install fire-resistant barrier between fireplace and combustible wall",
                        "requirements": [
                            "Install fire-resistant board (Fireline, Fyrchek) on wall behind fireplace",
                            "Maintain minimum 50mm air gap between lining and combustible wall",
                            "Extend lining 300mm beyond fireplace sides and 500mm above",
                            "Seal all joints with fire-resistant sealant"
                        ],
                        "cost_impact": "medium", 
                        "difficulty": "moderate",
                        "code_references": ["NZBC G5.3", "AS/NZS 2785"]
                    },
                    {
                        "id": "relocate_fireplace",
                        "title": "Relocate Fireplace Position",
                        "description": "Move fireplace to achieve compliant clearances",
                        "requirements": [
                            "Relocate fireplace to position with adequate clearances",
                            "May require new flue installation and structural modifications",
                            "Update building consent for changed location",
                            "Consider impact on room layout and functionality"
                        ],
                        "cost_impact": "high",
                        "difficulty": "complex", 
                        "code_references": ["NZBC G5", "Building Consent Requirements"]
                    }
                ]
            },
            
            # Insulation Compliance Issues
            "insulation_compliance": {
                "patterns": [
                    r"insulation.*r.*value.*insufficient",
                    r"thermal.*performance.*fail",
                    r"h1.*compliance.*issue",
                    r"climate.*zone.*insulation.*wrong"
                ],
                "alternatives": [
                    {
                        "id": "upgraded_insulation",
                        "title": "Upgrade to Higher R-Value Insulation",
                        "description": "Install insulation with higher thermal performance",
                        "requirements": [
                            "Zone 1: Minimum R-2.9 ceiling, R-1.5 walls, R-1.3 floor",
                            "Zone 2: Minimum R-3.3 ceiling, R-1.8 walls, R-1.3 floor", 
                            "Zone 3: Minimum R-3.6 ceiling, R-2.0 walls, R-1.3 floor",
                            "Ensure no thermal bridging or compression of insulation"
                        ],
                        "cost_impact": "low",
                        "difficulty": "easy",
                        "code_references": ["NZBC H1.2", "H1/AS1 Table 1"]
                    },
                    {
                        "id": "continuous_insulation",
                        "title": "Continuous Insulation System",
                        "description": "Add continuous insulation layer to reduce thermal bridging",
                        "requirements": [
                            "Install rigid foam insulation over structural framing",
                            "Minimum 25mm polyester or 20mm PIR/PUR foam",
                            "Tape all joints to eliminate thermal bridges",
                            "Adjust cladding fixings for additional thickness"
                        ],
                        "cost_impact": "medium",
                        "difficulty": "moderate",
                        "code_references": ["NZBC H1.3", "H1/AS1 Paragraph 3.1.1"]
                    },
                    {
                        "id": "alternative_compliance",
                        "title": "Alternative Solution with Energy Modeling",
                        "description": "Use calculation method to demonstrate compliance",
                        "requirements": [
                            "Engage building physicist for thermal modeling",
                            "Use AccuRate, BESS, or equivalent software",
                            "Demonstrate equivalent or better performance than Acceptable Solution",
                            "May allow trade-offs between building elements"
                        ],
                        "cost_impact": "medium",
                        "difficulty": "complex",
                        "code_references": ["NZBC H1", "H1/VM1 Verification Method"]
                    }
                ]
            },
            
            # Material Compatibility Issues  
            "material_compatibility": {
                "patterns": [
                    r"galvanic.*corrosion.*risk",
                    r"incompatible.*materials.*contact",
                    r"e2.*table.*21.*fail",
                    r"metal.*compatibility.*issue"
                ],
                "alternatives": [
                    {
                        "id": "isolation_barrier", 
                        "title": "Install Isolation Barrier Between Materials",
                        "description": "Separate incompatible materials with appropriate barrier",
                        "requirements": [
                            "Install non-conductive barrier (plastic, rubber, paint) between metals",
                            "Use compatible fasteners for each material type",
                            "Refer to E2/AS1 Table 21 for approved material combinations",
                            "Ensure barrier maintains weathertightness"
                        ],
                        "cost_impact": "low",
                        "difficulty": "easy",
                        "code_references": ["E2/AS1 Table 21", "NZBC E2.3.7"]
                    },
                    {
                        "id": "material_substitution",
                        "title": "Substitute with Compatible Materials", 
                        "description": "Replace one material with compatible alternative",
                        "requirements": [
                            "Select materials that are compatible according to E2/AS1 Table 21",
                            "Ensure substitute material meets structural and durability requirements",
                            "Update specifications and building consent if required",
                            "Consider cost and availability of substitute materials"
                        ],
                        "cost_impact": "medium", 
                        "difficulty": "moderate",
                        "code_references": ["E2/AS1 Table 21", "Material Standards"]
                    }
                ]
            },
            
            # Structural Design Issues
            "structural_compliance": {
                "patterns": [
                    r"lintel.*size.*inadequate",
                    r"beam.*span.*excessive", 
                    r"foundation.*bearing.*insufficient",
                    r"seismic.*design.*fail"
                ],
                "alternatives": [
                    {
                        "id": "larger_structural_member",
                        "title": "Increase Structural Member Size",
                        "description": "Use larger beam, lintel, or foundation to carry loads",
                        "requirements": [
                            "Calculate required size using NZS 3604 span tables or engineering",
                            "Ensure adequate bearing at supports",
                            "Check deflection limits for intended use",
                            "Verify connection details can transfer loads"
                        ],
                        "cost_impact": "medium",
                        "difficulty": "moderate", 
                        "code_references": ["NZS 3604", "NZBC B1", "AS/NZS 1170"]
                    },
                    {
                        "id": "additional_support",
                        "title": "Add Intermediate Support",
                        "description": "Reduce span by adding posts, beams, or walls",
                        "requirements": [
                            "Install intermediate support to reduce spans to acceptable limits",
                            "Ensure new supports have adequate foundations", 
                            "Maintain required clear heights and space functionality",
                            "Update architectural drawings for new supports"
                        ],
                        "cost_impact": "medium",
                        "difficulty": "moderate",
                        "code_references": ["NZS 3604 Span Tables", "NZBC B1"]
                    },
                    {
                        "id": "engineered_solution",
                        "title": "Engage Structural Engineer",
                        "description": "Design alternative structural solution outside standard scope",
                        "requirements": [
                            "Engage Chartered Professional Engineer (CPEng)",
                            "Provide engineering design and calculations",
                            "May use alternative materials or construction methods",
                            "PS1 and PS4 documentation required for building consent"
                        ],
                        "cost_impact": "high",
                        "difficulty": "complex",
                        "code_references": ["NZBC B1", "Building Act 2004"]
                    }
                ]
            },
            
            # Weathertightness Issues
            "weathertightness_compliance": {
                "patterns": [
                    r"weathertight.*fail",
                    r"moisture.*penetration.*risk",
                    r"e2.*compliance.*issue",
                    r"cladding.*installation.*non.*compliant"
                ],
                "alternatives": [
                    {
                        "id": "improved_flashing",
                        "title": "Install Enhanced Flashing System",
                        "description": "Upgrade flashing details to prevent water penetration",
                        "requirements": [
                            "Install head flashing over all openings with 15° minimum fall",
                            "Jamb flashings must extend 25mm past opening and be sealed",
                            "Sill flashings must project 45mm from wall and have end dams",
                            "All flashings to be corrosion-resistant metal minimum 0.40mm thick"
                        ],
                        "cost_impact": "low",
                        "difficulty": "moderate",
                        "code_references": ["E2/AS1 Figure 27", "NZBC E2.3.2"]
                    },
                    {
                        "id": "cavity_system_upgrade",
                        "title": "Install Drained Cavity System",
                        "description": "Add cavity system to manage moisture penetration",
                        "requirements": [
                            "Install 20mm minimum drained cavity behind cladding",
                            "Use cavity battens minimum 45x20mm treated timber at 600mm centres",
                            "Install building wrap over framing, under cavity battens",
                            "Provide ventilation gaps at top and bottom of cavity"
                        ],
                        "cost_impact": "medium",
                        "difficulty": "moderate", 
                        "code_references": ["E2/AS1 Paragraph 9.1.5", "NZBC E2.3.3"]
                    }
                ]
            }
        }
    
    async def analyze_compliance_issues(self, query: str, context: str = "") -> List[ComplianceIssue]:
        """Analyze text for potential compliance issues and suggest alternatives"""
        
        issues = []
        query_lower = query.lower()
        context_lower = context.lower()
        combined_text = f"{query_lower} {context_lower}"
        
        for issue_type, config in self.fail_case_patterns.items():
            # Check if any pattern matches
            for pattern in config["patterns"]:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    
                    # Determine severity based on keywords
                    severity = self._determine_severity(combined_text, issue_type)
                    
                    issue = ComplianceIssue(
                        issue_type=issue_type,
                        description=self._get_issue_description(issue_type, combined_text),
                        severity=severity,
                        code_reference=self._get_primary_code_reference(issue_type),
                        alternatives=config["alternatives"]
                    )
                    
                    issues.append(issue)
                    logger.info(f"Identified compliance issue: {issue_type} - {severity}")
                    break  # Only match first pattern per issue type
        
        return issues
    
    def _determine_severity(self, text: str, issue_type: str) -> str:
        """Determine severity of compliance issue based on context"""
        
        critical_keywords = ["fail", "non-compliant", "dangerous", "unsafe", "prohibited"]
        major_keywords = ["insufficient", "inadequate", "risk", "concern", "problem"] 
        
        if any(keyword in text for keyword in critical_keywords):
            return "critical"
        elif any(keyword in text for keyword in major_keywords):
            return "major"
        else:
            return "minor"
    
    def _get_issue_description(self, issue_type: str, text: str) -> str:
        """Generate description for the identified issue"""
        
        descriptions = {
            "hearth_clearances": "Fireplace hearth clearances may not meet minimum NZ Building Code requirements. Insufficient clearances to combustible materials pose fire risk.",
            "insulation_compliance": "Insulation thermal performance may not meet H1 energy efficiency requirements for the building's climate zone.",
            "material_compatibility": "Materials in direct contact may be incompatible and risk galvanic corrosion or deterioration.",
            "structural_compliance": "Structural elements may not meet load-bearing requirements or span limits per NZS 3604 or NZ Building Code.",
            "weathertightness_compliance": "Weathertightness details may not prevent moisture penetration as required by E2 external moisture provisions."
        }
        
        return descriptions.get(issue_type, "Potential building code compliance issue identified.")
    
    def _get_primary_code_reference(self, issue_type: str) -> str:
        """Get the primary building code reference for the issue type"""
        
        references = {
            "hearth_clearances": "NZBC Clause G5.3",
            "insulation_compliance": "NZBC Clause H1.2", 
            "material_compatibility": "E2/AS1 Table 21",
            "structural_compliance": "NZBC Clause B1",
            "weathertightness_compliance": "NZBC Clause E2"
        }
        
        return references.get(issue_type, "NZ Building Code")
    
    async def get_compliance_guidance(self, query: str) -> Dict[str, Any]:
        """Get comprehensive compliance guidance including alternatives"""
        
        # Search knowledge base for relevant information
        relevant_docs = await self.document_processor.search_documents(query, limit=3)
        
        # Analyze for compliance issues
        context = " ".join([doc["content"] for doc in relevant_docs]) if relevant_docs else ""
        issues = await self.analyze_compliance_issues(query, context)
        
        # Format response
        guidance = {
            "query": query,
            "compliance_status": "review_required" if issues else "likely_compliant",
            "issues_found": len(issues),
            "issues": [],
            "general_guidance": self._get_general_guidance(query),
            "recommended_actions": []
        }
        
        for issue in issues:
            issue_data = {
                "type": issue.issue_type,
                "description": issue.description,
                "severity": issue.severity,
                "code_reference": issue.code_reference,
                "alternatives": []
            }
            
            for alt in issue.alternatives:
                alt_data = {
                    "id": alt["id"],
                    "title": alt["title"], 
                    "description": alt["description"],
                    "requirements": alt["requirements"],
                    "cost_impact": alt["cost_impact"],
                    "difficulty": alt["difficulty"],
                    "code_references": alt["code_references"]
                }
                issue_data["alternatives"].append(alt_data)
            
            guidance["issues"].append(issue_data)
        
        # Add recommended actions
        if issues:
            guidance["recommended_actions"] = [
                "Review building consent documentation for approved details",
                "Consult with Licensed Building Practitioner (LBP) for professional advice",
                "Consider engaging specialist (engineer, building physicist) if required",
                "Verify compliance with local territorial authority requirements"
            ]
        else:
            guidance["recommended_actions"] = [
                "Proceed with installation following manufacturer specifications",
                "Ensure all work complies with building consent conditions",
                "Maintain documentation for building code compliance certificate"
            ]
        
        return guidance
    
    def _get_general_guidance(self, query: str) -> str:
        """Provide general guidance based on query content"""
        
        query_lower = query.lower()
        
        if "fireplace" in query_lower or "hearth" in query_lower:
            return "All solid fuel appliance installations must comply with NZBC Clause G5 and manufacturer specifications. When manufacturer requirements are stricter than code minimums, follow manufacturer specifications."
        
        elif "insulation" in query_lower or "thermal" in query_lower:
            return "Insulation must meet minimum R-values for the building's climate zone per NZBC Clause H1. Installation quality significantly affects performance - avoid compression and thermal bridging."
        
        elif "structural" in query_lower or "beam" in query_lower or "lintel" in query_lower:
            return "Structural elements must comply with NZBC Clause B1. Use NZS 3604 for standard construction or engage a structural engineer for complex designs."
        
        elif "cladding" in query_lower or "weathertight" in query_lower:
            return "Cladding systems must comply with NZBC Clause E2 for external moisture management. Follow manufacturer installation instructions and E2/AS1 details."
        
        else:
            return "Ensure all building work complies with the NZ Building Code and any specific requirements in your building consent. When in doubt, consult with licensed professionals."