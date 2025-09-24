#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Elasticsearch eCommerce MCP Server...${NC}"

# Check if we're in the MCP directory
if [ ! -f "server.py" ]; then
    echo -e "${RED}Error: server.py not found. Please run this script from the MCP directory.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo -e "${RED}Error: Virtual environment not found. Please run ../setup_env.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source ../venv/bin/activate

# Install MCP dependencies if not already installed
echo -e "${GREEN}Installing MCP dependencies...${NC}"
pip install -r requirements.txt

# Check if environment variables are set
if [ -z "$ES_URL" ] || [ -z "$ES_API_KEY" ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    source ../variables.env
fi

# Validate required variables
if [ -z "$ES_URL" ] || [ -z "$ES_API_KEY" ]; then
    echo -e "${RED}Error: ES_URL and ES_API_KEY environment variables must be set${NC}"
    echo -e "${RED}Please ensure ../variables.env is properly configured${NC}"
    exit 1
fi

echo -e "${GREEN}Environment variables loaded successfully${NC}"
echo -e "${GREEN}ES_URL: ${ES_URL}${NC}"
echo -e "${GREEN}Starting MCP server...${NC}"

# Run the MCP server
python server.py
