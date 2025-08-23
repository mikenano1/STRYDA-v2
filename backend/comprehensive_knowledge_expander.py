"""
STRYDA.ai Comprehensive Knowledge Expansion Engine
Systematically processes all NZ building documentation to create the ultimate building assistant
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
import json
from comprehensive_pdf_sources import (
    ALL_COMPREHENSIVE_SOURCES, 
    get_sources_by_priority, 
    get_sources_by_type,
    NZBC_COMPLETE_SOURCES,
    COUNCIL_REGULATION_SOURCES, 
    MANUFACTURER_SPEC_SOURCES,
    NZ_STANDARDS_SOURCES
)
from enhanced_pdf_processor import EnhancedPDFProcessor
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class ComprehensiveKnowledgeExpander:
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
        self.enhanced_pdf_processor = EnhancedPDFProcessor(document_processor)
        self.expansion_stats = {
            'total_sources': len(ALL_COMPREHENSIVE_SOURCES),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'documents_created': 0,
            'chunks_created': 0,
            'start_time': None,
            'current_phase': None
        }
        
        # Processing phases for systematic expansion
        self.phases = {
            'phase_1_critical': {
                'name': 'Critical Building Codes & Safety',
                'sources': get_sources_by_priority('critical'),
                'description': 'Essential NZBC fire safety, structural, and weathertightness requirements'
            },
            'phase_2_core_nzbc': {
                'name': 'Complete NZ Building Code',
                'sources': NZBC_COMPLETE_SOURCES,
                'description': 'All NZBC clauses A-H for comprehensive compliance coverage'
            },
            'phase_3_major_councils': {
                'name': 'Major Council Regulations',
                'sources': COUNCIL_REGULATION_SOURCES,
                'description': 'District plans and consent requirements from major NZ cities'
            },
            'phase_4_manufacturer_specs': {
                'name': 'Manufacturer Specifications',
                'sources': MANUFACTURER_SPEC_SOURCES,
                'description': 'Installation guides from major NZ building product manufacturers'
            },
            'phase_5_nz_standards': {
                'name': 'NZ Standards & AS/NZS',
                'sources': NZ_STANDARDS_SOURCES,
                'description': 'Official NZ construction standards and technical specifications'
            }
        }
    
    async def expand_knowledge_systematically(self, phases_to_run: List[str] = None):
        """Run systematic knowledge expansion across all phases"""
        
        if phases_to_run is None:
            phases_to_run = list(self.phases.keys())
        
        self.expansion_stats['start_time'] = datetime.utcnow()
        logger.info("🚀 Starting Comprehensive NZ Building Knowledge Expansion")
        logger.info(f"📊 Total phases: {len(phases_to_run)}")
        logger.info(f"📋 Total sources: {sum(len(self.phases[phase]['sources']) for phase in phases_to_run)}")
        
        phase_results = {}
        
        for phase_key in phases_to_run:
            if phase_key not in self.phases:
                logger.warning(f"Unknown phase: {phase_key}")
                continue
                
            phase = self.phases[phase_key]
            self.expansion_stats['current_phase'] = phase['name']
            
            logger.info(f"\n🎯 PHASE: {phase['name']}")
            logger.info(f"📖 {phase['description']}")
            logger.info(f"📄 Sources to process: {len(phase['sources'])}")
            
            phase_result = await self._process_phase(phase_key, phase)
            phase_results[phase_key] = phase_result
            
            # Log phase completion
            logger.info(f"✅ PHASE COMPLETE: {phase['name']}")
            logger.info(f"   📊 Success rate: {phase_result['success_rate']:.1f}%")
            logger.info(f"   📚 Documents created: {phase_result['documents_created']}")
            logger.info(f"   🧩 Chunks created: {phase_result['chunks_created']}")
            
        # Final expansion summary
        total_processing_time = (datetime.utcnow() - self.expansion_stats['start_time']).total_seconds()
        
        final_summary = {
            'expansion_complete': True,
            'total_processing_time_minutes': total_processing_time / 60,
            'phases_completed': len(phase_results),
            'total_documents_created': self.expansion_stats['documents_created'],
            'total_chunks_created': self.expansion_stats['chunks_created'],
            'overall_success_rate': (self.expansion_stats['successful'] / self.expansion_stats['processed'] * 100) if self.expansion_stats['processed'] > 0 else 0,
            'phase_results': phase_results,
            'completion_timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("🎉 COMPREHENSIVE KNOWLEDGE EXPANSION COMPLETE!")
        logger.info(f"⏱️  Total time: {final_summary['total_processing_time_minutes']:.1f} minutes")
        logger.info(f"📚 Total documents: {final_summary['total_documents_created']:,}")
        logger.info(f"🧩 Total chunks: {final_summary['total_chunks_created']:,}")
        logger.info(f"✅ Success rate: {final_summary['overall_success_rate']:.1f}%")
        
        return final_summary
    
    async def _process_phase(self, phase_key: str, phase: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single expansion phase"""
        
        phase_start_time = datetime.utcnow()
        phase_stats = {
            'phase_name': phase['name'],
            'sources_processed': 0,
            'successful': 0,
            'failed': 0,
            'documents_created': 0,
            'chunks_created': 0,
            'processing_errors': [],
            'successful_sources': []
        }
        
        # Process sources in batches to avoid overwhelming the system
        batch_size = 5  # Process 5 PDFs at a time
        sources = phase['sources']
        
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(sources) + batch_size - 1) // batch_size
            
            logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} sources)")
            
            try:
                # Process batch through enhanced PDF processor
                batch_result = await self.enhanced_pdf_processor.process_pdf_batch(batch)
                
                # Update phase statistics
                phase_stats['sources_processed'] += len(batch)
                phase_stats['successful'] += len(batch_result.get('processed', []))
                phase_stats['failed'] += len(batch_result.get('failed', []))
                phase_stats['documents_created'] += batch_result.get('total_documents', 0)
                phase_stats['chunks_created'] += batch_result.get('total_chunks', 0)
                
                # Track successful sources
                for success in batch_result.get('processed', []):
                    phase_stats['successful_sources'].append(success['title'])
                
                # Track failures
                for failure in batch_result.get('failed', []):
                    phase_stats['processing_errors'].append({
                        'title': failure['title'],
                        'error': failure['error']
                    })
                
                # Update overall stats
                self.expansion_stats['processed'] += len(batch)
                self.expansion_stats['successful'] += len(batch_result.get('processed', []))
                self.expansion_stats['failed'] += len(batch_result.get('failed', []))
                self.expansion_stats['documents_created'] += batch_result.get('total_documents', 0)
                self.expansion_stats['chunks_created'] += batch_result.get('total_chunks', 0)
                
                logger.info(f"   ✅ Batch {batch_num} complete: {len(batch_result.get('processed', []))}/{len(batch)} successful")
                
                # Brief pause between batches to avoid overwhelming the system
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Batch {batch_num} processing error: {e}")
                phase_stats['processing_errors'].append({
                    'batch': batch_num,
                    'error': str(e)
                })
                phase_stats['sources_processed'] += len(batch)
                phase_stats['failed'] += len(batch)
                self.expansion_stats['processed'] += len(batch)
                self.expansion_stats['failed'] += len(batch)
        
        # Calculate phase metrics
        phase_processing_time = (datetime.utcnow() - phase_start_time).total_seconds()
        phase_stats['processing_time_minutes'] = phase_processing_time / 60
        phase_stats['success_rate'] = (phase_stats['successful'] / phase_stats['sources_processed'] * 100) if phase_stats['sources_processed'] > 0 else 0
        
        return phase_stats
    
    async def run_critical_expansion_only(self):
        """Quick expansion focusing only on critical building safety documents"""
        logger.info("🔥 Running CRITICAL EXPANSION ONLY")
        logger.info("⚡ Focus: Fire safety, structural, weathertightness, electrical")
        
        return await self.expand_knowledge_systematically(['phase_1_critical'])
    
    async def run_nzbc_complete_expansion(self):
        """Expand with complete NZ Building Code coverage"""
        logger.info("📋 Running COMPLETE NZBC EXPANSION")
        logger.info("📖 Target: All NZBC clauses A-H")
        
        return await self.expand_knowledge_systematically(['phase_2_core_nzbc'])
    
    async def run_full_expansion(self):
        """Run complete knowledge expansion across all phases"""
        logger.info("🌟 Running FULL COMPREHENSIVE EXPANSION")
        logger.info("🎯 Target: Transform STRYDA into ultimate NZ building assistant")
        
        return await self.expand_knowledge_systematically()
    
    async def get_expansion_progress(self) -> Dict[str, Any]:
        """Get current expansion progress"""
        current_knowledge_stats = await self.document_processor.get_knowledge_stats()
        
        return {
            'current_knowledge_base': current_knowledge_stats,
            'expansion_stats': self.expansion_stats,
            'estimated_final_size': {
                'documents': current_knowledge_stats.get('total_documents', 0) + self.expansion_stats['total_sources'] * 3,  # Estimate 3 documents per source
                'chunks': current_knowledge_stats.get('total_chunks', 0) + self.expansion_stats['total_sources'] * 10  # Estimate 10 chunks per source
            },
            'phases_available': list(self.phases.keys()),
            'current_phase': self.expansion_stats.get('current_phase'),
            'completion_percentage': (self.expansion_stats['processed'] / self.expansion_stats['total_sources'] * 100) if self.expansion_stats['total_sources'] > 0 else 0
        }

async def main():
    """Demo the comprehensive knowledge expansion"""
    from document_processor import DocumentProcessor
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize components (simulated)
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    document_processor = DocumentProcessor(client, "stryda_ai")
    
    # Create knowledge expander
    expander = ComprehensiveKnowledgeExpander(document_processor)
    
    # Show expansion plan
    progress = await expander.get_expansion_progress()
    
    print("🚀 STRYDA.ai COMPREHENSIVE KNOWLEDGE EXPANSION READY")
    print("=" * 60)
    print(f"📊 Current Knowledge Base: {progress['current_knowledge_base'].get('total_documents', 0):,} documents")
    print(f"🎯 Target Expansion: {len(ALL_COMPREHENSIVE_SOURCES):,} new sources")
    print(f"📈 Estimated Final Size: {progress['estimated_final_size']['documents']:,} documents")
    print(f"🧩 Estimated Final Chunks: {progress['estimated_final_size']['chunks']:,} chunks")
    print("\n📋 Available Expansion Options:")
    
    for phase_key, phase in expander.phases.items():
        print(f"   • {phase['name']}: {len(phase['sources'])} sources")
        print(f"     {phase['description']}")
    
    print("\n🎯 Ready to transform STRYDA into the ultimate NZ building assistant!")

if __name__ == "__main__":
    asyncio.run(main())