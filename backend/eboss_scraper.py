"""
STRYDA.ai EBOSS Product Database Scraper
Comprehensive scraper for eboss.co.nz to collect all 5,374+ NZ building products
with intelligent categorization and Building Code mapping
"""

import asyncio
import aiohttp
import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger(__name__)

class EBOSSProductScraper:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.base_url = "https://www.eboss.co.nz"
        self.session = None
        self.scraped_products = []
        self.scraped_brands = []
        
        # Product categorization mapping to Building Code
        self.category_mappings = {
            # External Building Envelope
            "wall-cladding": {
                "building_codes": ["E2", "B2", "F2"],
                "keywords": ["cladding", "exterior", "wall", "facade", "weatherboard"],
                "applications": ["weathertightness", "durability", "fire_safety"]
            },
            "roofing-and-decking": {
                "building_codes": ["E2", "B1", "B2", "F2"],
                "keywords": ["roof", "roofing", "tile", "metal", "membrane", "decking"],
                "applications": ["structural", "weathertightness", "durability", "fire_safety"]
            },
            "windows-and-doors": {
                "building_codes": ["H1", "E2", "F2", "G5"],
                "keywords": ["window", "door", "glazing", "frame", "sash"],
                "applications": ["thermal", "weathertightness", "fire_safety", "ventilation"]
            },
            "glazing": {
                "building_codes": ["H1", "F2"],
                "keywords": ["glass", "glazing", "double", "thermal", "safety"],
                "applications": ["thermal_performance", "fire_safety"]
            },
            
            # Internal Systems
            "wall-and-ceiling-linings": {
                "building_codes": ["F2", "G5"],
                "keywords": ["plasterboard", "lining", "ceiling", "gib", "interior"],
                "applications": ["fire_safety", "ventilation", "interior_environment"]
            },
            "floors": {
                "building_codes": ["B1", "B2", "F2"],
                "keywords": ["flooring", "timber", "concrete", "carpet", "vinyl"],
                "applications": ["structural", "durability", "fire_safety"]
            },
            "insulation": {
                "building_codes": ["H1"],
                "keywords": ["insulation", "thermal", "r-value", "bulk", "reflective"],
                "applications": ["energy_efficiency", "thermal_performance"]
            },
            
            # Structural & Hardware
            "structural": {
                "building_codes": ["B1"],
                "keywords": ["structural", "beam", "steel", "timber", "connection"],
                "applications": ["structural_integrity", "seismic"]
            },
            "hardware": {
                "building_codes": ["B1", "F2", "G5"],
                "keywords": ["hardware", "fastener", "fixing", "bracket", "hinge"],
                "applications": ["structural", "fire_safety", "accessibility"]
            },
            
            # Services & Specialties
            "plumbing": {
                "building_codes": ["G1", "G2", "G12", "G13"],
                "keywords": ["plumbing", "pipe", "fitting", "water", "drainage"],
                "applications": ["water_supply", "sanitary", "drainage"]
            },
            "electrical": {
                "building_codes": ["G9"],
                "keywords": ["electrical", "cable", "fitting", "switch", "lighting"],
                "applications": ["electrical_supply", "lighting"]
            },
            "hvac": {
                "building_codes": ["G4", "G5"],
                "keywords": ["heating", "ventilation", "air", "hvac", "climate"],
                "applications": ["ventilation", "interior_environment"]
            },
            "fire_safety": {
                "building_codes": ["C1", "C2", "C3", "C4", "F2"],
                "keywords": ["fire", "smoke", "alarm", "sprinkler", "exit"],
                "applications": ["fire_safety", "means_of_escape"]
            }
        }
        
        # Common NZ building product terms for enhanced categorization
        self.nz_building_terms = {
            "materials": [
                "timber", "steel", "concrete", "aluminium", "fibre cement", 
                "weatherboard", "brick", "stone", "composite", "vinyl"
            ],
            "applications": [
                "residential", "commercial", "industrial", "coastal", "alpine",
                "high wind", "seismic", "bushfire", "cyclone", "earthquake"
            ],
            "compliance": [
                "codecompliant", "branz", "appraisal", "acceptable solution",
                "verification method", "alternative solution", "nzs", "building code"
            ],
            "performance": [
                "weathertight", "thermal", "acoustic", "structural", "fire rated",
                "wind load", "seismic", "durability", "maintenance free"
            ]
        }
        
        # Major NZ suppliers for prioritization
        self.priority_brands = [
            "james-hardie", "dimond-roofing", "vantage-windows-and-doors",
            "metro-performance-glass", "altherm-window-systems", "gib",
            "roofing-industries", "metalcraft", "colorsteel", "resene",
            "bradford-insulation", "kingspan-insulated-panels", "knauf-insulation",
            "first-windows-and-doors", "juralco", "monier", "gerard-roofs"
        ]
    
    async def scrape_all_products(self) -> Dict[str, Any]:
        """Main method to scrape all EBOSS products with comprehensive categorization"""
        
        logger.info("🚀 Starting comprehensive EBOSS product scraping...")
        
        start_time = datetime.now()
        scraping_stats = {
            "started_at": start_time.isoformat(),
            "total_products": 0,
            "total_brands": 0,
            "products_by_category": {},
            "products_by_brand": {},
            "building_code_mappings": {},
            "processing_errors": [],
            "scraping_duration": 0
        }
        
        try:
            # Initialize session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            
            # Step 1: Scrape all brands first
            logger.info("📋 Phase 1: Scraping all brand information...")
            await self._scrape_all_brands(scraping_stats)
            
            # Step 2: Scrape products by priority (major brands first)
            logger.info("🏗️ Phase 2: Scraping products by priority brands...")
            await self._scrape_priority_brand_products(scraping_stats)
            
            # Step 3: Scrape remaining products via pagination
            logger.info("📦 Phase 3: Scraping remaining products via library pagination...")
            await self._scrape_library_products(scraping_stats)
            
            # Step 4: Process and categorize all products
            logger.info("🏷️ Phase 4: Processing and categorizing all products...")
            await self._process_all_products(scraping_stats)
            
            # Calculate final stats
            end_time = datetime.now()
            scraping_stats["completed_at"] = end_time.isoformat()
            scraping_stats["scraping_duration"] = int((end_time - start_time).total_seconds())
            
            logger.info(f"✅ EBOSS scraping completed! {scraping_stats['total_products']} products from {scraping_stats['total_brands']} brands")
            
            return scraping_stats
            
        except Exception as e:
            logger.error(f"❌ Error in EBOSS scraping: {e}")
            scraping_stats["processing_errors"].append(f"Fatal error: {str(e)}")
            raise e
        finally:
            if self.session:
                await self.session.close()
    
    async def _scrape_all_brands(self, stats: Dict[str, Any]):
        """Scrape all brand information from the brands A-Z page"""
        
        brands_url = f"{self.base_url}/library/brands"
        
        try:
            async with self.session.get(brands_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all brand links
                    brand_links = soup.find_all('a', href=re.compile(r'/library/[^/]+$'))
                    
                    for link in brand_links:
                        try:
                            brand_href = link.get('href', '')
                            if brand_href and '/library/' in brand_href:
                                brand_slug = brand_href.split('/library/')[-1]
                                brand_name = link.get_text(strip=True)
                                
                                if brand_name and brand_slug not in ['brands', 'category']:
                                    brand_info = {
                                        "slug": brand_slug,
                                        "name": brand_name,
                                        "url": urljoin(self.base_url, brand_href),
                                        "products": [],
                                        "is_priority": brand_slug in self.priority_brands
                                    }
                                    self.scraped_brands.append(brand_info)
                        
                        except Exception as e:
                            stats["processing_errors"].append(f"Error processing brand {link}: {str(e)}")
                    
                    stats["total_brands"] = len(self.scraped_brands)
                    logger.info(f"📋 Found {stats['total_brands']} brands")
                    
        except Exception as e:
            logger.error(f"Error scraping brands: {e}")
            stats["processing_errors"].append(f"Brand scraping error: {str(e)}")
    
    async def _scrape_priority_brand_products(self, stats: Dict[str, Any]):
        """Scrape products from priority brands first"""
        
        priority_brands = [brand for brand in self.scraped_brands if brand["is_priority"]]
        
        logger.info(f"🎯 Scraping {len(priority_brands)} priority brands...")
        
        for brand in priority_brands[:10]:  # Limit to top 10 priority brands for now
            try:
                await self._scrape_brand_products(brand, stats)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error scraping priority brand {brand['name']}: {e}")
                stats["processing_errors"].append(f"Priority brand error {brand['name']}: {str(e)}")
    
    async def _scrape_brand_products(self, brand: Dict[str, Any], stats: Dict[str, Any]):
        """Scrape all products for a specific brand"""
        
        try:
            async with self.session.get(brand["url"]) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find product links
                    product_links = soup.find_all('a', href=re.compile(r'/library/[^/]+/[^/]+$'))
                    
                    for link in product_links:
                        product_href = link.get('href', '')
                        if product_href:
                            product_data = await self._scrape_single_product(product_href, brand)
                            if product_data:
                                brand["products"].append(product_data)
                                self.scraped_products.append(product_data)
                    
                    logger.info(f"📦 {brand['name']}: {len(brand['products'])} products")
                    
        except Exception as e:
            logger.error(f"Error scraping brand {brand['name']}: {e}")
    
    async def _scrape_library_products(self, stats: Dict[str, Any]):
        """Scrape products via main library pagination (for comprehensive coverage)"""
        
        page = 0
        max_pages = 20  # Limit for initial implementation
        products_per_page = 48
        
        while page < max_pages:
            try:
                start_param = page * products_per_page
                library_url = f"{self.base_url}/library?start={start_param}"
                
                async with self.session.get(library_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find product links that we haven't already scraped
                        product_links = soup.find_all('a', href=re.compile(r'/library/[^/]+/[^/]+$'))
                        
                        new_products = 0
                        for link in product_links:
                            product_href = link.get('href', '')
                            if product_href and not any(p.get('url', '').endswith(product_href) for p in self.scraped_products):
                                product_data = await self._scrape_single_product(product_href)
                                if product_data:
                                    self.scraped_products.append(product_data)
                                    new_products += 1
                        
                        logger.info(f"📄 Page {page + 1}: {new_products} new products")
                        
                        # If no products found, we've reached the end
                        if not product_links:
                            break
                        
                        page += 1
                        await asyncio.sleep(0.5)  # Rate limiting
                        
                    else:
                        logger.warning(f"Failed to load page {page + 1}: HTTP {response.status}")
                        break
                        
            except Exception as e:
                logger.error(f"Error scraping library page {page + 1}: {e}")
                stats["processing_errors"].append(f"Library page {page + 1} error: {str(e)}")
                break
        
        stats["total_products"] = len(self.scraped_products)
    
    async def _scrape_single_product(self, product_href: str, brand_info: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Scrape detailed information for a single product"""
        
        try:
            product_url = urljoin(self.base_url, product_href)
            
            async with self.session.get(product_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract basic product information
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Product"
                    
                    # Extract description/content
                    description_elems = soup.find_all(['p', 'div'], class_=re.compile(r'description|content|summary'))
                    description = ' '.join([elem.get_text(strip=True) for elem in description_elems[:3]])
                    
                    # Extract specifications if available
                    spec_text = ""
                    spec_sections = soup.find_all(['div', 'section'], class_=re.compile(r'spec|technical|detail'))
                    for section in spec_sections[:2]:
                        spec_text += section.get_text(strip=True) + " "
                    
                    # Determine brand from URL if not provided
                    if not brand_info:
                        url_parts = product_href.split('/')
                        brand_slug = url_parts[2] if len(url_parts) > 2 else "unknown"
                        brand_name = brand_slug.replace('-', ' ').title()
                    else:
                        brand_slug = brand_info["slug"]
                        brand_name = brand_info["name"]
                    
                    # Auto-categorize the product
                    categories = self._categorize_product(title, description, spec_text)
                    
                    product_data = {
                        "title": title,
                        "description": description,
                        "specifications": spec_text,
                        "url": product_url,
                        "brand_slug": brand_slug,
                        "brand_name": brand_name,
                        "categories": categories,
                        "building_codes": self._extract_building_codes(title, description, spec_text),
                        "applications": self._extract_applications(title, description, spec_text),
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    return product_data
                    
        except Exception as e:
            logger.error(f"Error scraping product {product_href}: {e}")
            return None
    
    def _categorize_product(self, title: str, description: str, specs: str) -> List[str]:
        """Automatically categorize product based on content analysis"""
        
        content = f"{title} {description} {specs}".lower()
        categories = []
        
        for category, mapping in self.category_mappings.items():
            # Check if any category keywords are present
            if any(keyword in content for keyword in mapping["keywords"]):
                categories.append(category)
        
        # If no specific category found, try to infer from common terms
        if not categories:
            if any(term in content for term in ["wall", "cladding", "exterior"]):
                categories.append("wall-cladding")
            elif any(term in content for term in ["roof", "roofing", "tile"]):
                categories.append("roofing-and-decking")
            elif any(term in content for term in ["window", "door", "glazing"]):
                categories.append("windows-and-doors")
            elif any(term in content for term in ["insulation", "thermal", "r-value"]):
                categories.append("insulation")
            else:
                categories.append("general")
        
        return categories
    
    def _extract_building_codes(self, title: str, description: str, specs: str) -> List[str]:
        """Extract relevant Building Code clauses from product information"""
        
        content = f"{title} {description} {specs}".lower()
        building_codes = set()
        
        # Direct code references
        code_patterns = [
            r'\b([a-z]\d+(?:\.\d+)*)\b',  # E2, H1.2, etc.
            r'\bnzbc\s+([a-z]\d+)\b',     # NZBC E2
            r'clause\s+([a-z]\d+)\b'      # Clause E2
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, content)
            building_codes.update(matches)
        
        # Inferred codes from categories
        categories = self._categorize_product(title, description, specs)
        for category in categories:
            if category in self.category_mappings:
                building_codes.update(self.category_mappings[category]["building_codes"])
        
        return list(building_codes)
    
    def _extract_applications(self, title: str, description: str, specs: str) -> List[str]:
        """Extract building applications and use cases"""
        
        content = f"{title} {description} {specs}".lower()
        applications = []
        
        # Check for specific application terms
        for app_category, terms in self.nz_building_terms.items():
            found_terms = [term for term in terms if term in content]
            applications.extend(found_terms)
        
        return applications
    
    async def _process_all_products(self, stats: Dict[str, Any]):
        """Process and store all scraped products in the knowledge base"""
        
        logger.info(f"🏷️ Processing {len(self.scraped_products)} products...")
        
        # Group products by category and brand
        for product in self.scraped_products:
            # Update category stats
            for category in product.get("categories", []):
                if category not in stats["products_by_category"]:
                    stats["products_by_category"][category] = 0
                stats["products_by_category"][category] += 1
            
            # Update brand stats
            brand = product.get("brand_slug", "unknown")
            if brand not in stats["products_by_brand"]:
                stats["products_by_brand"][brand] = 0
            stats["products_by_brand"][brand] += 1
            
            # Update building code stats
            for code in product.get("building_codes", []):
                if code not in stats["building_code_mappings"]:
                    stats["building_code_mappings"][code] = 0
                stats["building_code_mappings"][code] += 1
        
        # Store products in knowledge base (process in batches)
        batch_size = 10
        processed_count = 0
        
        for i in range(0, len(self.scraped_products), batch_size):
            batch = self.scraped_products[i:i + batch_size]
            
            for product in batch:
                try:
                    await self._store_product_in_knowledge_base(product)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error storing product {product.get('title', 'Unknown')}: {e}")
                    stats["processing_errors"].append(f"Storage error: {str(e)}")
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Processed and stored {processed_count} products")
    
    async def _store_product_in_knowledge_base(self, product: Dict[str, Any]):
        """Store individual product in the knowledge base with proper categorization"""
        
        # Create comprehensive content for the knowledge base
        content_parts = []
        
        # Product header
        content_parts.append(f"PRODUCT: {product['title']}")
        content_parts.append(f"BRAND: {product['brand_name']}")
        
        # Categories and Building Code compliance
        if product.get("categories"):
            content_parts.append(f"CATEGORIES: {', '.join(product['categories'])}")
        
        if product.get("building_codes"):
            content_parts.append(f"BUILDING CODES: {', '.join(product['building_codes'])}")
        
        # Main content
        if product.get("description"):
            content_parts.append(f"DESCRIPTION:\n{product['description']}")
        
        if product.get("specifications"):
            content_parts.append(f"SPECIFICATIONS:\n{product['specifications']}")
        
        # Applications
        if product.get("applications"):
            content_parts.append(f"APPLICATIONS: {', '.join(product['applications'])}")
        
        # Source
        content_parts.append(f"SOURCE: EBOSS Product Library - {product['url']}")
        
        content_text = '\n\n'.join(content_parts)
        
        # Create metadata
        metadata = {
            "document_type": "eboss_product",
            "product_source": "eboss",
            "brand_slug": product.get("brand_slug"),
            "brand_name": product.get("brand_name"),
            "categories": product.get("categories", []),
            "building_codes": product.get("building_codes", []),
            "applications": product.get("applications", []),
            "tags": ["product", "eboss", "nz_building"] + product.get("categories", [])
        }
        
        # Process and store in knowledge base
        doc_title = f"EBOSS Product: {product['title']} - {product['brand_name']}"
        
        await self.document_processor.process_and_store_document(
            title=doc_title,
            content=content_text,
            source_url=product['url'],
            document_type="eboss_product",
            metadata=metadata
        )

# Usage functions for the main application
async def scrape_eboss_products(document_processor) -> Dict[str, Any]:
    """Main function to scrape all EBOSS products"""
    
    scraper = EBOSSProductScraper(document_processor)
    return await scraper.scrape_all_products()

async def get_eboss_scraping_stats() -> Dict[str, Any]:
    """Get current EBOSS scraping statistics"""
    
    # This would query the database for EBOSS product statistics
    # For now, return a placeholder
    return {
        "last_scrape": "Not yet scraped",
        "total_products": 0,
        "total_brands": 0,
        "status": "ready_to_scrape"
    }