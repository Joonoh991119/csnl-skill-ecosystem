# RAG Pipeline Setup Guide for Neuroscience Papers

This guide will help you set up a complete Retrieval-Augmented Generation (RAG) pipeline to search and analyze your neuroscience papers on visual working memory and attention.

## Prerequisites

- Mac Mini M4 Pro with 64GB RAM
- PostgreSQL installed and running (verified on your system)
- Python 3.9+
- OpenAI API account (for embeddings and LLM)
- Zotero account with API access
- About 50 neuroscience papers in your Zotero library

## System Requirements

Your Mac Mini M4 Pro easily handles this workload:
- Vector embeddings are 1536-dimensional (using text-embedding-3-small)
- 50 papers with ~1000 word chunks = ~5000-10000 total chunks
- Storage: ~50MB for embeddings (1536 floats × 50k chunks)
- Memory: <2GB for operations (pgvector handles queries efficiently)
- Processing time: ~2-3 minutes for full ingestion with M4 Pro

## Step 1: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:
- `ZOTERO_API_KEY`: Get from https://www.zotero.org/settings/keys
- `ZOTERO_USER_ID`: Your Zotero user ID (shown in API settings)
- `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys
- `DB_PASSWORD`: Your PostgreSQL password

Optional variables:
- `DB_HOST`: localhost (default)
- `DB_PORT`: 5432 (default)
- `DB_NAME`: neuroscience_rag (customizable)
- `CHUNK_SIZE`: 1000 (words per chunk)
- `EMBEDDING_MODEL`: text-embedding-3-small (OpenAI model)

## Step 3: Set Up PostgreSQL Database

```bash
# Ensure PostgreSQL is running
brew services start postgresql  # if needed

# Verify PostgreSQL is accessible
psql -U postgres -c "SELECT version();"

# Create database and tables
python3 01_setup_database.py
```

Expected output:
```
Installing pgvector extension...
Creating papers table...
Creating chunks table...
Creating vector index...
Creating search history table...
Database setup completed successfully!
```

## Step 4: Ingest Papers from Zotero

```bash
# This will:
# 1. Fetch all papers from your Zotero library
# 2. Extract PDF text using PyPDF2
# 3. Store metadata in PostgreSQL
# 4. Save documents for chunking

python3 02_ingest_papers.py
```

Expected output:
```
Fetching papers from Zotero...
Found 50 relevant papers
Ingesting 50 papers...
Ingestion complete:
  Ingested: 50
  Skipped: 0
  Documents saved to: ./documents/
```

Monitor this process:
```bash
# In another terminal, check database growth
watch -n 2 'psql -U postgres -d neuroscience_rag -c "SELECT COUNT(*) as paper_count FROM papers;"'
```

## Step 5: Generate Embeddings and Chunk Documents

```bash
# This will:
# 1. Split documents into overlapping chunks
# 2. Generate embeddings using OpenAI API
# 3. Store embeddings in PostgreSQL with pgvector
# 4. Create vector index for fast retrieval

python3 03_chunking_and_embeddings.py
```

Expected output:
```
Found 50 documents to process
Processing documents: 100%
Generating embeddings for X chunks...
Embedding generation complete:
  Total chunks created: ~8000-10000
  Embedding model: text-embedding-3-small
```

Cost estimation:
- OpenAI embeddings: ~$0.02 per 1M tokens
- 50 papers ~500k words = ~65k tokens = ~$0.001

Verify embeddings:
```bash
psql -U postgres -d neuroscience_rag -c "SELECT COUNT(*) as total_chunks FROM chunks WHERE embedding IS NOT NULL;"
```

## Step 6: Query Your Papers

### Interactive Mode

```bash
python3 04_rag_query_engine.py
```

Then type your questions:
```
Your question: What papers discuss the relationship between VWM capacity and attention control?
Your question: How does working memory load affect attentional filtering?
Your question: stats
Your question: quit
```

### Command Line Mode

```bash
python3 04_rag_query_engine.py "What papers discuss VWM capacity and attention control?"
```

### Programmatic Usage

```python
from rag_query_engine import RAGQueryEngine

engine = RAGQueryEngine(top_k=5)

# Search only (no LLM)
results = engine.query(
    "How does attention modulate visual working memory?",
    use_llm=False
)

# Search + LLM synthesis
results = engine.query(
    "What neural mechanisms underlie VWM capacity limitations?",
    use_llm=True
)

# Get statistics
stats = engine.get_search_stats()
print(f"Total searches: {stats['total_searches']}")
```

## Query Examples

Try these example queries to test your pipeline:

1. "What is the relationship between visual working memory capacity and attention control?"
2. "How does working memory load affect attentional filtering?"
3. "What neural mechanisms limit visual working memory capacity?"
4. "How does attention modulate consolidation of working memory representations?"
5. "What are the neurophysiological correlates of working memory maintenance?"

## Advanced Configuration

### Adjust Chunk Size and Overlap

For more granular retrieval, reduce chunk size:
```bash
CHUNK_SIZE=500 CHUNK_OVERLAP=100 python3 03_chunking_and_embeddings.py
```

### Use Different Embedding Models

OpenAI provides several models:
```bash
# Smaller, faster, cheaper
EMBEDDING_MODEL=text-embedding-3-small python3 03_chunking_and_embeddings.py

# Larger, slower, more accurate
EMBEDDING_MODEL=text-embedding-3-large python3 03_chunking_and_embeddings.py
```

### Scale to More Papers

The pipeline scales easily:
- For 200+ papers: Use `CHUNK_SIZE=500` for more granular retrieval
- For 1000+ papers: Consider adding IVFFlat index parameters
- For high concurrency: Use connection pooling (psycopg2-pool)

### Monitor Database

```bash
# Check all metrics
psql -U postgres -d neuroscience_rag << EOF
SELECT 'Papers' as metric, COUNT(*) as count FROM papers
UNION ALL
SELECT 'Chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'Searches', COUNT(*) FROM search_history;
EOF

# Check search performance
psql -U postgres -d neuroscience_rag -c "SELECT * FROM search_history ORDER BY created_at DESC LIMIT 10;"
```

## Troubleshooting

### PostgreSQL Connection Error
```bash
# Make sure PostgreSQL is running
brew services start postgresql

# Test connection
psql -U postgres -c "SELECT 1"
```

### Missing API Keys
```bash
# Verify all required vars are set
grep -E "ZOTERO_|OPENAI_|DB_" .env
```

### Slow Embeddings
- First run generates embeddings (rate-limited by OpenAI)
- Subsequent queries are cached (1-2ms latency)
- Consider batching large ingestations

### Memory Issues
- Your 64GB RAM easily handles this workload
- pgvector IVFFlat index uses ~5-10% RAM
- Monitor: `top -p $(pgrep postgres)`

### Low Recall
- Increase `top_k` parameter (default 5)
- Try different chunk sizes
- Check query relevance score
- Add synonyms in query (e.g., "VWM" = "visual working memory")

## Database Maintenance

### Backup Your Database

```bash
pg_dump -U postgres neuroscience_rag > backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
psql -U postgres -c "DROP DATABASE neuroscience_rag;"
psql -U postgres < backup_20240101.sql
```

### Clear Search History

```bash
psql -U postgres -d neuroscience_rag -c "DELETE FROM search_history;"
```

### Re-index Vector Columns

```bash
psql -U postgres -d neuroscience_rag -c "REINDEX INDEX chunks_embedding_idx;"
```

## Performance Metrics

On your Mac Mini M4 Pro, you should see:
- Ingest papers: ~50-100 papers/minute
- Generate embeddings: ~20-50 tokens/second (depends on OpenAI rate limits)
- Query latency: 50-200ms (search) + 1-3s (LLM generation)
- Vector search index size: ~50-100MB for 10k chunks

## Next Steps

1. Experiment with different query types and chunk sizes
2. Add semantic similarity filtering for citation networks
3. Create topic-specific collections for subcategories
4. Export results for literature review generation
5. Integrate with citation managers for automated updates

## Support & Resources

- Zotero API: https://www.zotero.org/support/dev/web_api/v3/start
- LangChain Docs: https://python.langchain.com/
- pgvector: https://github.com/pgvector/pgvector
- OpenAI Embeddings: https://platform.openai.com/docs/models/embeddings
