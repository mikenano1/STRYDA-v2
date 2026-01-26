"""
STRYDA.ai Analytics Engine
Tracks user queries and generates dynamic quick questions based on search patterns
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
        self.db = document_processor.db
        self.collection = self.db.query_analytics
        
        # Question templates for generating dynamic questions
        self.question_templates = {
            'size_requirements': "What size {component} do I need for {context}?",
            'clearance_rules': "What are the {safety_type} clearance rules for {item}?", 
            'compliance_check': "Is {item} compliant with {standard}?",
            'installation_method': "What's the right way to install {product}?",
            'waterproofing': "How much {protection_type} is needed for {area}?",
            'consent_requirements': "Do I need a consent for {work_type}?",
            'difference_explanation': "What's the difference between {item1} and {item2}?",
            'process_guidance': "What are the rules for {process_type}?",
        }
        
        # Common NZ building terms for intelligent question generation
        self.building_terms = {
            'components': ['lintel', 'beam', 'post', 'foundation', 'slab', 'footing'],
            'safety_types': ['fire', 'structural', 'electrical', 'fall protection'],
            'items': ['fireplace', 'hot water cylinder', 'switchboard', 'deck', 'stairs'],
            'standards': ['NZS 3604', 'NZS 4230', 'AS/NZS 3000', 'NZBC G5', 'NZBC E2'],
            'products': ['vinyl cladding', 'metal roofing', 'insulation', 'plasterboard'],
            'protection_types': ['waterproofing', 'insulation', 'fire protection'],
            'areas': ['bathroom', 'kitchen', 'deck', 'basement', 'roof space'],
            'work_types': ['re-roof', 'deck extension', 'bathroom renovation', 'garage conversion'],
            'processes': ['getting a Code Compliance Certificate', 'building consent application', 'final inspection']
        }
    
    async def track_user_query(self, query: str, user_session: str = None, response_useful: bool = None):
        """Track user queries for analytics and learning purposes"""
        try:
            # Clean and normalize the query
            normalized_query = self._normalize_query(query)
            
            # Extract key terms and categories
            extracted_terms = self._extract_key_terms(normalized_query)
            
            # Store the query analytics
            query_record = {
                'original_query': query,
                'normalized_query': normalized_query,
                'extracted_terms': extracted_terms,
                'user_session': user_session,
                'timestamp': datetime.utcnow(),
                'response_useful': response_useful,
                'query_length': len(query.split()),
                'query_category': self._categorize_query(normalized_query)
            }
            
            await self.collection.insert_one(query_record)
            logger.info(f"Tracked user query: {normalized_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error tracking user query: {e}")
    
    async def generate_popular_questions(self, limit: int = 8) -> List[str]:
        """Generate dynamic quick questions based on user search patterns"""
        try:
            # Get recent queries (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_queries = await self.collection.find({
                'timestamp': {'$gte': thirty_days_ago}
            }).to_list(1000)
            
            if len(recent_queries) < 10:  # Not enough data, use fallback
                return self._get_fallback_questions()
            
            # Analyze query patterns
            popular_terms = self._analyze_query_patterns(recent_queries)
            
            # Generate questions based on patterns
            dynamic_questions = self._generate_questions_from_patterns(popular_terms)
            
            # Mix with high-performing fallback questions
            fallback_questions = self._get_fallback_questions()
            
            # Combine and prioritize
            combined_questions = dynamic_questions[:limit//2] + fallback_questions[:limit//2]
            
            return combined_questions[:limit]
            
        except Exception as e:
            logger.error(f"Error generating popular questions: {e}")
            return self._get_fallback_questions()
    
    def _normalize_query(self, query: str) -> str:
        """Clean and normalize query text"""
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove special characters but keep spaces and basic punctuation
        normalized = re.sub(r'[^\w\s\?\.\-]', ' ', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _extract_key_terms(self, query: str) -> Dict[str, List[str]]:
        """Extract key building-related terms from the query"""
        terms = {
            'components': [],
            'standards': [],
            'processes': [],
            'materials': []
        }
        
        # Look for NZ standards
        nz_standards = re.findall(r'nzs\s*\d+', query)
        terms['standards'].extend(nz_standards)
        
        # Look for building code clauses
        bc_clauses = re.findall(r'[a-z]\d+(?:\.\d+)*', query)
        terms['standards'].extend([f"NZBC {clause.upper()}" for clause in bc_clauses])
        
        # Look for common building components
        for category, term_list in self.building_terms.items():
            for term in term_list:
                if term.lower() in query:
                    terms[category].append(term)
        
        return terms
    
    def _categorize_query(self, query: str) -> str:
        """Categorize the query type"""
        if any(word in query for word in ['what size', 'how big', 'dimensions']):
            return 'sizing'
        elif any(word in query for word in ['clearance', 'distance', 'spacing']):
            return 'clearances'
        elif any(word in query for word in ['install', 'installation', 'how to']):
            return 'installation'
        elif any(word in query for word in ['compliant', 'compliance', 'meets standard']):
            return 'compliance'
        elif any(word in query for word in ['consent', 'permit', 'approval']):
            return 'consents'
        elif any(word in query for word in ['waterproof', 'seal', 'moisture']):
            return 'waterproofing'
        elif any(word in query for word in ['difference', 'vs', 'between']):
            return 'comparison'
        else:
            return 'general'
    
    def _analyze_query_patterns(self, queries: List[Dict]) -> Dict[str, int]:
        """Analyze patterns in user queries"""
        term_frequency = Counter()
        category_frequency = Counter()
        
        for query in queries:
            # Count extracted terms
            for category, terms in query.get('extracted_terms', {}).items():
                for term in terms:
                    term_frequency[term] += 1
            
            # Count query categories
            category = query.get('query_category', 'general')
            category_frequency[category] += 1
        
        return {
            'popular_terms': dict(term_frequency.most_common(20)),
            'popular_categories': dict(category_frequency.most_common(10))
        }
    
    def _generate_questions_from_patterns(self, patterns: Dict) -> List[str]:
        """Generate questions based on popular search patterns"""
        questions = []
        popular_terms = patterns.get('popular_terms', {})
        popular_categories = patterns.get('popular_categories', {})
        
        # Generate questions based on popular terms and categories
        for category, count in popular_categories.items():
            if category == 'sizing' and count > 2:
                # Find popular components
                components = [term for term in popular_terms if term in self.building_terms.get('components', [])]
                if components:
                    questions.append(f"What size {components[0]} do I need for residential construction?")
            
            elif category == 'clearances' and count > 2:
                # Find popular safety items
                safety_items = [term for term in popular_terms if term in self.building_terms.get('items', [])]
                if safety_items:
                    questions.append(f"What are the fire clearance rules for {safety_items[0]}?")
            
            elif category == 'compliance' and count > 2:
                # Find popular standards
                standards = [term for term in popular_terms if 'NZS' in term or 'NZBC' in term]
                if standards:
                    questions.append(f"How do I ensure compliance with {standards[0]}?")
        
        return questions[:4]  # Return top 4 dynamic questions
    
    def _get_fallback_questions(self) -> List[str]:
        """High-quality fallback questions based on research"""
        return [
            'What size lintel do I need for this window?',
            'What are the fire clearance rules for a fireplace?',
            'Do I need a consent for a re-roof?',
            'Is this timber compliant with NZS 3604?',
            'What\'s the right way to install vinyl cladding?',
            'How much waterproofing is needed for a bathroom?',
            'What\'s the difference between a CCC and a CoC?',
            'What are the rules for getting a Code Compliance Certificate?',
            'What are the insulation requirements for Auckland?',
            'How do I check for building code compliance?'
        ]
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        try:
            # Get recent query stats
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            total_queries = await self.collection.count_documents({
                'timestamp': {'$gte': thirty_days_ago}
            })
            
            # Get category breakdown
            pipeline = [
                {'$match': {'timestamp': {'$gte': thirty_days_ago}}},
                {'$group': {'_id': '$query_category', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            
            category_stats = await self.collection.aggregate(pipeline).to_list(20)
            
            return {
                'total_queries_30_days': total_queries,
                'category_breakdown': category_stats,
                'data_sufficient_for_learning': total_queries >= 50,
                'last_updated': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {
                'total_queries_30_days': 0,
                'category_breakdown': [],
                'data_sufficient_for_learning': False,
                'last_updated': datetime.utcnow()
            }