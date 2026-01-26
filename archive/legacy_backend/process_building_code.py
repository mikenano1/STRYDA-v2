#!/usr/bin/env python3
"""
Script to process the NZ Building Code PDF and integrate it into STRYDA.ai
"""

import os
import asyncio
import aiohttp
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_building_code_pdf():
    """Process the Building Code PDF via the FastAPI endpoint"""
    
    # Building Code PDF URL from the uploaded asset
    pdf_url = "https://customer-assets.emergentagent.com/job_tradecode-nz/artifacts/gmjcq49m_building-code.pdf"
    api_url = "http://localhost:8001/api/knowledge/process-pdf"
    
    payload = {
        "pdf_url": pdf_url,
        "title": "New Zealand Building Code Handbook 2024",
        "document_type": "nzbc"
    }
    
    logger.info("🚀 Starting NZ Building Code PDF processing...")
    logger.info(f"PDF URL: {pdf_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ PDF processing request successful!")
                    logger.info(f"Response: {result}")
                    
                    # Monitor processing status
                    await monitor_processing_status(session)
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ PDF processing request failed: HTTP {response.status}")
                    logger.error(f"Error: {error_text}")
                    
    except Exception as e:
        logger.error(f"❌ Error processing Building Code PDF: {e}")

async def monitor_processing_status(session):
    """Monitor the PDF processing status"""
    
    status_url = "http://localhost:8001/api/knowledge/pdf-status"
    stats_url = "http://localhost:8001/api/knowledge/stats"
    
    logger.info("📊 Monitoring processing status...")
    
    # Wait a bit for processing to start
    await asyncio.sleep(5)
    
    for i in range(12):  # Check for up to 2 minutes
        try:
            # Get PDF processing status
            async with session.get(status_url) as response:
                if response.status == 200:
                    status = await response.json()
                    logger.info(f"PDF Status - Documents: {status['total_pdf_documents']}, Chunks: {status['total_pdf_chunks']}")
            
            # Get overall knowledge base stats
            async with session.get(stats_url) as response:
                if response.status == 200:
                    stats = await response.json()
                    logger.info(f"Knowledge Base - Total Documents: {stats['total_documents']}, Total Chunks: {stats['total_chunks']}")
                    
                    # Check if we have significantly more documents (indicating processing success)
                    if stats['total_documents'] > 20:  # We started with ~7, so 20+ indicates PDF processing
                        logger.info("🎉 Building Code processing appears to be complete!")
                        break
            
            await asyncio.sleep(10)  # Wait 10 seconds before next check
            
        except Exception as e:
            logger.error(f"Error monitoring status: {e}")
            await asyncio.sleep(10)
    
    logger.info("📋 Final status check complete")

async def test_enhanced_chat():
    """Test the enhanced chat with Building Code knowledge"""
    
    chat_url = "http://localhost:8001/api/chat/enhanced"
    
    test_queries = [
        "What are the minimum clearances for a fireplace hearth in New Zealand?",
        "What insulation R-values are required for Zone 2 climate areas?",
        "What are the structural requirements for timber framing in NZS 3604?",
        "What weathertightness requirements apply to external cladding systems?"
    ]
    
    logger.info("🧪 Testing enhanced chat with Building Code knowledge...")
    
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(test_queries, 1):
            try:
                payload = {
                    "message": query,
                    "session_id": f"test_session_{i}",
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True
                }
                
                logger.info(f"\n📝 Test {i}: {query}")
                
                async with session.post(chat_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Response length: {len(result['response'])} characters")
                        logger.info(f"📚 Citations: {len(result['citations'])}")
                        logger.info(f"🔍 Sources: {result['sources_used']}")
                        logger.info(f"⚡ Processing time: {result['processing_time_ms']:.1f}ms")
                        logger.info(f"📊 Confidence: {result['confidence_score']:.2f}")
                        
                        # Show first 200 characters of response
                        preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                        logger.info(f"Preview: {preview}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Chat test failed: HTTP {response.status} - {error_text}")
                
                await asyncio.sleep(2)  # Brief pause between tests
                
            except Exception as e:
                logger.error(f"Error in chat test {i}: {e}")

if __name__ == "__main__":
    async def main():
        logger.info("🏗️ STRYDA.ai Building Code Integration Starting...")
        
        # Step 1: Process the PDF
        await process_building_code_pdf()
        
        # Step 2: Wait for processing to complete
        logger.info("⏳ Waiting for PDF processing to complete...")
        await asyncio.sleep(30)  # Give it time to process
        
        # Step 3: Test the enhanced chat
        await test_enhanced_chat()
        
        logger.info("🎯 Building Code integration complete!")
    
    asyncio.run(main())