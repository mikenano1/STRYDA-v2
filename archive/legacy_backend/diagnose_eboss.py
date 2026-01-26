#!/usr/bin/env python3
"""
Diagnostic script to test EBOSS website connectivity and structure
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_eboss_connectivity():
    """Test basic connectivity to EBOSS website"""
    
    base_url = "https://www.eboss.co.nz"
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    ) as session:
        
        # Test 1: Check main website
        logger.info("🌐 Testing main EBOSS website...")
        try:
            async with session.get(base_url) as response:
                logger.info(f"Main site status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    logger.info(f"Main site content length: {len(html)} chars")
                else:
                    logger.error(f"Main site failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Main site error: {e}")
        
        # Test 2: Check brands page
        logger.info("📋 Testing brands page...")
        brands_url = f"{base_url}/library/brands"
        try:
            async with session.get(brands_url) as response:
                logger.info(f"Brands page status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find brand links
                    brand_links = soup.find_all('a', href=re.compile(r'/library/[^/]+$'))
                    logger.info(f"Found {len(brand_links)} brand links")
                    
                    # Show first few brands
                    for i, link in enumerate(brand_links[:5]):
                        brand_href = link.get('href', '')
                        brand_name = link.get_text(strip=True)
                        logger.info(f"  Brand {i+1}: {brand_name} -> {brand_href}")
                else:
                    logger.error(f"Brands page failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Brands page error: {e}")
        
        # Test 3: Check library pagination
        logger.info("📦 Testing library pagination...")
        library_url = f"{base_url}/library?start=0"
        try:
            async with session.get(library_url) as response:
                logger.info(f"Library page status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find product links
                    product_links = soup.find_all('a', href=re.compile(r'/library/[^/]+/[^/]+$'))
                    logger.info(f"Found {len(product_links)} product links on first page")
                    
                    # Show first few products
                    for i, link in enumerate(product_links[:3]):
                        product_href = link.get('href', '')
                        product_text = link.get_text(strip=True)
                        logger.info(f"  Product {i+1}: {product_text} -> {product_href}")
                else:
                    logger.error(f"Library page failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Library page error: {e}")
        
        # Test 4: Test specific brand page
        logger.info("🏢 Testing specific brand page...")
        brand_url = f"{base_url}/library/james-hardie"
        try:
            async with session.get(brand_url) as response:
                logger.info(f"James Hardie brand page status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find product links
                    product_links = soup.find_all('a', href=re.compile(r'/library/[^/]+/[^/]+$'))
                    logger.info(f"Found {len(product_links)} James Hardie products")
                    
                    if product_links:
                        # Test accessing a specific product
                        test_product = product_links[0]
                        product_href = test_product.get('href', '')
                        product_name = test_product.get_text(strip=True)
                        
                        logger.info(f"🔍 Testing product: {product_name}")
                        product_url = f"{base_url}{product_href}"
                        
                        async with session.get(product_url) as prod_response:
                            logger.info(f"Product page status: {prod_response.status}")
                            if prod_response.status == 200:
                                prod_html = await prod_response.text()
                                prod_soup = BeautifulSoup(prod_html, 'html.parser')
                                
                                # Get product title
                                title_elem = prod_soup.find('h1')
                                title = title_elem.get_text(strip=True) if title_elem else "No title found"
                                logger.info(f"Product title: {title}")
                                
                                # Check for content
                                content_length = len(prod_html)
                                logger.info(f"Product content length: {content_length} chars")
                            else:
                                logger.error(f"Product page failed: HTTP {prod_response.status}")
                else:
                    logger.error(f"James Hardie brand page failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Brand page error: {e}")

if __name__ == "__main__":
    asyncio.run(test_eboss_connectivity())