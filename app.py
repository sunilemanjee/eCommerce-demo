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
INDEX_NAME = os.getenv('INDEX_NAME', 'ecommerce_shein_products')
RECOMMENDATION_ENGINE_INDEX_NAME = os.getenv('RECOMMENDATION_ENGINE_INDEX_NAME', 'ecommerce_shein_recommendations')

# Initialize Elasticsearch client
es = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
    verify_certs=False
)

# Default weights for the hybrid query
DEFAULT_WEIGHTS = {
    'description_semantic_elser': 2,
    'description_semantic_google': 2.5,
    'description_semantic_e5': 2,
    'product_name_semantic_elser': 2,
    'product_name_semantic_google': 2.5,
    'product_name_semantic_e5': 2,
    'multi_match': 2,
    'model_number': 2.9,
    'product_id': 2.9
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
        rerank_field = data.get('rerank_field', 'description')
        
        # Generate the hybrid query
        search_query = generate_hybrid_query(query_text, weights, multi_match_fields, enable_reranking, rerank_field)
        
        # Execute the search
        response = es.search(
            index=INDEX_NAME,
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
        rerank_field = data.get('rerank_field', 'description')
        
        # Generate the hybrid query
        search_query = generate_hybrid_query(query_text, weights, multi_match_fields, enable_reranking, rerank_field)
        
        return jsonify({
            'success': True,
            'query': search_query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        product_id = data.get('product_id', '')
        
        print(f"DEBUG: Looking for recommendations for product_id: {product_id}")
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400
        
        # Query the recommendations index
        recommendation_query = {
            "query": {
                "term": {
                    "product_id": product_id
                }
            },
            "size": 1
        }
        
        recommendation_response = es.search(
            index=RECOMMENDATION_ENGINE_INDEX_NAME,
            body=recommendation_query
        )
        
        print(f"DEBUG: Recommendation query response: {recommendation_response}")
        
        if not recommendation_response['hits']['hits']:
            print(f"DEBUG: No recommendations found for product_id: {product_id}")
            return jsonify({
                'success': True,
                'recommendations': []
            })
        
        # Extract recommended product IDs from the recommendation field
        recommendation_doc = recommendation_response['hits']['hits'][0]['_source']
        recommendation_field = recommendation_doc.get('recommendation', {})
        
        # Get the top recommended product IDs (rank_features field contains product_id: score pairs)
        recommended_product_ids = []
        if recommendation_field:
            # Sort by score and get top 5 recommendations
            sorted_recommendations = sorted(recommendation_field.items(), key=lambda x: x[1], reverse=True)
            recommended_product_ids = [product_id for product_id, score in sorted_recommendations[:5]]
            print(f"DEBUG: Found recommended product IDs: {recommended_product_ids}")
        
        if not recommended_product_ids:
            print(f"DEBUG: No recommended product IDs found")
            return jsonify({
                'success': True,
                'recommendations': []
            })
        
        # Query the products index to get full product details for recommended items
        # Search by product_id field using terms query
        products_query = {
            "query": {
                "terms": {
                    "product_id": recommended_product_ids
                }
            },
            "size": len(recommended_product_ids)
        }
        
        products_response = es.search(
            index=INDEX_NAME,
            body=products_query
        )
        
        # Process recommended products
        recommendations = []
        for hit in products_response['hits']['hits']:
            source = hit['_source']
            product = {
                'id': hit['_id'],
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
            recommendations.append(product)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_hybrid_query(query_text, weights, multi_match_fields, enable_reranking=False, rerank_field='description'):
    """Generate the hybrid query using bool/should structure or reranking structure"""
    
    if enable_reranking:
        return generate_reranking_query(query_text, weights, multi_match_fields, rerank_field)
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
        if field in weights:
            should_clauses.append({
                "match": {
                    field: {
                        "query": query_text,
                        "boost": weights[field]
                    }
                }
            })
    
    # Add multi_match clause
    if 'multi_match' in weights and multi_match_fields:
        should_clauses.append({
            "multi_match": {
                "query": query_text,
                "fields": multi_match_fields,
                "boost": weights['multi_match']
            }
        })
    
    # Add model_number clauses (term, prefix, wildcard)
    if 'model_number' in weights:
        should_clauses.append({
            "term": {
                "model_number": {
                    "value": query_text,
                    "boost": weights['model_number']
                }
            }
        })
        should_clauses.append({
            "prefix": {
                "model_number": {
                    "boost": weights['model_number'],
                    "value": query_text
                }
            }
        })
        should_clauses.append({
            "wildcard": {
                "model_number": {
                    "boost": weights['model_number'],
                    "value": f"*{query_text}*"
                }
            }
        })
    
    # Add product_id clauses (term, prefix, wildcard)
    if 'product_id' in weights:
        should_clauses.append({
            "term": {
                "product_id": {
                    "value": query_text,
                    "boost": weights['product_id']
                }
            }
        })
        should_clauses.append({
            "prefix": {
                "product_id": {
                    "boost": weights['product_id'],
                    "value": query_text
                }
            }
        })
        should_clauses.append({
            "wildcard": {
                "product_id": {
                    "boost": weights['product_id'],
                    "value": f"*{query_text}*"
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

def generate_reranking_query(query_text, weights, multi_match_fields, rerank_field='description'):
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
        if field_name in weights:
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
    if 'multi_match' in weights and multi_match_fields:
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
    
    # Add model_number retrievers (term, prefix, wildcard)
    if 'model_number' in weights:
        # Term query
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "term": {
                            "model_number": {
                                "value": query_text,
                                "boost": weights['model_number']
                            }
                        }
                    }
                }
            },
            "weight": weights['model_number']
        })
        # Prefix query
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "prefix": {
                            "model_number": {
                                "boost": weights['model_number'],
                                "value": query_text
                            }
                        }
                    }
                }
            },
            "weight": weights['model_number']
        })
        # Wildcard query
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "wildcard": {
                            "model_number": {
                                "boost": weights['model_number'],
                                "value": f"*{query_text}*"
                            }
                        }
                    }
                }
            },
            "weight": weights['model_number']
        })
    
    # Add product_id retrievers (term, prefix, wildcard)
    if 'product_id' in weights:
        # Term query
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "term": {
                            "product_id": {
                                "value": query_text,
                                "boost": weights['product_id']
                            }
                        }
                    }
                }
            },
            "weight": weights['product_id']
        })
        # Prefix query
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "prefix": {
                            "product_id": {
                                "boost": weights['product_id'],
                                "value": query_text
                            }
                        }
                    }
                }
            },
            "weight": weights['product_id']
        })
        # Wildcard query
        retrievers.append({
            "normalizer": "minmax",
            "retriever": {
                "standard": {
                    "query": {
                        "wildcard": {
                            "product_id": {
                                "boost": weights['product_id'],
                                "value": f"*{query_text}*"
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
                "field": rerank_field,  # Field to rerank on
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
