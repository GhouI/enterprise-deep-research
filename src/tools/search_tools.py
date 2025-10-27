"""
Search tools for the research agent.

This module contains the implementation of search tools that can be used by the research agent.
Each tool follows the LangChain tool calling pattern and provides a standardized interface.
"""

import logging
import traceback
from typing import Dict, List, Optional, Any, Union, Type, Annotated

# Maximum number of words allowed in raw content
MAX_RAW_CONTENT_WORDS = 2000

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Base parameter models for tools
class SearchParameters(BaseModel):
    """Parameters for search tools."""

    query: str = Field(..., description="The search query to execute")
    top_k: Optional[int] = Field(5, description="Number of results to return")


# Mock search function for testing
def mock_search_tool(query, index=0, state=None, config=None, selected_tool=None):
    """Mock implementation of search for testing."""
    logger.info(f"Mock search executed with query: {query} using tool: {selected_tool}")

    # Return empty results for testing
    return [], query, selected_tool, []


class GeneralSearchTool(BaseTool):
    """Tool for general web search."""

    name: str = "general_search"
    description: str = (
        "General web search for broad topics that don't fit specialized categories"
    )
    args_schema: Type[BaseModel] = SearchParameters
    config: Optional[Dict] = None

    def _run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute a general web search."""
        logger.info(
            f"[GeneralSearchTool._run] Executing general search for query: {query}"
        )
        logger.info(
            f"[GeneralSearchTool._run] Parameters: query={query}, top_k={top_k}, config_type={type(self.config).__name__ if self.config else 'None'}"
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
                    f"[GeneralSearchTool._run] Extracted query string from dict: {search_query}"
                )
            else:
                search_query = query

            # Try to import the real search module if available
            try:
                from src.utils import general_deep_search

                logger.info(
                    f"[GeneralSearchTool._run] Successfully imported general_deep_search from src.utils"
                )
                # Execute the search with the real implementation
                logger.info(
                    f"[GeneralSearchTool._run] Calling general_deep_search with query: {search_query}"
                )
                search_results = general_deep_search(
                    query=search_query,
                    include_raw_content=True,
                    top_k=top_k,
                    config=self.config,
                )
                logger.info(
                    f"[GeneralSearchTool._run] general_deep_search returned {len(search_results.get('results', []))} results"
                )

                # Format the results and extract raw content
                formatted_sources = []
                raw_contents = []

                domains = []
                if "results" in search_results:
                    from urllib.parse import urlparse

                    for res in search_results["results"]:
                        formatted_sources.append(
                            f"* {res.get('title', 'Untitled')} : {res.get('url', 'No URL')}"
                        )
                        if "raw_content" in res and res["raw_content"]:
                            # Limit raw content to MAX_RAW_CONTENT_WORDS
                            content = res["raw_content"]
                            words = content.split()
                            if len(words) > MAX_RAW_CONTENT_WORDS:
                                content = " ".join(words[:MAX_RAW_CONTENT_WORDS])
                            raw_contents.append(content)

                        # Extract domains within the same loop
                        url = res.get("url", "")
                        if url:
                            parsed_url = urlparse(url)
                            domain = parsed_url.netloc
                            if domain and domain not in domains:
                                domains.append(domain)

                logger.info(
                    f"[GeneralSearchTool._run] Formatted {len(formatted_sources)} sources, extracted {len(raw_contents)} raw contents, and {len(domains)} domains"
                )

                result = {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_query,
                    "tools": ["general_search"],
                    "domains": domains,
                    "citations": [],
                }
                logger.info(
                    f"[GeneralSearchTool._run] Returning result with keys: {list(result.keys())}"
                )
                return result
            except ImportError as ie:
                # Use mock implementation for testing
                logger.warning(f"[GeneralSearchTool._run] ImportError: {str(ie)}")
                logger.info(
                    f"[GeneralSearchTool._run] Using mock search implementation for: {search_query}"
                )
                formatted_sources, search_str, selected_tool, domains = (
                    mock_search_tool(
                        search_query,
                        index=0,
                        state=None,
                        config=self.config,
                        selected_tool="general_search",
                    )
                )

                # Mock search doesn't provide raw content
                raw_contents = []

                result = {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_str,
                    "tools": ["general_search"],
                    "domains": domains,
                    "citations": [],
                }
                logger.info(
                    f"[GeneralSearchTool._run] Returning result from mock search with keys: {list(result.keys())}"
                )
                return result
        except Exception as e:
            logger.error(f"[GeneralSearchTool._run] Error in general search: {str(e)}")
            logger.error(
                f"[GeneralSearchTool._run] Traceback: {traceback.format_exc()}"
            )
            # Return empty results on error
            return {
                "formatted_sources": [],
                "raw_contents": [],
                "search_string": str(query),
                "tools": ["general_search"],
                "domains": [],
                "citations": [],
            }


class AcademicSearchTool(BaseTool):
    """Tool for academic and scholarly search."""

    name: str = "academic_search"
    description: str = (
        "Search for academic papers, research publications, and scholarly content"
    )
    args_schema: Type[BaseModel] = SearchParameters
    config: Optional[Dict] = None

    def _run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute an academic search."""
        logger.info(
            f"[AcademicSearchTool._run] Executing academic search for query: {query}"
        )
        logger.info(
            f"[AcademicSearchTool._run] Parameters: query={query}, top_k={top_k}, config_type={type(self.config).__name__ if self.config else 'None'}"
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
                    f"[AcademicSearchTool._run] Extracted query string from dict: {search_query}"
                )
            else:
                search_query = query

            # Try to import the real search module if available
            try:
                from src.utils import academic_search

                logger.info(
                    f"[AcademicSearchTool._run] Successfully imported academic_search from src.utils"
                )
                # Execute the search with the real implementation
                logger.info(
                    f"[AcademicSearchTool._run] Calling academic_search with query: {search_query}"
                )
                search_results = academic_search(
                    query=search_query,
                    include_raw_content=True,
                    top_k=top_k,
                    config=self.config,
                )
                logger.info(
                    f"[AcademicSearchTool._run] academic_search returned {len(search_results.get('results', []))} results"
                )

                # Format the results and extract raw content
                formatted_sources = []
                raw_contents = []
                citations = []

                domains = []
                if "results" in search_results:
                    from urllib.parse import urlparse
                    from src.utils import extract_author_and_year_from_content

                    for res in search_results["results"]:
                        title = res.get("title", "Untitled") or "Untitled"
                        url = res.get("url", "No URL") or "No URL"
                        raw_content = res.get("raw_content", "") or ""

                        # Extract author and year for academic search
                        # Ensure all parameters are strings to avoid NoneType errors
                        first_author, year = extract_author_and_year_from_content(
                            str(title), str(raw_content), str(url)
                        )

                        # Store citation info with author and year
                        citation_info = {
                            "title": title,
                            "url": url,
                            "author": first_author,
                            "year": year,
                        }
                        citations.append(citation_info)

                        formatted_sources.append(f"* {title} : {url}")
                        if raw_content:
                            # Limit raw content to MAX_RAW_CONTENT_WORDS
                            content = raw_content
                            words = content.split()
                            if len(words) > MAX_RAW_CONTENT_WORDS:
                                content = " ".join(words[:MAX_RAW_CONTENT_WORDS])
                            raw_contents.append(content)

                        # Extract domains within the same loop
                        if url and url != "No URL":
                            parsed_url = urlparse(url)
                            domain = parsed_url.netloc
                            if domain and domain not in domains:
                                domains.append(domain)

                logger.info(
                    f"[AcademicSearchTool._run] Formatted {len(formatted_sources)} sources, extracted {len(raw_contents)} raw contents, and {len(domains)} domains"
                )

                result = {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_query,
                    "tools": ["academic_search"],
                    "domains": domains,
                    "citations": citations,
                }
                logger.info(
                    f"[AcademicSearchTool._run] Returning result with keys: {list(result.keys())}"
                )
                return result
            except ImportError as ie:
                # Use mock implementation for testing
                logger.warning(f"[AcademicSearchTool._run] ImportError: {str(ie)}")
                logger.info(
                    f"[AcademicSearchTool._run] Using mock search implementation for: {search_query}"
                )
                formatted_sources, search_str, selected_tool, domains = (
                    mock_search_tool(
                        search_query,
                        index=0,
                        state=None,
                        config=self.config,
                        selected_tool="academic_search",
                    )
                )

                # Mock search doesn't provide raw content
                raw_contents = []

                result = {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_str,
                    "tools": ["academic_search"],
                    "domains": domains,
                    "citations": [],
                }
                logger.info(
                    f"[AcademicSearchTool._run] Returning result from mock search with keys: {list(result.keys())}"
                )
                return result
        except Exception as e:
            logger.error(
                f"[AcademicSearchTool._run] Error in academic search: {str(e)}"
            )
            logger.error(
                f"[AcademicSearchTool._run] Traceback: {traceback.format_exc()}"
            )
            # Return empty results on error
            return {
                "formatted_sources": [],
                "raw_contents": [],
                "search_string": query,
                "tools": ["academic_search"],
                "domains": [],
                "citations": [],
            }


class GithubSearchTool(BaseTool):
    """Tool for GitHub-specific search."""

    name: str = "github_search"
    description: str = "Search for repositories, code, and profiles on GitHub"
    args_schema: Type[BaseModel] = SearchParameters
    config: Optional[Dict] = None

    def _run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute a GitHub search."""
        logger.info(
            f"[GithubSearchTool._run] Executing GitHub search for query: {query}"
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
                    f"[GithubSearchTool._run] Extracted query string from dict: {search_query}"
                )
            else:
                search_query = query

            # Try to import the real search module if available
            try:
                from src.utils import github_search

                # Execute the search with the real implementation
                search_results = github_search(
                    query=search_query,
                    include_raw_content=True,
                    top_k=top_k,
                    min_score=0.1,
                    config=self.config,
                )

                # Format the results and extract raw content
                formatted_sources = []
                raw_contents = []
                domains = ["github.com"]  # Always include GitHub domain
                if "results" in search_results:
                    for res in search_results["results"]:
                        formatted_sources.append(
                            f"GitHub: {res.get('title', 'Untitled Repository')} : {res.get('url', 'No URL')}"
                        )
                        if "raw_content" in res and res["raw_content"]:
                            # Limit raw content to MAX_RAW_CONTENT_WORDS
                            content = res["raw_content"]
                            words = content.split()
                            if len(words) > MAX_RAW_CONTENT_WORDS:
                                content = " ".join(words[:MAX_RAW_CONTENT_WORDS])
                            raw_contents.append(content)

                return {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_query,
                    "tools": ["github_search"],
                    "domains": domains,
                    "citations": [],
                }
            except ImportError:
                # Use mock implementation for testing
                formatted_sources, search_str, selected_tool, domains = (
                    mock_search_tool(
                        search_query,
                        index=1,
                        state=None,
                        config=self.config,
                        selected_tool="github_search",
                    )
                )

                # Mock search doesn't provide raw content
                raw_contents = []

                return {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_str,
                    "tools": ["github_search"],
                    "domains": domains or ["github.com"],
                    "citations": [],
                }
        except Exception as e:
            logger.error(f"[GithubSearchTool._run] Error in GitHub search: {str(e)}")
            # Return empty results on error
            return {
                "formatted_sources": [],
                "raw_contents": [],
                "search_string": str(query),
                "tools": ["github_search"],
                "domains": ["github.com"],
                "citations": [],
            }


class LinkedinSearchTool(BaseTool):
    """Tool for LinkedIn profile search."""

    name: str = "linkedin_search"
    description: str = "Search for profiles, companies, and job listings on LinkedIn"
    args_schema: Type[BaseModel] = SearchParameters
    config: Optional[Dict] = None

    def _run(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Execute a LinkedIn search."""
        logger.info(
            f"[LinkedinSearchTool._run] Executing LinkedIn search for query: {query}"
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
                    f"[LinkedinSearchTool._run] Extracted query string from dict: {search_query}"
                )
            else:
                search_query = query

            # Try to import the real search module if available
            try:
                from src.utils import linkedin_search

                # Execute the search with the real implementation
                search_results = linkedin_search(
                    query=search_query,
                    include_raw_content=True,
                    top_k=top_k,
                    min_score=0.1,
                    config=self.config,
                )

                # Format the results and extract raw content
                formatted_sources = []
                raw_contents = []
                domains = ["linkedin.com"]  # Always include LinkedIn domain
                if "results" in search_results:
                    for res in search_results["results"]:
                        formatted_sources.append(
                            f"LinkedIn: {res.get('title', 'Untitled Profile')} : {res.get('url', 'No URL')}"
                        )
                        if "raw_content" in res and res["raw_content"]:
                            # Limit raw content to MAX_RAW_CONTENT_WORDS
                            content = res["raw_content"]
                            words = content.split()
                            if len(words) > MAX_RAW_CONTENT_WORDS:
                                content = " ".join(words[:MAX_RAW_CONTENT_WORDS])
                            raw_contents.append(content)

                return {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_query,
                    "tools": ["linkedin_search"],
                    "domains": domains,
                    "citations": [],
                }
            except ImportError:
                # Use mock implementation for testing
                formatted_sources, search_str, selected_tool, domains = (
                    mock_search_tool(
                        search_query,
                        index=3,
                        state=None,
                        config=self.config,
                        selected_tool="linkedin_search",
                    )
                )

                # Mock search doesn't provide raw content
                raw_contents = []

                return {
                    "formatted_sources": formatted_sources,
                    "raw_contents": raw_contents,
                    "search_string": search_str,
                    "tools": ["linkedin_search"],
                    "domains": domains or ["linkedin.com"],
                    "citations": [],
                }
        except Exception as e:
            logger.error(
                f"[LinkedinSearchTool._run] Error in LinkedIn search: {str(e)}"
            )
            # Return empty results on error
            return {
                "formatted_sources": [],
                "raw_contents": [],
                "search_string": str(query),
                "tools": ["linkedin_search"],
                "domains": ["linkedin.com"],
                "citations": [],
            }


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
                        relevance_score = res.get("relevance_score", None)

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

                        # Add relevance score if available
                        if relevance_score is not None:
                            citation_info["relevance_score"] = relevance_score

                        # For academic/proprietary papers, try to extract author info
                        if source_type in ["paper", "report"] and content:
                            try:
                                from src.utils import extract_author_and_year_from_content
                                first_author, year = extract_author_and_year_from_content(
                                    str(title), str(content), str(url)
                                )
                                citation_info["author"] = first_author
                                citation_info["year"] = year or (publication_date[:4] if publication_date else None)
                            except ImportError:
                                # If extract_author_and_year_from_content not available, skip
                                pass

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
