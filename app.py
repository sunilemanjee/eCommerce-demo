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
RERANK_INFERENCE_ID = os.getenv('RERANK_INFERENCE_ID', '.rerank-v1-elasticsearch')

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
    'multi_match': 2,
    'model_number': 2,
    'product_id': 2
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
        enable_reranking = data.get('enable_reranking', False)
        
        # Generate the hybrid query
        search_query = generate_hybrid_query(query_text, weights, multi_match_fields, enable_reranking)
        
        # Execute the search
        response = es.search(
            index='ecommerce_shein_products',
            body=search_query
        )
        
        # Process results
        products = []
        for hit in response['hits']['hits']:
            # Handle both _source and fields response formats
            if '_source' in hit:
                source = hit['_source']
            else:
                # For reranking queries that use fields
                source = {}
                for field in hit.get('fields', {}):
                    values = hit['fields'][field]
                    # Take the first value if it's a list
                    source[field] = values[0] if isinstance(values, list) and len(values) > 0 else values
            
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
                'in_stock': source.get('in_stock', False),
                'model_number': source.get('model_number', '')
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
        enable_reranking = data.get('enable_reranking', False)
        
        # Generate the hybrid query
        search_query = generate_hybrid_query(query_text, weights, multi_match_fields, enable_reranking)
        
        return jsonify({
            'success': True,
            'query': search_query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_hybrid_query(query_text, weights, multi_match_fields, enable_reranking=False):
    """Generate the hybrid query using bool/should structure or reranking structure"""
    
    if enable_reranking:
        return generate_reranking_query(query_text, weights, multi_match_fields)
    else:
        return generate_standard_query(query_text, weights, multi_match_fields)

def generate_standard_query(query_text, weights, multi_match_fields):
    """Generate the standard hybrid query using bool/should structure"""
    
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
    
    # Add model_number clause
    if 'model_number' in weights and weights['model_number'] > 0:
        should_clauses.append({
            "match": {
                "model_number": {
                    "query": query_text,
                    "boost": weights['model_number']
                }
            }
        })
    
    # Add product_id clause
    if 'product_id' in weights and weights['product_id'] > 0:
        should_clauses.append({
            "match": {
                "product_id": {
                    "query": query_text,
                    "boost": weights['product_id']
                }
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

def generate_reranking_query(query_text, weights, multi_match_fields):
    """Generate the reranking query using text_similarity_reranker structure"""
    
    # Build retrievers for the linear combination
    retrievers = []
    
    # Add semantic search retrievers
    semantic_fields = [
        ('description_semantic_elser', 'description_semantic_elser', 2.0),
        ('description_semantic_google', 'description_semantic_google', 2.0),
        ('description_semantic_e5', 'description_semantic_e5', 2.0),
        ('product_name_semantic_elser', 'product_name_semantic_elser', 2.0),
        ('product_name_semantic_google', 'product_name_semantic_google', 2.0),
        ('product_name_semantic_e5', 'product_name_semantic_e5', 2.0)
    ]
    
    for field_name, field_path, default_weight in semantic_fields:
        if field_name in weights and weights[field_name] > 0:
            retrievers.append({
                "normalizer": "minmax",
                "retriever": {
                    "standard": {
                        "query": {
                            "match": {
                                field_path: {
                                    "query": query_text,
                                    "boost": weights[field_name]
                                }
                            }
                        }
                    }
                },
                "weight": weights[field_name]
            })
    
    # Add multi_match retriever
    if 'multi_match' in weights and weights['multi_match'] > 0 and multi_match_fields:
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "multi_match": {
                            "query": query_text,
                            "fields": multi_match_fields,
                            "boost": weights['multi_match']
                        }
                    }
                }
            },
            "weight": weights['multi_match']
        })
    
    # Add model_number retriever
    if 'model_number' in weights and weights['model_number'] > 0:
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "match": {
                            "model_number": {
                                "query": query_text,
                                "boost": weights['model_number']
                            }
                        }
                    }
                }
            },
            "weight": weights['model_number']
        })
    
    # Add product_id retriever
    if 'product_id' in weights and weights['product_id'] > 0:
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "match": {
                            "product_id": {
                                "query": query_text,
                                "boost": weights['product_id']
                            }
                        }
                    }
                }
            },
            "weight": weights['product_id']
        })
    
    # Build the reranking query
    query = {
        "_source": False,
        "fields": [
            "product_name",
            "description",
            "main_image",
            "final_price",
            "currency",
            "rating",
            "reviews_count",
            "in_stock",
            "model_number"
        ],
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
        "retriever": {
            "text_similarity_reranker": {
                "field": "description",  # Field to rerank on
                "inference_id": RERANK_INFERENCE_ID,
                "inference_text": query_text,
                "rank_window_size": 20,
                "retriever": {
                    "linear": {
                        "rank_window_size": 100,
                        "retrievers": retrievers
                    }
                }
            }
        },
        "size": 20
    }
    
    return query

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
