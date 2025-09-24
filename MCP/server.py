#!/usr/bin/env python3
"""
MCP Server for Elasticsearch eCommerce Product Search
A lightweight MCP server that provides tools to query Elasticsearch for eCommerce products.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Elasticsearch configuration from environment variables
ES_URL = os.getenv("ES_URL")
ES_API_KEY = os.getenv("ES_API_KEY")
RERANK_INFERENCE_ID = os.getenv("RERANK_INFERENCE_ID", ".rerank-v1-elasticsearch")

if not ES_URL or not ES_API_KEY:
    print("Error: ES_URL and ES_API_KEY environment variables must be set", file=sys.stderr)
    sys.exit(1)

# Parse Elasticsearch URL
parsed_url = urlparse(ES_URL)
ES_HOST = f"{parsed_url.scheme}://{parsed_url.netloc}"
ES_INDEX = "ecommerce_shein_products"

# Create MCP server instance
server = Server("elasticsearch-ecommerce-server")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="query_elasticsearch_products",
                description="Query Elasticsearch ecommerce_shein_products index to fetch products based on search terms",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find products (e.g., 'dog bed', 'wireless headphones')"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    if name == "query_elasticsearch_products":
        return await query_elasticsearch_products(arguments.get("query", ""))
    else:
        raise ValueError(f"Unknown tool: {name}")

async def query_elasticsearch_products(query: str) -> CallToolResult:
    """
    Query Elasticsearch for products using the specified query structure.
    
    Args:
        query: The search term to find products
        
    Returns:
        CallToolResult with the search results
    """
    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: Query parameter is required")]
        )
    
    try:
        # Construct the Elasticsearch query using ES|QL
        esql_query = f"""
        FROM {ES_INDEX} METADATA _score
        | WHERE MATCH(description_semantic_google, "{query}") OR MATCH(description, "{query}")
        | LIMIT 20
        | RERANK rerank_score = "hobbit" ON description WITH {{ "inference_id" : "{RERANK_INFERENCE_ID}" }}
        | LIMIT 10
        | KEEP _score, product_id, product_name, description, in_stock, initial_price, final_price, related_products, main_image
        """
        
        # Prepare the request
        headers = {
            "Authorization": f"ApiKey {ES_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": esql_query.strip()
        }
        
        # Make the request to Elasticsearch
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ES_HOST}/_query",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format the results
                if "values" in result:
                    products = []
                    columns = result.get("columns", [])
                    
                    for row in result["values"]:
                        product = {}
                        for i, column in enumerate(columns):
                            if i < len(row):
                                product[column["name"]] = row[i]
                        products.append(product)
                    
                    # Format the response
                    if products:
                        formatted_results = json.dumps(products, indent=2)
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text", 
                                    text=f"Found {len(products)} products for query '{query}':\n\n{formatted_results}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text", 
                                    text=f"No products found for query '{query}'"
                                )
                            ]
                        )
                else:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text", 
                                text=f"Unexpected response format: {json.dumps(result, indent=2)}"
                            )
                        ]
                    )
            else:
                error_text = f"Elasticsearch request failed with status {response.status_code}: {response.text}"
                return CallToolResult(
                    content=[TextContent(type="text", text=error_text)]
                )
                
    except Exception as e:
        error_text = f"Error querying Elasticsearch: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_text)]
        )

async def main():
    """Main entry point for the MCP server."""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="elasticsearch-ecommerce-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
