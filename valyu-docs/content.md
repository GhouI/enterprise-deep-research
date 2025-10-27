# Search Quickstart

> Search across web, research, and financial data sources - get AI ready search results

Search across Valyu's comprehensive knowledge base including web content, academic journals, financial data, and proprietary datasets. The DeepSearch API returns AI ready search results that are perfect for RAG pipelines, AI agents, and applications.

## Why Use the DeepSearch API

The DeepSearch API provides **AI ready search results** that enable:

* **Comprehensive Coverage** - Search web, research journals, books, and live financial data
* **Real-Time Results** - Access up-to-the-minute information from sources
* **Precise Filtering** - Control sources, dates, relevance scores, and result count
* **RAG-Ready** - Perfect for Retrieval-Augmented Generation and AI agent workflows

## Key DeepSearch Features

<CardGroup cols={2}>
  <Card title="Multi-Source Search" icon="globe">
    Search web content alongside research papers, books,
    and financial market data in one API call.
  </Card>

  {" "}

  <Card title="AI Ready" icon="book-open">
    Get AI ready search results that can you pass directly to your AI's context
    window.
  </Card>

  {" "}

  <Card title="Source Control" icon="filter">
    Include or exclude specific domains, URLs, and datasets to focus on
    authoritative sources.
  </Card>

  <Card title="Date Filtering" icon="calendar-days">
    Filter results by publication date to get recent
    or historical content.
  </Card>
</CardGroup>

## Getting Started

### Basic Search Query

Search across all available sources with a simple query:

<CodeGroup>
  ```python Python theme={null}
  from valyu import Valyu

  valyu = Valyu() # Uses VALYU_API_KEY from env

  response = valyu.search(
      query="latest developments in quantum computing",
      max_num_results=5,
      search_type="all",
  )

  for result in response["results"]:
      print(f"Title: {result['title']}")
      print(f"URL: {result['url']}")
      print(f"Source: {result['source_type']}")
      print(f"Content: {result['content'][:200]}...")
      print("---")

  ```

  ```javascript JavaScript theme={null}
  import { Valyu } from "valyu-js";

  const valyu = new Valyu(); // Uses VALYU_API_KEY from env

  const response = await valyu.search({
    query: "latest developments in quantum computing",
    maxNumResults: 5,
    searchType: "all",
  });

  response.results.forEach(result => {
    console.log(`Title: ${result.title}`);
    console.log(`URL: ${result.url}`);
    console.log(`Source: ${result.sourceType}`);
    console.log(`Content: ${result.content.substring(0, 200)}...`);
    console.log("---");
  });
  ```

  ```bash cURL theme={null}
  curl -X POST https://api.valyu.ai/v1/deepsearch \
    -H "Content-Type: application/json" \
    -H "x-api-key: YOUR_API_KEY" \
    -d '{
      "query": "latest developments in quantum computing",
      "max_num_results": 5,
      "search_type": "all"
    }'
  ```
</CodeGroup>

### Fast Mode for Reduced Latency

Enable fast mode for quicker search speed but shorter results. Best for general purpose queries:

<CodeGroup>
  ```python Python theme={null}
  from valyu import Valyu

  valyu = Valyu()

  # Fast mode search for reduced latency

  response = valyu.search(
      query="latest market trends in tech stocks",
      fast_mode=True, # Enable fast mode
      max_num_results=5,
      search_type="all",
  )

  for result in response["results"]:
      print(f"Title: {result['title']}")
      print(f"Source: {result['source_type']}")
      print(f"Content: {result['content'][:200]}...")
      print("---")

  ```

  ```javascript JavaScript theme={null}
  import { Valyu } from "valyu-js";

  const valyu = new Valyu();

  const response = await valyu.search({
    query: "latest market trends in tech stocks",
    fastMode: true, // Enable fast mode
    maxNumResults: 5,
    searchType: "all",
  });

  response.results.forEach(result => {
    console.log(`Title: ${result.title}`);
    console.log(`Source: ${result.sourceType}`);
    console.log(`Content: ${result.content.substring(0, 200)}...`);
    console.log("---");
  });
  ```

  ```bash cURL theme={null}
  curl -X POST https://api.valyu.ai/v1/deepsearch \
    -H "Content-Type: application/json" \
    -H "x-api-key: YOUR_API_KEY" \
    -d '{
      "query": "latest market trends in tech stocks",
      "fast_mode": true,
      "max_num_results": 5,
      "search_type": "all"
    }'
  ```
</CodeGroup>

This returns raw search results with metadata, relevance scores, and full content for each match.

### Search Type Options

Control which data sources to search:

| **Type**      | **Description**                               | **Best For**                   |
| ------------- | --------------------------------------------- | ------------------------------ |
| `all`         | Search web and proprietary sources (default)  | Comprehensive coverage         |
| `web`         | Web search only                               | Current events, general topics |
| `proprietary` | Research, financial, and premium sources only | Research, technical analysis   |

## Advanced Features

### AI Agent vs User Queries

Optimize retrieval based on the caller type:

<CodeGroup>
  ```python Python theme={null}
  from valyu import Valyu

  valyu = Valyu()

  # AI agent making a tool call

  agent_response = valyu.search(
      query="latest AI research papers",
      is_tool_call=True, # Optimized for AI processing
      max_num_results=10,
  )

  # Direct user query

  user_response = valyu.search(
      query="explain quantum computing basics",
      is_tool_call=False, # Optimized for human consumption
      max_num_results=5,
  )

  ```

  ```javascript JavaScript theme={null}
  import { Valyu } from "valyu-js";

  const valyu = new Valyu();

  // AI agent making a tool call
  const agentResponse = await valyu.search({
    query: "latest AI research papers",
    isToolCall: true, // Optimized for AI processing
    maxNumResults: 10,
  });

  // Direct user query
  const userResponse = await valyu.search({
    query: "explain quantum computing basics",
    isToolCall: false, // Optimized for human consumption
    maxNumResults: 5,
  });
  ```

  ```bash cURL theme={null}
  curl -X POST https://api.valyu.ai/v1/deepsearch \
    -H "Content-Type: application/json" \
    -H "x-api-key: YOUR_API_KEY" \
    -d '{
      "query": "latest AI research papers",
      "is_tool_call": true,
      "max_num_results": 10
    }'
  ```
</CodeGroup>

### Response Length Control

Control how much content is returned per result:

<CodeGroup>
  ```python Python theme={null}
  from valyu import Valyu

  valyu = Valyu()

  # Short snippets for quick overview

  response = valyu.search(
      query="renewable energy trends",
      response_length="short", # ~25k characters per result
      max_num_results=10,
  )

  # Full content for detailed analysis

  response = valyu.search(
      query="financial market analysis",
      response_length="max", # Full content
      max_num_results=3,
  )

  # Custom character limit

  response = valyu.search(
      query="technical documentation",
      response_length=5000, # Exactly 5000 characters
      max_num_results=5,
  )

  ```

  ```javascript JavaScript theme={null}
  import { Valyu } from "valyu-js";

  const valyu = new Valyu();

  // Short snippets for quick overview
  const response = await valyu.search({
    query: "renewable energy trends",
    responseLength: "short", // ~25k characters per result
    maxNumResults: 10,
  });

  // Full content for detailed analysis
  const response2 = await valyu.search({
    query: "financial market analysis",
    responseLength: "max", // Full content
    maxNumResults: 3,
  });

  // Custom character limit
  const response3 = await valyu.search({
    query: "technical documentation",
    responseLength: 5000, // Exactly 5000 characters
    maxNumResults: 5,
  });
  ```

  ```bash cURL theme={null}
  curl -X POST https://api.valyu.ai/v1/deepsearch \
    -H "Content-Type: application/json" \
    -H "x-api-key: YOUR_API_KEY" \
    -d '{
      "query": "renewable energy trends",
      "response_length": "short",
      "max_num_results": 10
    }'
  ```
</CodeGroup>

**Response Length Options:**

* `"short"`: \~25,000 characters per result
* `"medium"`: \~50,000 characters per result
* `"large"`: \~100,000 characters per result
* `"max"`: Full content available
* Custom integer: Exact character count

### Advanced Feature Guides

Check out our guides for other advanced features:

<CardGroup cols={2}>
  <Card title="Source Filtering" icon="filter" href="/search/filtering/sources">
    **Include or exclude specific domains and datasets** - Control exactly which sources to search for more targeted results
  </Card>

  {" "}

  <Card title="Date Filtering" icon="calendar-days" href="/search/filtering/date">
    **Filter by time periods** - Focus on recent content or historical data with
    flexible date range controls
  </Card>

  {" "}

  <Card title="Prompting Guide" icon="square-pen" href="/search/prompting">
    **Craft effective search queries** - Learn how to write queries that get the
    most relevant results
  </Card>

  <Card title="Tips & Tricks" icon="lightbulb" href="/search/tips-and-tricks">
    **Optimize your searches** - Advanced techniques for better performance and cost control
  </Card>
</CardGroup>

## Response Format

### Standard Search Response

```json  theme={null}
{
  "success": true,
  "error": "",
  "tx_id": "tx_12345678-1234-1234-1234-123456789abc",
  "query": "latest developments in quantum computing",
  "results": [
    {
      "title": "Quantum Computing Breakthrough: New Error Correction Method",
      "url": "https://nature.com/articles/quantum-error-correction-2024?utm_source=valyu",
      "content": "Researchers at MIT have developed a revolutionary quantum error correction method that reduces error rates by 90% while maintaining computational speed. This breakthrough addresses one of the fundamental challenges in scaling quantum computers...",
      "description": "Major breakthrough in quantum error correction methodology",
      "source": "academic",
      "price": 0.005,
      "length": 15420,
      "data_type": "unstructured",
      "source_type": "paper",
      "publication_date": "2024-03-15",
      "id": "https://nature.com/articles/quantum-error-correction-2024",
      "image_url": {
        "main": "https://nature.com/quantum-diagram.jpg"
      },
      "relevance_score": 0.94
    },
    {
      "title": "IBM Announces 1000-Qubit Quantum Processor",
      "url": "https://techcrunch.com/2024/05/12/ibm-quantum-1000-qubit?utm_source=valyu",
      "content": "IBM has unveiled its latest quantum processor featuring over 1000 qubits, marking a significant milestone in quantum computing hardware development. The new processor, called Condor, demonstrates improved coherence times and reduced error rates...",
      "description": "IBM's latest quantum hardware milestone announcement",
      "source": "web",
      "price": 0.003,
      "length": 8950,
      "data_type": "unstructured",
      "source_type": "website",
      "publication_date": "2024-05-12",
      "id": "https://techcrunch.com/2024/05/12/ibm-quantum-1000-qubit",
      "image_url": {
        "main": "https://techcrunch.com/ibm-quantum-chip.jpg"
      },
      "relevance_score": 0.87
    }
  ],
  "results_by_source": {
    "academic": 1,
    "web": 1
  },
  "total_results": 25,
  "total_cost_dollars": 0.008,
  "total_characters": 24370
}
```

### Top-level fields

| **Field**            | **Description**                                                  |
| -------------------- | ---------------------------------------------------------------- |
| `success`            | Indicates whether the search completed successfully              |
| `error`              | Empty string on success; populated when warnings or errors occur |
| `tx_id`              | Unique transaction identifier for tracing and support            |
| `query`              | The processed search query                                       |
| `results`            | Ranked array of result objects                                   |
| `results_by_source`  | Count of results returned per source type                        |
| `total_results`      | Total number of matches available for the query                  |
| `total_cost_dollars` | Total cost of the request in USD                                 |
| `total_characters`   | Combined character count across all returned results             |
| `fast_mode`          | Present when the query ran in fast mode (omitted otherwise)      |

### Result fields

| **Field**          | **Description**                                                    |
| ------------------ | ------------------------------------------------------------------ |
| `title`            | Title of the document or article                                   |
| `url`              | Canonical URL for the result (tracking parameters may be appended) |
| `content`          | Extracted text content, trimmed according to the `response_length` |
| `description`      | High-level summary of the result                                   |
| `source`           | High-level source category such as `web` or `academic`             |
| `price`            | Cost in USD attributed to this individual result                   |
| `length`           | Character count returned for this result                           |
| `data_type`        | Data modality for the result (for example `unstructured`)          |
| `source_type`      | Specific source classification (see [Source types](#source-types)) |
| `publication_date` | ISO 8601 publication date when available                           |
| `id`               | Stable identifier or canonical reference for the result            |
| `image_url`        | Images extracted from the page                                     |
| `relevance_score`  | Ranking score between 0 and 1 indicating result relevance          |

## Source types

| **Type**         | **Datasets**                                                                         | **Description**                                                                               |
| ---------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `general`        | `valyu-wikipedia` and similar general-reference corpora                              | General knowledge indexes (e.g., Wikipedia) served from LanceDB                               |
| `website`        | Brave web search pipeline (fast + full), Spider scraper fallback, LinkedIn processor | General web articles extracted or scraped by the web processing stack                         |
| `forum`          | Brave QA hits handled by the web processor                                           | Community Q\&A snippets surfaced when Brave supplies QA payloads                              |
| `paper`          | `valyu/valyu-arxiv` and other academic research indexes                              | Academic paper corpora (ArXiv, etc.) routed through the academic server                       |
| `data`           | Finance server market data integrations (quotes, FX, fundamentals, etc.)             | Structured market metrics and analytics returned by the finance search pipeline               |
| `report`         | `valyu/valyu-sec-filings (SEC filings service)`                                      | Regulatory filing documents returned from the SEC microservice                                |
| `health_data`    | WHO Global Health Observatory ingestion                                              | Global health indicator records delivered by the WHO handler                                  |
| `clinical_trial` | `valyu/valyu-clinical-trials (ClinicalTrials.gov)`                                   | Structured clinical-study summaries produced by the clinical trials handler                   |
| `drug_label`     | `valyu/valyu-drug-labels (FDA DailyMed)`                                             | Drug labeling content (warnings, dosing, contraindications) processed by the DailyMed handler |
| `grants`         | NIH RePORTER grants ingestion                                                        | NIH funding project data generated by the NIH handler                                         |

## Best Practices

1. **Be Specific**: Use detailed queries for better search results
2. **Set Appropriate Price Limits**: Balance cost with data quality needs
3. **Filter Results**: Use parameters to get only the most relevant content
4. **Choose the Right Search Type**: Match `search_type` to your use case
5. **Monitor Costs**: Track `price_per_result` and `total_cost_dollars` in responses
6. **Optimize for Tool Calls**: Set `is_tool_call=true` for AI agent usage

For detailed guidance on optimizing your searches, see our [Tips & Tricks guide](/search/tips-and-tricks) and [Prompting Guide](/search/prompting).

### Error Handling

```python  theme={null}
from valyu import Valyu

valyu = Valyu()

try:
    response = valyu.search(
        query="quantum computing applications",
        max_num_results=10,
        search_type="all",
    )

    if response.get("success"):
        for result in response["results"]:
            print(f"Found: {result['title']}")
            print(f"Source: {result['source_type']}")
    else:
        print(f"Search failed: {response.get('error', 'Unknown error')}")

except Exception as e:
    print(f"Request failed: {e}")
```

<Card title="Try the DeepSearch API" icon="rocket" href="/api-reference/endpoint/deepsearch">
  Explore the complete API reference with interactive examples and detailed
  parameter documentation.
</Card>

## Next Steps

<CardGroup cols={2}>
  <Card title="API Reference" icon="code" href="/api-reference/endpoint/deepsearch">
    Complete parameter documentation and examples
  </Card>

  {" "}

  <Card title="Python SDK" icon="python" href="/sdk/python-sdk">
    Easy integration with Python applications
  </Card>

  {" "}

  <Card title="TypeScript SDK" icon="js" href="/sdk/typescript-sdk">
    Type-safe integration for JavaScript/TypeScript
  </Card>

  <Card title="Integration Guides" icon="plug" href="/integrations/langchain">
    Connect with LangChain, LlamaIndex, and more
  </Card>
</CardGroup>
