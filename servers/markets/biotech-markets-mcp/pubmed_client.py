"""
PubMed API client for biotech company publication tracking.

Uses PubMed E-utilities API to search for publications mentioning companies
in author affiliations or abstracts.
"""

import requests
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import quote

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.cache import get_cache, build_cache_key

# PubMed E-utilities API base URL
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
EFETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"

# Initialize cache
_cache = get_cache()


def _rate_limit():
    """Rate limit: PubMed recommends no more than 3 requests per second."""
    time.sleep(0.35)  # Slightly more than 0.33s


def search_company_publications(company_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for publications mentioning a company in author affiliations.
    
    Args:
        company_name: Company name to search for
        limit: Maximum number of publications to return
    
    Returns:
        List of publication dictionaries
    """
    _rate_limit()
    
    try:
        # Search for company name in affiliation field
        query = f'"{company_name}"[Affiliation]'
        query_encoded = quote(query)
        
        # Step 1: Search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": query_encoded,
            "retmax": min(limit, 100),
            "retmode": "json",
            "sort": "pub_date",
            "sort_order": "desc"
        }
        
        response = requests.get(ESEARCH_URL, params=search_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pmids = data.get("esearchresult", {}).get("idlist", [])
        
        if not pmids:
            return []
        
        # Step 2: Fetch publication details
        return get_publication_details(pmids[:limit])
        
    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return []


def get_publication_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """
    Get detailed information for a list of PubMed IDs.
    
    Args:
        pmids: List of PubMed IDs
    
    Returns:
        List of publication dictionaries with details
    """
    if not pmids:
        return []
    
    _rate_limit()
    
    try:
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        response = requests.get(EFETCH_URL, params=fetch_params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response (simplified)
        # In production, would use proper XML parsing (xml.etree.ElementTree)
        xml_content = response.text
        
        publications = []
        
        # Simple XML parsing - look for key fields
        # This is simplified - full parsing would use ElementTree
        import re
        
        # Extract PMIDs
        pmid_matches = re.findall(r'<PMID[^>]*>(\d+)</PMID>', xml_content)
        
        # Extract titles
        title_matches = re.findall(r'<ArticleTitle[^>]*>(.*?)</ArticleTitle>', xml_content, re.DOTALL)
        
        # Extract abstracts
        abstract_matches = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml_content, re.DOTALL)
        
        # Extract publication dates
        pub_date_matches = re.findall(r'<PubDate>.*?<Year>(\d+)</Year>', xml_content, re.DOTALL)
        
        # Extract authors
        author_matches = re.findall(r'<Author[^>]*>.*?<LastName>(.*?)</LastName>.*?<ForeName>(.*?)</ForeName>', xml_content, re.DOTALL)
        
        # Combine into publications
        for i, pmid in enumerate(pmid_matches[:len(pmids)]):
            pub = {
                "pmid": pmid,
                "title": title_matches[i] if i < len(title_matches) else "",
                "abstract": abstract_matches[i] if i < len(abstract_matches) else "",
                "publication_year": pub_date_matches[i] if i < len(pub_date_matches) else "",
                "authors": author_matches[i:i+5] if i < len(author_matches) else [],  # First 5 authors
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"
            }
            publications.append(pub)
        
        return publications
        
    except Exception as e:
        print(f"Error fetching publication details: {e}")
        return []


def get_publication_mentions(company_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent publications mentioning a company.
    
    Args:
        company_name: Company name
        limit: Maximum number of publications
    
    Returns:
        List of publication mentions
    """
    return search_company_publications(company_name, limit=limit)


def search_by_target(target: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for publications about a specific target (e.g., "PD-1", "HER2").
    
    Args:
        target: Target name or identifier
        limit: Maximum number of publications
    
    Returns:
        List of publications
    """
    _rate_limit()
    
    try:
        # Search for target in title/abstract
        query = f'"{target}"[Title/Abstract]'
        query_encoded = quote(query)
        
        search_params = {
            "db": "pubmed",
            "term": query_encoded,
            "retmax": min(limit, 100),
            "retmode": "json",
            "sort": "pub_date",
            "sort_order": "desc"
        }
        
        response = requests.get(ESEARCH_URL, params=search_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pmids = data.get("esearchresult", {}).get("idlist", [])
        
        if not pmids:
            return []
        
        return get_publication_details(pmids[:limit])
        
    except Exception as e:
        print(f"Error searching PubMed by target: {e}")
        return []

