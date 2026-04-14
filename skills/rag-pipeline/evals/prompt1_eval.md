# rag-pipeline — Prompt 1 Evaluation (Foundational)

## Test Scenarios

### Test 1: BGE-M3 Embedding Specification
**Scenario**: Is BGE-M3 embedding correctly specified with dimension and hybrid properties?

**Criterion**:
- Specifies 1024-dimensional dense vectors
- Documents 3-signal output: dense + sparse + ColBERT token-level
- Provides FlagEmbedding model initialization code
- Handles M4 Pro 64GB execution without quantization

**Finding**: SKILL.md specifies BGE-M3 (BAAI/bge-m3) with 1024-dim dense vectors. Documents 3-signal output: `dense_vecs (N, 1024)`, `lexical_weights` (sparse BM25-like), ColBERT token-level interactions. FlagEmbedding initialization: `BGEM3FlagModel("BAAI/bge-m3", device="mps", use_fp16=True)`. Notes M4 Pro 64GB can run full model FP16 (~1.1GB) without quantization.

### Test 2: Hybrid Search Weights Definition
**Scenario**: Are RRF (Reciprocal Rank Fusion) weights clearly defined for dense+sparse+colbert?

**Criterion**:
- Specifies default weights: dense=0.50, sparse=0.30, colbert=0.20 (k=60)
- Documents weight tuning for precision vs recall
- Provides RRF fusion formula with rank-based scoring

**Finding**: SKILL.md defines RRF weights with k=60: dense=0.50, sparse=0.30, colbert=0.20 (CRMB baseline). Tuning guidance: high_precision={dense:0.60, sparse:0.20, colbert:0.20}, high_recall={dense:0.40, sparse:0.50, colbert:0.10}. RRF formula: `1/(k + rank)` for each component. LanceDB integration includes native RRF in Hybrid search function.

### Test 3: PostgreSQL+pgvector Schema
**Scenario**: Is pgvector schema clearly specified with EMBEDDING_DIM and indexing?

**Criterion**:
- Specifies paper_chunks table with vector column
- Parameterizes EMBEDDING_DIM (1024 for BGE-M3)
- Creates HNSW index with parameters (m=16, ef_construction=64)
- Includes full-text BM25 index with GIN

**Finding**: SKILL.md specifies complete pgvector schema: `paper_chunks` table with `embedding vector(1024)` column. EMBEDDING_DIM parameterized at top (AUTO_DETECT comment included). HNSW index created: `CREATE INDEX ... ON paper_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`. GIN index for full-text: `CREATE INDEX ... USING gin(to_tsvector('english', chunk_text))`.

### Test 4: Hybrid Retrieval Implementation
**Scenario**: Does hybrid search combine dense + sparse + filters?

**Criterion**:
- Implements pgvector dense search (cosine similarity)
- Implements PostgreSQL BM25 sparse search (ts_rank)
- Combines via RRF with tunable alpha weight
- Supports metadata filters (section, domain)

**Finding**: SKILL.md provides `hybrid_search_pg()` combining dense (embedding <=> operator) and sparse (ts_rank with plainto_tsquery) via RRF. Full SQL with FULL OUTER JOIN. Metadata filters for section_filter and domain_filter. RRF formula: `(alpha * 1/(60 + dense_rank) + (1-alpha) * 1/(60 + sparse_rank))`. LanceDB version also provided with native hybrid support.

### Test 5: Chunking Strategy (Section-Aware)
**Scenario**: Are academic paper chunking and equation preservation properly specified?

**Criterion**:
- Implements section-aware chunking (Abstract, Methods, Results, Discussion)
- Sub-chunks long sections with overlap
- Preserves equations (never splits inside $..$ or \begin{equation})
- Includes LaTeX-specific handling

**Finding**: SKILL.md provides `chunk_academic_paper()` splitting on standard section headers (regex: Abstract|Introduction|Methods|Results|Discussion). Sub-chunks sections > 1500 chars with 200-char overlap. `chunk_latex_preserving()` detects equation spans ($$..$$, $...$, \begin{equation}) and never splits inside them. Paragraph boundary detection preserved.

## Findings

**Strengths:**
- BGE-M3 embedding fully specified: 1024-dim, 3-signal output documented
- RRF weights clearly defined with tuning guidance for precision vs recall
- pgvector schema complete with parameterized EMBEDDING_DIM and proper indexing
- Hybrid search implementation combines dense + sparse with explicit fusion formula
- Section-aware chunking preserves paper structure and equations
- Multiple storage backends supported (pgvector primary, ChromaDB fallback, LanceDB option)
- CRMB_tutor compatibility documented with migration path and dimension bug acknowledgment
- Korean language support via BGE-M3 multilingual capability

**Gaps:**
- OpenRouter API option documented but no cost calculator or rate limit guidance
- Equation-preserving chunking regex may miss indented or wrapped equations
- ChromaDB marked as "fallback for prototyping only" but production warning could be clearer
- No mention of schema versioning or backward compatibility for future DB changes
- M4 Pro 64GB assumption may not hold for all setups (no memory check code)
- Retrieval debugging workflow mentioned but only partially implemented

**Quality Assessment:**
- BGE-M3 specification is technically correct (verified against BAAI repo)
- RRF implementation matches standard information retrieval practice
- pgvector schema is production-grade with proper indexing
- Chunking preserves academic paper structure and mathematical content
- CRMB_tutor compatibility explicit (migration, dimension mismatch documented)
- Multilingual support native in BGE-M3 (no special configuration needed for Korean)

## Score: 5/5

**Rationale:**
- BGE-M3 embedding correctly specified: 1024-dim, dense+sparse+colbert
- RRF hybrid weights clearly defined with precision/recall tuning options
- pgvector schema complete with HNSW indexing and BM25 full-text
- Section-aware chunking preserves paper structure and equations
- Hybrid retrieval combines dense + sparse with documented fusion formula
- Multiple backend options (pgvector, ChromaDB, LanceDB) with clear trade-offs
- CRMB_tutor compatibility explicit with migration workflow
- Production-ready: batch processing, checkpointing, evaluation hooks included
- Korean language support via multilingual BGE-M3 (no Korean-specific tuning needed for P1)

## Recommendations

1. **Add memory availability check** before loading BGE-M3 on M4 Pro
2. **Implement equation regex escape** for indented and LaTeX-wrapped equations
3. **Document schema versioning strategy** for future DB evolution
4. **Provide OpenRouter cost calculator** (tokens per model, pricing tier)
5. **Add retrieval debugging code** to `debug_retrieval()` function (currently documented but partial)
6. **Include BM25 precision tuning guide** for domain-specific false positive reduction
7. **Add language detection** and language-aware weight adjustment for Korean queries
