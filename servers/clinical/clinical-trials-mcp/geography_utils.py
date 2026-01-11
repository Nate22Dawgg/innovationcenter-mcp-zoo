"""
Geography utilities for clinical trial matching.

Provides functions for parsing geographic locations and calculating distances
between patient locations and trial sites.
"""

import re
from typing import Dict, Optional, Tuple, List
import math


# Common city coordinates (for basic proximity calculation without geocoding API)
# This is a limited set - in production, you'd use a geocoding service
CITY_COORDINATES = {
    # Major US cities
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "houston": (29.7604, -95.3698),
    "phoenix": (33.4484, -112.0740),
    "philadelphia": (39.9526, -75.1652),
    "san antonio": (29.4241, -98.4936),
    "san diego": (32.7157, -117.1611),
    "dallas": (32.7767, -96.7970),
    "san jose": (37.3382, -121.8863),
    "austin": (30.2672, -97.7431),
    "jacksonville": (30.3322, -81.6557),
    "fort worth": (32.7555, -97.3308),
    "columbus": (39.9612, -82.9988),
    "charlotte": (35.2271, -80.8431),
    "san francisco": (37.7749, -122.4194),
    "indianapolis": (39.7684, -86.1581),
    "seattle": (47.6062, -122.3321),
    "denver": (39.7392, -104.9903),
    "washington": (38.9072, -77.0369),
    "boston": (42.3601, -71.0589),
    "el paso": (31.7619, -106.4850),
    "detroit": (42.3314, -83.0458),
    "nashville": (36.1627, -86.7816),
    "portland": (45.5152, -122.6784),
    "oklahoma city": (35.4676, -97.5164),
    "las vegas": (36.1699, -115.1398),
    "memphis": (35.1495, -90.0490),
    "louisville": (38.2527, -85.7585),
    "baltimore": (39.2904, -76.6122),
    "milwaukee": (43.0389, -87.9065),
    "albuquerque": (35.0844, -106.6504),
    "tucson": (32.2226, -110.9747),
    "fresno": (36.7378, -119.7871),
    "sacramento": (38.5816, -121.4944),
    "kansas city": (39.0997, -94.5786),
    "mesa": (33.4152, -111.8315),
    "atlanta": (33.7490, -84.3880),
    "omaha": (41.2565, -95.9345),
    "colorado springs": (38.8339, -104.8214),
    "raleigh": (35.7796, -78.6382),
    "virginia beach": (36.8529, -75.9780),
    "miami": (25.7617, -80.1918),
    "oakland": (37.8044, -122.2712),
    "minneapolis": (44.9778, -93.2650),
    "tulsa": (36.1540, -95.9928),
    "cleveland": (41.4993, -81.6944),
    "wichita": (37.6872, -97.3301),
    "arlington": (32.7357, -97.1081),
}


def parse_geography(geography: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Parse and normalize geography input.
    
    Args:
        geography: Dictionary with city, state, zip, country fields
    
    Returns:
        Normalized geography dictionary or None if invalid
    """
    if not geography:
        return None
    
    parsed = {}
    if geography.get("city"):
        parsed["city"] = geography["city"].strip().lower()
    if geography.get("state"):
        parsed["state"] = geography["state"].strip().upper()
    if geography.get("zip"):
        parsed["zip"] = geography["zip"].strip()
    if geography.get("country"):
        parsed["country"] = geography["country"].strip()
    
    return parsed if parsed else None


def get_city_coordinates(city: str) -> Optional[Tuple[float, float]]:
    """
    Get approximate coordinates for a city name.
    
    This is a simple lookup - in production, use a geocoding service.
    
    Args:
        city: City name (case-insensitive)
    
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    city_lower = city.lower().strip()
    return CITY_COORDINATES.get(city_lower)


def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
    
    Returns:
        Distance in miles
    """
    # Earth radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def parse_trial_location(location_str: str) -> Optional[Dict[str, str]]:
    """
    Parse a trial location string into components.
    
    Args:
        location_str: Location string like "Boston, MA" or "New York, NY, United States"
    
    Returns:
        Dictionary with city, state, country or None if parsing fails
    """
    if not location_str:
        return None
    
    # Try to parse common formats
    parts = [p.strip() for p in location_str.split(",")]
    
    parsed = {}
    if len(parts) >= 1:
        parsed["city"] = parts[0]
    if len(parts) >= 2:
        # Could be state or country
        if len(parts[2:]) > 0:
            parsed["state"] = parts[1]
            parsed["country"] = ", ".join(parts[2:])
        else:
            # Check if it's a 2-letter code (likely state) or longer (likely country)
            if len(parts[1]) == 2:
                parsed["state"] = parts[1]
            else:
                parsed["country"] = parts[1]
    if len(parts) >= 3:
        parsed["country"] = parts[2]
    
    return parsed if parsed else None


def calculate_trial_proximity(
    patient_geography: Optional[Dict[str, str]],
    trial_locations: List[str]
) -> Optional[float]:
    """
    Calculate the minimum distance from patient location to any trial location.
    
    Args:
        patient_geography: Patient's geography (from parse_geography)
        trial_locations: List of trial location strings
    
    Returns:
        Minimum distance in miles, or None if cannot calculate
    """
    if not patient_geography or not trial_locations:
        return None
    
    patient_city = patient_geography.get("city")
    if not patient_city:
        return None
    
    patient_coords = get_city_coordinates(patient_city)
    if not patient_coords:
        return None
    
    min_distance = None
    
    for loc_str in trial_locations:
        parsed_loc = parse_trial_location(loc_str)
        if not parsed_loc:
            continue
        
        trial_city = parsed_loc.get("city", "").lower()
        trial_coords = get_city_coordinates(trial_city)
        
        if trial_coords:
            distance = calculate_distance(
                patient_coords[0], patient_coords[1],
                trial_coords[0], trial_coords[1]
            )
            if min_distance is None or distance < min_distance:
                min_distance = distance
    
    return min_distance


def matches_geography(
    patient_geography: Optional[Dict[str, str]],
    trial_locations: List[str],
    max_distance_miles: int = 100
) -> Tuple[bool, Optional[float]]:
    """
    Check if trial locations match patient geography.
    
    Args:
        patient_geography: Patient's geography
        trial_locations: List of trial location strings
        max_distance_miles: Maximum allowed distance (0 = no limit)
    
    Returns:
        Tuple of (matches, distance_miles)
    """
    if not patient_geography:
        return (True, None)  # No geography filter
    
    if max_distance_miles == 0:
        return (True, None)  # No distance limit
    
    # Check country match first (simple string matching)
    patient_country = patient_geography.get("country", "").lower()
    if patient_country:
        for loc_str in trial_locations:
            loc_lower = loc_str.lower()
            # Simple country matching
            if patient_country in loc_lower or any(
                country in loc_lower
                for country in ["united states", "usa", "us"]
                if patient_country in ["united states", "usa", "us"]
            ):
                distance = calculate_trial_proximity(patient_geography, [loc_str])
                if distance is None or distance <= max_distance_miles:
                    return (True, distance)
    
    # Check state match
    patient_state = patient_geography.get("state", "").upper()
    if patient_state:
        for loc_str in trial_locations:
            if patient_state in loc_str.upper():
                distance = calculate_trial_proximity(patient_geography, [loc_str])
                if distance is None or distance <= max_distance_miles:
                    return (True, distance)
    
    # Check city/distance
    distance = calculate_trial_proximity(patient_geography, trial_locations)
    if distance is not None:
        return (distance <= max_distance_miles, distance)
    
    # If we can't calculate distance, allow it but mark as unknown
    return (True, None)
