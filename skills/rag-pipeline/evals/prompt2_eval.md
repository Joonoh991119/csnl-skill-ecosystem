# Evaluation: EVAL PROMPT 2 (Edge Cases) - Hybrid Search Precision in LanceDB

**Date**: 2026-04-14  
**Evaluator**: Claude Agent  
**Skill**: rag-pipeline (RAG_PIPELINE_GUIDE.md)  
**Query Focus**: Hybrid search precision issues with BM25 false positives  

---

## 1. Query Completeness Assessment

### The Challenge
The user has a domain-specific problem:
- 50,000 CRMB (likely neuroscience domain) chunks stored in LanceDB (vector DB)
- BGE-M3 embeddings at 1024 dimensions (dense, high-quality model)
- Hybrid search (semantic + BM25) producing false positives
- BM25 matching "boundary" in unrelated vision chapters instead of "boundary completion in FCS"
- Goal: Improve precision without losing recall

### Sufficiency of Guidance
**Rating: 2/5 - INSUFFICIENT**

The skill provides:
- ✓ General RAG architecture overview (3-stage system)
- ✓ Embedding model alternatives (sentence-transformers models)
- ✓ Database schema basics (pgvector with PostgreSQL)
- ✓ Basic vector search and re-ranking concepts
- ✓ Performance tuning hints (batch size, index optimization)

The skill DOES NOT provide:
- ✗ Any mention of LanceDB or alternative vector databases
- ✗ Hybrid search configuration or best practices
- ✗ BM25 tuning strategies (term weighting, tokenization)
- ✗ Methods to weight semantic vs. lexical components
- ✗ Query expansion or term normalization techniques
- ✗ Precision/recall trade-off analysis
- ✗ Domain-specific vocabulary handling (what is "FCS"? boundary completion terminology)
- ✗ False positive filtering strategies

---

## 2. Specific Gaps Analysis

### Gap 1: Technology Stack Mismatch
**Problem**: Skill assumes PostgreSQL + pgvector  
**User's Context**: LanceDB (native multi-modal vector DB, different API/indexing)  
**Impact**: All specific code examples are not directly applicable

```markdown
Current skill mentions:
- PostgreSQL + pgvector for vector storage
- IVFFLAT indexing
- psycopg2 connection

User needs:
- LanceDB connection patterns
- Lance's native ANN indexing
- Hybrid search API specific to LanceDB
```

### Gap 2: Missing Hybrid Search Guidance
**Problem**: No discussion of hybrid search or combining BM25 + semantic search  
**Skill Content**:
- Section: "Query Pipeline" shows only embedding → similarity search → re-ranking
- No mention of BM25, keyword matching, or hybrid configurations
- Re-ranking assumes cross-encoder for semantic scores only

**What User Needs**:
- How to configure hybrid search in LanceDB
- BM25 component tuning (term frequency scaling, field weighting)
- Proper fusion of semantic + lexical scores (RRF, weighted sum)
- Threshold adjustment per component

### Gap 3: Domain-Specific Tokenization & Vocabulary
**Problem**: No guidance on handling domain jargon or compound terms  
**Relevant Sections**: None in skill

**User's Issue**: "boundary completion in FCS" vs "boundary" alone
- FCS is likely a domain acronym (Flow Cytometry Scoring? Functional Connectivity Space?)
- "boundary completion" is a multi-word concept

**Missing Guidance**:
- Custom tokenization for acronyms
- Domain lexicon integration
- Query term weighting (boost "FCS" more than "boundary")
- Phrase-aware indexing vs. word-level indexing

### Gap 4: Precision vs. Recall Trade-offs
**Problem**: User wants to "fix precision without losing recall" but skill doesn't discuss this tension

**Missing Content**:
```
What the skill should include:
- Similarity threshold adjustment (higher = better precision, lower = better recall)
- Number of returned results (k vs. retrieval depth)
- Re-ranking weight adjustment (emphasize exact matches vs. semantic matches)
- Document-level filtering (restrict to relevant papers first)
```

### Gap 5: Practical Debugging Strategies
**Problem**: Skill has "Troubleshooting" section but lacks diagnostic tools for precision issues

**What's Missing**:
- How to identify which component (BM25 vs. semantic) causes false positives
- Query analysis tools (is "boundary" tokenized correctly? Does embedding capture intent?)
- Manual inspection workflow (sample false positives, analyze why they ranked high)
- A/B testing hybrid parameters
- Metrics beyond accuracy (precision@k, recall@k, MRR)

---

## 3. Scoring Breakdown

### Relevance: 2/5
The skill covers RAG fundamentals but misses the specific edge case entirely:
- ✗ Wrong database technology (PostgreSQL vs. LanceDB)
- ✗ No hybrid search coverage
- ✓ Good on general embeddings and re-ranking concepts
- ✗ No domain-specific NLP guidance

**Why Not 1**: The re-ranking and embedding model selection sections have some transferable concepts.

### Completeness: 2/5
The skill provides breadth but not depth where needed:
- Covers basic RAG pipeline architecture
- Covers embedding model selection
- Does NOT cover hybrid search, precision tuning, or LanceDB specifics
- Troubleshooting section is too generic

**Why Not 1**: Skill is complete for basic use cases; just doesn't address edge cases.

### Actionability: 1/5
A user cannot directly apply this skill to solve the stated problem:
- Code examples assume PostgreSQL, not LanceDB
- No concrete hybrid search tuning examples
- No BM25 parameter recommendations
- Missing step-by-step diagnosis workflow

**Why Not 2**: The skill provides zero actionable guidance for hybrid search tuning.

### Overall Skill Score: **1.7/5** (Low utility for this edge case)

---

## 4. Improvement Recommendations

### Priority 1: Add Hybrid Search Section (CRITICAL)

**Where**: Add after "Query Pipeline" section  
**Content to Include**:

```markdown
## Hybrid Search: Combining BM25 + Semantic Retrieval

### Overview
Hybrid search combines:
- **Semantic Search**: Vector similarity (understands meaning)
- **Lexical Search**: BM25/TF-IDF (matches exact terms and phrases)

### When to Use Hybrid Search
- Domain-specific acronyms or compound terms (e.g., "boundary completion in FCS")
- Queries mixing common and rare terms
- When recall of all matching documents matters more than ranking

### LanceDB Hybrid Search Configuration

#### Basic Setup
\`\`\`python
import lancedb

# Connect to LanceDB
db = lancedb.connect("./data/lancedb")
table = db.open_table("chunks")

# Hybrid search: combine BM25 + vector similarity
results = table.search("boundary completion in FCS").where(
    "hybrid_search=true"  # Enable BM25 + semantic
).select(
    ["chunk_id", "content", "bm25_score", "semantic_score"]
).limit(10).to_list()
\`\`\`

#### Understanding Score Components
\`\`\`python
# Result structure:
# {
#   "content": "...",
#   "bm25_score": 12.5,          # Higher = more keyword matches
#   "semantic_score": 0.87,      # 0-1: semantic similarity
#   "hybrid_score": 0.92         # Fused score (method-dependent)
# }
\`\`\`

### BM25 Tuning for Precision

#### Problem: False Positives on Common Words
When "boundary" appears in unrelated contexts:

\`\`\`python
# Solution 1: Increase BM25 k1 parameter (reduces term saturation)
# - Default k1=1.2 means term frequency matters a lot
# - Higher k1 (e.g., 2.0) emphasizes first few matches
# - Lower k1 (e.g., 0.5) treats repeated terms as less important

# Solution 2: Use phrase queries
query = "\"boundary completion\" in FCS"  # Phrase match
results = table.search(query).to_list()

# Solution 3: Field-specific weighting
# Weight exact matches in title/abstract higher than body
# (Requires custom indexing; see advanced section)
\`\`\`

#### Reducing "Boundary" False Positives
\`\`\`python
# Approach A: Reduce BM25 weight in fusion
# If hybrid_score = 0.6 * bm25_norm + 0.4 * semantic_norm
# Try:        hybrid_score = 0.3 * bm25_norm + 0.7 * semantic_norm

# Approach B: Stopword filtering
# Add common domain terms to BM25 stopword list
# "boundary", "completion" as separate concepts - boost "FCS" matches

# Approach C: Query expansion
# "boundary completion in FCS" → 
# "boundary completion in flow cytometry" + synonym expansion
# Boosts semantic matching on expanded terms
\`\`\`

### Precision vs. Recall Trade-offs

| Adjustment | Effect | Use When |
|-----------|--------|----------|
| Increase semantic weight | Higher precision, lower recall | Exact matches matter most |
| Increase BM25 weight | Captures variant terminology | Terminology varies in corpus |
| Raise similarity threshold | Fewer results, higher quality | Low-precision is critical |
| Use phrase queries | Very high precision | Compound terms (e.g., "boundary completion") |
| Field-specific boosting | Precision if key info in title/abstract | Structure available |

\`\`\`

### Debugging Hybrid Search Issues

#### Step 1: Isolate Component Performance
\`\`\`python
# Test BM25 alone
bm25_results = table.search("boundary completion in FCS", 
    search_type="bm25").limit(10).to_list()

# Test semantic alone
semantic_results = table.search("boundary completion in FCS",
    search_type="vector").limit(10).to_list()

# Compare false positives between approaches
# If BM25 results include vision papers, reduce BM25 weight
\`\`\`

#### Step 2: Analyze False Positive Patterns
\`\`\`python
# For each false positive result:
# 1. Why did BM25 rank it high? (term frequency analysis)
# 2. Is the semantic score low? (indicates wrong paper)
# 3. Which words caused the match?

# Example: If "boundary detection in vision" ranks high for 
# "boundary completion in FCS":
# - "boundary" matches but context is wrong (vision vs. neuroscience)
# - Solution: Add domain context to query or filter by paper topic
\`\`\`

#### Step 3: Iterative Tuning
\`\`\`python
from sklearn.metrics import precision_recall_fscore_support

# Evaluate hybrid search quality
results = table.search(query).limit(20).to_list()
relevant = [r for r in results if is_relevant(r)]  # Manual labeling

precision = len(relevant) / len(results)
recall = len(relevant) / total_relevant_docs

print(f"Precision@20: {precision:.2%}")
print(f"Recall@20: {recall:.2%}")

# Iterate: adjust weights, retest
\`\`\`

### Advanced: Custom Fusion Methods

\`\`\`python
# Reciprocal Rank Fusion (RRF): Rank-based fusion
# Less sensitive to score scaling differences
def rrf_fusion(bm25_rank, semantic_rank, k=60):
    return 1/(k + bm25_rank) + 1/(k + semantic_rank)

# Weighted Score Fusion: Normalize then weight
# Useful if one component dominates
def weighted_fusion(bm25_score, semantic_score, bm25_weight=0.3):
    norm_bm25 = bm25_score / max_bm25  # Normalize to 0-1
    return (bm25_weight * norm_bm25) + ((1-bm25_weight) * semantic_score)
\`\`\`
```

### Priority 2: Add LanceDB-Specific Section

**Where**: Add under "System Components"  
**Content**: Connection patterns, indexing, native hybrid search API

### Priority 3: Expand Troubleshooting for Retrieval Quality

**Where**: Extend "Troubleshooting" section  
**New Subsection**: "Retrieval Precision Issues"

```markdown
### Retrieval Precision Issues

**Problem**: Hybrid search returns many false positives

1. Check BM25 component dominates (too high weight on keyword matches)
2. Analyze tokenization (is "boundary completion" split or kept as phrase?)
3. Test semantic embedding (use same BGE-M3 for query and documents)
4. Inspect corpus for vocabulary overlap (vision papers vs. neuroscience)

**Solution Workflow**:
- Step 1: Isolate component performance (BM25 vs. semantic)
- Step 2: Analyze top-10 false positives for patterns
- Step 3: Adjust fusion weights or add query refinements
- Step 4: Test with domain-specific benchmark queries
```

### Priority 4: Add Domain-Specific Guidance

**Where**: New "Advanced Topics" subsection  
**Content**: Handling acronyms, compound terms, domain vocabulary

```markdown
### Domain-Specific RAG Tuning

#### Acronyms and Specialized Terminology
- Expand acronyms in preprocessing: "FCS" → "Flow Cytometry Scoring" (if applicable)
- Use domain lexicon in query expansion
- Consider custom tokenizer aware of domain compound terms

#### Compound Concepts
For multi-word concepts like "boundary completion":
- Prefer phrase indexing (exact phrase matches)
- Boost queries containing all words together
- Lower individual word weights to reduce false positives
```

### Priority 5: Create Quick Reference Card

**New File**: `/skills/rag-pipeline/HYBRID_SEARCH_QUICKREF.md`

```markdown
# Hybrid Search Quick Reference

## Problem: High False Positives in BM25

### Quick Fixes (try in order):
1. Reduce BM25 weight: `0.3 * bm25 + 0.7 * semantic`
2. Use phrase query: `"boundary completion" in FCS`
3. Increase similarity threshold: `min_score = 0.75`
4. Add domain filters: restrict to neuroscience papers

## Common Patterns:

| Pattern | Cause | Fix |
|---------|-------|-----|
| Unrelated keyword match | BM25 too high | Lower BM25 weight |
| Missing synonyms | Semantic too low | Use query expansion |
| Generic matches | Low threshold | Raise similarity floor |
| Domain mismatch | No domain context | Add domain filters |

## Configuration Template:

```json
{
  "hybrid_search": {
    "enabled": true,
    "bm25_weight": 0.3,
    "semantic_weight": 0.7,
    "min_similarity_score": 0.7,
    "use_phrase_matching": true,
    "embedding_model": "BGE-M3",
    "embedding_dim": 1024
  }
}
```
```

---

## 5. Critical Gaps Summary Table

| Gap | Severity | Skill Content | User Need | Fix |
|-----|----------|---|---|---|
| No LanceDB support | CRITICAL | PostgreSQL only | LanceDB-specific examples | Add LanceDB section |
| No hybrid search | CRITICAL | Vector search only | BM25 + semantic fusion | Add hybrid section |
| No precision tuning | HIGH | Generic re-ranking | Score weighting, thresholds | Add tuning guide |
| No domain guidance | HIGH | Generic terms | FCS terminology, acronyms | Add domain section |
| No debug workflow | HIGH | Generic troubleshooting | False positive analysis | Add diagnostic guide |
| BGE-M3 not mentioned | MEDIUM | sentence-transformers only | High-dim dense embeddings | Update embeddings section |

---

## 6. Conclusion

### Current Skill Utility: Poor for This Use Case
The skill provides excellent foundational knowledge for building a basic RAG system with PostgreSQL, but fails to address the specific challenge of:
1. Using LanceDB (different DB, different API)
2. Tuning hybrid search for precision
3. Handling domain-specific vocabulary
4. Debugging retrieval quality issues

### Why Users Would Struggle
A user attempting to follow this skill to solve the EVAL PROMPT 2 query would:
- Find PostgreSQL examples but needs LanceDB equivalents
- Understand basic RAG but not hybrid search mechanics
- Have no BM25 tuning reference
- Lack diagnostic steps to identify false positive sources

### Recommended Action
**Refactor Skill to Support Multiple Vector DBs**: Add sections for both PostgreSQL/pgvector AND LanceDB, with explicit hybrid search guidance for each. Prioritize the "Hybrid Search" section and "Debugging Precision Issues" troubleshooting.

---

## Appendix: Evaluation Methodology

**Scoring Criteria**:
- **Relevance (1-5)**: Does the skill address the specific query?
- **Completeness (1-5)**: Does it cover all necessary concepts?
- **Actionability (1-5)**: Can a user immediately apply the guidance?

**Scoring Scale**:
- 5: Excellent - fully addresses query, comprehensive, immediately actionable
- 4: Good - mostly addresses query, good coverage, mostly actionable
- 3: Fair - partially addresses query, some gaps, moderately actionable
- 2: Poor - tangentially related, significant gaps, minimal actionable guidance
- 1: Inadequate - unrelated or contradicts the query, not actionable

**Query Interpretation**:
- Domain: Neuroscience (CRMB), vector DB (LanceDB), embeddings (BGE-M3)
- Challenge: Hybrid search false positives + precision/recall balance
- Expected Skill Content: LanceDB config, BM25 tuning, fusion strategies, debug workflows
