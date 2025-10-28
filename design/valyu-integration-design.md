# Valyu DeepSearch API Integration - Architecture Design Specification

## Executive Summary

This document provides the complete architectural design for integrating Valyu DeepSearch API into the Enterprise Deep Research system. The integration follows existing patterns established by `GeneralSearchTool`, `AcademicSearchTool`, `GithubSearchTool`, and `LinkedinSearchTool` while leveraging Valyu's unique capabilities for AI-ready search results.

## 1. Overview

### 1.1 Integration Goals

- Add Valyu DeepSearch as a new search tool option alongside existing Tavily-based tools
- Maintain consistency with existing LangChain tool patterns
- Leverage Valyu's unique features: multi-source search, AI-optimized results, and proprietary datasets
- Provide standardized output format compatible with the existing research pipeline

### 1.2 Key Differentiators from Existing Tools

| Feature | Existing Tools (Tavily) | Valyu DeepSearch |
|---------|------------------------|------------------|
| Data Sources | Web search only | Web + Academic + Financial + Proprietary |
| Result Format | Title, URL, content, raw_content | AI-ready with relevance scores, source types, publication dates |
| Optimization | Basic scoring | `is_tool_call` for AI agent vs user queries |
| Performance | Standard | `fast_mode` for reduced latency |
| Content Control | Fixed format | `response_length` ("short", "medium", "large", "max", or int) |
| Search Types | Single mode | "all", "web", "proprietary" |
| Source Types | Generic | 11 specialized types (paper, data, report, clinical_trial, etc.) |

## 2. Architecture Components

### 2.1 ValyuSearchTool Class

**Location:** `C:\Users\Flare\Desktop\Projects\enterpirse-deepsearch\src\tools\search_tools.py`

#### Class Definition

```python
class ValyuSearchParameters(BaseModel):
    """Parameters for Valyu search tool."""

    query: str = Field(..., description="The search query to execute")
    top_k: Optional[int] = Field(5, description="Number of results to return")
    search_type: Optional[str] = Field(
        "all",
        description="Search type: 'all' (web+proprietary), 'web' (web only), or 'proprietary' (research/financial only)"
    )
    fast_mode: Optional[bool] = Field(
        False,
        description="Enable fast mode for reduced latency with shorter results"
    )
    is_tool_call: Optional[bool] = Field(
        True,
        description="Set to True for AI agent queries, False for user queries (optimizes retrieval)"
    )
    response_length: Optional[Union[str, int]] = Field(
        "medium",
        description="Response length: 'short' (~25k chars), 'medium' (~50k), 'large' (~100k), 'max' (full), or custom int"
    )


class ValyuSearchTool(BaseTool):
    """Tool for Valyu DeepSearch - AI-ready multi-source search.

    Searches across web, academic, financial, and proprietary data sources
    using Valyu's DeepSearch API. Returns AI-ready results optimized for
    RAG pipelines and agent workflows.

    Features:
    - Multi-source search (web + academic + financial + proprietary datasets)
    - AI-optimized results with is_tool_call parameter
    - Fast mode for reduced latency
    - Configurable response length
    - Rich metadata (relevance scores, publication dates, source types)
    """

    name: str = "valyu_search"
    description: str = (
        "AI-ready multi-source search across web, academic papers, financial data, "
        "and proprietary datasets. Best for comprehensive research requiring multiple "
        "authoritative sources. Returns results with relevance scores and rich metadata."
    )
    args_schema: Type[BaseModel] = ValyuSearchParameters
    config: Optional[Dict] = None

    def _run(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "all",
        fast_mode: bool = False,
        is_tool_call: bool = True,
        response_length: Union[str, int] = "medium"
    ) -> Dict[str, Any]:
        """Execute a Valyu DeepSearch query.

        Args:
            query: Search query string
            top_k: Maximum number of results to return (default: 5)
            search_type: "all", "web", or "proprietary" (default: "all")
            fast_mode: Enable for faster results with shorter content (default: False)
            is_tool_call: True for AI agent queries, False for user queries (default: True)
            response_length: "short", "medium", "large", "max", or int (default: "medium")

        Returns:
            Dict containing:
                - formatted_sources: List of formatted source strings ("* Title : URL")
                - raw_contents: List of content strings (limited to MAX_RAW_CONTENT_WORDS)
                - search_string: The processed query string
                - tools: List containing ["valyu_search"]
                - domains: List of unique domains from results
                - citations: List of citation dicts with title, url, author, year, source_type
        """
        logger.info(
            f"[ValyuSearchTool._run] Executing Valyu search for query: {query}"
        )
        logger.info(
            f"[ValyuSearchTool._run] Parameters: query={query}, top_k={top_k}, "
            f"search_type={search_type}, fast_mode={fast_mode}, is_tool_call={is_tool_call}, "
            f"response_length={response_length}, config_type={type(self.config).__name__ if self.config else 'None'}"
        )

        try:
            # Handle case where query is a dictionary (extract the actual query string)
            if isinstance(query, dict):
                search_query = query.get("query", "")
                if not search_query:
                    # Try other common keys that might contain the query
                    for key in ["search_query", "text", "question", "input"]:
                        if key in query and query[key]:
                            search_query = query[key]
                            break

                    # If still no query found, use the whole dict as context
                    if not search_query:
                        search_query = str(query)

                logger.info(
                    f"[ValyuSearchTool._run] Extracted query string from dict: {search_query}"
                )
            else:
                search_query = query

            # Try to import the real search module if available
            try:
                from src.utils import valyu_search

                logger.info(
                    f"[ValyuSearchTool._run] Successfully imported valyu_search from src.utils"
                )

                # Execute the search with the real implementation
                logger.info(
                    f"[ValyuSearchTool._run] Calling valyu_search with query: {search_query}"
                )
                search_results = valyu_search(
                    query=search_query,
                    max_num_results=top_k,
                    search_type=search_type,
                    fast_mode=fast_mode,
                    is_tool_call=is_tool_call,
                    response_length=response_length,
                    config=self.config,
                )

                logger.info(
                    f"[ValyuSearchTool._run] valyu_search returned {len(search_results.get('results', []))} results"
                )

                # Format the results and extract raw content
                formatted_sources = []
                raw_contents = []
                citations = []
                domains = []

                if "results" in search_results:
                    from urllib.parse import urlparse

                    for res in search_results["results"]:
                        title = res.get("title", "Untitled") or "Untitled"
                        url = res.get("url", "No URL") or "No URL"
                        content = res.get("content", "") or ""
                        source_type = res.get("source_type", "unknown")
                        publication_date = res.get("publication_date", "")

                        # Format source string
                        formatted_sources.append(f"* {title} : {url}")

                        # Extract and limit raw content to MAX_RAW_CONTENT_WORDS
                        if content:
                            words = content.split()
                            if len(words) > MAX_RAW_CONTENT_WORDS:
                                content = " ".join(words[:MAX_RAW_CONTENT_WORDS])
                            raw_contents.append(content)

                        # Extract domain
                        if url and url != "No URL":
                            parsed_url = urlparse(url)
                            domain = parsed_url.netloc
                            if domain and domain not in domains:
                                domains.append(domain)

                        # Build citation info (more detailed than other tools)
                        citation_info = {
                            "title": title,
                            "url": url,
                            "source_type": source_type,
                            "publication_date": publication_date,
                        }

                        # For academic papers, try to extract author info
                        if source_type == "paper" and content:
                            from src.utils import extract_author_and_year_from_content
                            first_author, year = extract_author_and_year_from_content(
                                str(title), str(content), str(url)
                            )
                            citation_info["author"] = first_author
                            citation_info["year"] = year or publication_date[:4] if publication_date else None

                        citations.append(citation_info)

                logger.info(
                    f"[ValyuSearchTool._run] Formatted {len(formatted_sources)} sources, "
                    f"extracted {len(raw_contents)} raw contents, and {len(domains)} domains"
                )

                result = {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_query,
                    "tools": ["valyu_search"],
                    "domains": domains,
                    "citations": citations,
                }

                logger.info(
                    f"[ValyuSearchTool._run] Returning result with keys: {list(result.keys())}"
                )
                return result

            except ImportError as ie:
                # Use mock implementation for testing
                logger.warning(f"[ValyuSearchTool._run] ImportError: {str(ie)}")
                logger.info(
                    f"[ValyuSearchTool._run] Using mock search implementation for: {search_query}"
                )
                formatted_sources, search_str, selected_tool, domains = (
                    mock_search_tool(
                        search_query,
                        index=0,
                        state=None,
                        config=self.config,
                        selected_tool="valyu_search",
                    )
                )

                # Mock search doesn't provide raw content
                raw_contents = []

                result = {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_str,
                    "tools": ["valyu_search"],
                    "domains": domains,
                    "citations": [],
                }
                logger.info(
                    f"[ValyuSearchTool._run] Returning result from mock search with keys: {list(result.keys())}"
                )
                return result

        except Exception as e:
            logger.error(f"[ValyuSearchTool._run] Error in Valyu search: {str(e)}")
            logger.error(
                f"[ValyuSearchTool._run] Traceback: {traceback.format_exc()}"
            )
            # Return empty results on error
            return {
                "formatted_sources": [],
                "raw_contents": [],
                "search_string": str(query),
                "tools": ["valyu_search"],
                "domains": [],
                "citations": [],
            }
```

### 2.2 valyu_search() Utility Function

**Location:** `C:\Users\Flare\Desktop\Projects\enterpirse-deepsearch\src\utils.py`

#### Function Signature

```python
@traceable
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(requests.exceptions.HTTPError),
)
def valyu_search(
    query: str,
    max_num_results: int = 5,
    search_type: str = "all",
    fast_mode: bool = False,
    is_tool_call: bool = True,
    response_length: Union[str, int] = "medium",
    config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Search using Valyu DeepSearch API.

    Searches across Valyu's comprehensive knowledge base including web content,
    academic journals, financial data, and proprietary datasets. Returns AI-ready
    search results optimized for RAG pipelines and agent workflows.

    Args:
        query: The search query to execute
        max_num_results: Maximum number of results to return (default: 5)
        search_type: Type of search to perform (default: "all")
            - "all": Search web and proprietary sources
            - "web": Web search only
            - "proprietary": Research, financial, and premium sources only
        fast_mode: Enable fast mode for reduced latency (default: False)
        is_tool_call: Optimize for AI agent (True) vs user (False) queries (default: True)
        response_length: Control content length per result (default: "medium")
            - "short": ~25,000 characters per result
            - "medium": ~50,000 characters per result
            - "large": ~100,000 characters per result
            - "max": Full content available
            - int: Custom character limit
        config: Optional configuration for LangSmith tracing

    Returns:
        dict: Search response containing:
            - success (bool): Whether the search completed successfully
            - error (str): Error message if any (empty on success)
            - tx_id (str): Transaction ID for tracing
            - query (str): The processed search query
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the document/article
                - url (str): Canonical URL for the result
                - content (str): Extracted text content (trimmed by response_length)
                - description (str): High-level summary
                - source (str): High-level source category ("web", "academic", etc.)
                - price (float): Cost in USD for this result
                - length (int): Character count of this result
                - data_type (str): Data modality (e.g., "unstructured")
                - source_type (str): Specific source classification (see Valyu docs)
                - publication_date (str): ISO 8601 publication date when available
                - id (str): Stable identifier or canonical reference
                - image_url (dict): Images extracted from the page
                - relevance_score (float): Ranking score between 0 and 1
            - results_by_source (dict): Count of results per source type
            - total_results (int): Total number of matches available
            - total_cost_dollars (float): Total cost of the request
            - total_characters (int): Combined character count across all results
            - fast_mode (bool): Present if query ran in fast mode

    Raises:
        ValueError: If VALYU_API_KEY environment variable is not set
        requests.exceptions.HTTPError: On API errors (with retry logic)

    Example:
        >>> results = valyu_search(
        ...     query="quantum computing breakthroughs 2024",
        ...     max_num_results=5,
        ...     search_type="all",
        ...     is_tool_call=True,
        ...     response_length="medium"
        ... )
        >>> for result in results["results"]:
        ...     print(f"{result['title']} - {result['source_type']}")
    """

    # Validate API key
    api_key = os.getenv("VALYU_API_KEY")
    if not api_key:
        raise ValueError("VALYU_API_KEY environment variable is not set")

    # Validate and sanitize query
    query = query.strip()
    if not query:
        logger.error("Empty query after stripping whitespace")
        return {
            "success": False,
            "error": "Empty query provided",
            "results": [],
            "query": "",
            "total_results": 0,
        }

    # Validate search_type
    valid_search_types = ["all", "web", "proprietary"]
    if search_type not in valid_search_types:
        logger.warning(
            f"Invalid search_type '{search_type}', defaulting to 'all'. "
            f"Valid options: {valid_search_types}"
        )
        search_type = "all"

    # Validate response_length
    if isinstance(response_length, str):
        valid_lengths = ["short", "medium", "large", "max"]
        if response_length not in valid_lengths:
            logger.warning(
                f"Invalid response_length '{response_length}', defaulting to 'medium'. "
                f"Valid options: {valid_lengths} or custom int"
            )
            response_length = "medium"
    elif isinstance(response_length, int):
        if response_length <= 0:
            logger.warning(
                f"Invalid response_length {response_length}, must be positive. "
                f"Defaulting to 'medium'"
            )
            response_length = "medium"
    else:
        logger.warning(
            f"Invalid response_length type {type(response_length)}, defaulting to 'medium'"
        )
        response_length = "medium"

    # Log parameters for debugging
    search_params = {
        "query": query,
        "max_num_results": max_num_results,
        "search_type": search_type,
        "fast_mode": fast_mode,
        "is_tool_call": is_tool_call,
        "response_length": response_length,
    }
    logger.info(f"Valyu search parameters:\n{json.dumps(search_params, indent=2)}")

    try:
        # Initialize Valyu client
        from valyu import Valyu

        valyu_client = Valyu(api_key=api_key)

        # Execute search
        logger.info(f"Executing Valyu search for query: {query}")
        response = valyu_client.search(
            query=query,
            max_num_results=max_num_results,
            search_type=search_type,
            fast_mode=fast_mode,
            is_tool_call=is_tool_call,
            response_length=response_length,
        )

        # Validate response structure
        if not isinstance(response, dict):
            logger.error(f"Unexpected response type from Valyu API: {type(response)}")
            return {
                "success": False,
                "error": f"Unexpected response type: {type(response)}",
                "results": [],
                "query": query,
                "total_results": 0,
            }

        # Check for success
        if not response.get("success", False):
            error_msg = response.get("error", "Unknown error from Valyu API")
            logger.error(f"Valyu API returned error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "results": [],
                "query": query,
                "total_results": 0,
            }

        # Log successful response
        num_results = len(response.get("results", []))
        total_cost = response.get("total_cost_dollars", 0)
        logger.info(
            f"Valyu search successful: {num_results} results, "
            f"cost: ${total_cost:.4f}, "
            f"tx_id: {response.get('tx_id', 'N/A')}"
        )

        return response

    except ImportError as e:
        error_msg = (
            "Valyu Python SDK not installed. "
            "Install with: pip install valyu"
        )
        logger.error(f"{error_msg} - {str(e)}")
        return {
            "success": False,
            "error": error_msg,
            "results": [],
            "query": query,
            "total_results": 0,
        }

    except requests.exceptions.HTTPError as e:
        # Handle specific HTTP error codes
        status_code = e.response.status_code if hasattr(e, 'response') else None

        if status_code == 401:
            error_msg = "Valyu API authentication error: Invalid API key"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "results": [],
                "query": query,
                "total_results": 0,
            }
        elif status_code == 422:
            error_msg = f"Valyu API validation error: {e.response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "results": [],
                "query": query,
                "total_results": 0,
            }
        elif status_code == 429:
            logger.warning(f"Valyu API rate limit exceeded. Retrying...")
            raise  # Re-raise to trigger retry
        else:
            logger.warning(f"Valyu API HTTP error {status_code}. Retrying...")
            raise  # Re-raise to trigger retry

    except Exception as e:
        error_msg = f"Unexpected error in Valyu search: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": error_msg,
            "results": [],
            "query": query,
            "total_results": 0,
        }
```

## 3. Error Handling Strategy

### 3.1 Error Categories and Responses

| Error Type | HTTP Code | Retry? | Response Action |
|------------|-----------|--------|-----------------|
| Missing API Key | N/A | No | Raise ValueError immediately |
| Invalid API Key | 401 | No | Return empty results with error message |
| Validation Error | 422 | No | Return empty results with error details |
| Rate Limit | 429 | Yes | Exponential backoff (2s, 4s, 8s, 16s, 32s, 60s max) |
| Server Error | 500-599 | Yes | Exponential backoff, max 5 attempts |
| Network Error | N/A | Yes | Exponential backoff, max 5 attempts |
| SDK Import Error | N/A | No | Return error message with installation instructions |
| Unexpected Error | N/A | No | Log full traceback, return empty results |

### 3.2 Error Response Format

All error responses follow this standardized format:

```python
{
    "success": False,
    "error": "Human-readable error message",
    "results": [],
    "query": original_query,
    "total_results": 0,
    # Optional fields preserved if available:
    # "tx_id", "total_cost_dollars", etc.
}
```

### 3.3 Logging Strategy

- **INFO level**: Normal operations, parameter logging, successful responses
- **WARNING level**: Retryable errors, invalid parameters (auto-corrected)
- **ERROR level**: Non-retryable errors, failures after max retries

## 4. Dependencies

### 4.1 Required Package

Add to `requirements.txt`:

```
valyu>=0.1.0
```

**Note**: Based on the API documentation showing `from valyu import Valyu`, the package name is `valyu`. The exact version constraint should be confirmed when the package is available on PyPI.

### 4.2 Installation Command

```bash
pip install valyu
```

### 4.3 Environment Variables

Required:
- `VALYU_API_KEY`: Valyu API authentication key

Optional (for tracing):
- `LANGSMITH_API_KEY`: For LangSmith tracing integration

## 5. Integration Points with Existing Codebase

### 5.1 Tool Registration

The `ValyuSearchTool` must be registered in the tool selection logic where other search tools are registered. This typically occurs in:
- Agent initialization code
- Tool factory/builder patterns
- Configuration files that list available tools

### 5.2 Shared Utilities

The integration leverages these existing utilities from `src/utils.py`:

1. **`extract_author_and_year_from_content()`** - For academic paper citations
2. **`MAX_RAW_CONTENT_WORDS`** constant (2000 words) - For content limiting
3. **Logging configuration** - Uses existing logger setup
4. **Retry decorators** - Uses `@traceable` and `@retry` patterns
5. **URL parsing** - Uses `urllib.parse.urlparse()` for domain extraction

### 5.3 Response Format Compatibility

The tool returns the exact same format as existing search tools:

```python
{
    "formatted_sources": List[str],      # "* Title : URL" format
    "raw_contents": List[str],           # Limited to MAX_RAW_CONTENT_WORDS
    "search_string": str,                # The processed query
    "tools": List[str],                  # ["valyu_search"]
    "domains": List[str],                # Unique domains from results
    "citations": List[Dict[str, Any]],   # Citation metadata
}
```

## 6. Usage Examples

### 6.1 Basic Usage (matches existing tools)

```python
from src.tools.search_tools import ValyuSearchTool

# Initialize tool
valyu_tool = ValyuSearchTool()

# Execute search
results = valyu_tool._run(
    query="quantum computing breakthroughs 2024",
    top_k=5
)

# Access results
for source in results["formatted_sources"]:
    print(source)
```

### 6.2 Advanced Usage (leveraging Valyu features)

```python
# AI agent query with proprietary data sources
results = valyu_tool._run(
    query="SEC filings for tech companies Q4 2024",
    top_k=10,
    search_type="proprietary",  # Research + financial sources only
    is_tool_call=True,           # Optimized for AI processing
    response_length="large"      # More content per result
)

# Fast mode for quick overview
results = valyu_tool._run(
    query="current market trends",
    top_k=3,
    fast_mode=True,              # Reduced latency
    response_length="short"      # Shorter snippets
)

# Academic research with full content
results = valyu_tool._run(
    query="machine learning papers 2024",
    top_k=5,
    search_type="proprietary",   # Access academic datasets
    response_length="max"        # Full paper content
)
```

### 6.3 Comparison with Existing Tools

```python
# General search (Tavily) - basic web search
general_tool = GeneralSearchTool()
general_results = general_tool._run(
    query="quantum computing",
    top_k=5
)
# Returns: Web results only, basic scoring

# Academic search (Tavily) - domain-filtered web search
academic_tool = AcademicSearchTool()
academic_results = academic_tool._run(
    query="quantum computing",
    top_k=5
)
# Returns: Results from academic domains, enhanced query, citation extraction

# Valyu search - multi-source with AI optimization
valyu_tool = ValyuSearchTool()
valyu_results = valyu_tool._run(
    query="quantum computing",
    top_k=5,
    search_type="all",
    is_tool_call=True
)
# Returns: Web + academic + proprietary sources, AI-optimized, rich metadata
```

### 6.4 Key Differences in Output

```python
# Valyu citations include more metadata than other tools
valyu_citation = {
    "title": "Quantum Error Correction Breakthrough",
    "url": "https://nature.com/...",
    "source_type": "paper",           # NEW: Specific source classification
    "publication_date": "2024-03-15", # NEW: ISO date
    "author": "Smith",                # Extracted for papers
    "year": "2024"                    # Extracted or from pub_date
}

# Compare to Academic search citation
academic_citation = {
    "title": "Quantum Error Correction Breakthrough",
    "url": "https://nature.com/...",
    "author": "Smith",
    "year": "2024"
}
```

## 7. Testing Strategy

### 7.1 Unit Tests

Required test cases for `valyu_search()`:

1. **Success Cases**
   - Basic search with default parameters
   - All search_type options ("all", "web", "proprietary")
   - Fast mode enabled/disabled
   - All response_length options ("short", "medium", "large", "max", custom int)
   - is_tool_call True/False

2. **Error Cases**
   - Missing VALYU_API_KEY
   - Invalid API key (401)
   - Validation error (422)
   - Rate limit (429) with retry
   - Server error (500) with retry
   - Network timeout with retry
   - SDK import error
   - Empty query
   - Invalid search_type
   - Invalid response_length

3. **Edge Cases**
   - Query as dictionary (extraction logic)
   - No results returned
   - Malformed response from API
   - Missing fields in results
   - Very long query strings
   - Special characters in query

### 7.2 Integration Tests

1. **Tool Integration**
   - ValyuSearchTool initialization
   - Tool execution through LangChain interface
   - Mock fallback when SDK not available
   - Error propagation to tool caller

2. **Result Format Validation**
   - Verify all required keys in response
   - Validate formatted_sources format
   - Verify raw_contents word limit (MAX_RAW_CONTENT_WORDS)
   - Check domain extraction
   - Validate citation structure

3. **Compatibility Tests**
   - Results compatible with existing research pipeline
   - Citation format compatible with report generation
   - Domain list compatible with source tracking

### 7.3 Mock Implementation

For testing without API access:

```python
def mock_valyu_search(query, **kwargs):
    """Mock implementation for testing."""
    return {
        "success": True,
        "error": "",
        "tx_id": "mock_tx_12345",
        "query": query,
        "results": [
            {
                "title": "Mock Result 1",
                "url": "https://example.com/1",
                "content": "Mock content " * 100,
                "description": "Mock description",
                "source": "web",
                "source_type": "website",
                "relevance_score": 0.95,
                "publication_date": "2024-01-01",
                "price": 0.001,
                "length": 1000,
            }
        ],
        "total_results": 1,
        "total_cost_dollars": 0.001,
        "total_characters": 1000,
    }
```

## 8. Performance Considerations

### 8.1 Latency Optimization

- Use `fast_mode=True` for quick searches where comprehensive results aren't critical
- Set appropriate `response_length` based on use case:
  - "short" for quick summaries
  - "medium" for balanced results (default)
  - "large"/"max" only when full content needed
- Limit `max_num_results` to minimum needed (default: 5)

### 8.2 Cost Management

Valyu API charges per result. The response includes:
- `price`: Cost for individual result
- `total_cost_dollars`: Total cost for the request

Best practices:
- Monitor `total_cost_dollars` in logs
- Set appropriate `max_num_results` limits
- Use `fast_mode` to reduce per-result cost
- Choose `search_type="web"` when proprietary sources not needed

### 8.3 Content Limiting

Raw content is limited to `MAX_RAW_CONTENT_WORDS` (2000 words) to:
- Prevent excessive memory usage
- Maintain consistency with existing tools
- Control token costs for downstream LLM processing

## 9. Security Considerations

### 9.1 API Key Management

- API key stored in environment variable `VALYU_API_KEY`
- Never log or expose API key in error messages
- Validate key presence before any API calls
- Use same security practices as existing TAVILY_API_KEY

### 9.2 Input Validation

- Sanitize query strings (strip whitespace)
- Validate enum values (search_type, response_length)
- Prevent injection attacks through query parameter
- Limit query length if Valyu API has constraints

### 9.3 Response Validation

- Validate response structure before processing
- Handle missing or malformed fields gracefully
- Prevent errors from malformed URLs in results
- Sanitize content before storing/displaying

## 10. Migration and Rollout Plan

### 10.1 Phase 1: Implementation
1. Add `valyu>=0.1.0` to requirements.txt
2. Implement `valyu_search()` function in src/utils.py
3. Implement `ValyuSearchTool` class in src/tools/search_tools.py
4. Add unit tests for both components

### 10.2 Phase 2: Integration
1. Register ValyuSearchTool in tool selection logic
2. Add integration tests
3. Update documentation
4. Add example usage in README

### 10.3 Phase 3: Validation
1. Test with real Valyu API key
2. Compare results with existing search tools
3. Validate cost and performance metrics
4. Gather initial user feedback

### 10.4 Phase 4: Production
1. Deploy to production environment
2. Monitor error rates and costs
3. Collect usage metrics
4. Iterate based on feedback

## 11. Monitoring and Observability

### 11.1 Key Metrics

Track these metrics for Valyu integration:
- **Request count**: Total Valyu API calls
- **Success rate**: Percentage of successful searches
- **Average latency**: Response time distribution
- **Cost per search**: Average `total_cost_dollars`
- **Results per search**: Average number of results returned
- **Error rate by type**: 401, 422, 429, 500, etc.

### 11.2 Logging

All logs include:
- Query parameters (sanitized)
- Response metadata (tx_id, result count, cost)
- Error details with stack traces
- Performance metrics (latency)

### 11.3 Alerts

Set up alerts for:
- Elevated error rates (>5% failures)
- API authentication failures
- Rate limit hits
- Unusually high costs
- SDK import failures

## 12. Documentation Requirements

### 12.1 Code Documentation

- Comprehensive docstrings for all functions/classes
- Type hints for all parameters and return values
- Usage examples in docstrings
- Link to Valyu API documentation

### 12.2 User Documentation

Update README.md with:
- Valyu search tool description
- Setup instructions (API key)
- Usage examples
- Comparison with other search tools
- Cost considerations

### 12.3 Developer Documentation

Create integration guide covering:
- Architecture overview
- Implementation details
- Testing procedures
- Troubleshooting common issues
- Contributing guidelines

## 13. Future Enhancements

### 13.1 Advanced Filtering

Consider adding support for:
- Source filtering (include/exclude domains)
- Date range filtering
- Price limits per result
- Minimum relevance score threshold

### 13.2 Result Caching

Implement caching layer to:
- Reduce API costs for repeated queries
- Improve response times
- Handle rate limits gracefully

### 13.3 Hybrid Search

Combine Valyu with existing tools:
- Use Valyu for proprietary/academic sources
- Use Tavily for general web search
- Merge and deduplicate results

### 13.4 Source-Specific Tools

Create specialized variants:
- `ValyuAcademicTool`: Only search academic sources
- `ValyuFinancialTool`: Only search financial data
- `ValyuHealthTool`: Only search health datasets

## 14. Acceptance Criteria Checklist

- [ ] ValyuSearchTool extends BaseTool correctly
- [ ] Tool follows exact pattern of existing search tools
- [ ] All Valyu API parameters mapped to tool parameters
- [ ] Returns standardized format: {formatted_sources, raw_contents, search_string, tools, domains, citations}
- [ ] valyu_search() function follows general_deep_search() pattern
- [ ] Proper error handling for all error types
- [ ] API key retrieved from VALYU_API_KEY environment variable
- [ ] Raw content limited to MAX_RAW_CONTENT_WORDS
- [ ] Retry logic implemented with exponential backoff
- [ ] LangSmith tracing support via @traceable
- [ ] Comprehensive logging at appropriate levels
- [ ] Mock fallback for testing without API
- [ ] Documentation includes usage examples
- [ ] Unit tests cover success and error cases
- [ ] Integration tests verify compatibility
- [ ] Type hints on all functions
- [ ] Docstrings follow existing conventions

## 15. Appendix

### 15.1 Valyu API Response Example

```json
{
  "success": true,
  "error": "",
  "tx_id": "tx_12345678-1234-1234-1234-123456789abc",
  "query": "quantum computing",
  "results": [
    {
      "title": "Quantum Computing Breakthrough",
      "url": "https://nature.com/articles/...",
      "content": "Full content text...",
      "description": "Summary...",
      "source": "academic",
      "price": 0.005,
      "length": 15420,
      "data_type": "unstructured",
      "source_type": "paper",
      "publication_date": "2024-03-15",
      "id": "https://nature.com/articles/...",
      "image_url": {"main": "https://..."},
      "relevance_score": 0.94
    }
  ],
  "results_by_source": {"academic": 1},
  "total_results": 25,
  "total_cost_dollars": 0.008,
  "total_characters": 24370
}
```

### 15.2 Comparison Table: Valyu vs Existing Tools

| Feature | GeneralSearchTool | AcademicSearchTool | ValyuSearchTool |
|---------|------------------|-------------------|-----------------|
| Data Sources | Web (Tavily) | Web filtered to academic domains | Web + Academic + Financial + Proprietary |
| Score Boosting | Basic Tavily scoring | Domain-based boost (30% for top sources) | Native relevance_score (0-1) |
| Raw Content | From Tavily | From Tavily | From Valyu (AI-optimized) |
| Metadata | Title, URL, content, score | + author, year | + source_type, pub_date, price, relevance |
| Citations | Basic | Author + year extraction | Rich metadata + source classification |
| Optimization | None | Academic domain filter + query enhancement | is_tool_call + fast_mode + response_length |
| Cost Tracking | Not available | Not available | Per-result and total cost |
| Latency Control | None | None | fast_mode option |

### 15.3 Source Type Mapping

Valyu's 11 source types and their use cases:

| Source Type | Description | Best Use Case |
|-------------|-------------|---------------|
| `general` | Wikipedia, reference | General knowledge |
| `website` | General web articles | Current events, news |
| `forum` | Q&A communities | Community knowledge |
| `paper` | Academic papers (ArXiv, etc.) | Research, citations |
| `data` | Financial market data | Market analysis |
| `report` | SEC filings | Financial research |
| `health_data` | WHO global health | Health statistics |
| `clinical_trial` | ClinicalTrials.gov | Medical research |
| `drug_label` | FDA DailyMed | Drug information |
| `grants` | NIH funding data | Research funding |

---

**Document Version:** 1.0
**Last Updated:** 2025-10-27
**Author:** Agent Developer
**Status:** Ready for Implementation
