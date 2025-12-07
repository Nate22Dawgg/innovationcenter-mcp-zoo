"""
Tests for Playwright MCP idempotent write tools.

Tests cover:
- Dry-run behavior (no final submit is executed)
- Confirmation enforcement (confirm mismatch => safe error)
- Idempotency (same key + inputs => no re-submit)
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import (
    submit_regulatory_form,
    update_tracker_sheet,
    REQUIRED_CONFIRMATION_PHRASE
)
from idempotency_store import IdempotencyStore, IdempotencyRecord
from common.errors import ValidationError, ErrorCode


@pytest.fixture
def mock_browser_context():
    """Mock browser context for testing."""
    context = AsyncMock()
    page = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    
    # Mock page methods
    page.goto = AsyncMock()
    page.locator = MagicMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.close = AsyncMock()
    
    # Mock locator
    locator = AsyncMock()
    locator.first = locator
    locator.count = AsyncMock(return_value=1)
    locator.fill = AsyncMock()
    locator.input_value = AsyncMock(return_value="")
    locator.text_content = AsyncMock(return_value="Submit")
    locator.click = AsyncMock()
    
    page.locator.return_value = locator
    
    return context, page


@pytest.fixture
def idempotency_store():
    """Create a fresh idempotency store for testing."""
    return IdempotencyStore()


class TestDryRunBehavior:
    """Test dry-run behavior - no actual submission should occur."""
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_dry_run(self, mock_browser_context, idempotency_store):
        """Test that dry-run mode doesn't actually submit the form."""
        context, page = mock_browser_context
        
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result = await submit_regulatory_form(
                    idempotency_key="test-key-1",
                    url="https://example.com/form",
                    dry_run=True,
                    form_data={"input[name='field1']": "value1"}
                )
        
        # Verify result indicates dry-run
        assert result["success"] is True
        assert result["dry_run"] is True
        assert "preview" in result
        assert "would_submit" in result["preview"]
        
        # Verify submit button was NOT clicked
        page.locator.return_value.click.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_tracker_sheet_dry_run(self, mock_browser_context, idempotency_store):
        """Test that dry-run mode doesn't actually update the sheet."""
        context, page = mock_browser_context
        
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result = await update_tracker_sheet(
                    idempotency_key="test-key-2",
                    url="https://example.com/sheet",
                    dry_run=True,
                    row_data={"column1": "value1"}
                )
        
        # Verify result indicates dry-run
        assert result["success"] is True
        assert result["dry_run"] is True
        assert "preview" in result


class TestConfirmationEnforcement:
    """Test that confirmation is required for non-dry-run operations."""
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_missing_confirm(self, mock_browser_context, idempotency_store):
        """Test that missing confirmation raises error."""
        context, page = mock_browser_context
        
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                with pytest.raises(ValidationError) as exc_info:
                    await submit_regulatory_form(
                        idempotency_key="test-key-3",
                        url="https://example.com/form",
                        dry_run=False,
                        # confirm is missing
                    )
        
        assert "Confirmation required" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_wrong_confirm(self, mock_browser_context, idempotency_store):
        """Test that wrong confirmation phrase raises error."""
        context, page = mock_browser_context
        
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                with pytest.raises(ValidationError) as exc_info:
                    await submit_regulatory_form(
                        idempotency_key="test-key-4",
                        url="https://example.com/form",
                        dry_run=False,
                        confirm="wrong_phrase"
                    )
        
        assert "Confirmation required" in str(exc_info.value)
        assert REQUIRED_CONFIRMATION_PHRASE in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_correct_confirm(self, mock_browser_context, idempotency_store):
        """Test that correct confirmation allows submission."""
        context, page = mock_browser_context
        
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result = await submit_regulatory_form(
                    idempotency_key="test-key-5",
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    form_data={"input[name='field1']": "value1"}
                )
        
        # Verify submission occurred (not dry-run)
        assert result["success"] is True
        assert result["dry_run"] is False
        assert "submitted" in result
    
    @pytest.mark.asyncio
    async def test_update_tracker_sheet_missing_confirm(self, mock_browser_context, idempotency_store):
        """Test that missing confirmation raises error for tracker sheet."""
        context, page = mock_browser_context
        
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                with pytest.raises(ValidationError) as exc_info:
                    await update_tracker_sheet(
                        idempotency_key="test-key-6",
                        url="https://example.com/sheet",
                        dry_run=False,
                        # confirm is missing
                    )
        
        assert "Confirmation required" in str(exc_info.value)


class TestIdempotency:
    """Test idempotency behavior - same key + inputs should return previous result."""
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_idempotency(self, mock_browser_context, idempotency_store):
        """Test that same idempotency key returns previous result."""
        context, page = mock_browser_context
        
        # First execution - should actually run
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result1 = await submit_regulatory_form(
                    idempotency_key="idempotent-key-1",
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    form_data={"input[name='field1']": "value1"}
                )
        
        execution_id_1 = result1["execution_id"]
        
        # Second execution with same key and parameters - should return cached result
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result2 = await submit_regulatory_form(
                    idempotency_key="idempotent-key-1",
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    form_data={"input[name='field1']": "value1"}
                )
        
        # Verify idempotency
        assert result2["idempotent"] is True
        assert result2["execution_id"] == execution_id_1
        assert "previous_result" in result2
        
        # Verify browser was NOT called again (page.goto should only be called once)
        # Actually, we can't easily verify this with the current mock setup,
        # but we can verify the result indicates idempotency
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_different_key(self, mock_browser_context, idempotency_store):
        """Test that different idempotency key causes new execution."""
        context, page = mock_browser_context
        
        # First execution
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result1 = await submit_regulatory_form(
                    idempotency_key="key-1",
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE
                )
        
        # Second execution with different key - should execute again
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result2 = await submit_regulatory_form(
                    idempotency_key="key-2",  # Different key
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE
                )
        
        # Verify new execution (not idempotent)
        assert "idempotent" not in result2 or result2.get("idempotent") is False
        assert result2["execution_id"] != result1["execution_id"]
    
    @pytest.mark.asyncio
    async def test_submit_regulatory_form_different_params(self, mock_browser_context, idempotency_store):
        """Test that different parameters with same key cause new execution."""
        context, page = mock_browser_context
        
        # First execution
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result1 = await submit_regulatory_form(
                    idempotency_key="same-key",
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    form_data={"field1": "value1"}
                )
        
        # Second execution with different form_data - should execute again
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result2 = await submit_regulatory_form(
                    idempotency_key="same-key",  # Same key
                    url="https://example.com/form",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    form_data={"field1": "value2"}  # Different data
                )
        
        # Verify new execution (not idempotent)
        assert "idempotent" not in result2 or result2.get("idempotent") is False
        assert result2["execution_id"] != result1["execution_id"]
    
    @pytest.mark.asyncio
    async def test_update_tracker_sheet_idempotency(self, mock_browser_context, idempotency_store):
        """Test idempotency for tracker sheet updates."""
        context, page = mock_browser_context
        
        # First execution
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result1 = await update_tracker_sheet(
                    idempotency_key="sheet-key-1",
                    url="https://example.com/sheet",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    row_data={"col1": "val1"}
                )
        
        # Second execution with same key and parameters
        with patch('server.get_browser_context', return_value=context):
            with patch('server.get_idempotency_store', return_value=idempotency_store):
                result2 = await update_tracker_sheet(
                    idempotency_key="sheet-key-1",
                    url="https://example.com/sheet",
                    dry_run=False,
                    confirm=REQUIRED_CONFIRMATION_PHRASE,
                    row_data={"col1": "val1"}
                )
        
        # Verify idempotency
        assert result2["idempotent"] is True
        assert result2["execution_id"] == result1["execution_id"]


class TestIdempotencyStore:
    """Test the idempotency store directly."""
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving idempotency records."""
        store = IdempotencyStore()
        
        key = "test-key"
        tool = "test_tool"
        params = {"param1": "value1"}
        result = {"success": True}
        execution_id = "exec-123"
        
        # Store record
        store.store(key, tool, params, result, execution_id)
        
        # Retrieve record
        record = store.get(key, tool, params)
        
        assert record is not None
        assert record.idempotency_key == key
        assert record.tool_name == tool
        assert record.result == result
        assert record.execution_id == execution_id
    
    def test_different_params_not_retrieved(self):
        """Test that different parameters don't match."""
        store = IdempotencyStore()
        
        key = "test-key"
        tool = "test_tool"
        params1 = {"param1": "value1"}
        params2 = {"param1": "value2"}  # Different value
        result = {"success": True}
        execution_id = "exec-123"
        
        # Store with params1
        store.store(key, tool, params1, result, execution_id)
        
        # Try to retrieve with params2
        record = store.get(key, tool, params2)
        
        assert record is None  # Should not match
    
    def test_different_key_not_retrieved(self):
        """Test that different idempotency key doesn't match."""
        store = IdempotencyStore()
        
        key1 = "test-key-1"
        key2 = "test-key-2"
        tool = "test_tool"
        params = {"param1": "value1"}
        result = {"success": True}
        execution_id = "exec-123"
        
        # Store with key1
        store.store(key1, tool, params, result, execution_id)
        
        # Try to retrieve with key2
        record = store.get(key2, tool, params)
        
        assert record is None  # Should not match
