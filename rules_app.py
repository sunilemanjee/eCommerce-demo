import os
import json
import signal
import sys
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
INDEX_NAME = os.getenv('INDEX_NAME', 'ecommerce_shein_products')
KIBANA_QUERY_RULES = os.getenv('KIBANA_QUERY_RULES')

# Initialize Elasticsearch client
es = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
    verify_certs=False
)

@app.route('/')
def index():
    return render_template('rules_index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        search_type = data.get('search_type', 'text')  # 'text' or 'rules'
        
        if not query_text.strip():
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        # Generate query based on search type
        if search_type == 'text':
            search_query = {
                "query": {
                    "match": {
                        "product_name": query_text
                    }
                }
            }
        else:  # rules
            search_query = {
                "retriever": {
                    "rule": {
                        "match_criteria": {
                            "product_name": query_text
                        },
                        "ruleset_ids": [
                            "labubu"
                        ],
                        "retriever": {
                            "standard": {
                                "query": {
                                    "match": {
                                        "product_name": query_text
                                    }
                                }
                            }
                        }
                    }
                }
            }
        
        # Execute the search
        response = es.search(
            index=INDEX_NAME,
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
            'query': search_query,
            'search_type': search_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/kibana-query-rules-url', methods=['GET'])
def get_kibana_query_rules_url():
    """Get the Kibana query rules URL from environment variables"""
    try:
        if not KIBANA_QUERY_RULES:
            return jsonify({
                'success': False,
                'error': 'KIBANA_QUERY_RULES environment variable not set'
            }), 400
        
        return jsonify({
            'success': True,
            'url': KIBANA_QUERY_RULES
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app.run(debug=True, host='0.0.0.0', port=8047)
