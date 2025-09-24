#!/usr/bin/env python3
"""
Example usage of the Elasticsearch eCommerce MCP Server
"""

import asyncio
import json
from server import query_elasticsearch_products

async def main():
    """Example usage of the MCP server."""
    
    # Example queries to test
    test_queries = [
        "wireless headphones",
        "summer dress",
        "laptop bag",
        "kitchen utensils"
    ]
    
    print("Elasticsearch eCommerce MCP Server - Example Usage")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        print("-" * 30)
        
        try:
            result = await query_elasticsearch_products(query)
            
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        # Parse the JSON response to show a summary
                        try:
                            data = json.loads(content.text.split('\n\n')[1])  # Get the JSON part
                            print(f"✅ Found {len(data)} products")
                            
                            # Show first product as example
                            if data:
                                first_product = data[0]
                                print(f"   📦 Top result: {first_product.get('product_name', 'N/A')[:60]}...")
                                print(f"   💰 Price: ${first_product.get('final_price', 'N/A')}")
                                print(f"   📊 Score: {first_product.get('_score', 'N/A'):.3f}")
                        except (json.JSONDecodeError, IndexError):
                            print(content.text)
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Example completed!")

if __name__ == "__main__":
    asyncio.run(main())
