# Elasticsearch eCommerce MCP Server

A lightweight MCP (Model Context Protocol) server that provides tools to query Elasticsearch for eCommerce products from the Shein product catalog.

## Features

- **Streamable HTTP**: Built with `httpx` for efficient async HTTP requests
- **ES|QL Queries**: Uses Elasticsearch Query Language for advanced product search
- **Semantic Search**: Leverages both semantic and text-based search capabilities
- **Reranking**: Uses Elasticsearch's reranking capabilities for improved relevance
- **Environment-based Configuration**: Uses environment variables for secure configuration

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables by sourcing the setup script:
```bash
source ../setup_env.sh
```

## Usage

The server provides one main tool:

### `query_elasticsearch_products`

Query the Elasticsearch `ecommerce_shein_products` index to fetch products based on search terms.

**Parameters:**
- `query` (string, required): The search term to find products (e.g., "dog bed", "wireless headphones")

**Query Structure:**
The tool uses the following ES|QL query structure:
```sql
FROM ecommerce_shein_products METADATA _score
| WHERE MATCH(description_semantic_google, "user_query") OR MATCH(description, "user_query")
| LIMIT 20
| RERANK rerank_score = "hobbit" ON description WITH { "inference_id" : ".rerank-v1-elasticsearch" }
| LIMIT 10
| KEEP _score, product_id, product_name, description, in_stock, initial_price, final_price, related_products, main_image
```

**Response Fields:**
- `_score`: Relevance score
- `product_id`: Unique product identifier
- `product_name`: Product name
- `description`: Product description
- `in_stock`: Stock availability
- `initial_price`: Original price
- `final_price`: Current/sale price
- `related_products`: Related product information
- `main_image`: Product image URL

## Running the Server

```bash
python server.py
```

The server uses stdio transport for communication with MCP clients.

## Environment Variables

The following environment variables are required (set via `../variables.env`):

- `ES_URL`: Elasticsearch cluster URL
- `ES_API_KEY`: Elasticsearch API key for authentication
- `RERANK_INFERENCE_ID`: Inference ID for reranking (defaults to ".rerank-v1-elasticsearch")

## Architecture

- **Async/Await**: Built with Python asyncio for efficient concurrent operations
- **HTTP Client**: Uses `httpx` for streaming HTTP requests to Elasticsearch
- **MCP Protocol**: Implements the Model Context Protocol for tool integration
- **Error Handling**: Comprehensive error handling with informative error messages
