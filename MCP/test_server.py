#!/usr/bin/env python3
"""
Test script for the Elasticsearch eCommerce MCP Server
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import query_elasticsearch_products

async def test_query():
    """Test the Elasticsearch query functionality."""
    print("Testing Elasticsearch eCommerce MCP Server...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if environment variables are set
    if not os.getenv("ES_URL") or not os.getenv("ES_API_KEY"):
        print("Error: Environment variables not set. Please run: source ../variables.env")
        return
    
    # Test with a sample query
    test_query = "dog bed"
    print(f"Testing query: '{test_query}'")
    
    try:
        result = await query_elasticsearch_products(test_query)
        
        if result.content:
            print("Query successful!")
            print("Result:")
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
        else:
            print("No content returned from query")
            
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())



