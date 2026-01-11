"""
Investment analysis tools for real estate properties.

Provides high-level workflow tools for property investment analysis:
- generate_property_investment_brief: Comprehensive investment brief for a single property
- compare_properties: Side-by-side comparison of multiple properties
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.cache import build_cache_key, get_cache
from data_source_router import DataSourceRouter


def _extract_address_components(address: str) -> Dict[str, Optional[str]]:
    """
    Extract address components from a full address string.
    
    Args:
        address: Full address string (e.g., "123 Main St, New York, NY 10001")
    
    Returns:
        Dictionary with street, city, state, zip_code
    """
    parts = address.split(",")
    result = {
        "street": None,
        "city": None,
        "state": None,
        "zip_code": None
    }
    
    if len(parts) >= 1:
        result["street"] = parts[0].strip()
    if len(parts) >= 2:
        result["city"] = parts[1].strip()
    if len(parts) >= 3:
        state_zip = parts[2].strip().split()
        if state_zip:
            result["state"] = state_zip[0]
            if len(state_zip) > 1:
                result["zip_code"] = state_zip[1]
    
    return result


def _calculate_yield_estimate(
    estimated_value: Optional[float],
    annual_rent: Optional[float],
    tax_amount: Optional[float]
) -> Optional[float]:
    """
    Calculate yield/cap rate estimate.
    
    Args:
        estimated_value: Property value
        annual_rent: Annual rental income (12 * monthly rent)
        tax_amount: Annual tax amount
    
    Returns:
        Yield percentage or None if insufficient data
    """
    if not estimated_value or estimated_value <= 0:
        return None
    
    net_income = None
    if annual_rent:
        net_income = annual_rent
        if tax_amount:
            net_income -= tax_amount
    
    if net_income and net_income > 0:
        return (net_income / estimated_value) * 100
    
    return None


def _calculate_irr_estimate(
    estimated_value: Optional[float],
    annual_rent: Optional[float],
    tax_amount: Optional[float],
    years: int = 10
) -> Optional[float]:
    """
    Calculate a simple IRR estimate (simplified heuristic).
    
    This is a basic heuristic, not a full IRR calculation.
    For a proper IRR, we'd need cash flow projections over time.
    
    Args:
        estimated_value: Property value
        annual_rent: Annual rental income
        tax_amount: Annual tax amount
        years: Investment horizon (default: 10 years)
    
    Returns:
        Estimated IRR percentage or None if insufficient data
    """
    if not estimated_value or estimated_value <= 0:
        return None
    
    if not annual_rent:
        return None
    
    net_annual_income = annual_rent
    if tax_amount:
        net_annual_income -= tax_amount
    
    if net_annual_income <= 0:
        return None
    
    # Simple heuristic: assume property appreciates at 3% annually
    # and calculate approximate IRR
    appreciation_rate = 0.03
    future_value = estimated_value * ((1 + appreciation_rate) ** years)
    total_return = (net_annual_income * years) + (future_value - estimated_value)
    
    # Approximate IRR using simplified formula
    # This is a heuristic, not a true IRR calculation
    if total_return > 0:
        approximate_irr = ((total_return / estimated_value) / years) * 100
        return approximate_irr
    
    return None


def _identify_red_flags(
    property_data: Dict[str, Any],
    tax_records: Dict[str, Any],
    recent_sales: List[Dict[str, Any]],
    market_trends: Dict[str, Any]
) -> List[str]:
    """
    Identify red flags for a property investment.
    
    Args:
        property_data: Property lookup data
        tax_records: Tax records data
        recent_sales: Recent sales data
        market_trends: Market trends data
    
    Returns:
        List of red flag strings
    """
    red_flags = []
    
    # Check for missing critical data
    if "error" in property_data:
        red_flags.append("Property data lookup failed or incomplete")
    
    if "error" in tax_records:
        red_flags.append("Tax records unavailable")
    
    # Check for unusual tax history
    if "tax_records" in tax_records:
        tax_data = tax_records.get("tax_records", {})
        if tax_data.get("tax_amount") and tax_data.get("assessed_value"):
            tax_rate = (tax_data["tax_amount"] / tax_data["assessed_value"]) * 100
            if tax_rate > 3.0:  # High tax rate threshold
                red_flags.append(f"High property tax rate: {tax_rate:.2f}%")
    
    # Check for recent foreclosure or distress sales
    if recent_sales:
        for sale in recent_sales:
            sale_type = sale.get("sale_type", "").lower()
            if "foreclosure" in sale_type or "distress" in sale_type:
                red_flags.append("Recent foreclosure or distress sale detected")
                break
    
    # Check market trends
    if market_trends:
        price_trend = market_trends.get("price_trend", "")
        if price_trend == "decreasing":
            red_flags.append("Market prices are decreasing")
        
        days_on_market = market_trends.get("days_on_market", 0)
        if days_on_market > 90:
            red_flags.append(f"High days on market: {days_on_market} days")
    
    # Check for missing square footage (important for analysis)
    prop_details = property_data.get("property_data", {})
    if not prop_details.get("square_feet"):
        red_flags.append("Square footage data missing")
    
    # Check for very old property
    year_built = prop_details.get("year_built")
    if year_built and year_built < 1950:
        red_flags.append(f"Very old property (built {year_built}) - may need significant maintenance")
    
    return red_flags


async def generate_property_investment_brief(
    address: str,
    property_id: Optional[str] = None,
    county: Optional[str] = None,
    state: Optional[str] = None,
    router: Optional[DataSourceRouter] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive investment brief for a property.
    
    This tool aggregates data from multiple sources:
    - Property lookup
    - Tax records
    - Recent sales
    - Market trends
    
    Uses caching to avoid redundant API calls.
    
    Args:
        address: Property address or property ID
        property_id: Optional property ID (APN or other identifier)
        county: County name (optional, helps with routing)
        state: State abbreviation (optional, helps with routing)
        router: DataSourceRouter instance (optional, will create if not provided)
    
    Returns:
        PropertyInvestmentBrief dictionary
    """
    if router is None:
        cache = get_cache()
        router = DataSourceRouter(cache=cache)
    
    # Use common cache for expensive lookups
    cache = get_cache()
    server_name = "real-estate-mcp"
    
    result = {
        "address": address,
        "property_id": property_id,
        "tax_info": {},
        "recent_sales": [],
        "rent_comps": {},
        "red_flags": [],
        "property_details": {}
    }
    
    try:
        # Extract address components for lookups
        addr_components = _extract_address_components(address)
        if not state and addr_components.get("state"):
            state = addr_components["state"]
        if not county and addr_components.get("city"):
            # Try to infer county from city (this is a simplification)
            pass
        
        # 1. Property lookup (cached)
        cache_key_lookup = build_cache_key(
            server_name,
            "property_lookup",
            {"address": address, "county": county, "state": state}
        )
        property_data = cache.get(cache_key_lookup)
        if property_data is None:
            property_data = router.get_property_lookup(address, county, state)
            if "error" not in property_data:
                # Cache for 7 days (property data is relatively stable)
                cache.set(cache_key_lookup, property_data, ttl_seconds=7 * 24 * 60 * 60)
        
        # Extract property details
        prop_data = property_data.get("property_data", {})
        result["property_id"] = result["property_id"] or prop_data.get("apn")
        result["estimated_value"] = prop_data.get("estimated_value")
        result["price_per_sqft"] = None
        if prop_data.get("square_feet") and result["estimated_value"]:
            result["price_per_sqft"] = result["estimated_value"] / prop_data["square_feet"]
        
        result["property_details"] = {
            "property_type": prop_data.get("property_type"),
            "square_feet": prop_data.get("square_feet"),
            "bedrooms": prop_data.get("bedrooms"),
            "bathrooms": prop_data.get("bathrooms"),
            "year_built": prop_data.get("year_built"),
            "lot_size": prop_data.get("lot_size")
        }
        
        # 2. Tax records (cached)
        cache_key_tax = build_cache_key(
            server_name,
            "tax_records",
            {"address": address, "county": county, "state": state}
        )
        tax_records = cache.get(cache_key_tax)
        if tax_records is None:
            tax_records = router.get_tax_records(address, county, state)
            if "error" not in tax_records:
                # Cache for 1 year (tax data changes annually)
                cache.set(cache_key_tax, tax_records, ttl_seconds=365 * 24 * 60 * 60)
        
        tax_data = tax_records.get("tax_records", {})
        result["tax_info"] = {
            "assessed_value": tax_data.get("assessed_value"),
            "tax_amount": tax_data.get("tax_amount"),
            "tax_year": tax_data.get("tax_year"),
            "tax_rate": None
        }
        if tax_data.get("assessed_value") and tax_data.get("tax_amount"):
            result["tax_info"]["tax_rate"] = (
                (tax_data["tax_amount"] / tax_data["assessed_value"]) * 100
            )
        
        # 3. Recent sales (cached)
        zip_code = addr_components.get("zip_code")
        if zip_code:
            cache_key_sales = build_cache_key(
                server_name,
                "recent_sales",
                {"zip_code": zip_code, "days": 90, "limit": 10}
            )
            recent_sales_data = cache.get(cache_key_sales)
            if recent_sales_data is None:
                recent_sales_data = router.search_recent_sales(zip_code, days=90, limit=10)
                if "error" not in recent_sales_data:
                    # Cache for 1 day (sales data updates daily)
                    cache.set(cache_key_sales, recent_sales_data, ttl_seconds=24 * 60 * 60)
            
            # Filter for this property's sales
            sales_list = recent_sales_data.get("recent_sales", [])
            if isinstance(sales_list, list):
                result["recent_sales"] = [
                    {
                        "sale_date": sale.get("sale_date"),
                        "sale_price": sale.get("sale_price"),
                        "sale_type": sale.get("sale_type", "arms_length")
                    }
                    for sale in sales_list[:5]  # Limit to 5 most recent
                ]
        
        # 4. Market trends (cached)
        if zip_code:
            cache_key_trends = build_cache_key(
                server_name,
                "market_trends",
                {"zip_code": zip_code}
            )
            market_trends = cache.get(cache_key_trends)
            if market_trends is None:
                market_trends = router.get_market_trends(zip_code=zip_code)
                if "error" not in market_trends:
                    # Cache for 7 days (market trends update weekly)
                    cache.set(cache_key_trends, market_trends, ttl_seconds=7 * 24 * 60 * 60)
            
            result["market_trends"] = {
                "median_price": market_trends.get("median_price"),
                "price_trend": market_trends.get("price_trend"),
                "days_on_market": market_trends.get("days_on_market")
            }
        else:
            result["market_trends"] = {}
        
        # 5. Rent comps estimation
        # This is a simplified estimation - in production, you'd use rental comps API
        estimated_rent = None
        if prop_data.get("square_feet") and result.get("price_per_sqft"):
            # Rough heuristic: rent is typically 0.8-1.2% of property value per month
            if result["estimated_value"]:
                estimated_rent = result["estimated_value"] * 0.01  # 1% of value per month
                result["rent_comps"] = {
                    "estimated_monthly_rent": estimated_rent,
                    "rent_per_sqft": estimated_rent / prop_data["square_feet"] if prop_data["square_feet"] else None,
                    "comparable_rents": []  # Would be populated from rental comps API
                }
        
        # 6. Calculate yield and IRR estimates
        annual_rent = estimated_rent * 12 if estimated_rent else None
        result["yield_estimate"] = _calculate_yield_estimate(
            result["estimated_value"],
            annual_rent,
            result["tax_info"].get("tax_amount")
        )
        result["irr_estimate"] = _calculate_irr_estimate(
            result["estimated_value"],
            annual_rent,
            result["tax_info"].get("tax_amount")
        )
        
        # 7. Identify red flags
        result["red_flags"] = _identify_red_flags(
            property_data,
            tax_records,
            result["recent_sales"],
            result["market_trends"]
        )
        
    except Exception as e:
        result["error"] = str(e)
        result["red_flags"].append(f"Error during analysis: {str(e)}")
    
    return result


async def compare_properties(
    properties: List[str],
    county: Optional[str] = None,
    state: Optional[str] = None,
    router: Optional[DataSourceRouter] = None
) -> Dict[str, Any]:
    """
    Compare multiple properties side-by-side for investment analysis.
    
    Args:
        properties: List of property addresses or property IDs
        county: County name (optional, if all properties are in same county)
        state: State abbreviation (optional, if all properties are in same state)
        router: DataSourceRouter instance (optional)
    
    Returns:
        PropertyComparison dictionary with per-property metrics and summary
    """
    if router is None:
        cache = get_cache()
        router = DataSourceRouter(cache=cache)
    
    result = {
        "properties": [],
        "summary": {
            "best_yield": None,
            "best_value": None,
            "lowest_risk": None,
            "recommendation": "",
            "comparison_metrics": {}
        }
    }
    
    try:
        # Generate briefs for all properties
        property_briefs = []
        for prop_address in properties:
            brief = await generate_property_investment_brief(
                prop_address,
                county=county,
                state=state,
                router=router
            )
            property_briefs.append(brief)
        
        # Build comparison data
        comparison_data = []
        yields = []
        price_per_sqft_list = []
        monthly_rents = []
        red_flag_counts = []
        
        for brief in property_briefs:
            prop_data = {
                "address": brief.get("address"),
                "property_id": brief.get("property_id"),
                "estimated_value": brief.get("estimated_value"),
                "price_per_sqft": brief.get("price_per_sqft"),
                "estimated_monthly_rent": brief.get("rent_comps", {}).get("estimated_monthly_rent"),
                "yield_estimate": brief.get("yield_estimate"),
                "irr_estimate": brief.get("irr_estimate"),
                "tax_amount": brief.get("tax_info", {}).get("tax_amount"),
                "red_flags": brief.get("red_flags", []),
                "property_details": brief.get("property_details", {})
            }
            comparison_data.append(prop_data)
            
            # Collect metrics for summary
            if prop_data["yield_estimate"]:
                yields.append((prop_data["address"], prop_data["yield_estimate"]))
            if prop_data["price_per_sqft"]:
                price_per_sqft_list.append((prop_data["address"], prop_data["price_per_sqft"]))
            if prop_data["estimated_monthly_rent"]:
                monthly_rents.append(prop_data["estimated_monthly_rent"])
            red_flag_counts.append((prop_data["address"], len(prop_data["red_flags"])))
        
        result["properties"] = comparison_data
        
        # Calculate summary
        if yields:
            best_yield = max(yields, key=lambda x: x[1])
            result["summary"]["best_yield"] = best_yield[0]
        
        if price_per_sqft_list:
            best_value = min(price_per_sqft_list, key=lambda x: x[1])
            result["summary"]["best_value"] = best_value[0]
        
        if red_flag_counts:
            lowest_risk = min(red_flag_counts, key=lambda x: x[1])
            result["summary"]["lowest_risk"] = lowest_risk[0]
        
        # Calculate average metrics
        if yields:
            result["summary"]["comparison_metrics"]["average_yield"] = sum(y[1] for y in yields) / len(yields)
        if price_per_sqft_list:
            result["summary"]["comparison_metrics"]["average_price_per_sqft"] = (
                sum(p[1] for p in price_per_sqft_list) / len(price_per_sqft_list)
            )
        if monthly_rents:
            result["summary"]["comparison_metrics"]["average_monthly_rent"] = (
                sum(monthly_rents) / len(monthly_rents)
            )
        
        # Generate recommendation
        recommendations = []
        if result["summary"]["best_yield"]:
            recommendations.append(f"Best yield: {result['summary']['best_yield']}")
        if result["summary"]["best_value"]:
            recommendations.append(f"Best value (lowest price/sqft): {result['summary']['best_value']}")
        if result["summary"]["lowest_risk"]:
            recommendations.append(f"Lowest risk (fewest red flags): {result['summary']['lowest_risk']}")
        
        result["summary"]["recommendation"] = "; ".join(recommendations) if recommendations else "Insufficient data for recommendation"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result
