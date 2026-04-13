# RAG Pipeline for Neuroscience Research

A production-ready Retrieval-Augmented Generation (RAG) pipeline for semantic search and analysis of your neuroscience paper collection on visual working memory and attention.

## What This Does

- **Extracts papers** from your Zotero library (metadata + PDFs)
- **Chunks documents** intelligently (1000-word chunks with 200-word overlap)
- **Generates embeddings** using OpenAI's text-embedding-3-small (1536 dimensions)
- **Stores vectors** in PostgreSQL with pgvector extension (fast cosine similarity search)
- **Supports semantic queries** like "What papers discuss VWM capacity and attention control?"
- **Augments results** with GPT-4 Turbo to synthesize across papers

## Quick Start

1. Configure environment variables:
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys and DB password
   ```

2. Run the quick-start script:
   ```bash
   chmod +x 06_quick_start.sh
   ./06_quick_start.sh
   ```

   Or manually:
   ```bash
   python3 01_setup_database.py      # Create PostgreSQL schema
   python3 02_ingest_papers.py        # Import from Zotero
   python3 03_chunking_and_embeddings.py  # Generate embeddings
   ```

3. Query your papers:
   ```bash
   python3 04_rag_query_engine.py "Your question here"
   ```

   Or interactive mode:
   ```bash
   python3 04_rag_query_engine.py
   ```

## Architecture

```
┌─────────────────┐
│   Zotero API    │
│   (50 papers)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 02_ingest_papers│  Extract metadata + PDF text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   documents/    │  ~50-100k words total
│   (50 files)    │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│ 03_chunking_and_embeddings│  Split + embed
│ (OpenAI API)             │
└────────┬─────────────────┘
         │
         ▼
┌────────────────────┐
│   PostgreSQL       │
│   - papers table   │
│   - chunks table   │
│   - embeddings     │
│   (vector index)   │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ 04_rag_query_engine│
│ - Semantic search  │
│ - LLM synthesis    │
└────────────────────┘
```

## File Structure

```
outputs/
├── requirements.txt                 # Python dependencies
├── .env.example                     # Configuration template
├── 01_setup_database.py             # Create PostgreSQL schema
├── 02_ingest_papers.py              # Extract from Zotero
├── 03_chunking_and_embeddings.py   # Generate embeddings
├── 04_rag_query_engine.py          # Query interface
├── 05_setup_guide.md               # Detailed setup guide
├── 06_quick_start.sh               # Automated setup
├── 07_example_usage.py             # Usage examples
├── README.md                       # This file
└── documents/                      # Generated during ingest
    ├── 1_abc123def.txt
    ├── 2_xyz789.txt
    └── ...
```

## Configuration

All configuration is done through `.env` file:

```env
# Zotero (get from https://www.zotero.org/settings/keys)
ZOTERO_API_KEY=your_key
ZOTERO_USER_ID=your_id

# OpenAI (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_key

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=neuroscience_rag
DB_USER=postgres
DB_PASSWORD=your_password

# RAG settings
CHUNK_SIZE=1000        # Words per chunk
CHUNK_OVERLAP=200      # Overlap between chunks
EMBEDDING_MODEL=text-embedding-3-small
```

## Usage Examples

### Interactive Query
```bash
python3 04_rag_query_engine.py
```

### Command Line Query
```bash
python3 04_rag_query_engine.py "What papers discuss VWM and attention?"
```

### Python API
```python
from rag_query_engine import RAGQueryEngine

engine = RAGQueryEngine(top_k=5)

# Semantic search only
results = engine.query(
    "How does attention modulate working memory?",
    use_llm=False
)

# Search + LLM synthesis
results = engine.query(
    "Neural mechanisms of working memory capacity",
    use_llm=True
)
```

### Batch Processing
```python
questions = [
    "VWM capacity and attention control",
    "Working memory load effects",
    "Neural correlates of working memory"
]
results = engine.batch_query(questions)
```

## Performance Expectations

On Mac Mini M4 Pro with 64GB RAM:

| Operation | Time | Notes |
|-----------|------|-------|
| Ingest 50 papers | 1-2 min | Depends on PDF extraction |
| Generate embeddings | 2-5 min | Depends on OpenAI rate limits |
| Semantic search | 50-100ms | Vector index lookup |
| LLM synthesis | 1-3s | GPT-4 Turbo generation |

## Database Schema

### papers table
```sql
id SERIAL PRIMARY KEY
zotero_id TEXT UNIQUE          -- Zotero item key
title TEXT                      -- Paper title
authors TEXT                    -- Comma-separated author list
year INTEGER                    -- Publication year
abstract TEXT                   -- Paper abstract
doi TEXT                        -- Digital Object Identifier
url TEXT                        -- Paper URL
pdf_path TEXT                   -- Local PDF file path
created_at TIMESTAMP
updated_at TIMESTAMP
```

### chunks table
```sql
id SERIAL PRIMARY KEY
paper_id INTEGER REFERENCES papers
chunk_text TEXT                 -- Document segment
chunk_index INTEGER             -- Chunk number within paper
embedding vector(1536)          -- OpenAI embedding (text-embedding-3-small)
created_at TIMESTAMP
```

### search_history table
```sql
id SERIAL PRIMARY KEY
query TEXT                      -- Search query
num_results INTEGER             -- Results returned
execution_time_ms FLOAT         -- Query execution time
created_at TIMESTAMP
```

## Query Types

The system supports any natural language query about:
- Specific topics: "attention", "working memory", "capacity"
- Relationships: "relationship between VWM and attention"
- Mechanisms: "neural mechanisms", "brain regions"
- Effects: "effects of load", "effects of distraction"
- Authors/years: "recent papers on", "classic studies of"

### Example Queries

1. "What papers discuss the relationship between visual working memory capacity and attention control?"
2. "How does working memory load affect attentional filtering?"
3. "What neural mechanisms limit working memory capacity?"
4. "How does attention modulate consolidation of working memory representations?"
5. "What are the neurophysiological correlates of working memory maintenance?"
6. "Can you summarize the most cited papers on VWM?"
7. "What's the evidence for capacity limits in visual working memory?"

## Troubleshooting

### No documents found
```bash
# Check if documents were created during ingestion
ls documents/
# Check database for papers
psql -U postgres -d neuroscience_rag -c "SELECT COUNT(*) FROM papers;"
```

### Slow embeddings
- First run is slow due to OpenAI rate limits
- Subsequent queries use cached embeddings
- Cost: ~$0.001 for 50 papers (~500k words)

### Poor search results
1. Increase `top_k` (default 5) to retrieve more candidates
2. Try different query formulations
3. Check relevance scores: `similarity_score > 0.7` = good match
4. Reduce `CHUNK_SIZE` for more granular retrieval

### PostgreSQL errors
```bash
# Verify PostgreSQL is running
brew services start postgresql

# Check connection
psql -U postgres -c "SELECT version();"

# Reset database
psql -U postgres -c "DROP DATABASE IF EXISTS neuroscience_rag;"
python3 01_setup_database.py
```

## Advanced Features

### Custom Chunking Strategy
Edit `03_chunking_and_embeddings.py` to:
- Use different text splitters (semantic-based)
- Add custom preprocessing for neuroscience terminology
- Implement hierarchical chunking (sections → paragraphs)

### Extended LLM Capabilities
Edit `04_rag_query_engine.py` to:
- Add citation extraction from retrieved passages
- Generate literature review summaries
- Create comparison matrices of findings
- Extract and organize key findings by topic

### Scale to Larger Collections
For 200+ papers:
- Use smaller chunk size (500 words)
- Enable batch processing
- Add citation network analysis
- Implement topic clustering

## Cost Estimation

For your 50-paper collection:

| Service | Quantity | Unit Cost | Total |
|---------|----------|-----------|-------|
| OpenAI Embeddings | 65k tokens | $0.02/1M | $0.001 |
| OpenAI LLM Queries | 100 queries | $0.01-0.03/query | $1-3 |
| PostgreSQL | Self-hosted | Free | Free |

## Requirements

- Python 3.9+
- PostgreSQL 12+ with pgvector extension
- 64GB RAM (easily handles this dataset)
- OpenAI API account
- Zotero account with API access

## License

This project is provided as-is for research purposes. Respect copyright and licensing of all papers in your Zotero library.

## Next Steps

1. Read `05_setup_guide.md` for detailed instructions
2. Run `06_quick_start.sh` to automate setup
3. Try `07_example_usage.py` for different query patterns
4. Explore database: `psql -U postgres -d neuroscience_rag`
5. Customize LLM prompts in `04_rag_query_engine.py`

## Support

For issues:
1. Check `05_setup_guide.md` troubleshooting section
2. Verify all environment variables are set
3. Ensure PostgreSQL is running
4. Check OpenAI API quota/rate limits
5. Verify Zotero API credentials
