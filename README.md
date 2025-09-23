# E-commerce Search Application

A Flask-based e-commerce search application that uses Elasticsearch with hybrid search capabilities. This application allows users to search through Shein products with configurable search weights and real-time query generation.

## Features

- **Hybrid Search**: Combines multiple semantic search models (ELSER, Google, E5) with traditional text search
- **Configurable Weights**: Adjust search field weights in real-time through a left sidebar
- **Multi-Match Fields**: Select which text fields to include in multi-match queries
- **Query Visualization**: View the generated Elasticsearch query with a collapsible modal
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Updates**: 2-second debounced updates when changing weights

## Prerequisites

- Python 3.8+
- Elasticsearch cluster with the `ecommerce_shein_products` index
- Required inference models configured in Elasticsearch:
  - ELSER model
  - Google embedding model
  - E5 embedding model

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd eCommerce-demo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Your variables.env file should contain export statements like:
export ES_URL="https://your-cluster.region.elastic.co:9243"
export ES_API_KEY="your-api-key-here"
export ELSER_INFERENCE_ID=".elser-2-elastic"
export EMBEDDING_INFERENCE_ID="google_vertex_ai_embeddings"
export E5_INFERENCE_ID=".multilingual-e5-small-elasticsearch"
```

## Running the Application

### Option 1: Using the startup script (Recommended)
```bash
./run_app.sh
```

### Option 2: Manual setup
```bash
# Setup environment (first time only)
source ./setup_env.sh

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source variables.env

# Start the application
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:8080
```

## Usage

### Search Interface

1. **Enter Search Query**: Type your search terms in the search input field
2. **Configure Weights**: Adjust the weights for different search fields in the left sidebar:
   - Description ELSER
   - Description Google
   - Description E5
   - Product Name ELSER
   - Product Name Google
   - Product Name E5
   - Multi Match

3. **Select Multi-Match Fields**: Choose which text fields to include in the multi-match query:
   - product_name
   - description
   - offers
   - related_products
   - top_reviews

4. **Search**: Click the "Search" button or press Enter to execute the search

### Query Visualization

- Click "Show Generated Query" to view the Elasticsearch query that will be executed
- The query updates automatically 2 seconds after making weight changes
- Use the "Copy Query" button to copy the query to your clipboard

## Architecture

### Backend (Flask)

- **app.py**: Main Flask application with search endpoints
- **Search Endpoint**: `/search` - Executes hybrid search and returns products
- **Query Generation**: `/generate_query` - Generates Elasticsearch query without execution

### Frontend

- **HTML**: Bootstrap-based responsive interface
- **CSS**: Custom styling with animations and responsive design
- **JavaScript**: Real-time weight updates with debouncing

### Elasticsearch Integration

The application uses a hybrid search approach combining:

1. **Semantic Search**: Multiple embedding models for semantic understanding
2. **Traditional Search**: Multi-match queries across text fields
3. **Linear Combination**: Weighted combination of different search methods

## Configuration

### Default Weights

All search fields start with a weight of 2.0. You can adjust these from 0 to 10 in 0.1 increments.

### Multi-Match Fields

By default, the multi-match query searches across:
- `description`
- `product_name`

You can add or remove fields as needed.

## API Endpoints

### POST /search
Execute a search with the given parameters.

**Request Body:**
```json
{
  "query": "search terms",
  "weights": {
    "description_semantic_elser": 2.0,
    "description_semantic_google": 2.0,
    "description_semantic_e5": 2.0,
    "product_name_semantic_elser": 2.0,
    "product_name_semantic_google": 2.0,
    "product_name_semantic_e5": 2.0,
    "multi_match": 2.0
  },
  "multi_match_fields": ["description", "product_name"]
}
```

**Response:**
```json
{
  "success": true,
  "products": [...],
  "total": 100,
  "query": {...}
}
```

### POST /generate_query
Generate the Elasticsearch query without executing it.

**Request Body:** Same as `/search`

**Response:**
```json
{
  "success": true,
  "query": {...}
}
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Verify your Elasticsearch URL and API key in `variables.env`
2. **No Results**: Check that the `ecommerce_shein_products` index exists and contains data
3. **Model Errors**: Ensure all inference models are properly configured in Elasticsearch

### Debug Mode

Run the application in debug mode for detailed error messages:
```bash
export FLASK_DEBUG=1
python app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
