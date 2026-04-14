---
name: rag-pipeline
description: >
  End-to-end RAG (Retrieval-Augmented Generation) pipeline builder for scientific document
  retrieval and knowledge base construction. Handles document ingestion, intelligent chunking
  (section-aware for academic papers), embedding generation (OpenRouter API or local M4 Pro
  64GB models like BGE-M3/Qwen3-Embedding-8B), vector storage (PostgreSQL+pgvector primary,
  ChromaDB fallback), and hybrid retrieval with re-ranking.
  MANDATORY TRIGGERS: Any mention of RAG, retrieval augmented generation, document search,
  semantic search, knowledge base construction, embedding, chunking, vector database,
  similarity search, building a search system, indexing documents, or "find relevant papers".
  Also trigger when user says "search my library", "find papers about X", "build a knowledge
  base", "index these documents", or needs to connect retrieval to generation. Even partial
  mentions like "I need to search through my papers" should trigger this skill.
---

# RAG Pipeline Builder

You build production-grade RAG pipelines for scientific document retrieval, optimized for
neuroscience and cognitive science literature.

## Pipeline Architecture

```
Documents → Ingestion → Chunking → Embedding → Vector Store → Retrieval → Re-ranking → Context Assembly → Generation
```

Each stage is configurable. Walk the user through decisions at each stage.

## Stage 1: Document Ingestion

Supported sources and how to handle each:

| Source | Method | Notes |
|---|---|---|
| PDF files | PyMuPDF (fitz) or pdfplumber | Preserves layout, extracts tables |
| Zotero library | Zotero MCP → get_content | Use existing MCP connection |
| arXiv papers | arXiv ID → fetch PDF/LaTeX | Prefer LaTeX for equation preservation |
| Notion pages | Notion MCP → notion-fetch | Markdown extraction |
| CSV/structured data | pandas → text conversion | Column descriptions as metadata |
| Web content | WebFetch tool | Extract main content, strip nav |

### Ingestion Script Template
```python
#!/usr/bin/env python3
"""Document ingestion for RAG pipeline"""
import fitz  # PyMuPDF
import json
from pathlib import Path

def ingest_pdf(pdf_path: str) -> dict:
    """Extract text, metadata, and structure from PDF."""
    doc = fitz.open(pdf_path)
    result = {
        'title': doc.metadata.get('title', ''),
        'authors': doc.metadata.get('author', ''),
        'pages': [],
        'full_text': ''
    }
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        result['pages'].append({
            'page_num': page_num + 1,
            'text': text,
            'images': len(page.get_images())
        })
        result['full_text'] += text + '\n'
    return result
```

## Stage 2: Chunking Strategies

Choose based on document type:

### Academic Paper Chunking (Recommended for papers)
```python
import re

def chunk_academic_paper(text: str, metadata: dict) -> list:
    """Section-aware chunking that preserves paper structure."""
    sections = re.split(
        r'\n(?=(?:Abstract|Introduction|Methods?|Materials?\s+and\s+Methods?|'
        r'Results?|Discussion|Conclusion|References|Acknowledgment))',
        text, flags=re.IGNORECASE
    )

    chunks = []
    for section in sections:
        if len(section) < 100:
            continue
        section_title = section.split('\n')[0].strip()

        # Sub-chunk if section > 1500 chars (overlap 200)
        if len(section) > 1500:
            for i in range(0, len(section), 1300):
                chunk_text = section[i:i+1500]
                chunks.append({
                    'text': chunk_text,
                    'section': section_title,
                    'metadata': metadata,
                    'char_start': i,
                    'char_end': min(i+1500, len(section))
                })
        else:
            chunks.append({
                'text': section,
                'section': section_title,
                'metadata': metadata
            })
    return chunks
```

### Sliding Window Chunking (General purpose)
```python
def chunk_sliding_window(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Simple sliding window with overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) > 50:  # Skip tiny tail chunks
            chunks.append({'text': chunk, 'char_start': i})
    return chunks
```

### Equation-Preserving Chunking (For LaTeX sources)
```python
def chunk_latex_preserving(text: str) -> list:
    """Never split inside $...$ or \\begin{equation}...\\end{equation}."""
    # Find all equation spans
    equation_spans = []
    for match in re.finditer(r'\$\$.*?\$\$|\$.*?\$|\\begin\{equation\}.*?\\end\{equation\}',
                             text, re.DOTALL):
        equation_spans.append((match.start(), match.end()))

    # Chunk at paragraph boundaries, never inside equations
    # ... implementation preserves equation integrity
```

## Stage 3: Embedding

Choose based on your priority: quality (OpenRouter API), cost (local 64GB), or speed (Ollama).

### Option A: OpenRouter API (Recommended for highest quality)
```python
import requests

def embed_openrouter(texts: list, model: str = "openai/text-embedding-3-large") -> list:
    """Embed via OpenRouter API — access to strongest embedding models."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers=headers,
        json={"model": model, "input": texts}
    )
    return [item['embedding'] for item in response.json()['data']]
```

> Use OpenRouter when embedding quality matters most (initial indexing, production).
> Models available: text-embedding-3-large, voyage-3-large, etc.
> Cost: ~$0.13 per 1M tokens for text-embedding-3-large.

### Option B: Local M4 Pro 64GB (Best cost/quality tradeoff)
```python
from sentence_transformers import SentenceTransformer
import torch

def embed_local(texts: list, model_name: str = "BAAI/bge-m3") -> list:
    """Embed via sentence-transformers with MPS acceleration on M4 Pro 64GB.
    
    64GB allows running full BGE-M3 (no quantization) or Qwen3-Embedding-8B.
    """
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)
    embeddings = model.encode(
        texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True
    )
    return embeddings.tolist()

# Model options for 64GB (all fit comfortably):
# - "BAAI/bge-m3"              → 568M params, FP16 ~1.1GB, dense+sparse+multi-vector
# - "Qwen/Qwen3-Embedding-8B" → 8B params, FP16 ~16GB, 100+ languages, highest quality
# - "Qwen/Qwen3-Embedding-4B" → 4B params, FP16 ~8GB, good quality/speed balance
# - "nomic-ai/nomic-embed-text-v1.5" → 137M params, lightweight speed option
```

### Option C: Ollama (Simplest setup)
```python
import requests

def embed_ollama(texts: list, model: str = "nomic-embed-text") -> list:
    """Embed via local Ollama server. Simplest to set up."""
    embeddings = []
    for text in texts:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text}
        )
        embeddings.append(response.json()['embedding'])
    return embeddings
```

## Stage 4: Vector Storage

### PostgreSQL + pgvector (Primary — production-grade)

pgvector gives you: real SQL queries over metadata, ACID transactions, mature ecosystem,
excellent scaling, and the ability to combine vector search with relational joins.

```python
import psycopg2
from pgvector.psycopg2 import register_vector
import numpy as np

# Configuration — adjust embedding dimension to match your model
EMBEDDING_DIM = 1024  # BGE-M3: 1024, OpenAI text-embedding-3-large: 3072, Voyage-3: 1024
# Auto-detect: EMBEDDING_DIM = model.get_sentence_embedding_dimension()

def setup_pgvector(conn_string: str = "postgresql://localhost:5432/csnl_rag", embedding_dim: int = EMBEDDING_DIM):
    """Initialize PostgreSQL with pgvector extension."""
    conn = psycopg2.connect(conn_string)
    register_vector(conn)
    cur = conn.cursor()
    
    # Enable pgvector
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create chunks table with vector column
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS paper_chunks (
            id SERIAL PRIMARY KEY,
            paper_id TEXT NOT NULL,
            paper_title TEXT,
            authors TEXT,
            year INTEGER,
            section TEXT,          -- 'abstract', 'methods', 'results', etc.
            chunk_text TEXT NOT NULL,
            chunk_index INTEGER,
            embedding vector({embedding_dim}),  -- Parameterized: set EMBEDDING_DIM at top
            created_at TIMESTAMP DEFAULT NOW(),
            
            -- Metadata for filtering
            domain TEXT,            -- 'vwm', 'attention', 'neural_coding', etc.
            zotero_key TEXT,        -- Link back to Zotero library
            doi TEXT
        )
    """)
    
    # Create HNSW index for fast approximate nearest neighbor search
    cur.execute("""
        CREATE INDEX IF NOT EXISTS paper_chunks_embedding_idx 
        ON paper_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Create GIN index for full-text search (BM25-like)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS paper_chunks_text_idx
        ON paper_chunks
        USING gin(to_tsvector('english', chunk_text))
    """)
    
    conn.commit()
    return conn

def insert_chunks(conn, chunks: list, embeddings: list):
    """Insert chunks with their embeddings into pgvector."""
    cur = conn.cursor()
    for chunk, emb in zip(chunks, embeddings):
        cur.execute("""
            INSERT INTO paper_chunks 
            (paper_id, paper_title, authors, year, section, chunk_text, chunk_index, 
             embedding, domain, zotero_key, doi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            chunk['metadata'].get('paper_id', ''),
            chunk['metadata'].get('title', ''),
            chunk['metadata'].get('authors', ''),
            chunk['metadata'].get('year'),
            chunk.get('section', ''),
            chunk['text'],
            chunk.get('chunk_index', 0),
            np.array(emb),
            chunk['metadata'].get('domain', ''),
            chunk['metadata'].get('zotero_key', ''),
            chunk['metadata'].get('doi', '')
        ))
    conn.commit()

def search_pgvector(conn, query_embedding, k: int = 10, 
                    section_filter: str = None, domain_filter: str = None):
    """Semantic search with optional metadata filters."""
    cur = conn.cursor()
    
    where_clauses = []
    params = [np.array(query_embedding), k]
    
    if section_filter:
        where_clauses.append("section = %s")
        params.insert(-1, section_filter)
    if domain_filter:
        where_clauses.append("domain = %s")
        params.insert(-1, domain_filter)
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    cur.execute(f"""
        SELECT paper_id, paper_title, section, chunk_text, 
               1 - (embedding <=> %s) AS similarity
        FROM paper_chunks
        {where_sql}
        ORDER BY embedding <=> %s
        LIMIT %s
    """, [np.array(query_embedding)] + params[1:-1] + [np.array(query_embedding), k])
    
    return cur.fetchall()
```

### Hybrid Search (pgvector dense + PostgreSQL full-text)
```python
def hybrid_search_pg(conn, query: str, query_embedding, k: int = 10, alpha: float = 0.7):
    """Combine pgvector cosine similarity with PostgreSQL ts_rank (BM25-like)."""
    cur = conn.cursor()
    cur.execute("""
        WITH dense AS (
            SELECT id, chunk_text, paper_title, section,
                   1 - (embedding <=> %s) AS dense_score,
                   ROW_NUMBER() OVER (ORDER BY embedding <=> %s) AS dense_rank
            FROM paper_chunks
            ORDER BY embedding <=> %s
            LIMIT %s
        ),
        sparse AS (
            SELECT id, 
                   ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', %s)) AS sparse_score,
                   ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', %s)) DESC) AS sparse_rank
            FROM paper_chunks
            WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', %s)
            LIMIT %s
        )
        SELECT COALESCE(d.id, s.id) AS id,
               COALESCE(d.chunk_text, pc.chunk_text) AS chunk_text,
               COALESCE(d.paper_title, pc.paper_title) AS paper_title,
               COALESCE(d.section, pc.section) AS section,
               (%(alpha)s * COALESCE(1.0 / (60 + d.dense_rank), 0) + 
                (1 - %(alpha)s) * COALESCE(1.0 / (60 + s.sparse_rank), 0)) AS rrf_score
        FROM dense d
        FULL OUTER JOIN sparse s ON d.id = s.id
        LEFT JOIN paper_chunks pc ON COALESCE(d.id, s.id) = pc.id
        ORDER BY rrf_score DESC
        LIMIT %(k)s
    """, {
        'embedding': np.array(query_embedding),
        'query': query,
        'alpha': alpha,
        'k': k,
        'limit': k * 3
    })
    return cur.fetchall()
```

### ChromaDB (Fallback for development/prototyping only)
```python
import chromadb

client = chromadb.PersistentClient(path="./vector_db_dev")
collection = client.get_or_create_collection(
    name="csnl_papers_dev",
    metadata={"hnsw:space": "cosine"}
)
# Use for quick prototyping before migrating to pgvector
```

> **Why PostgreSQL over ChromaDB/LanceDB?**
> - pgvector: ACID, real SQL joins (paper metadata + vectors), mature ops tooling, backup/restore, 
>   connection pooling, monitoring (pg_stat). Industry standard.
> - ChromaDB: Fine for prototyping but lacks SQL joins, transactions, mature backup.
> - LanceDB: Good for columnar analytics but less ecosystem support than PostgreSQL.

## Stage 5: Retrieval + Re-ranking

### Hybrid Retrieval (Dense + Sparse)
```python
def hybrid_retrieve(query: str, collection, k: int = 10, alpha: float = 0.7):
    """Combine dense vector search with BM25 sparse retrieval."""
    # Dense retrieval
    dense_results = collection.query(query_texts=[query], n_results=k*2)

    # BM25 sparse (requires rank_bm25)
    from rank_bm25 import BM25Okapi
    corpus = [doc for doc in all_documents]  # Pre-tokenized
    bm25 = BM25Okapi(corpus)
    sparse_scores = bm25.get_scores(query.split())

    # Reciprocal Rank Fusion
    combined = reciprocal_rank_fusion(dense_results, sparse_scores, alpha=alpha)
    return combined[:k]
```

## Stage 6: Context Assembly

```python
def assemble_context(retrieved_chunks: list, query: str, max_tokens: int = 4000) -> str:
    """Assemble retrieved chunks into a coherent context block."""
    context_parts = []
    total_chars = 0
    for chunk in retrieved_chunks:
        if total_chars + len(chunk['text']) > max_tokens * 4:  # ~4 chars per token
            break
        source = chunk.get('source', 'Unknown')
        section = chunk.get('section', '')
        context_parts.append(f"[Source: {source} | Section: {section}]\n{chunk['text']}")
        total_chars += len(chunk['text'])

    return "\n\n---\n\n".join(context_parts)
```

## Quick Start Command

### PostgreSQL + pgvector setup (macOS)
```bash
# 1. Install PostgreSQL (if not already)
brew install postgresql@16
brew services start postgresql@16

# 2. Install pgvector extension
brew install pgvector
# Or from source: cd /tmp && git clone https://github.com/pgvector/pgvector.git && cd pgvector && make && make install

# 3. Create database
createdb csnl_rag
psql csnl_rag -c "CREATE EXTENSION vector;"

# 4. Python dependencies
pip install psycopg2-binary pgvector sentence-transformers pymupdf rank-bm25 --break-system-packages

# 5. (Optional) Ollama for lightweight embedding
brew install ollama && ollama serve
ollama pull nomic-embed-text
```

### Verify installation
```python
import psycopg2
from pgvector.psycopg2 import register_vector
conn = psycopg2.connect("postgresql://localhost:5432/csnl_rag")
register_vector(conn)
cur = conn.cursor()
cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
print(f"pgvector version: {cur.fetchone()[0]}")  # Should print 0.7.x or later
```

## CRMB_tutor Compatibility

This skill is designed to integrate with the existing CRMB_tutor pipeline
(https://github.com/Joonoh991119/CRMB_tutor). Key compatibility notes:

### LanceDB → pgvector Migration
CRMB_tutor currently uses LanceDB with BGE-M3 (1024d). To migrate:

```python
import lancedb
import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector

def migrate_lancedb_to_pgvector(lance_path: str, pg_conn_string: str):
    """Migrate existing LanceDB vectors to pgvector."""
    # Read from LanceDB
    db = lancedb.connect(lance_path)
    table = db.open_table("chunks")  # adjust table name
    df = table.to_pandas()
    
    # Write to pgvector
    conn = psycopg2.connect(pg_conn_string)
    register_vector(conn)
    cur = conn.cursor()
    
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO paper_chunks (paper_id, chunk_text, section, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (row.get('doc_id', ''), row['text'], row.get('section', ''), 
              np.array(row['vector'])))
    conn.commit()
    print(f"Migrated {len(df)} chunks from LanceDB to pgvector")
```

### Embedding Dimension — KNOWN BUG IN CRMB_tutor
CRMB_tutor has a dimension mismatch (see DIMENSION_MISMATCH_BUG.md):
- `settings.py`: LOCAL_EMBEDDING_DIM = 1024 (BGE-large-en-v1.5)
- `lance_store.py`: hardcodes `pa.list_(pa.float32(), 3072)` in schema

Before migrating, verify the actual dimension of existing vectors:
```python
import lancedb
db = lancedb.connect("./db/cmrb_lance")
table = db.open_table("cmrb_chunks")
sample = table.head(1).to_pandas()
actual_dim = len(sample['vector'].iloc[0])
print(f"Actual embedding dimension: {actual_dim}")
# Then set EMBEDDING_DIM = actual_dim
```

The skill's `EMBEDDING_DIM` config variable handles this — set it to match
whatever CRMB_tutor actually uses before running migration.

### Existing Chunker Compatibility
CRMB's `chunker_v2.py` already handles Marker-parsed markdown. The skill's
section-aware chunking complements this by adding academic paper section detection
on top of the existing chunk boundaries.

### FlagEmbedding vs sentence-transformers
CRMB_tutor uses `FlagEmbedding.BGEM3FlagModel` (3-signal: dense + sparse + ColBERT)
while this skill defaults to `sentence_transformers.SentenceTransformer` (dense-only).

For CRMB compatibility, use FlagEmbedding instead:
```python
from FlagEmbedding import BGEM3FlagModel
model = BGEM3FlagModel("BAAI/bge-m3", device="mps", use_fp16=True)
# 3-signal embedding:
output = model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=False)
dense_vecs = output['dense_vecs']     # (N, 1024)
sparse_weights = output['lexical_weights']  # sparse BM25-like
```
RRF weights from CRMB: dense=0.50, sparse=0.30, colbert=0.20 (k=60).

## Integration Points

- **Zotero MCP**: Use `search_library` → `get_content` for document ingestion
- **Paper Search MCP**: Use for discovering new papers to add to the index
- **sci-viz skill**: Visualize retrieval metrics (precision@k, recall curves)
- **eval-runner skill**: Benchmark retrieval quality on test queries
- **tutor-content-gen skill**: Consumes retrieved context to generate educational content
- **CRMB_tutor**: Direct integration with existing parsing pipeline + LanceDB migration
