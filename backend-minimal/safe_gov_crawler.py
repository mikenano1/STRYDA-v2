#!/usr/bin/env python3
"""
STRYDA Government PDF Crawler - Safe, Allowlisted, Licensing-Compliant
Crawls ONLY public, free government building PDFs
"""

import os
import requests
import urllib.robotparser
from urllib.parse import urljoin, urlparse
import hashlib
import time
import re
from datetime import datetime
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PDFCandidate:
    """PDF candidate for ingestion"""
    url: str
    source_domain: str
    title: str
    estimated_source: str
    estimated_edition: str
    estimated_year: str
    file_size: int
    sha256: str
    discovered_from: str

class SafeGovernmentCrawler:
    """Safe, compliant crawler for government building PDFs"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        
        # ALLOWLIST: Only these domains (government/public)
        self.allowed_domains = [
            "building.govt.nz",
            "codehub.building.govt.nz", 
            "mbie.govt.nz",
            "health.govt.nz"
        ]
        
        # BLOCKLIST: Never crawl these terms/paths
        self.blocklist_terms = [
            "login", "purchase", "standards.govt.nz", "shop", "copyright",
            "subscribe", "account", "payment", "cart", "buy", "order"
        ]
        
        # Target building codes (free government acceptable solutions)
        self.target_codes = [
            "F4/AS1", "F4-AS1", "f4as1",  # Balustrades/Safety from falling
            "E1/AS1", "E1-AS1", "e1as1",  # Surface water
            "E3/AS1", "E3-AS1", "e3as1",  # Internal moisture
            "G12/AS1", "G12-AS1", "g12as1", # Water supplies
            "G13/AS1", "G13-AS1", "g13as1"  # Foul water
        ]
        
        self.discovered_pdfs = []
        self.rate_limit_delay = 1.0  # 1 second between requests
        
    def is_url_safe(self, url: str) -> bool:
        """Check if URL is safe to crawl"""
        url_lower = url.lower()
        
        # Check blocklist
        for blocked_term in self.blocklist_terms:
            if blocked_term in url_lower:
                return False
        
        # Check domain allowlist
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        return any(allowed in domain for allowed in self.allowed_domains)
    
    def respect_robots_txt(self, base_url: str) -> bool:
        """Check robots.txt compliance"""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch('*', base_url)
        except Exception:
            # If robots.txt fails, be conservative and allow
            return True
    
    def discover_pdf_links(self, seed_url: str, max_depth: int = 2) -> List[str]:
        """Discover PDF links from seed URL"""
        discovered = []
        
        if not self.is_url_safe(seed_url) or not self.respect_robots_txt(seed_url):
            print(f"⛔ URL not safe or robots.txt blocked: {seed_url}")
            return discovered
        
        try:
            print(f"🔍 Scanning: {seed_url}")
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(seed_url, timeout=10, headers={
                'User-Agent': 'STRYDA-Building-Code-Assistant/1.0 (Building Code Research)'
            })
            
            if response.status_code != 200:
                return discovered
            
            content = response.text
            
            # Find PDF links
            pdf_link_pattern = r'href=["\']([^"\']+\.pdf)["\']'
            pdf_matches = re.findall(pdf_link_pattern, content, re.IGNORECASE)
            
            for pdf_path in pdf_matches:
                pdf_url = urljoin(seed_url, pdf_path)
                
                if self.is_url_safe(pdf_url):
                    # Check if it's likely a building code PDF
                    if any(code.lower() in pdf_url.lower() for code in self.target_codes):
                        discovered.append(pdf_url)
                        print(f"   ✅ Found target PDF: {pdf_url}")
            
            # Also scan for direct mentions of building codes in page content
            for code in self.target_codes:
                code_pattern = rf'\b{re.escape(code)}\b'
                if re.search(code_pattern, content, re.IGNORECASE):
                    print(f"   🎯 Page mentions {code}")
            
        except Exception as e:
            print(f"⚠️ Failed to scan {seed_url}: {e}")
        
        return discovered
    
    def analyze_pdf_candidate(self, pdf_url: str) -> Optional[PDFCandidate]:
        """Analyze PDF for metadata without downloading full content"""
        if not self.is_url_safe(pdf_url):
            return None
        
        try:
            print(f"📋 Analyzing: {pdf_url}")
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # HEAD request for metadata
            head_response = requests.head(pdf_url, timeout=10)
            
            if head_response.status_code != 200:
                return None
            
            content_type = head_response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                return None
            
            file_size = int(head_response.headers.get('content-length', 0))
            
            # Skip very large files (>40MB)
            if file_size > 40 * 1024 * 1024:
                print(f"   ⚠️ Too large: {file_size:,} bytes")
                return None
            
            # Parse URL for source identification
            url_parts = urlparse(pdf_url)
            filename = url_parts.path.split('/')[-1]
            
            # Extract source information from filename/URL
            source_name = "Unknown"
            edition = "Unknown"
            year = "Unknown"
            
            # Pattern matching for building codes
            filename_lower = filename.lower()
            url_lower = pdf_url.lower()
            
            for code in self.target_codes:
                if code.lower() in url_lower:
                    source_name = code.upper().replace('-', '/')
                    break
            
            # Try to extract year from filename
            year_match = re.search(r'20\d{2}', filename)
            if year_match:
                year = year_match.group()
            
            # Try to extract edition/amendment
            amd_match = re.search(r'(amd|amendment)\s*(\d+)', filename, re.IGNORECASE)
            if amd_match:
                edition = f"Amendment {amd_match.group(2)}"
            elif re.search(r'edition', filename, re.IGNORECASE):
                edition_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*edition', filename, re.IGNORECASE)
                if edition_match:
                    edition = f"Edition {edition_match.group(1)}"
            
            # Quick SHA-256 of first 1KB for initial dedup check
            try:
                partial_response = requests.get(pdf_url, headers={'Range': 'bytes=0-1023'}, timeout=5)
                partial_sha = hashlib.sha256(partial_response.content).hexdigest()[:16]
            except:
                partial_sha = hashlib.sha256(pdf_url.encode()).hexdigest()[:16]
            
            candidate = PDFCandidate(
                url=pdf_url,
                source_domain=url_parts.netloc,
                title=filename.replace('.pdf', '').replace('-', ' '),
                estimated_source=source_name,
                estimated_edition=edition,
                estimated_year=year,
                file_size=file_size,
                sha256=partial_sha,
                discovered_from=url_parts.netloc
            )
            
            print(f"   ✅ {source_name} ({file_size:,} bytes, est. {year})")
            
            return candidate
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            return None
    
    def run_discovery_crawl(self) -> Dict[str, Any]:
        """Run discovery crawl in DRY_RUN mode"""
        run_id = f"gov_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print("🕷️ STRYDA GOVERNMENT PDF CRAWLER (DRY RUN)")
        print("=" * 70)
        print(f"Run ID: {run_id}")
        print(f"Mode: {'DRY RUN (discovery only)' if self.dry_run else 'LIVE INGESTION'}")
        print(f"Allowed domains: {self.allowed_domains}")
        print(f"Rate limit: {self.rate_limit_delay}s between requests")
        print()
        
        # Seed URLs for government building code pages
        seed_urls = [
            "https://www.building.govt.nz/building-code/",
            "https://www.building.govt.nz/building-code/acceptable-solutions-and-verification-methods/",
            "https://codehub.building.govt.nz/acceptable-solutions-and-verification-methods",
            "https://www.mbie.govt.nz/building-and-construction/building-code/",
        ]
        
        candidates = []
        discovered_urls = set()
        
        for seed_url in seed_urls:
            print(f"🌱 Crawling seed: {seed_url}")
            
            try:
                pdf_links = self.discover_pdf_links(seed_url)
                
                for pdf_url in pdf_links:
                    if pdf_url not in discovered_urls:
                        discovered_urls.add(pdf_url)
                        
                        candidate = self.analyze_pdf_candidate(pdf_url)
                        if candidate:
                            candidates.append(candidate)
                
            except Exception as e:
                print(f"❌ Seed crawl failed: {e}")
        
        # Generate discovery report
        report = {
            "run_id": run_id,
            "started_at": datetime.now().isoformat(),
            "mode": "DRY_RUN" if self.dry_run else "LIVE",
            "seeds": seed_urls,
            "discovered_pdf_count": len(discovered_urls),
            "analyzed_candidates": len(candidates),
            "total_size_mb": sum(c.file_size for c in candidates) // (1024 * 1024),
            "candidates": [
                {
                    "url": c.url,
                    "estimated_source": c.estimated_source,
                    "estimated_edition": c.estimated_edition,
                    "estimated_year": c.estimated_year,
                    "file_size_mb": round(c.file_size / (1024 * 1024), 1),
                    "domain": c.source_domain
                }
                for c in candidates[:20]  # Top 20 for review
            ]
        }
        
        print(f"\n📊 DISCOVERY SUMMARY:")
        print(f"   PDFs discovered: {len(discovered_urls)}")
        print(f"   Viable candidates: {len(candidates)}")
        print(f"   Total estimated size: {report['total_size_mb']} MB")
        
        if candidates:
            print(f"\n📋 TOP CANDIDATES FOR APPROVAL:")
            for i, candidate in enumerate(candidates[:10], 1):
                print(f"   {i:2d}. {candidate.estimated_source} ({candidate.file_size_mb} MB, {candidate.estimated_year})")
                print(f"       {candidate.url}")
        
        return report

if __name__ == "__main__":
    # Run in DRY_RUN mode for approval
    crawler = SafeGovernmentCrawler(dry_run=True)
    discovery_report = crawler.run_discovery_crawl()
    
    # Save report for review
    os.makedirs("tmp", exist_ok=True)
    
    import json
    with open("tmp/gov_pdf_discovery_report.json", "w") as f:
        json.dump(discovery_report, f, indent=2)
    
    print(f"\n📋 Discovery report saved: tmp/gov_pdf_discovery_report.json")
    print("Ready for approval to proceed with live ingestion.")