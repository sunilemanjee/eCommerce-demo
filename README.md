# E-commerce Search Applications

A collection of Flask-based e-commerce search applications that demonstrate different Elasticsearch search capabilities. These applications allow users to search through Shein products using various search strategies and configurations.

## Applications Overview

This repository contains three individual search applications that can be run simultaneously:

### 1. **Hybrid Search App** (Port 8080)
- **Hybrid Search**: Combines multiple semantic search models (ELSER, Google, E5) with traditional text search
- **Configurable Weights**: Adjust search field weights in real-time through a left sidebar
- **Multi-Match Fields**: Select which text fields to include in multi-match queries
- **Semantic Reranking**: Advanced reranking capabilities for improved relevance
- **Query Visualization**: View the generated Elasticsearch query with a collapsible modal
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Updates**: 2-second debounced updates when changing weights

### 2. **Synonym App** (Port 8046)
- **Synonym Search**: Clean, focused interface for synonym-based product search
- **Synonyms Index**: Uses `ecommerce_shein_products_with_synonyms` index
- **Match Query**: Simple match query on `product_name` field
- **Highlights**: Shows search term highlights in results
- **Same UI**: Maintains the beautiful design of the original app

### 3. **Rules App** (Port 8047)
- **Dual Search Modes**: Toggle between text search and query rules
- **Text Search**: Standard match query on `product_name`
- **Query Rules**: Uses Elasticsearch query rules with "labubu" ruleset
- **Visual Indicators**: Shows which search type was used for each result
- **Comparison**: Easy side-by-side comparison of different search approaches
- **Index**: Uses `ecommerce_shein_products` (INDEX_NAME environment variable)

## Features

## Prerequisites

- Python 3.8+
- Elasticsearch cluster with the following indices:
  - `ecommerce_shein_products` (for Original Complex App and Rules App)
  - `ecommerce_shein_products_with_synonyms` (for Synonyms App)
- Required inference models configured in Elasticsearch (for Original Complex App):
  - ELSER model
  - Google embedding model
  - E5 embedding model
- Query rules configured in Elasticsearch (for Rules App):
  - "labubu" ruleset

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
export INDEX_NAME="ecommerce_shein_products"
export INDEX_WITH_SYNONYMS="ecommerce_shein_products_with_synonyms"
export UI_PORT="8533"
```

## Running the Applications

### 🚀 **Recommended: Run All Applications**
```bash
./run_apps.sh
```
This will start all three individual applications simultaneously:
- **Hybrid Search App**: http://localhost:8080
- **Synonym App**: http://localhost:8046
- **Rules App**: http://localhost:8047

The script automatically:
- Sets up the virtual environment if needed
- Loads environment variables from `variables.env`
- Kills any existing processes on the required ports
- Starts all three applications in the background
- Provides status updates and process IDs
- Handles cleanup when you press Ctrl+C

### Option 2: Run Individual Applications Manually

#### Hybrid Search App
```bash
source venv/bin/activate
source variables.env
python app.py
# Available at: http://localhost:8080
```

#### Synonym App
```bash
source venv/bin/activate
source variables.env
python simple_app.py
# Available at: http://localhost:8046
```

#### Rules App
```bash
source venv/bin/activate
source variables.env
python rules_app.py
# Available at: http://localhost:8047
```


## Usage

### Hybrid Search App (Port 8080)

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

### Synonym App (Port 8046)

1. **Enter Search Query**: Type your search terms in the search input field
2. **Search**: Click the "Search" button or press Enter to execute the search
3. **View Results**: Results will show highlights of matching terms
4. **Product Details**: Click on any product to view detailed information

### Rules App (Port 8047)

1. **Enter Search Query**: Type your search terms in the search input field
2. **Select Search Type**: Choose between:
   - **Text Search**: Standard match query on product_name
   - **Query Rules**: Uses Elasticsearch query rules with "labubu" ruleset
3. **Search**: Click the "Search" button or press Enter to execute the search
4. **Compare Results**: Results will show which search type was used with colored badges

### Query Visualization (All Apps)

- Click "Show Generated Query" to view the Elasticsearch query that will be executed
- The query updates automatically 2 seconds after making weight changes (Original Complex App)
- Use the "Copy Query" button to copy the query to your clipboard

## Architecture

### Backend (Flask)

#### Hybrid Search App
- **app.py**: Main Flask application with hybrid search endpoints
- **Search Endpoint**: `/search` - Executes hybrid search and returns products
- **Query Generation**: `/generate_query` - Generates Elasticsearch query without execution
- **Recommendations**: `/recommendations` - Provides product recommendations

#### Synonym App
- **simple_app.py**: Simplified Flask application
- **Search Endpoint**: `/search` - Executes simple match query with highlights

#### Rules App
- **rules_app.py**: Flask application with dual search modes
- **Search Endpoint**: `/search` - Executes either text search or query rules based on selection

### Frontend

- **HTML**: Bootstrap-based responsive interface
- **CSS**: Custom styling with animations and responsive design
- **JavaScript**: Real-time weight updates with debouncing (Hybrid Search App)

### Elasticsearch Integration

#### Hybrid Search App
Uses a hybrid search approach combining:
1. **Semantic Search**: Multiple embedding models for semantic understanding
2. **Traditional Search**: Multi-match queries across text fields
3. **Linear Combination**: Weighted combination of different search methods

#### Synonym App
- **Simple Match Query**: Basic match query on product_name field
- **Highlights**: Shows search term highlights in results
- **Synonyms Index**: Uses `ecommerce_shein_products_with_synonyms` index

#### Rules App
- **Text Search**: Standard match query on product_name
- **Query Rules**: Uses Elasticsearch query rules with "labubu" ruleset
- **Dual Mode**: Toggle between different search approaches

## Configuration

### Hybrid Search App

#### Default Weights
All search fields start with a weight of 2.0. You can adjust these from 0 to 10 in 0.1 increments.

#### Multi-Match Fields
By default, the multi-match query searches across:
- `description`
- `product_name`

You can add or remove fields as needed.

### Synonym App
- Uses `INDEX_WITH_SYNONYMS` environment variable
- Simple configuration with no weights or complex options

### Rules App
- Uses `INDEX_NAME` environment variable
- Toggle between text search and query rules modes
- No additional configuration required

## API Endpoints

### Hybrid Search App (Port 8080)

#### POST /search
Execute a hybrid search with the given parameters.

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

#### POST /generate_query
Generate the Elasticsearch query without executing it.

#### POST /recommendations
Get product recommendations for a given product ID.

### Synonym App (Port 8046)

#### POST /search
Execute a simple match search.

**Request Body:**
```json
{
  "query": "search terms"
}
```

### Rules App (Port 8047)

#### POST /search
Execute either text search or query rules search.

**Request Body:**
```json
{
  "query": "search terms",
  "search_type": "text"  // or "rules"
}
```

### Common Response Format
```json
{
  "success": true,
  "products": [...],
  "total": 100,
  "query": {...}
}
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Verify your Elasticsearch URL and API key in `variables.env`
2. **No Results**: Check that the required indices exist and contain data:
   - `ecommerce_shein_products` (for Original Complex App and Rules App)
   - `ecommerce_shein_products_with_synonyms` (for Synonym App)
3. **Model Errors**: Ensure all inference models are properly configured in Elasticsearch (Original Complex App)
4. **Query Rules Errors**: Verify the "labubu" ruleset is configured in Elasticsearch (Rules App)
5. **Port Conflicts**: Make sure ports 8080, 8046, and 8047 are available

### Debug Mode

Run individual applications in debug mode for detailed error messages:
```bash
export FLASK_DEBUG=1
python app.py              # Original Complex App
python simple_app.py       # Synonyms App
python rules_app.py        # Rules App
```

### File Structure

```
eCommerce-demo/
├── app.py                 # Hybrid Search App
├── simple_app.py          # Synonym App
├── rules_app.py           # Rules App
├── run_apps.sh            # Run All Apps Simultaneously
├── setup_env.sh           # Environment setup script
├── templates/
│   ├── index.html         # Hybrid Search App template
│   ├── simple_index.html  # Synonym App template
│   └── rules_index.html   # Rules App template
├── static/
│   ├── css/
│   │   ├── style.css      # Hybrid Search App styles
│   │   ├── simple_style.css # Synonym App styles
│   │   └── rules_style.css  # Rules App styles
│   └── js/
│       ├── app.js         # Hybrid Search App JavaScript
│       ├── simple_app.js  # Synonym App JavaScript
│       └── rules_app.js   # Rules App JavaScript
├── mappings/              # Elasticsearch field mappings
├── variables.env          # Environment configuration
└── requirements.txt       # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
