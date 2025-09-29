import os
import json
from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables from variables.env
# Handle both export format and key=value format
def load_env_variables():
    env_vars = {}
    try:
        with open('variables.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('export '):
                        # Handle export format: export KEY="value"
                        key_value = line[7:]  # Remove 'export '
                        if '=' in key_value:
                            key, value = key_value.split('=', 1)
                            # Remove quotes if present and any trailing comments
                            value = value.strip('"\'')
                            # Remove inline comments (everything after #)
                            if '#' in value:
                                value = value.split('#')[0].strip()
                            # Remove any remaining quotes
                            value = value.strip('"\'')
                            env_vars[key] = value
                    elif '=' in line:
                        # Handle key=value format
                        key, value = line.split('=', 1)
                        value = value.strip('"\'')
                        env_vars[key] = value
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
    except FileNotFoundError:
        print("Warning: variables.env file not found")
    except Exception as e:
        print(f"Error loading environment variables: {e}")

# Load environment variables
load_env_variables()

app = Flask(__name__)

# Elasticsearch configuration
ES_URL = os.getenv('ES_URL')
ES_API_KEY = os.getenv('ES_API_KEY')
INDEX_WITH_SYNONYMS = os.getenv('INDEX_WITH_SYNONYMS', 'ecommerce_shein_products_with_synonyms')

# Initialize Elasticsearch client
es = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
    verify_certs=False
)

@app.route('/')
def index():
    return render_template('simple_index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        
        if not query_text.strip():
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        # Simple query as requested
        search_query = {
            "query": {
                "match": {
                    "product_name": query_text
                }
            },
            "highlight": {
                "fields": {
                    "product_name": {}
                }
            },
            "size": 20
        }
        
        # Execute the search
        response = es.search(
            index=INDEX_WITH_SYNONYMS,
            body=search_query
        )
        
        # Process results
        products = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            
            product = {
                'id': hit['_id'],
                'score': hit['_score'],
                'product_id': source.get('product_id', ''),
                'product_name': source.get('product_name', ''),
                'description': source.get('description', ''),
                'main_image': source.get('main_image', ''),
                'final_price': source.get('final_price', 0),
                'currency': source.get('currency', ''),
                'rating': source.get('rating', 0),
                'reviews_count': source.get('reviews_count', 0),
                'in_stock': source.get('in_stock', False),
                'model_number': source.get('model_number', '')
            }
            
            # Add highlights if available
            if 'highlight' in hit:
                product['highlights'] = hit['highlight']
            
            products.append(product)
        
        return jsonify({
            'success': True,
            'products': products,
            'total': response['hits']['total']['value'],
            'query': search_query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8046)
