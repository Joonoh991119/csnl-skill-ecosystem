#!/bin/bash

# Quick Start Script for RAG Pipeline
# Automates the complete setup process

set -e

echo "=========================================="
echo "RAG Pipeline Quick Start"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo "✓ PostgreSQL found"
echo ""

# Check PostgreSQL is running
echo "Checking PostgreSQL connection..."
if ! psql -U postgres -c "SELECT 1" &> /dev/null; then
    echo "ERROR: Cannot connect to PostgreSQL"
    echo "Start PostgreSQL with: brew services start postgresql"
    exit 1
fi
echo "✓ PostgreSQL is running"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check environment file
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    echo "Copy .env.example to .env and configure:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Verify required environment variables
echo "Verifying environment configuration..."
required_vars=("ZOTERO_API_KEY" "ZOTERO_USER_ID" "OPENAI_API_KEY" "DB_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep "^${var}=.*_here$" .env > /dev/null; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "ERROR: Missing or unconfigured variables: ${missing_vars[*]}"
    echo "Edit .env file and set all required variables"
    exit 1
fi

echo "✓ All required environment variables configured"
echo ""

# Step 1: Setup database
echo "Step 1: Setting up PostgreSQL database..."
python3 01_setup_database.py
echo ""

# Step 2: Ingest papers
echo "Step 2: Ingesting papers from Zotero..."
python3 02_ingest_papers.py
echo ""

# Step 3: Generate embeddings
echo "Step 3: Generating embeddings..."
python3 03_chunking_and_embeddings.py
echo ""

# Print summary
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Your RAG pipeline is ready. You can now:"
echo ""
echo "1. Interactive mode:"
echo "   python3 04_rag_query_engine.py"
echo ""
echo "2. Command line query:"
echo "   python3 04_rag_query_engine.py \"Your question here\""
echo ""
echo "3. See database statistics:"
echo "   psql -U postgres -d neuroscience_rag -c "
echo "     'SELECT COUNT(*) as papers FROM papers;'"
echo ""
echo "Try a test query:"
echo "   python3 04_rag_query_engine.py \\"
echo "     \"What papers discuss VWM capacity and attention control?\""
echo ""
