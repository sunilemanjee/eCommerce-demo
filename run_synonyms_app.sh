#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Simple E-commerce Search Application...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Virtual environment not found. Running setup...${NC}"
    source ./setup_env.sh
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if variables.env exists
if [ ! -f "variables.env" ]; then
    echo -e "${RED}Error: variables.env file not found${NC}"
    echo "Please create variables.env with your Elasticsearch configuration"
    exit 1
fi

# Load environment variables
source variables.env

echo -e "${GREEN}Starting Simple Flask application...${NC}"
echo -e "${BLUE}Application will be available at: http://localhost:8046${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the application${NC}"

# Start the Simple Flask application
python simple_app.py
