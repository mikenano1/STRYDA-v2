"""
STRYDA.ai Enhanced Search Engine
Advanced multi-section search and combination for comprehensive building advice
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class EnhancedSearchEngine:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        
        # Related concept groups for building documents
        self.concept_groups = {
            'structural_sizing': [
                'beam', 'joist', 'rafter', 'lintel', 'span', 'load', 'sizing', 'dimensions',
                'structural', 'timber', 'steel', 'concrete', 'lvl', 'glulam'
            ],
            'metal_roofing': [
                'metal', 'roof', 'roofing', 'cladding', 'fixing', 'fastener', 'purlin',
                'corrugated', 'colorsteel', 'installation', 'flashing', 'weathering'
            ],
            'fire_safety': [
                'fire', 'fireplace', 'clearance', 'combustible', 'hearth', 'flue',
                'safety', 'protection', 'flame', 'heat', 'installation'
            ],
            'building_compliance': [
                'nzbc', 'building', 'code', 'clause', 'compliance', 'consent',
                'standard', 'requirement', 'regulation', 'certification'
            ],
            'weatherproofing': [
                'weather', 'moisture', 'water', 'weathertight', 'cavity', 'drainage',
                'flashing', 'membrane', 'sealant', 'joint', 'penetration'
            ]
        }
        
        # Minimum similarity threshold for related sections
        self.min_related_similarity = 0.15
        
        # Maximum sections to combine for comprehensive answers
        self.max_combined_sections = 8
    
    async def enhanced_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform enhanced search with section combination"""
        
        logger.info(f"🔍 Enhanced search: {query}")
        
        # Get initial search results
        initial_results = await self.document_processor.search_documents(
            query=query,
            limit=limit * 2  # Get more results for analysis
        )
        
        if not initial_results:
            return {
                "results": [],
                "total_found": 0,
                "search_method": "enhanced_no_results"
            }
        
        # Analyze query for concept groups
        query_concepts = self._analyze_query_concepts(query)
        
        # Group related sections
        grouped_sections = self._group_related_sections(initial_results, query_concepts)
        
        # Combine sections within groups for better context
        enhanced_results = await self._combine_related_sections(grouped_sections, query)
        
        # Re-rank results based on combined relevance
        final_results = self._rank_combined_results(enhanced_results, query)
        
        logger.info(f"✅ Enhanced search complete: {len(final_results)} combined results")
        
        return {
            "results": final_results[:limit],
            "total_found": len(final_results),
            "search_method": "enhanced_multi_section",
            "concepts_detected": query_concepts,
            "sections_combined": sum(len(group['sections']) for group in grouped_sections)
        }
    
    def _analyze_query_concepts(self, query: str) -> List[str]:
        """Analyze query to identify relevant concept groups"""
        
        query_lower = query.lower()
        detected_concepts = []
        
        for concept_group, keywords in self.concept_groups.items():
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            
            # If significant portion of keywords match, include this concept
            if matches >= 2 or (matches >= 1 and len(keywords) <= 5):
                detected_concepts.append(concept_group)
        
        logger.info(f"🎯 Detected concepts: {detected_concepts}")
        return detected_concepts
    
    def _group_related_sections(self, search_results: List[Dict], 
                              query_concepts: List[str]) -> List[Dict[str, Any]]:
        """Group related sections that should be combined"""
        
        groups = []
        used_results = set()
        
        # Group by document title patterns (e.g., same structural guide sections)
        document_groups = defaultdict(list)
        
        for i, result in enumerate(search_results):
            if i in used_results:
                continue
                
            title = result.get('title', '')
            base_title = self._extract_base_title(title)
            
            # Look for related sections from same document
            related_sections = [result]
            used_results.add(i)
            
            for j, other_result in enumerate(search_results[i+1:], i+1):
                if j in used_results:
                    continue
                    
                other_title = other_result.get('title', '')
                other_base_title = self._extract_base_title(other_title)
                
                # Check if sections are related
                if self._are_sections_related(result, other_result, base_title, other_base_title):
                    related_sections.append(other_result)
                    used_results.add(j)
                    
                    # Limit section combination
                    if len(related_sections) >= self.max_combined_sections:
                        break
            
            groups.append({
                'base_title': base_title,
                'sections': related_sections,
                'concepts': query_concepts,
                'combined_score': sum(s.get('similarity_score', 0) for s in related_sections)
            })
        
        # Sort groups by combined relevance
        groups.sort(key=lambda g: g['combined_score'], reverse=True)
        
        logger.info(f"📊 Created {len(groups)} section groups")
        return groups
    
    def _extract_base_title(self, title: str) -> str:
        """Extract base document title without section indicators"""
        
        # Remove common section indicators
        patterns_to_remove = [
            r'\s*-\s*\d+\.?\d*\s*.*$',  # - 1.1 Section
            r'\s*\([^)]*\)$',  # (Part 1)
            r'\s*Part\s+\d+.*$',  # Part 1
            r'\s*Section\s+\d+.*$',  # Section 1
            r'\s*-\s*[A-Z]\d+.*$',  # - G5.1
            r'\s*\d+\.\d+.*$',  # 1.1 onwards
        ]
        
        base_title = title
        for pattern in patterns_to_remove:
            base_title = re.sub(pattern, '', base_title, flags=re.IGNORECASE).strip()
        
        return base_title
    
    def _are_sections_related(self, section1: Dict, section2: Dict, 
                            base_title1: str, base_title2: str) -> bool:
        """Check if two sections should be combined"""
        
        # Same base document
        if base_title1 == base_title2:
            return True
        
        # Similar titles (e.g., different parts of structural guide)
        title_similarity = self._calculate_title_similarity(base_title1, base_title2)
        if title_similarity > 0.7:
            return True
        
        # Similar content patterns
        content1 = section1.get('content', '')
        content2 = section2.get('content', '')
        
        # Check for shared technical terms
        shared_terms = self._count_shared_technical_terms(content1, content2)
        if shared_terms >= 5:
            return True
        
        # Check similarity scores
        sim1 = section1.get('similarity_score', 0)
        sim2 = section2.get('similarity_score', 0)
        
        # Both sections have reasonable similarity to query
        if sim1 > self.min_related_similarity and sim2 > self.min_related_similarity:
            return True
        
        return False
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        
        words1 = set(re.findall(r'\w+', title1.lower()))
        words2 = set(re.findall(r'\w+', title2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _count_shared_technical_terms(self, content1: str, content2: str) -> int:
        """Count shared technical building terms between two content sections"""
        
        # Technical building terms that indicate related content
        technical_terms = [
            'beam', 'joist', 'rafter', 'stud', 'plate', 'lintel', 'purlin',
            'fixing', 'fastener', 'screw', 'nail', 'bolt', 'anchor',
            'load', 'span', 'support', 'bearing', 'deflection', 'stress',
            'timber', 'steel', 'concrete', 'lvl', 'glulam', 'metal',
            'installation', 'fixing', 'connection', 'joint', 'detail',
            'clearance', 'spacing', 'dimension', 'requirement', 'specification'
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        shared_count = 0
        for term in technical_terms:
            if term in content1_lower and term in content2_lower:
                shared_count += 1
        
        return shared_count
    
    async def _combine_related_sections(self, grouped_sections: List[Dict], 
                                      query: str) -> List[Dict[str, Any]]:
        """Combine sections within each group for comprehensive context"""
        
        combined_results = []
        
        for group in grouped_sections:
            sections = group['sections']
            
            if len(sections) == 1:
                # Single section - use as is
                combined_results.append(sections[0])
                continue
            
            # Combine multiple sections
            combined_content = self._merge_section_contents(sections, query)
            combined_title = self._create_combined_title(sections)
            
            # Calculate combined metadata
            total_similarity = sum(s.get('similarity_score', 0) for s in sections)
            avg_similarity = total_similarity / len(sections)
            
            combined_result = {
                'title': combined_title,
                'content': combined_content,
                'similarity_score': min(avg_similarity * 1.2, 1.0),  # Boost for combination
                'metadata': {
                    'combined_sections': len(sections),
                    'source_sections': [s.get('title', '') for s in sections],
                    'document_type': sections[0].get('metadata', {}).get('document_type', ''),
                    'processing_method': 'enhanced_section_combination'
                },
                'chunk_id': f"combined_{sections[0].get('chunk_id', 'unknown')}",
                'is_combined': True
            }
            
            combined_results.append(combined_result)
        
        return combined_results
    
    def _merge_section_contents(self, sections: List[Dict], query: str) -> str:
        """Intelligently merge content from multiple sections"""
        
        # Sort sections by relevance to query
        sections_sorted = sorted(sections, key=lambda s: s.get('similarity_score', 0), reverse=True)
        
        merged_content = f"=== COMPREHENSIVE INFORMATION ===\n\n"
        
        for i, section in enumerate(sections_sorted):
            content = section.get('content', '').strip()
            title = section.get('title', f'Section {i+1}')
            
            # Clean title for section header
            clean_title = re.sub(r'^.*?-\s*', '', title).strip()
            
            merged_content += f"### {clean_title}\n\n{content}\n\n"
            
            # Add separator between sections
            if i < len(sections_sorted) - 1:
                merged_content += "---\n\n"
        
        # Ensure reasonable length (not too long for context)
        if len(merged_content) > 8000:
            # Truncate while keeping most relevant sections
            truncated = merged_content[:7500]
            # Find last complete section
            last_separator = truncated.rfind("\n\n---\n\n")
            if last_separator > 3000:
                merged_content = truncated[:last_separator] + "\n\n[Additional sections available - ask for more specific details]"
        
        return merged_content
    
    def _create_combined_title(self, sections: List[Dict]) -> str:
        """Create a title for combined sections"""
        
        if not sections:
            return "Combined Building Information"
        
        # Extract base title
        first_title = sections[0].get('title', '')
        base_title = self._extract_base_title(first_title)
        
        if len(sections) == 2:
            return f"{base_title} - Combined Information"
        else:
            return f"{base_title} - Comprehensive Guide ({len(sections)} sections)"
    
    def _rank_combined_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Re-rank results based on combined relevance and quality"""
        
        query_lower = query.lower()
        
        for result in results:
            score = result.get('similarity_score', 0)
            
            # Boost for combined sections (more comprehensive)
            if result.get('is_combined', False):
                section_count = result.get('metadata', {}).get('combined_sections', 1)
                combination_boost = min(section_count * 0.05, 0.3)  # Up to 30% boost
                score += combination_boost
            
            # Boost for query term matches in content
            content = result.get('content', '').lower()
            query_words = re.findall(r'\w+', query_lower)
            
            matches = sum(1 for word in query_words if word in content)
            term_boost = min(matches * 0.02, 0.2)  # Up to 20% boost
            score += term_boost
            
            # Boost for technical completeness
            if any(term in content for term in ['specification', 'requirement', 'installation', 'compliance']):
                score += 0.1
            
            result['final_relevance_score'] = min(score, 1.0)
        
        # Sort by final relevance score
        results.sort(key=lambda r: r.get('final_relevance_score', 0), reverse=True)
        return results


# Global instance
enhanced_search_engine = None

def get_enhanced_search_engine(document_processor):
    global enhanced_search_engine
    if enhanced_search_engine is None:
        enhanced_search_engine = EnhancedSearchEngine(document_processor)
    return enhanced_search_engine