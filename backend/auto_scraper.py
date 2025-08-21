"""
STRYDA.ai Automated Web Scraping Pipeline
Auto-fetches latest MBIE documents, Standards NZ, and manufacturer updates
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScrapingTarget:
    """Configuration for a scraping target"""
    name: str
    base_url: str
    scraping_patterns: List[str]
    update_frequency: timedelta
    last_scraped: Optional[datetime] = None
    document_type: str = "auto_scraped"

class AutomatedScraper:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.session = None
        self.scraping_targets = self._configure_scraping_targets()
        
    def _configure_scraping_targets(self) -> List[ScrapingTarget]:
        """Configure automated scraping targets"""
        
        return [
            # MBIE Building Code Updates
            ScrapingTarget(
                name="MBIE Building Code",
                base_url="https://www.building.govt.nz/building-code-compliance/",
                scraping_patterns=[
                    r'/building-code-compliance/[a-z]-[^/]+/[a-z]\d+-[^/]+/',
                    r'/assets/Uploads/building-code/.*\.pdf$'
                ],
                update_frequency=timedelta(days=7),  # Weekly check
                document_type="nzbc"
            ),
            
            # Standards New Zealand
            ScrapingTarget(
                name="Standards NZ Updates",
                base_url="https://www.standards.govt.nz/",
                scraping_patterns=[
                    r'/shop/nzs-\d+',
                    r'/news/.*building.*standard'
                ],
                update_frequency=timedelta(days=14),  # Bi-weekly
                document_type="nzs"
            ),
            
            # BRANZ Build Magazine
            ScrapingTarget(
                name="BRANZ Build Articles", 
                base_url="https://www.branz.co.nz/",
                scraping_patterns=[
                    r'/articles/.*',
                    r'/pubs/build-magazine/.*'
                ],
                update_frequency=timedelta(days=7),
                document_type="branz"
            ),
            
            # Licensed Building Practitioners
            ScrapingTarget(
                name="LBP Code Updates",
                base_url="https://www.lbp.govt.nz/",
                scraping_patterns=[
                    r'/for-lbps/skills-maintenance/codewords/.*',
                    r'/news/.*building.*code'
                ],
                update_frequency=timedelta(days=7),
                document_type="lbp"
            ),
            
            # Major Manufacturers
            ScrapingTarget(
                name="GIB Technical Updates",
                base_url="https://www.gib.co.nz/",
                scraping_patterns=[
                    r'/technical-support/.*',
                    r'/news/.*technical.*'
                ],
                update_frequency=timedelta(days=30),  # Monthly
                document_type="manufacturer"
            ),
            
            ScrapingTarget(
                name="James Hardie Updates",
                base_url="https://www.jameshardie.co.nz/",
                scraping_patterns=[
                    r'/technical-support/.*',
                    r'/products/.*/installation.*'
                ],
                update_frequency=timedelta(days=30),
                document_type="manufacturer"
            ),
            
            ScrapingTarget(
                name="Resene Technical Updates",
                base_url="https://www.resene.co.nz/",
                scraping_patterns=[
                    r'/technical-advice/.*',
                    r'/news/.*technical.*'
                ],
                update_frequency=timedelta(days=30),
                document_type="manufacturer"
            )
        ]
    
    async def __aenter__(self):
        """Initialize async HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'STRYDA.ai Auto-Scraper - NZ Building Code Research Bot'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
    
    async def run_automated_scraping(self) -> Dict[str, Any]:
        """Run automated scraping for all configured targets"""
        
        results = {
            "scraping_session_id": hashlib.md5(str(datetime.now()).encode()).hexdigest(),
            "started_at": datetime.now().isoformat(),
            "targets_processed": 0,
            "documents_found": 0,
            "documents_updated": 0,
            "errors": [],
            "target_results": []
        }
        
        logger.info("Starting automated STRYDA.ai document scraping...")
        
        async with self:
            for target in self.scraping_targets:
                target_result = await self._scrape_target(target)
                results["target_results"].append(target_result)
                results["targets_processed"] += 1
                results["documents_found"] += target_result["documents_found"]
                results["documents_updated"] += target_result["documents_processed"]
                
                if target_result["errors"]:
                    results["errors"].extend(target_result["errors"])
                
                # Rate limiting between targets
                await asyncio.sleep(2)
        
        results["completed_at"] = datetime.now().isoformat()
        logger.info(f"Automated scraping completed: {results['documents_updated']} documents updated")
        
        return results
    
    async def _scrape_target(self, target: ScrapingTarget) -> Dict[str, Any]:
        """Scrape a specific target for updates"""
        
        result = {
            "target_name": target.name,
            "base_url": target.base_url,
            "started_at": datetime.now().isoformat(),
            "documents_found": 0,
            "documents_processed": 0,
            "errors": [],
            "new_documents": []
        }
        
        # Check if scraping is due
        if target.last_scraped:
            time_since_last = datetime.now() - target.last_scraped
            if time_since_last < target.update_frequency:
                result["skipped"] = f"Not due for scraping (last: {target.last_scraped})"
                return result
        
        try:
            logger.info(f"Scraping target: {target.name}")
            
            # Get main page content
            async with self.session.get(target.base_url) as response:
                if response.status != 200:
                    result["errors"].append(f"HTTP {response.status} for {target.base_url}")
                    return result
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find links matching patterns
                found_urls = []
                for pattern in target.scraping_patterns:
                    links = soup.find_all('a', href=re.compile(pattern))
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(target.base_url, href)
                            found_urls.append({
                                "url": full_url,
                                "title": link.get_text(strip=True)[:100],
                                "pattern": pattern
                            })
                
                result["documents_found"] = len(found_urls)
                
                # Process each found URL
                for url_info in found_urls[:10]:  # Limit to 10 per target
                    try:
                        doc_result = await self._process_document_url(url_info, target)
                        if doc_result:
                            result["documents_processed"] += 1
                            result["new_documents"].append(doc_result)
                        
                        # Rate limiting between documents
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        result["errors"].append(f"Error processing {url_info['url']}: {str(e)}")
                
                # Update last scraped time
                target.last_scraped = datetime.now()
                
        except Exception as e:
            result["errors"].append(f"Target scraping failed: {str(e)}")
            logger.error(f"Error scraping {target.name}: {e}")
        
        result["completed_at"] = datetime.now().isoformat()
        return result
    
    async def _process_document_url(self, url_info: Dict[str, Any], target: ScrapingTarget) -> Optional[Dict[str, Any]]:
        """Process individual document URL"""
        
        try:
            async with self.session.get(url_info["url"]) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract content
                content = self._extract_page_content(soup)
                
                if len(content.strip()) < 300:  # Skip pages with minimal content
                    return None
                
                # Generate content hash for deduplication
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Check if document already exists
                existing = await self.document_processor.db.processed_documents.find_one(
                    {"content_hash": content_hash}
                )
                
                if existing:
                    return None  # Already processed
                
                # Extract metadata
                metadata = self._extract_document_metadata(soup, url_info, target)
                
                # Process and store document
                doc_id = await self.document_processor.process_and_store_document(
                    title=url_info["title"] or self._extract_title(soup),
                    content=content,
                    source_url=url_info["url"],
                    document_type=target.document_type,
                    metadata=metadata
                )
                
                return {
                    "document_id": doc_id,
                    "title": url_info["title"],
                    "url": url_info["url"],
                    "content_length": len(content),
                    "metadata": metadata
                }
                
        except Exception as e:
            logger.error(f"Error processing document {url_info['url']}: {e}")
            return None
    
    def _extract_page_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()
        
        # Look for main content containers
        content_containers = [
            soup.find('main'),
            soup.find('article'),
            soup.find('div', class_='content'),
            soup.find('div', class_='main-content'),
            soup.find('div', id='content'),
            soup.find('div', id='main')
        ]
        
        # Use first found container or entire body
        content_element = None
        for container in content_containers:
            if container:
                content_element = container
                break
        
        if not content_element:
            content_element = soup.find('body') or soup
        
        # Extract and clean text
        text = content_element.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        
        # Try different title sources
        title_element = (
            soup.find('h1') or 
            soup.find('title') or
            soup.find('h2')
        )
        
        if title_element:
            return title_element.get_text(strip=True)[:200]
        
        return "Auto-scraped Document"
    
    def _extract_document_metadata(self, soup: BeautifulSoup, url_info: Dict[str, Any], target: ScrapingTarget) -> Dict[str, Any]:
        """Extract metadata from document"""
        
        metadata = {
            "scraping_target": target.name,
            "scraped_at": datetime.now().isoformat(),
            "source_pattern": url_info.get("pattern", ""),
            "auto_scraped": True,
            "tags": []
        }
        
        # Extract date information
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
        ]
        
        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                metadata["document_date"] = match.group(1)
                break
        
        # Extract building code references
        code_refs = re.findall(r'([A-Z]\d+(?:\.\d+)*|NZS\s*\d+(?::\d+)?)', page_text, re.IGNORECASE)
        if code_refs:
            metadata["building_code_refs"] = list(set(code_refs[:10]))
            metadata["tags"].extend([f"code_{ref.lower().replace(' ', '_')}" for ref in code_refs[:5]])
        
        # Extract keywords based on target type
        if target.document_type == "nzbc":
            metadata["category"] = "building_code"
            metadata["tags"].extend(["nzbc", "building_code", "compliance"])
        elif target.document_type == "manufacturer":
            metadata["category"] = "manufacturer_guide"
            metadata["tags"].extend(["manufacturer", "installation", "technical"])
        elif target.document_type == "nzs":
            metadata["category"] = "nz_standard"
            metadata["tags"].extend(["nzs", "standard", "technical"])
        
        # Extract technical terms
        technical_terms = [
            "clearance", "insulation", "weathertight", "fireplace", "thermal",
            "structural", "seismic", "foundation", "framing", "cladding"
        ]
        
        found_terms = []
        page_text_lower = page_text.lower()
        for term in technical_terms:
            if term in page_text_lower:
                found_terms.append(term)
        
        if found_terms:
            metadata["tags"].extend(found_terms)
        
        return metadata
    
    async def schedule_periodic_scraping(self, interval_hours: int = 24):
        """Schedule periodic automated scraping"""
        
        logger.info(f"Scheduling automated scraping every {interval_hours} hours")
        
        while True:
            try:
                results = await self.run_automated_scraping()
                
                # Log results
                logger.info(f"Scheduled scraping completed: {results['documents_updated']} documents updated")
                
                if results['errors']:
                    logger.warning(f"Scraping errors: {len(results['errors'])}")
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Scheduled scraping failed: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def force_update_target(self, target_name: str) -> Dict[str, Any]:
        """Force update a specific target regardless of schedule"""
        
        target = None
        for t in self.scraping_targets:
            if t.name == target_name:
                target = t
                break
        
        if not target:
            return {"error": f"Target '{target_name}' not found"}
        
        # Reset last scraped to force update
        target.last_scraped = None
        
        async with self:
            result = await self._scrape_target(target)
            
        return result