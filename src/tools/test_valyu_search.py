"""
Test suite for Valyu search functionality.

This module contains comprehensive tests for:
- ValyuSearchTool: LangChain tool wrapper for Valyu search
- valyu_search: Core utility function for Valyu API integration

Tests cover both success and error paths, with proper mocking of external dependencies.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import json
from typing import Dict, Any

# Import the tools and utilities to test
# Import directly from modules to avoid issues with missing optional dependencies
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Directly load and execute the modules to avoid __init__.py issues
import importlib.util
import types

# Create placeholder modules for the hierarchy to make patches work
src_module = types.ModuleType('src')
sys.modules['src'] = src_module

src_tools_module = types.ModuleType('src.tools')
sys.modules['src.tools'] = src_tools_module
src_module.tools = src_tools_module

# Load search_tools module
search_tools_path = os.path.join(os.path.dirname(__file__), "search_tools.py")
spec = importlib.util.spec_from_file_location("src.tools.search_tools", search_tools_path)
search_tools = importlib.util.module_from_spec(spec)
sys.modules['src.tools.search_tools'] = search_tools
src_tools_module.search_tools = search_tools
spec.loader.exec_module(search_tools)

ValyuSearchTool = search_tools.ValyuSearchTool
ValyuSearchParameters = search_tools.ValyuSearchParameters

# Load utils module
utils_path = os.path.join(os.path.dirname(__file__), "../utils.py")
utils_spec = importlib.util.spec_from_file_location("src.utils", utils_path)
utils_module = importlib.util.module_from_spec(utils_spec)
sys.modules['src.utils'] = utils_module
src_module.utils = utils_module
utils_spec.loader.exec_module(utils_module)

valyu_search = utils_module.valyu_search

# Also add the valyu_search to tools module for patching in tool tests
src_tools_module.valyu_search = valyu_search

# Create a mock valyu module to avoid import errors during patching
mock_valyu_module = types.ModuleType('valyu')
sys.modules['valyu'] = mock_valyu_module
# Add a placeholder Valyu class that will be mocked in tests
mock_valyu_module.Valyu = type('Valyu', (), {})


class MockValyuResponse:
    """Mock response object for Valyu API calls."""

    def __init__(self, success=True, results=None, error=None, total_cost_dollars=0.001, tx_id="test-tx-123"):
        self.data = {
            "success": success,
            "results": results or [],
            "error": error,
            "total_cost_dollars": total_cost_dollars,
            "tx_id": tx_id,
        }

    def get(self, key, default=None):
        """Mock dict-like get method."""
        return self.data.get(key, default)

    def __getitem__(self, key):
        """Mock dict-like indexing."""
        return self.data[key]


def create_mock_valyu_result(
    title="Test Article Title",
    url="https://example.com/article",
    content="This is test content for the article.",
    source_type="web",
    publication_date="2024-01-15T10:30:00Z",
    relevance_score=0.95,
    description="Test description",
    source="web",
    price=0.0001,
    length=1000,
    data_type="unstructured",
    result_id="test-result-123",
) -> Dict[str, Any]:
    """Create a mock Valyu search result with all expected fields.

    Args:
        title: Result title
        url: Result URL
        content: Main content text
        source_type: Specific source classification (web, paper, report, etc.)
        publication_date: ISO 8601 publication date
        relevance_score: Score between 0 and 1
        description: High-level summary
        source: High-level source category
        price: Cost in USD for this result
        length: Character count
        data_type: Data modality
        result_id: Stable identifier

    Returns:
        Dict containing all fields expected in a Valyu result
    """
    return {
        "title": title,
        "url": url,
        "content": content,
        "raw_content": content,  # For include_raw_content mode
        "description": description,
        "source": source,
        "source_type": source_type,
        "publication_date": publication_date,
        "relevance_score": relevance_score,
        "price": price,
        "length": length,
        "data_type": data_type,
        "id": result_id,
        "image_url": {},
    }


class TestValyuSearchTool(unittest.TestCase):
    """Test cases for ValyuSearchTool class."""

    def test_valyu_search_tool_creation(self):
        """Test that ValyuSearchTool is properly initialized with correct attributes."""
        tool = ValyuSearchTool()

        # Verify tool attributes
        self.assertEqual(tool.name, "valyu_search")
        self.assertIn("multi-source search", tool.description.lower())
        self.assertIn("academic", tool.description.lower())
        self.assertIn("financial", tool.description.lower())
        self.assertEqual(tool.args_schema, ValyuSearchParameters)
        self.assertIsNone(tool.config)

    def test_valyu_search_tool_parameters(self):
        """Test that ValyuSearchParameters schema defines all required parameters."""
        # Create an instance to verify field definitions
        params = ValyuSearchParameters(query="test query")

        # Verify required fields
        self.assertEqual(params.query, "test query")

        # Verify optional fields with defaults
        self.assertEqual(params.top_k, 5)
        self.assertEqual(params.search_type, "all")
        self.assertEqual(params.fast_mode, False)
        self.assertEqual(params.is_tool_call, True)
        self.assertEqual(params.response_length, "medium")

        # Test with custom values
        custom_params = ValyuSearchParameters(
            query="custom query",
            top_k=10,
            search_type="web",
            fast_mode=True,
            is_tool_call=False,
            response_length="large",
        )
        self.assertEqual(custom_params.top_k, 10)
        self.assertEqual(custom_params.search_type, "web")
        self.assertTrue(custom_params.fast_mode)
        self.assertFalse(custom_params.is_tool_call)
        self.assertEqual(custom_params.response_length, "large")

    @patch("src.utils.valyu_search")
    def test_valyu_search_tool_with_mock(self, mock_valyu_search):
        """Test ValyuSearchTool execution with mocked valyu_search function."""
        # Setup mock response
        mock_results = [
            create_mock_valyu_result(
                title="AI in Healthcare",
                url="https://example.com/ai-healthcare",
                content="Artificial intelligence is transforming healthcare delivery.",
                source_type="web",
                relevance_score=0.92,
            ),
            create_mock_valyu_result(
                title="Medical AI Research Paper",
                url="https://arxiv.org/abs/2024.12345",
                content="This paper explores deep learning applications in medical diagnosis.",
                source_type="paper",
                publication_date="2024-03-15T00:00:00Z",
                relevance_score=0.88,
            ),
        ]

        mock_response = {
            "success": True,
            "results": mock_results,
            "total_cost_dollars": 0.002,
            "tx_id": "test-tx-456",
        }
        mock_valyu_search.return_value = mock_response

        # Create tool and execute
        tool = ValyuSearchTool()
        result = tool._run(query="AI in healthcare", top_k=2)

        # Verify valyu_search was called correctly
        mock_valyu_search.assert_called_once()
        call_kwargs = mock_valyu_search.call_args[1]
        self.assertEqual(call_kwargs["query"], "AI in healthcare")
        self.assertEqual(call_kwargs["max_num_results"], 2)

        # Verify result structure
        self.assertIn("formatted_sources", result)
        self.assertIn("raw_contents", result)
        self.assertIn("search_string", result)
        self.assertIn("tools", result)
        self.assertIn("domains", result)
        self.assertIn("citations", result)

        # Verify formatted sources
        self.assertEqual(len(result["formatted_sources"]), 2)
        self.assertIn("AI in Healthcare", result["formatted_sources"][0])
        self.assertIn("https://example.com/ai-healthcare", result["formatted_sources"][0])

        # Verify tools list
        self.assertEqual(result["tools"], ["valyu_search"])

        # Verify domains extraction
        self.assertIn("example.com", result["domains"])
        self.assertIn("arxiv.org", result["domains"])

        # Verify citations
        self.assertEqual(len(result["citations"]), 2)
        self.assertEqual(result["citations"][0]["title"], "AI in Healthcare")
        self.assertEqual(result["citations"][0]["source_type"], "web")

    @patch("src.utils.valyu_search")
    def test_valyu_search_tool_error_handling(self, mock_valyu_search):
        """Test ValyuSearchTool error handling when valyu_search raises exceptions."""
        # Test with ImportError (SDK not installed)
        mock_valyu_search.side_effect = ImportError("No module named 'valyu'")

        tool = ValyuSearchTool()
        result = tool._run(query="test query")

        # Should return empty results with proper structure
        self.assertEqual(result["formatted_sources"], [])
        self.assertEqual(result["raw_contents"], [])
        self.assertEqual(result["search_string"], "test query")
        self.assertEqual(result["tools"], ["valyu_search"])
        self.assertEqual(result["domains"], [])
        self.assertEqual(result["citations"], [])

    @patch("src.utils.valyu_search")
    def test_valyu_search_tool_dict_query(self, mock_valyu_search):
        """Test ValyuSearchTool handling of dictionary query parameter."""
        mock_response = {
            "success": True,
            "results": [],
            "total_cost_dollars": 0.001,
            "tx_id": "test-tx-789",
        }
        mock_valyu_search.return_value = mock_response

        tool = ValyuSearchTool()

        # Test with dict containing 'query' key
        result = tool._run(query={"query": "extracted query"})
        call_kwargs = mock_valyu_search.call_args[1]
        self.assertEqual(call_kwargs["query"], "extracted query")

        # Test with dict containing alternative keys
        mock_valyu_search.reset_mock()
        result = tool._run(query={"search_query": "alternative query"})
        call_kwargs = mock_valyu_search.call_args[1]
        self.assertEqual(call_kwargs["query"], "alternative query")

    @patch("src.utils.valyu_search")
    def test_valyu_search_tool_return_format(self, mock_valyu_search):
        """Test that ValyuSearchTool returns standardized format matching other tools."""
        mock_response = {
            "success": True,
            "results": [
                create_mock_valyu_result(
                    title="Test",
                    url="https://test.com",
                    content="Long content " * 500,  # Create long content
                )
            ],
            "total_cost_dollars": 0.001,
            "tx_id": "test-tx-999",
        }
        mock_valyu_search.return_value = mock_response

        tool = ValyuSearchTool()
        result = tool._run(query="test")

        # Verify all required keys are present
        required_keys = ["formatted_sources", "raw_contents", "search_string", "tools", "domains", "citations"]
        for key in required_keys:
            self.assertIn(key, result, f"Missing required key: {key}")

        # Verify types
        self.assertIsInstance(result["formatted_sources"], list)
        self.assertIsInstance(result["raw_contents"], list)
        self.assertIsInstance(result["search_string"], str)
        self.assertIsInstance(result["tools"], list)
        self.assertIsInstance(result["domains"], list)
        self.assertIsInstance(result["citations"], list)

        # Verify content is limited (MAX_RAW_CONTENT_WORDS = 2000)
        if result["raw_contents"]:
            word_count = len(result["raw_contents"][0].split())
            self.assertLessEqual(word_count, 2000, "Raw content should be limited to 2000 words")


class TestValyuSearchFunction(unittest.TestCase):
    """Test cases for valyu_search utility function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_valyu_search_missing_api_key(self):
        """Test that valyu_search raises ValueError when VALYU_API_KEY is not set."""
        # Ensure API key is not in environment
        if "VALYU_API_KEY" in os.environ:
            del os.environ["VALYU_API_KEY"]

        with self.assertRaises(ValueError) as context:
            valyu_search(query="test query")

        self.assertIn("VALYU_API_KEY", str(context.exception))

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    def test_valyu_search_empty_query(self):
        """Test that valyu_search handles empty queries gracefully."""
        # Test with empty string
        result = valyu_search(query="")
        self.assertEqual(result["results"], [])
        self.assertFalse(result["success"])
        self.assertIn("Empty query", result["error"])

        # Test with whitespace only
        result = valyu_search(query="   ")
        self.assertEqual(result["results"], [])
        self.assertFalse(result["success"])
        self.assertIn("Empty query", result["error"])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_parameter_validation(self, mock_valyu_class):
        """Test valyu_search validates and sanitizes input parameters."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Setup successful mock response
        mock_client.search.return_value = {
            "success": True,
            "results": [],
            "total_cost_dollars": 0.001,
            "tx_id": "test-tx",
        }

        # Test invalid search_type (should default to 'all')
        result = valyu_search(query="test", search_type="invalid_type")
        call_kwargs = mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["search_type"], "all")

        # Test invalid response_length string (should default to 'medium')
        mock_client.search.reset_mock()
        result = valyu_search(query="test", response_length="invalid")
        call_kwargs = mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["response_length"], "medium")

        # Test invalid response_length int (should default to 'medium')
        mock_client.search.reset_mock()
        result = valyu_search(query="test", response_length=-100)
        call_kwargs = mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["response_length"], "medium")

        # Test valid search_type values
        for valid_type in ["all", "web", "proprietary"]:
            mock_client.search.reset_mock()
            result = valyu_search(query="test", search_type=valid_type)
            call_kwargs = mock_client.search.call_args[1]
            self.assertEqual(call_kwargs["search_type"], valid_type)

        # Test valid response_length values
        for valid_length in ["short", "medium", "large", "max"]:
            mock_client.search.reset_mock()
            result = valyu_search(query="test", response_length=valid_length)
            call_kwargs = mock_client.search.call_args[1]
            self.assertEqual(call_kwargs["response_length"], valid_length)

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_success(self, mock_valyu_class):
        """Test successful valyu_search API call with proper response handling."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Create mock response
        mock_results = [
            create_mock_valyu_result(
                title="Climate Change Impact",
                url="https://research.example.com/climate",
                content="Climate change is affecting global ecosystems.",
                source_type="paper",
                publication_date="2024-02-20T00:00:00Z",
                relevance_score=0.94,
            ),
            create_mock_valyu_result(
                title="Economic Effects of Climate Policy",
                url="https://finance.example.com/climate-policy",
                content="Economic analysis of climate change mitigation strategies.",
                source_type="report",
                relevance_score=0.87,
            ),
        ]

        mock_response = {
            "success": True,
            "results": mock_results,
            "total_cost_dollars": 0.003,
            "tx_id": "test-tx-success-123",
        }
        mock_client.search.return_value = mock_response

        # Execute search
        result = valyu_search(
            query="climate change impact",
            max_num_results=2,
            search_type="all",
            fast_mode=False,
            is_tool_call=True,
            response_length="medium",
            include_raw_content=True,
        )

        # Verify API was called with correct parameters
        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["query"], "climate change impact")
        self.assertEqual(call_kwargs["max_num_results"], 2)
        self.assertEqual(call_kwargs["search_type"], "all")
        self.assertFalse(call_kwargs["fast_mode"])
        self.assertTrue(call_kwargs["is_tool_call"])
        self.assertEqual(call_kwargs["response_length"], "medium")

        # Verify response structure
        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["total_cost_dollars"], 0.003)
        self.assertEqual(result["tx_id"], "test-tx-success-123")

        # Verify raw_content handling
        self.assertIsNotNone(result["results"][0]["raw_content"])
        self.assertIsNotNone(result["results"][1]["raw_content"])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_raw_content_handling(self, mock_valyu_class):
        """Test valyu_search properly handles include_raw_content parameter."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Mock response without raw_content
        mock_results = [
            {
                "title": "Test",
                "url": "https://test.com",
                "content": "Test content",
                "source_type": "web",
                "relevance_score": 0.9,
            }
        ]
        mock_response = {"success": True, "results": mock_results, "total_cost_dollars": 0.001, "tx_id": "test-tx"}
        mock_client.search.return_value = mock_response

        # Test with include_raw_content=True
        result = valyu_search(query="test", include_raw_content=True)
        self.assertEqual(result["results"][0]["raw_content"], "Test content")

        # Test with include_raw_content=False
        result = valyu_search(query="test", include_raw_content=False)
        self.assertIsNone(result["results"][0]["raw_content"])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_api_error_401(self, mock_valyu_class):
        """Test valyu_search handling of 401 authentication errors."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Create mock HTTP error with 401 status
        import requests

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_client.search.side_effect = http_error

        # Execute search (should not retry on 401)
        result = valyu_search(query="test query")

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertIn("authentication error", result["error"].lower())
        self.assertIn("Invalid API key", result["error"])
        self.assertEqual(result["results"], [])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_api_error_422(self, mock_valyu_class):
        """Test valyu_search handling of 422 validation errors."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Create mock HTTP error with 422 status
        import requests

        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Invalid query parameter"
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_client.search.side_effect = http_error

        # Execute search (should not retry on 422)
        result = valyu_search(query="test query")

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertIn("validation error", result["error"].lower())
        self.assertIn("Invalid query parameter", result["error"])
        self.assertEqual(result["results"], [])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_api_error_429(self, mock_valyu_class):
        """Test valyu_search handling of 429 rate limit errors (should retry).

        Note: This test verifies that retries are attempted. Due to the retry decorator's
        exponential backoff (up to 5 attempts), this test may take ~30 seconds to complete.
        """
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Create mock HTTP error with 429 status
        import requests

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        http_error = requests.exceptions.HTTPError(response=mock_response)

        # Set side effect to fail twice then succeed to speed up the test
        mock_client.search.side_effect = [
            http_error,
            http_error,
            {"success": True, "results": [], "total_cost_dollars": 0.001, "tx_id": "test-tx"}
        ]

        # Execute search (should retry and eventually succeed)
        result = valyu_search(query="test query")

        # Verify retry attempts were made (should have called 3 times: 2 failures + 1 success)
        self.assertEqual(mock_client.search.call_count, 3)
        self.assertTrue(result["success"])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_api_error_500(self, mock_valyu_class):
        """Test valyu_search handling of 500 server errors (should retry).

        Note: This test verifies that retries are attempted. The retry decorator will
        attempt the call multiple times before giving up.
        """
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Create mock HTTP error with 500 status
        import requests

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        http_error = requests.exceptions.HTTPError(response=mock_response)

        # Set side effect to fail once then succeed to speed up the test
        mock_client.search.side_effect = [
            http_error,
            {"success": True, "results": [], "total_cost_dollars": 0.001, "tx_id": "test-tx"}
        ]

        # Execute search (should retry and eventually succeed)
        result = valyu_search(query="test query")

        # Verify retry attempts were made (should have called 2 times: 1 failure + 1 success)
        self.assertEqual(mock_client.search.call_count, 2)
        self.assertTrue(result["success"])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    def test_valyu_search_import_error(self):
        """Test valyu_search handling when Valyu SDK is not installed."""
        # Temporarily remove the valyu module to simulate it not being installed
        saved_valyu = sys.modules.pop('valyu', None)
        try:
            result = valyu_search(query="test query")

            # Verify error response
            self.assertFalse(result["success"])
            self.assertIn("not installed", result["error"])
            self.assertIn("pip install valyu", result["error"])
            self.assertEqual(result["results"], [])
        finally:
            # Restore valyu module
            if saved_valyu:
                sys.modules['valyu'] = saved_valyu
            else:
                # Re-create the mock if it wasn't there before
                mock_valyu_module = types.ModuleType('valyu')
                sys.modules['valyu'] = mock_valyu_module
                mock_valyu_module.Valyu = type('Valyu', (), {})

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_unexpected_response_type(self, mock_valyu_class):
        """Test valyu_search handling of unexpected response types from API."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Return non-dict response
        mock_client.search.return_value = "unexpected string response"

        result = valyu_search(query="test query")

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertIn("Unexpected response type", result["error"])
        self.assertEqual(result["results"], [])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_api_returns_error(self, mock_valyu_class):
        """Test valyu_search handling when API returns success=False."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # API returns error response
        mock_response = {
            "success": False,
            "error": "Query processing failed",
            "results": [],
        }
        mock_client.search.return_value = mock_response

        result = valyu_search(query="test query")

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Query processing failed")
        self.assertEqual(result["results"], [])

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_valyu_search_with_custom_config(self, mock_valyu_class):
        """Test valyu_search with custom RunnableConfig for tracing."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        mock_response = {
            "success": True,
            "results": [],
            "total_cost_dollars": 0.001,
            "tx_id": "test-tx",
        }
        mock_client.search.return_value = mock_response

        # Create mock config
        mock_config = {"run_name": "test_run", "tags": ["test"]}

        # Execute with config (should not affect the Valyu API call)
        result = valyu_search(query="test query", config=mock_config)

        # Verify the search was successful
        self.assertTrue(result["success"])


class TestValyuSearchIntegration(unittest.TestCase):
    """Integration tests for Valyu search tool and function working together."""

    @patch.dict(os.environ, {"VALYU_API_KEY": "test-key-123"})
    @patch("valyu.Valyu")
    def test_end_to_end_search_workflow(self, mock_valyu_class):
        """Test complete workflow from tool invocation to formatted results."""
        mock_client = MagicMock()
        mock_valyu_class.return_value = mock_client

        # Create realistic mock response
        mock_results = [
            create_mock_valyu_result(
                title="Quantum Computing Breakthroughs 2024",
                url="https://research.quantum.edu/breakthroughs-2024",
                content="Recent advances in quantum computing have achieved unprecedented qubit stability.",
                source_type="paper",
                publication_date="2024-01-10T00:00:00Z",
                relevance_score=0.96,
            ),
            create_mock_valyu_result(
                title="Industry Applications of Quantum Technology",
                url="https://tech.business.com/quantum-apps",
                content="Major tech companies are investing billions in quantum computing infrastructure.",
                source_type="web",
                relevance_score=0.89,
            ),
            create_mock_valyu_result(
                title="Quantum Finance Models",
                url="https://fintech.journal.com/quantum-finance",
                content="Quantum algorithms are revolutionizing portfolio optimization and risk analysis.",
                source_type="report",
                publication_date="2023-11-15T00:00:00Z",
                relevance_score=0.85,
            ),
        ]

        mock_response = {
            "success": True,
            "results": mock_results,
            "total_cost_dollars": 0.005,
            "tx_id": "test-integration-tx-123",
        }
        mock_client.search.return_value = mock_response

        # Execute search through the tool
        tool = ValyuSearchTool()
        result = tool._run(
            query="quantum computing applications",
            top_k=3,
            search_type="all",
            fast_mode=False,
            is_tool_call=True,
            response_length="medium",
        )

        # Verify complete result structure
        self.assertEqual(len(result["formatted_sources"]), 3)
        self.assertEqual(len(result["raw_contents"]), 3)
        self.assertEqual(result["search_string"], "quantum computing applications")
        self.assertEqual(result["tools"], ["valyu_search"])

        # Verify domain extraction
        self.assertIn("research.quantum.edu", result["domains"])
        self.assertIn("tech.business.com", result["domains"])
        self.assertIn("fintech.journal.com", result["domains"])

        # Verify citations
        self.assertEqual(len(result["citations"]), 3)
        citation_titles = [c["title"] for c in result["citations"]]
        self.assertIn("Quantum Computing Breakthroughs 2024", citation_titles)
        self.assertIn("Industry Applications of Quantum Technology", citation_titles)
        self.assertIn("Quantum Finance Models", citation_titles)

        # Verify source types in citations
        source_types = [c["source_type"] for c in result["citations"]]
        self.assertIn("paper", source_types)
        self.assertIn("web", source_types)
        self.assertIn("report", source_types)

        # Verify formatted sources contain both title and URL
        for formatted_source in result["formatted_sources"]:
            self.assertIn("* ", formatted_source)
            self.assertIn(" : ", formatted_source)
            self.assertIn("http", formatted_source)


def run_tests():
    """Run all tests with verbose output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValyuSearchTool))
    suite.addTests(loader.loadTestsFromTestCase(TestValyuSearchFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestValyuSearchIntegration))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
