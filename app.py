import os
import json
from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import time

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
ELSER_INFERENCE_ID = os.getenv('ELSER_INFERENCE_ID')
EMBEDDING_INFERENCE_ID = os.getenv('EMBEDDING_INFERENCE_ID', '.elser-2-elasticsearch')
E5_INFERENCE_ID = os.getenv('E5_INFERENCE_ID', '.elser-2-elasticsearch')

# Initialize Elasticsearch client
es = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
    verify_certs=False
)

# Default weights for the hybrid query
DEFAULT_WEIGHTS = {
    'description_semantic_elser': 2,
    'description_semantic_google': 2,
    'description_semantic_e5': 2,
    'product_name_semantic_elser': 2,
    'product_name_semantic_google': 2,
    'product_name_semantic_e5': 2,
    'multi_match': 2
}

# Text fields available for multi_match
TEXT_FIELDS = [
    'product_name',
    'description',
    'offers',
    'related_products',
    'top_reviews'
]

@app.route('/')
def index():
    return render_template('index.html', 
                         default_weights=DEFAULT_WEIGHTS,
                         text_fields=TEXT_FIELDS)

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        weights = data.get('weights', DEFAULT_WEIGHTS)
        multi_match_fields = data.get('multi_match_fields', ['description', 'product_name'])
        
        # Generate the hybrid query
        search_query = generate_hybrid_query(query_text, weights, multi_match_fields)
        
        # Execute the search
        response = es.search(
            index='ecommerce_shein_products',
            body=search_query
        )
        
        # Process results
        products = []
        for hit in response['hits']['hits']:
            source = hit.get('_source', {})
            product = {
                'id': hit['_id'],
                'score': hit['_score'],
                'product_name': source.get('product_name', ''),
                'description': source.get('description', ''),
                'main_image': source.get('main_image', ''),
                'final_price': source.get('final_price', 0),
                'currency': source.get('currency', ''),
                'rating': source.get('rating', 0),
                'reviews_count': source.get('reviews_count', 0),
                'in_stock': source.get('in_stock', False)
            }
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

@app.route('/generate_query', methods=['POST'])
def generate_query():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        weights = data.get('weights', DEFAULT_WEIGHTS)
        multi_match_fields = data.get('multi_match_fields', ['description', 'product_name'])
        
        # Generate the hybrid query
        search_query = generate_hybrid_query(query_text, weights, multi_match_fields)
        
        return jsonify({
            'success': True,
            'query': search_query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_hybrid_query(query_text, weights, multi_match_fields):
    """Generate the hybrid query using bool/should structure"""
    
    # Build should clauses for hybrid search
    should_clauses = []
    
    # Add semantic search clauses
    semantic_fields = [
        'description_semantic_elser',
        'description_semantic_google', 
        'description_semantic_e5',
        'product_name_semantic_elser',
        'product_name_semantic_google',
        'product_name_semantic_e5'
    ]
    
    for field in semantic_fields:
        if field in weights and weights[field] > 0:
            should_clauses.append({
                "match": {
                    field: {
                        "query": query_text,
                        "boost": weights[field]
                    }
                }
            })
    
    # Add multi_match clause
    if 'multi_match' in weights and weights['multi_match'] > 0 and multi_match_fields:
        should_clauses.append({
            "multi_match": {
                "query": query_text,
                "fields": multi_match_fields,
                "boost": weights['multi_match']
            }
        })
    
    # Build the complete query
    query = {
        "query": {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        },
        "highlight": {
            "fields": {
                "product_name": {
                    "number_of_fragments": 1,
                    "order": "score"
                },
                "description": {
                    "number_of_fragments": 1,
                    "order": "score"
                }
            }
        },
        "size": 20
    }
    
    return query

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
