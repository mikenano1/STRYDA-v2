"""
STRYDA.ai Web Scraper for NZ Building Documents
Scrapes and processes official NZ building code documents and manufacturer manuals
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class NZBuildingDocumentScraper:
    def __init__(self):
        self.session = None
        
        # Priority NZ Building Authority URLs
        self.official_sources = {
            "mbie_building": "https://www.building.govt.nz/building-code-compliance/",
            "mbie_assets": "https://www.building.govt.nz/assets/Uploads/building-code/",
            "standards_nz": "https://www.standards.govt.nz/",
            "branz": "https://www.branz.co.nz/",
            "lbp_portal": "https://www.lbp.govt.nz/"
        }
        
        # Common manufacturer websites for building products
        self.manufacturer_sources = {
            "metrofires": "https://www.metrofires.co.nz/",
            "gib": "https://www.gib.co.nz/",
            "james_hardie": "https://www.jameshardie.co.nz/",
            "resene": "https://www.resene.co.nz/",
            "mitre10": "https://www.mitre10.co.nz/",
            "bunnings": "https://www.bunnings.co.nz/"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'STRYDA.ai Document Scraper - Building Code Research'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_mbie_building_code(self) -> List[Dict[str, Any]]:
        """Scrape MBIE Building Code compliance documents"""
        documents = []
        
        try:
            # Scrape main building code compliance page
            async with self.session.get(self.official_sources["mbie_building"]) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find building code clause links
                    clause_links = soup.find_all('a', href=re.compile(r'/building-code-compliance/[a-z]-'))
                    
                    for link in clause_links[:10]:  # Limit to first 10 for testing
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.official_sources["mbie_building"], href)
                            clause_title = link.get_text(strip=True)
                            
                            # Scrape individual clause page
                            clause_doc = await self._scrape_clause_page(full_url, clause_title)
                            if clause_doc:
                                documents.append(clause_doc)
                            
                            # Rate limiting
                            await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error scraping MBIE building code: {e}")
        
        return documents
    
    async def _scrape_clause_page(self, url: str, title: str) -> Optional[Dict[str, Any]]:
        """Scrape individual building code clause page"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract main content
                    content_div = soup.find('div', class_='content') or soup.find('main') or soup.find('article')
                    
                    if content_div:
                        # Clean up the content
                        content_text = self._clean_html_content(content_div)
                        
                        # Extract clause information from title/URL
                        clause_match = re.search(r'([A-Z]\d+)', title.upper())
                        clause_code = clause_match.group(1) if clause_match else "Unknown"
                        
                        return {
                            "title": title,
                            "content": content_text,
                            "source_url": url,
                            "document_type": "nzbc",
                            "metadata": {
                                "clause": clause_code,
                                "section": title,
                                "scraped_at": datetime.now().isoformat(),
                                "source": "MBIE",
                                "tags": self._extract_tags_from_content(content_text)
                            }
                        }
        
        except Exception as e:
            logger.error(f"Error scraping clause page {url}: {e}")
        
        return None
    
    async def scrape_manufacturer_manuals(self, manufacturer: str = "metrofires") -> List[Dict[str, Any]]:
        """Scrape manufacturer installation manuals and product info"""
        documents = []
        
        if manufacturer not in self.manufacturer_sources:
            logger.warning(f"Unknown manufacturer: {manufacturer}")
            return documents
        
        try:
            base_url = self.manufacturer_sources[manufacturer]
            
            # Scrape main manufacturer page
            async with self.session.get(base_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for installation guides, manuals, technical docs
                    manual_keywords = ['installation', 'manual', 'guide', 'technical', 'specification']
                    
                    for keyword in manual_keywords:
                        links = soup.find_all('a', string=re.compile(keyword, re.IGNORECASE))
                        links.extend(soup.find_all('a', href=re.compile(keyword, re.IGNORECASE)))
                        
                        for link in links[:5]:  # Limit per keyword
                            href = link.get('href')
                            if href:
                                full_url = urljoin(base_url, href)
                                link_text = link.get_text(strip=True)
                                
                                # Skip non-relevant links
                                if any(skip in href.lower() for skip in ['facebook', 'twitter', 'linkedin', 'youtube']):
                                    continue
                                
                                doc = await self._scrape_manufacturer_page(full_url, link_text, manufacturer)
                                if doc:
                                    documents.append(doc)
                                
                                await asyncio.sleep(1)  # Rate limiting
        
        except Exception as e:
            logger.error(f"Error scraping {manufacturer} manuals: {e}")
        
        return documents
    
    async def _scrape_manufacturer_page(self, url: str, title: str, manufacturer: str) -> Optional[Dict[str, Any]]:
        """Scrape individual manufacturer page"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract content
                    content = self._clean_html_content(soup)
                    
                    if len(content.strip()) < 200:  # Skip pages with minimal content
                        return None
                    
                    return {
                        "title": f"{manufacturer.title()} - {title}",
                        "content": content,
                        "source_url": url,
                        "document_type": "manufacturer",
                        "metadata": {
                            "manufacturer": manufacturer,
                            "product_category": self._categorize_product(content, title),
                            "scraped_at": datetime.now().isoformat(),
                            "tags": self._extract_tags_from_content(content)
                        }
                    }
        
        except Exception as e:
            logger.error(f"Error scraping manufacturer page {url}: {e}")
        
        return None
    
    def _clean_html_content(self, soup) -> str:
        """Clean and extract text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = []
        content_lower = content.lower()
        
        # Building code terms
        code_terms = [
            'clearance', 'insulation', 'weathertight', 'fireplace', 'hearth',
            'timber', 'concrete', 'steel', 'compliance', 'building consent',
            'dwang', 'nog', 'stud', 'framing', 'cladding', 'flashing'
        ]
        
        for term in code_terms:
            if term in content_lower:
                tags.append(term)
        
        # Building code clauses
        clause_pattern = r'[A-Z]\d+\.?\d*'
        clauses = re.findall(clause_pattern, content)
        tags.extend([f"clause_{clause.lower()}" for clause in clauses[:5]])
        
        return list(set(tags))  # Remove duplicates
    
    def _categorize_product(self, content: str, title: str) -> str:
        """Categorize product based on content and title"""
        content_title = (content + " " + title).lower()
        
        if any(term in content_title for term in ['fireplace', 'hearth', 'fire', 'chimney']):
            return 'heating'
        elif any(term in content_title for term in ['insulation', 'thermal', 'r-value']):
            return 'insulation'
        elif any(term in content_title for term in ['cladding', 'weatherboard', 'siding']):
            return 'cladding'
        elif any(term in content_title for term in ['timber', 'framing', 'stud', 'dwang']):
            return 'framing'
        elif any(term in content_title for term in ['gib', 'plasterboard', 'drywall']):
            return 'interior_lining'
        else:
            return 'general'

# Utility function for batch scraping
async def scrape_priority_documents() -> List[Dict[str, Any]]:
    """Scrape priority NZ building documents"""
    all_documents = []
    
    async with NZBuildingDocumentScraper() as scraper:
        # Scrape MBIE building code documents
        logger.info("Scraping MBIE building code documents...")
        mbie_docs = await scraper.scrape_mbie_building_code()
        all_documents.extend(mbie_docs)
        logger.info(f"Scraped {len(mbie_docs)} MBIE documents")
        
        # Scrape manufacturer manuals
        manufacturers = ["metrofires"]  # Start with one, expand later
        for manufacturer in manufacturers:
            logger.info(f"Scraping {manufacturer} documents...")
            mfr_docs = await scraper.scrape_manufacturer_manuals(manufacturer)
            all_documents.extend(mfr_docs)
            logger.info(f"Scraped {len(mfr_docs)} {manufacturer} documents")
    
    logger.info(f"Total scraped documents: {len(all_documents)}")
    return all_documents