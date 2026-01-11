"""
Unit tests for common.identifiers module.

Tests identifier normalization functions for:
- Tickers
- CIKs
- NCT IDs
- CPT codes
- HCPCS codes
- NPI
- Addresses
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.identifiers import (
    normalize_ticker,
    normalize_cik,
    normalize_nct_id,
    normalize_cpt_code,
    normalize_hcpcs_code,
    normalize_npi,
    normalize_address
)


class TestNormalizeTicker:
    """Tests for normalize_ticker function."""
    
    def test_basic_uppercase(self):
        """Test basic uppercase conversion."""
        assert normalize_ticker("aapl") == "AAPL"
        assert normalize_ticker("msft") == "MSFT"
        assert normalize_ticker("MRNA") == "MRNA"
    
    def test_whitespace_stripping(self):
        """Test whitespace stripping."""
        assert normalize_ticker(" AAPL ") == "AAPL"
        assert normalize_ticker("  MSFT  ") == "MSFT"
        assert normalize_ticker("\tBRK.B\n") == "BRK.B"
    
    def test_special_characters(self):
        """Test tickers with special characters."""
        assert normalize_ticker("brk.b") == "BRK.B"
        assert normalize_ticker("brk-a") == "BRK-A"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_ticker("") == ""
        assert normalize_ticker("   ") == ""
    
    def test_mixed_case(self):
        """Test mixed case conversion."""
        assert normalize_ticker("ApPl") == "AAPL"
        assert normalize_ticker("mSrN") == "MSRN"


class TestNormalizeCIK:
    """Tests for normalize_cik function."""
    
    def test_basic_zero_padding(self):
        """Test basic zero-padding to 10 digits."""
        assert normalize_cik("320193") == "0000320193"
        assert normalize_cik("789019") == "0000789019"
    
    def test_already_padded(self):
        """Test CIK that's already 10 digits."""
        assert normalize_cik("0000320193") == "0000320193"
        assert normalize_cik("0000789019") == "0000789019"
    
    def test_integer_input(self):
        """Test integer input."""
        assert normalize_cik(320193) == "0000320193"
        assert normalize_cik(789019) == "0000789019"
    
    def test_whitespace_stripping(self):
        """Test whitespace stripping."""
        assert normalize_cik(" 320193 ") == "0000320193"
        assert normalize_cik("\t789019\n") == "0000789019"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_cik("") == ""
        assert normalize_cik(None) == ""
    
    def test_single_digit(self):
        """Test single digit CIK."""
        assert normalize_cik("1") == "0000000001"
        assert normalize_cik(1) == "0000000001"
    
    def test_non_numeric_string(self):
        """Test non-numeric string (should return as-is)."""
        result = normalize_cik("ABC123")
        assert result == "ABC123"  # Returns as-is if not fully numeric


class TestNormalizeNCTID:
    """Tests for normalize_nct_id function."""
    
    def test_basic_formatting(self):
        """Test basic NCT ID formatting."""
        assert normalize_nct_id("nct01234567") == "NCT01234567"
        assert normalize_nct_id("NCT01234567") == "NCT01234567"
    
    def test_whitespace_removal(self):
        """Test whitespace removal."""
        assert normalize_nct_id("NCT 01234567") == "NCT01234567"
        assert normalize_nct_id("  NCT01234567  ") == "NCT01234567"
    
    def test_uppercase_conversion(self):
        """Test uppercase conversion."""
        assert normalize_nct_id("nct01234567") == "NCT01234567"
        assert normalize_nct_id("Nct01234567") == "NCT01234567"
    
    def test_padding_digits(self):
        """Test padding to 8 digits."""
        assert normalize_nct_id("NCT123") == "NCT00000123"
        assert normalize_nct_id("NCT1") == "NCT00000001"
    
    def test_truncating_digits(self):
        """Test truncating if more than 8 digits."""
        assert normalize_nct_id("NCT0123456789") == "NCT01234567"
    
    def test_digits_only(self):
        """Test digits-only input (should add NCT prefix)."""
        assert normalize_nct_id("01234567") == "NCT01234567"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_nct_id("") == ""
    
    def test_malformed(self):
        """Test malformed input (should return as-is)."""
        result = normalize_nct_id("INVALID123")
        assert result.startswith("INVALID")  # Returns as-is if malformed


class TestNormalizeCPTCode:
    """Tests for normalize_cpt_code function."""
    
    def test_basic_formatting(self):
        """Test basic CPT code formatting."""
        assert normalize_cpt_code("99213") == "99213"
        assert normalize_cpt_code("99214") == "99214"
    
    def test_whitespace_stripping(self):
        """Test whitespace stripping."""
        assert normalize_cpt_code(" 99213 ") == "99213"
        assert normalize_cpt_code("\t99214\n") == "99214"
    
    def test_modifier_removal(self):
        """Test modifier removal."""
        assert normalize_cpt_code("99213-25") == "99213"
        assert normalize_cpt_code("99214-59") == "99214"
        assert normalize_cpt_code("99213-25-59") == "99213"
    
    def test_padding(self):
        """Test padding to 5 digits."""
        assert normalize_cpt_code("123") == "00123"
        assert normalize_cpt_code("1") == "00001"
    
    def test_truncating(self):
        """Test truncating if more than 5 digits."""
        assert normalize_cpt_code("123456") == "12345"
    
    def test_non_numeric_removal(self):
        """Test removal of non-numeric characters."""
        assert normalize_cpt_code("99213-ABC") == "99213"
        assert normalize_cpt_code("99-213") == "99213"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_cpt_code("") == "00000"


class TestNormalizeHCPCSCode:
    """Tests for normalize_hcpcs_code function."""
    
    def test_basic_formatting(self):
        """Test basic HCPCS code formatting."""
        assert normalize_hcpcs_code("A0425") == "A0425"
        assert normalize_hcpcs_code("J1234") == "J1234"
    
    def test_uppercase_conversion(self):
        """Test uppercase conversion."""
        assert normalize_hcpcs_code("a0425") == "A0425"
        assert normalize_hcpcs_code("j1234") == "J1234"
    
    def test_whitespace_stripping(self):
        """Test whitespace stripping."""
        assert normalize_hcpcs_code(" A0425 ") == "A0425"
        assert normalize_hcpcs_code("\tJ1234\n") == "J1234"
    
    def test_modifier_removal(self):
        """Test modifier removal."""
        assert normalize_hcpcs_code("A0425-25") == "A0425"
        assert normalize_hcpcs_code("J1234-59") == "J1234"
    
    def test_padding(self):
        """Test padding to 5 characters."""
        assert normalize_hcpcs_code("A42") == "A4200"
        assert normalize_hcpcs_code("A") == "A0000"
    
    def test_truncating(self):
        """Test truncating if more than 5 characters."""
        assert normalize_hcpcs_code("A04256") == "A0425"
    
    def test_non_alphanumeric_removal(self):
        """Test removal of non-alphanumeric characters."""
        assert normalize_hcpcs_code("A-0425") == "A0425"
        assert normalize_hcpcs_code("A 0425") == "A0425"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_hcpcs_code("") == "00000"


class TestNormalizeNPI:
    """Tests for normalize_npi function."""
    
    def test_basic_formatting(self):
        """Test basic NPI formatting."""
        assert normalize_npi("1234567890") == "1234567890"
        assert normalize_npi(1234567890) == "1234567890"
    
    def test_hyphen_removal(self):
        """Test hyphen removal."""
        assert normalize_npi("123-456-7890") == "1234567890"
        assert normalize_npi("123-45-6789") == "1234567890"
    
    def test_whitespace_removal(self):
        """Test whitespace removal."""
        assert normalize_npi("123 456 7890") == "1234567890"
        assert normalize_npi(" 1234567890 ") == "1234567890"
    
    def test_padding(self):
        """Test padding to 10 digits."""
        assert normalize_npi("123456") == "0000123456"
        assert normalize_npi("1") == "0000000001"
    
    def test_truncating(self):
        """Test truncating if more than 10 digits."""
        assert normalize_npi("1234567890123") == "1234567890"
    
    def test_integer_input(self):
        """Test integer input."""
        assert normalize_npi(1234567890) == "1234567890"
        assert normalize_npi(123456) == "0000123456"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_npi("") == "0000000000"
        assert normalize_npi(None) == "0000000000"
    
    def test_non_numeric_removal(self):
        """Test removal of non-numeric characters."""
        assert normalize_npi("123-456-7890") == "1234567890"
        assert normalize_npi("123 ABC 456") == "1234567890"


class TestNormalizeAddress:
    """Tests for normalize_address function."""
    
    def test_dictionary_input(self):
        """Test dictionary input."""
        address = {
            "street": "123 Main St",
            "city": "Boston",
            "state": "ma",
            "zip": "02115"
        }
        result = normalize_address(address)
        assert result["street"] == "123 Main St"
        assert result["city"] == "Boston"
        assert result["state"] == "MA"  # Uppercased
        assert result["zip_code"] == "02115"
    
    def test_state_uppercase(self):
        """Test state code uppercasing."""
        address = {"state": "ca"}
        result = normalize_address(address)
        assert result["state"] == "CA"
    
    def test_zip_code_normalization(self):
        """Test ZIP code normalization."""
        address = {"zip": "02115-1234"}
        result = normalize_address(address)
        assert result["zip_code"] == "02115-1234"
        
        address2 = {"zip": "2115"}
        result2 = normalize_address(address2)
        assert result2["zip_code"] == "02115"  # Padded
    
    def test_field_name_aliases(self):
        """Test field name aliases."""
        address = {
            "street_address": "123 Main St",
            "state_code": "MA",
            "postal_code": "02115"
        }
        result = normalize_address(address)
        assert result["street"] == "123 Main St"
        assert result["state"] == "MA"
        assert result["zip_code"] == "02115"
    
    def test_string_input(self):
        """Test string input (simplified handling)."""
        result = normalize_address("123 Main St, Boston, MA 02115")
        assert result["street"] == "123 Main St, Boston, MA 02115"
        assert result["city"] is None
    
    def test_empty_input(self):
        """Test empty input."""
        result = normalize_address(None)
        assert result["street"] is None
        assert result["city"] is None
        assert result["state"] is None
        assert result["zip_code"] is None
    
    def test_empty_string_values(self):
        """Test empty string values converted to None."""
        address = {
            "street": "",
            "city": "Boston",
            "state": "",
            "zip_code": ""
        }
        result = normalize_address(address)
        assert result["street"] is None
        assert result["city"] == "Boston"
        assert result["state"] is None
        assert result["zip_code"] is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_none_values(self):
        """Test None value handling."""
        assert normalize_ticker(None) == ""
        assert normalize_cik(None) == ""
        assert normalize_nct_id(None) == ""
        assert normalize_cpt_code(None) == "00000"
        assert normalize_hcpcs_code(None) == "00000"
        assert normalize_npi(None) == "0000000000"
    
    def test_very_long_strings(self):
        """Test very long input strings."""
        long_ticker = "A" * 100
        assert len(normalize_ticker(long_ticker)) == 100  # No truncation for tickers
        
        long_cik = "1" * 20
        result = normalize_cik(long_cik)
        assert len(result) == 20  # May not truncate if non-numeric
    
    def test_special_characters(self):
        """Test special character handling."""
        assert normalize_ticker("BRK.B") == "BRK.B"
        assert normalize_ticker("BRK-A") == "BRK-A"
    
    def test_unicode_characters(self):
        """Test Unicode character handling."""
        # Should handle Unicode gracefully
        result = normalize_ticker("AAPL\u00A0")  # Non-breaking space
        assert result == "AAPL"  # Stripped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
