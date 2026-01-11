"""
Client for orchestrating calls to multiple MCP servers.

This client coordinates calls to upstream MCP servers to aggregate data
across markets and clinical domains.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.logging import get_logger
from common.cache import get_cache, build_cache_key
from common.identifiers import normalize_ticker, normalize_cik

logger = get_logger(__name__)


class MCPOrchestratorClient:
    """
    Client for orchestrating calls to multiple MCP servers.
    
    This client coordinates calls to:
    - biotech-markets-mcp: Company profiles and financials
    - sec-edgar-mcp: SEC filings and company information
    - clinical-trials-mcp or biomcp-mcp: Clinical trial data
    
    Note: In a production environment, this would call other MCP servers
    via their stdio or HTTP interfaces. For now, we import functions directly
    from other servers (creates coupling but is simpler for an orchestrator).
    """
    
    def __init__(self, config: Any, cache_ttl_seconds: int = 300):
        """
        Initialize the orchestrator client.
        
        Args:
            config: Server configuration
            cache_ttl_seconds: Cache TTL in seconds
        """
        self.config = config
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache = get_cache()
        
    def _get_biotech_markets_data(self, identifier: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get company data from biotech-markets-mcp.
        
        Args:
            identifier: Company identifier (ticker, company_name, or cik)
        
        Returns:
            Company profile data or None if unavailable
        """
        try:
            # Import from biotech-markets-mcp server
            # In production, this would call the MCP server via stdio/HTTP
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "servers" / "markets" / "biotech-markets-mcp"))
            
            from company_aggregator import get_profile
            
            # Determine identifier type
            company_name = identifier.get("company_name")
            ticker = identifier.get("ticker")
            
            if company_name:
                profile = get_profile(company_name, use_cache=True)
                return profile
            elif ticker:
                # Try to get by ticker (may need company name lookup first)
                # For now, return None if only ticker provided
                logger.warning(f"Ticker-only lookup not fully supported, need company name")
                return None
            else:
                return None
                
        except ImportError as e:
            logger.warning(f"Could not import from biotech-markets-mcp: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting biotech markets data: {e}")
            return None
    
    def _get_sec_data(self, identifier: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get SEC data from sec-edgar-mcp.
        
        Args:
            identifier: Company identifier (cik, ticker, or company_name)
        
        Returns:
            SEC company info or None if unavailable
        """
        try:
            # Import from sec-edgar-mcp server
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "servers" / "markets" / "sec-edgar-mcp"))
            
            from sec_edgar_client import get_company_info
            
            cik = identifier.get("cik")
            ticker = identifier.get("ticker")
            company_name = identifier.get("company_name")
            
            if cik:
                info = get_company_info(cik=cik)
                return info
            elif ticker or company_name:
                # Try to search by ticker/name
                # For now, return None if only ticker/name provided
                logger.warning(f"Ticker/name-only SEC lookup not fully supported, need CIK")
                return None
            else:
                return None
                
        except ImportError as e:
            logger.warning(f"Could not import from sec-edgar-mcp: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting SEC data: {e}")
            return None
    
    def _get_clinical_trials_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get clinical trials data.
        
        Args:
            company_name: Company name to search for
        
        Returns:
            Clinical trials summary or None if unavailable
        """
        try:
            # Try to import from clinical-trials-mcp or biomcp-mcp
            # For now, we'll use a simple approach
            # In production, this would call the MCP server via stdio/HTTP
            
            # Try biomcp-mcp first
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "servers" / "clinical" / "biomcp-mcp" / "src" / "biomcp"))
                # This is complex - for now, return a placeholder
                logger.info(f"Clinical trials lookup for {company_name} - placeholder")
                return {
                    "total_trials": 0,
                    "active_trials": 0,
                    "trials": []
                }
            except ImportError:
                pass
            
            # Try clinical-trials-mcp
            try:
                # Placeholder - would need actual implementation
                logger.info(f"Clinical trials lookup for {company_name} - placeholder")
                return {
                    "total_trials": 0,
                    "active_trials": 0,
                    "trials": []
                }
            except Exception:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting clinical trials data: {e}")
            return None
    
    def analyze_company(
        self,
        identifier: Dict[str, Any],
        include_financials: bool = True,
        include_clinical: bool = True,
        include_sec: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a company across markets and clinical domains.
        
        Args:
            identifier: Company identifier (ticker, company_name, cik, or combination)
            include_financials: Whether to include financial data
            include_clinical: Whether to include clinical trial data
            include_sec: Whether to include SEC filing data
        
        Returns:
            Combined analysis across all domains
        """
        # Check cache first
        cache_key = build_cache_key(
            "healthcare-equities-orchestrator",
            "analyze_company",
            {
                "identifier": identifier,
                "include_financials": include_financials,
                "include_clinical": include_clinical,
                "include_sec": include_sec
            }
        )
        
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.info("Returning cached analysis result")
            return cached_result
        
        # Normalize identifiers
        company_name = identifier.get("company_name")
        ticker = normalize_ticker(identifier.get("ticker", "")) if identifier.get("ticker") else None
        cik = normalize_cik(identifier.get("cik", "")) if identifier.get("cik") else None
        
        # Create normalized identifier dict for downstream calls
        normalized_identifier = {}
        if company_name:
            normalized_identifier["company_name"] = company_name
        if ticker:
            normalized_identifier["ticker"] = ticker
        if cik:
            normalized_identifier["cik"] = cik
        
        results = {
            "identifier": normalized_identifier,  # Use normalized identifiers in response
            "financials": None,
            "clinical": None,
            "sec": None,
            "risk_flags": [],
            "summary": {}
        }
        
        # Get biotech markets data (includes financials and pipeline)
        if include_financials:
            try:
                markets_data = self._get_biotech_markets_data(normalized_identifier)
                if markets_data:
                    results["financials"] = {
                        "company_name": markets_data.get("company_name"),
                        "normalized_name": markets_data.get("normalized_name"),
                        "pipeline": markets_data.get("pipeline", []),
                        "financial_summary": markets_data.get("financial_summary"),
                        "trials_summary": markets_data.get("trials_summary"),
                        "risk_flags": markets_data.get("risk_flags", [])
                    }
                    # Extract company name if not already set
                    if not company_name and markets_data.get("company_name"):
                        company_name = markets_data.get("company_name")
            except Exception as e:
                logger.error(f"Error getting financials: {e}")
        
        # Get SEC data
        if include_sec:
            try:
                sec_data = self._get_sec_data(normalized_identifier)
                if sec_data:
                    results["sec"] = sec_data
            except Exception as e:
                logger.error(f"Error getting SEC data: {e}")
        
        # Get clinical trials data
        if include_clinical and company_name:
            try:
                clinical_data = self._get_clinical_trials_data(company_name)
                if clinical_data:
                    results["clinical"] = clinical_data
            except Exception as e:
                logger.error(f"Error getting clinical data: {e}")
        
        # Aggregate risk flags
        all_risk_flags = []
        if results["financials"] and results["financials"].get("risk_flags"):
            all_risk_flags.extend(results["financials"]["risk_flags"])
        
        results["risk_flags"] = list(set(all_risk_flags))  # Deduplicate
        
        # Create summary
        results["summary"] = {
            "has_financials": results["financials"] is not None,
            "has_clinical": results["clinical"] is not None,
            "has_sec": results["sec"] is not None,
            "pipeline_drugs": len(results["financials"].get("pipeline", [])) if results["financials"] else 0,
            "total_trials": results["clinical"].get("total_trials", 0) if results["clinical"] else 0,
            "risk_flag_count": len(results["risk_flags"])
        }
        
        # Cache the result
        self._cache.set(cache_key, results, ttl_seconds=self.cache_ttl_seconds)
        
        return results
