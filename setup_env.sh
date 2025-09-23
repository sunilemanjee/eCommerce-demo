#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Python virtual environment...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if variables.env exists
if [ ! -f variables.env ]; then
    echo -e "${RED}Error: variables.env file not found${NC}"
    exit 1
fi

# Read variables from variables.env
source variables.env

# Validate required variables
if [ -z "$ES_URL" ] || [ -z "$ES_API_KEY" ] || [ -z "$ELSER_INFERENCE_ID" ] || [ -z "$EMBEDDING_INFERENCE_ID" ] || [ -z "$E5_INFERENCE_ID" ]; then
    echo -e "${RED}Error: ES_URL, ES_API_KEY, ELSER_INFERENCE_ID, EMBEDDING_INFERENCE_ID, and E5_INFERENCE_ID must be set in variables.env${NC}"
    exit 1
fi

# Validate URL format
if [[ ! $ES_URL =~ ^https?:// ]]; then
    echo -e "${RED}Error: ES_URL must start with http:// or https://${NC}"
    exit 1
fi

# Create .env file
cat > .env << EOL
# Elasticsearch Configuration
ES_URL=$ES_URL
ES_API_KEY=$ES_API_KEY
ELSER_INFERENCE_ID=$ELSER_INFERENCE_ID
EMBEDDING_INFERENCE_ID=$EMBEDDING_INFERENCE_ID
E5_INFERENCE_ID=$E5_INFERENCE_ID

# Generated on $(date)
EOL

echo -e "${GREEN}Environment file created successfully!${NC}"

# Check if .gitignore exists and contains .env
if [ -f .gitignore ]; then
    if ! grep -q "^\.env$" .gitignore; then
        echo ".env" >> .gitignore
    fi
    if ! grep -q "^venv$" .gitignore; then
        echo "venv" >> .gitignore
    fi
else
    echo -e "${GREEN}Creating .gitignore file...${NC}"
    echo -e ".env\nvenv" > .gitignore
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}To activate the virtual environment, run: source venv/bin/activate${NC}" 