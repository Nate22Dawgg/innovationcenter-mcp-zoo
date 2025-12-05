"""
VCR.py configuration for API response caching in tests.
"""

import vcr
from pathlib import Path

# Directory for VCR cassettes
CASSETTE_DIR = Path(__file__).parent / "vcr_cassettes"
CASSETTE_DIR.mkdir(parents=True, exist_ok=True)


def get_vcr_config(record_mode='once'):
    """
    Get VCR configuration for API response caching.
    
    Args:
        record_mode: VCR record mode
            - 'once': Record once, then use cassette (default)
            - 'new_episodes': Record new interactions, use existing
            - 'all': Always record (for updating cassettes)
            - 'none': Never record, only use existing cassettes
    
    Returns:
        VCR instance configured for testing
    """
    return vcr.VCR(
        cassette_library_dir=str(CASSETTE_DIR),
        record_mode=record_mode,
        match_on=['uri', 'method', 'body'],
        filter_headers=[
            'authorization',
            'api-key',
            'x-api-key',
            'X-API-Key',
            'Authorization',
        ],
        filter_query_parameters=[
            'api_key',
            'key',
            'apikey',
            'token',
            'access_token',
        ],
        filter_post_data_parameters=[
            'api_key',
            'key',
            'apikey',
            'token',
        ],
        # Preserve exact bytes for binary responses
        decode_compressed_response=True,
        # Serialize to YAML for readability
        serializer='yaml',
    )


# Default VCR instance
default_vcr = get_vcr_config()

