#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting All E-commerce Search Applications...${NC}"
echo -e "${BLUE}==============================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Running setup...${NC}"
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

# Kill any processes running on the required ports
echo -e "${BLUE}Checking for existing processes on required ports...${NC}"
for port in 8080 8046 8047; do
    if lsof -ti:${port} > /dev/null 2>&1; then
        echo -e "${BLUE}Found existing process on port ${port}, killing it...${NC}"
        kill -9 $(lsof -ti:${port}) 2>/dev/null || true
    fi
done
sleep 2
echo -e "${GREEN}All ports are now free.${NC}"

echo -e "${GREEN}Starting all applications...${NC}"
echo -e "${BLUE}Applications will be available at:${NC}"
echo -e "  • Hybrid Search App:    ${YELLOW}http://localhost:8080${NC}"
echo -e "  • Synonyms App:         ${YELLOW}http://localhost:8046${NC}"
echo -e "  • Rules App:            ${YELLOW}http://localhost:8047${NC}"
echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}Press Ctrl+C to stop all applications${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping all applications...${NC}"
    jobs -p | xargs -r kill
    echo -e "${GREEN}All applications stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start all three applications in background
echo -e "${BLUE}Starting Hybrid Search App on port 8080...${NC}"
python app.py &
APP1_PID=$!

echo -e "${BLUE}Starting Synonym App on port 8046...${NC}"
python simple_app.py &
APP2_PID=$!

echo -e "${BLUE}Starting Rules App on port 8047...${NC}"
python rules_app.py &
APP3_PID=$!

# Wait a moment for apps to start
sleep 3

# Check if all apps are running
if kill -0 $APP1_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Hybrid Search App is running (PID: $APP1_PID)${NC}"
else
    echo -e "${RED}✗ Hybrid Search App failed to start${NC}"
fi

if kill -0 $APP2_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Synonym App is running (PID: $APP2_PID)${NC}"
else
    echo -e "${RED}✗ Synonym App failed to start${NC}"
fi

if kill -0 $APP3_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Rules App is running (PID: $APP3_PID)${NC}"
else
    echo -e "${RED}✗ Rules App failed to start${NC}"
fi

echo ""
echo -e "${GREEN}All applications are running!${NC}"
echo -e "${BLUE}Open your browser and navigate to:${NC}"
echo -e "  • ${YELLOW}http://localhost:8080${NC} - Hybrid Search App"
echo -e "  • ${YELLOW}http://localhost:8046${NC} - Synonym App"  
echo -e "  • ${YELLOW}http://localhost:8047${NC} - Rules App"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all applications${NC}"

# Wait for all background processes
wait
