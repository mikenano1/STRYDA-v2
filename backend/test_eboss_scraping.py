#!/usr/bin/env python3
"""
Test script for EBOSS Product Database Scraping
Demonstrates the comprehensive product intelligence system for STRYDA.ai
"""

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

async def test_eboss_scraping():
    """Test the EBOSS product scraping system"""
    
    api_base = "http://localhost:8001/api"
    
    logger.info("🚀 Testing EBOSS Product Database Scraping System...")
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Check current EBOSS status
        logger.info("📊 Step 1: Checking current EBOSS product status...")
        try:
            async with session.get(f"{api_base}/products/eboss-status") as response:
                if response.status == 200:
                    status = await response.json()
                    logger.info(f"✅ Current EBOSS products: {status['total_products']}")
                    logger.info(f"📦 Total chunks: {status['total_chunks']}")
                    
                    if status['products_by_brand']:
                        logger.info("🏢 Top brands:")
                        for brand in status['products_by_brand'][:5]:
                            logger.info(f"   • {brand['_id']}: {brand['count']} products")
                else:
                    logger.warning(f"Failed to get EBOSS status: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error checking EBOSS status: {e}")
        
        # Step 2: Start EBOSS scraping (limited for testing)
        logger.info("🏗️ Step 2: Starting EBOSS product scraping...")
        scraping_payload = {
            "max_products": 100,  # Limited for testing
            "priority_brands_only": True
        }
        
        try:
            async with session.post(f"{api_base}/products/scrape-eboss", json=scraping_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ EBOSS scraping initiated!")
                    logger.info(f"📝 Message: {result['message']}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ EBOSS scraping failed: HTTP {response.status}")
                    logger.error(f"Error: {error_text}")
        except Exception as e:
            logger.error(f"Error starting EBOSS scraping: {e}")
        
        # Step 3: Wait and monitor progress
        logger.info("⏳ Step 3: Monitoring scraping progress...")
        await asyncio.sleep(10)  # Wait for scraping to start
        
        for i in range(6):  # Check 6 times over 1 minute
            try:
                async with session.get(f"{api_base}/products/eboss-status") as response:
                    if response.status == 200:
                        status = await response.json()
                        logger.info(f"📈 Progress check {i+1}: {status['total_products']} products, {status['total_chunks']} chunks")
                        
                        if status['total_products'] > 10:  # Some progress made
                            logger.info("🎉 Products are being scraped!")
                            break
            except Exception as e:
                logger.error(f"Error monitoring progress: {e}")
            
            await asyncio.sleep(10)
        
        # Step 4: Test product search functionality
        logger.info("🔍 Step 4: Testing product search functionality...")
        
        search_queries = [
            ("James Hardie cladding", None, "james-hardie", None),
            ("insulation", "insulation", None, "H1"),
            ("roofing", "roofing-and-decking", None, "E2"),
            ("windows", "windows-and-doors", None, "H1")
        ]
        
        for query, category, brand, building_code in search_queries:
            try:
                params = {"query": query, "limit": 5}
                if category:
                    params["category"] = category
                if brand:
                    params["brand"] = brand
                if building_code:
                    params["building_code"] = building_code
                
                async with session.get(f"{api_base}/products/search", params=params) as response:
                    if response.status == 200:
                        results = await response.json()
                        logger.info(f"🔍 Search '{query}': {results['total_found']} results")
                        
                        if results['results']:
                            logger.info(f"   📦 Sample: {results['results'][0].get('title', 'No title')}")
                    else:
                        logger.warning(f"Search failed for '{query}': HTTP {response.status}")
            
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
            
            await asyncio.sleep(1)
        
        # Step 5: Test enhanced chat with product knowledge
        logger.info("🧠 Step 5: Testing enhanced chat with product knowledge...")
        
        chat_queries = [
            "What James Hardie cladding products are suitable for coastal areas?",
            "Show me insulation products that meet H1 energy requirements",
            "What roofing options are available from Dimond Roofing?",
            "Which window systems offer the best thermal performance?"
        ]
        
        for chat_query in chat_queries:
            try:
                chat_payload = {
                    "message": chat_query,
                    "session_id": "test_eboss_session",
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True
                }
                
                async with session.post(f"{api_base}/chat/enhanced", json=chat_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"🧠 Query: {chat_query}")
                        logger.info(f"   📝 Response length: {len(result['response'])} chars")
                        logger.info(f"   📚 Sources: {result['sources_used']}")
                        logger.info(f"   🔗 Citations: {len(result['citations'])}")
                        
                        # Show preview of response
                        preview = result['response'][:150] + "..." if len(result['response']) > 150 else result['response']
                        logger.info(f"   📖 Preview: {preview}")
                        
                    else:
                        logger.warning(f"Chat failed: HTTP {response.status}")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in chat test: {e}")

async def test_knowledge_base_stats():
    """Test the overall knowledge base statistics"""
    
    api_base = "http://localhost:8001/api"
    
    logger.info("📊 Testing Knowledge Base Statistics...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{api_base}/knowledge/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    
                    logger.info("📈 Knowledge Base Overview:")
                    logger.info(f"   📚 Total Documents: {stats['total_documents']}")
                    logger.info(f"   📦 Total Chunks: {stats['total_chunks']}")
                    
                    logger.info("📋 Document Types:")
                    for doc_type, count in stats['documents_by_type'].items():
                        logger.info(f"   • {doc_type}: {count} documents")
                    
                    logger.info("🏷️ Categories Distribution:")
                    for category, count in list(stats['chunks_by_category'].items())[:10]:
                        logger.info(f"   • {category}: {count} chunks")
                else:
                    logger.error(f"Failed to get knowledge base stats: HTTP {response.status}")
        
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")

if __name__ == "__main__":
    async def main():
        logger.info("🎯 STRYDA.ai EBOSS Product Intelligence Testing Starting...")
        
        # Test 1: EBOSS Product Scraping
        await test_eboss_scraping()
        
        # Test 2: Knowledge Base Statistics
        await test_knowledge_base_stats()
        
        logger.info("🏆 EBOSS Product Intelligence Testing Complete!")
    
    asyncio.run(main())