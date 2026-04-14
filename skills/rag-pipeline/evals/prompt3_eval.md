# Evaluation: EVAL PROMPT 3 (Robustness) - Multilingual Retrieval in Hybrid Search

**Date**: 2026-04-14  
**Evaluator**: Claude Agent  
**Skill**: rag-pipeline (RAG_PIPELINE_GUIDE.md)  
**Query Focus**: Korean query handling, mixed-language corpus BM25 false positives, multilingual debugging  

---

## 1. Korean Query Handling Analysis

### The Challenge Scenario
- **Corpus**: 15,000 chunks across CRMB (neuroscience) + efficient coding papers
- **Query**: Korean language question: "경계 완성에서 확산 방정식이 어떻게 작동하나요?" (How does the diffusion equation work in boundary completion?)
- **Expected Result**: FCS chapters on boundary completion (correct domain)
- **Actual Problem**: BM25 matches "확산" (diffusion/spreading) in unrelated chemistry papers, ranks wrong chunks at positions 2-4

### How the Skill Handles Korean Queries: SEVERE GAPS

#### Gap 1: No Multilingual Embedding Model Guidance
**Current Skill State**:
- Recommends `sentence-transformers/all-MiniLM-l6-v2` (384-dim, English-optimized)
- Also mentions general sentence-transformers alternatives
- Zero discussion of multilingual models

**What Skill Should Address**:
- Korean embeddings require models trained on Korean text
- English-only models (`all-MiniLM-l6-v2`) will encode Korean queries as out-of-distribution tokens
- Semantic similarity in Korean embedding space will be degraded or nonsensical

**Specific Problem with Korean Queries**:
```
Query in Korean: "경계 완성에서 확산 방정식이 어떻게 작동하나요?"
Current model (all-MiniLM-l6-v2):
  - Treats Korean characters as rare/unknown tokens
  - Dense embedding may collapse semantic structure
  - Embedding quality: likely 2-3x worse than English equivalent

Recommended models for Korean:
  - BGE-M3 (1024-dim, multilingual, supports 100+ languages) ✓ SKILL MENTIONS
  - multilingual-e5-large (1024-dim, supports 100+ languages)
  - Korean-SBERT (ko-sroberta-multitask, optimized for Korean)
  
Quality Impact: BGE-M3 maintains semantic quality across languages (~5% degradation vs English)
               all-MiniLM-l6-v2 likely 30-50% quality loss on Korean
```

**Skill Rating on Korean Embedding**: 1/5
- Mentions BGE-M3 briefly in embedding alternatives
- Does NOT recommend it for multilingual scenarios
- Does NOT explain why default model fails on Korean
- Does NOT provide model selection guidance by language coverage

---

#### Gap 2: No Korean Tokenization Discussion
**Current Skill State**:
- Assumes English tokenization throughout
- No mention of token boundaries in non-English languages
- Chunk size (512 tokens) not discussed in multilingual context

**Korean-Specific Challenge**:
- Korean has no spaces between words (agglutinative language)
- Standard English tokenizers (word_tokenize, NLTK) don't work on Korean
- Korean requires specialized tokenizers: Mecab, KoNLPy, Komoran

```
English query tokenization (straightforward):
"boundary" + "completion" + "diffusion" + "equation" = 4 tokens

Korean query tokenization (requires Korean NLP):
"경계 완성에서 확산 방정식이 어떻게 작동하나요?"
Without Korean tokenizer: 
  - Treated as 7 random CJK characters/subword units
  - No semantic structure recognized
  
With Korean tokenizer (Mecab):
  - "경계" (boundary, noun)
  - "완성" (completion, noun)  
  - "에서" (in/at, postposition)
  - "확산" (diffusion, noun)
  - "방정식" (equation, noun)
  - → Proper morphological analysis
```

**Skill Rating on Korean Tokenization**: 0/5
- Zero mention of multilingual tokenization
- Assumes English word-splitting throughout
- No discussion of Korean-specific NLP requirements

---

### Summary: Korean Query Embedding Quality Assessment

| Aspect | Current Skill Guidance | Impact on Korean Query | Score |
|--------|----------------------|----------------------|-------|
| Multilingual Model Selection | BGE-M3 mentioned only as alternative | Would work if selected, but not recommended | 1/5 |
| Korean Token Handling | None | Query likely tokenized incorrectly | 0/5 |
| Query Preprocessing | Not discussed | Korean morphology ignored | 0/5 |
| Multilingual Semantic Similarity | Not addressed | ~2-3x quality loss vs English | 0/5 |
| **Korean Query Handling (Overall)** | **Negligible** | **Would likely fail silently** | **0.25/5** |

---

## 2. Mixed-Language BM25 False Positives Issue Coverage

### The Problem in Detail

**Scenario**: Hybrid search with 15,000 mixed-domain chunks
- Dense search (semantic): Correctly identifies FCS chapters on boundary completion
- BM25 search: Matches the Korean term "확산" (diffusion) in **unrelated chemistry paper chunks**
- RRF Fusion: Merges results with equal weight, moving chemistry papers to rank 2-4
- English equivalent works: "boundary completion diffusion" query retrieves correctly

### Root Cause Analysis

```
Korean Query: "경계 완성에서 확산 방정식이 어떻게 작동하나요?"

BM25 Tokenization:
  Language-unaware tokenizer → splits into characters/subwords
  "확산" (Korean for "diffusion") → tokenized as rare/foreign tokens
  
Then BM25 matching occurs:
  - Corpus contains chemistry papers with "확산" in diffusion equations
  - Chemistry papers have longer text → higher term frequency
  - BM25 scores these documents high
  
Result:
  Semantic ranking: FCS papers #1 (correct)
  BM25 ranking: Chemistry papers #2-4 (false positives)
  RRF fusion (equal weight): Chemistry papers appear in top results

English Query: "boundary completion diffusion"
  - BM25 correctly tokenizes "boundary", "completion", "diffusion"
  - FCS papers have these terms in correct context
  - Chemistry papers only have "diffusion"
  - BM25 correctly ranks FCS papers higher (term combination)
```

### How the Skill Addresses This Issue

**Current Skill State**:
- Mentions BM25 only once, in passing, in the "Query Pipeline" section
- Provides NO BM25 tuning guidance
- Discusses re-ranking using cross-encoders, not hybrid search fusion
- No mention of language-specific BM25 issues

**Specific Gaps**:

#### Gap 1: No BM25 False Positive Discussion
The skill's "Troubleshooting" section includes:
- "Embedding model quality issues" → suggests trying better models
- "Database performance" → suggests indexing
- "Re-ranking quality" → suggests cross-encoder adjustment
- **MISSING**: "Retrieved results include off-topic papers" (false positive handling)

**What User Needs**:
```
Diagnosis Steps:
1. Check if false positives appear in semantic results → issue in embedding
2. Check if false positives appear in BM25 results → issue in tokenization or weighting
3. Check if false positives appear after RRF fusion → tuning issue

For Korean queries specifically:
1. Tokenize query in English vs Korean
2. Compare BM25 matches between versions
3. Adjust BM25 weight in hybrid fusion (reduce from 0.5 to 0.2)
4. Add language filter or field-specific weighting
```

**Skill Rating on False Positive Diagnosis**: 0/5

#### Gap 2: No Language-Aware BM25 Tuning
**Problem**: BM25 treats all languages equally
- Standard BM25 k1=2.0, b=0.75 may not be appropriate for CJK (Chinese/Japanese/Korean) languages
- Korean has no spaces → different tokenization behavior
- Mixed-language corpus needs per-language parameter tuning

**Missing from Skill**:
- Any mention of language-specific BM25 parameters
- Tokenization strategy selection (English vs Korean vs mixed)
- Discussion of term frequency distribution across languages
- Weight adjustment for multilingual fusion

**Skill Rating on Language-Aware Tuning**: 0/5

#### Gap 3: No Hybrid Search Fusion Details
**Problem**: RRF (Reciprocal Rank Fusion) with equal weights is naive for multilingual data
- English queries with good BM25 matches → RRF works well
- Korean queries with poor BM25 matches → RRF doesn't adjust weight

**Skill's Current Approach**:
- Mentions re-ranking with cross-encoder
- Does NOT discuss BM25 + semantic fusion methods
- Does NOT provide guidance on weight adjustment

**Missing Guidance**:
```
Naive RRF:
  final_score = 1/(rank_semantic + 60) + 1/(rank_bm25 + 60)
  Works equally poorly for Korean queries (BM25 ranks false positives high)

Adaptive weighting:
  final_score = 0.7 * semantic_score + 0.3 * bm25_score  [for high BM25 quality]
  final_score = 0.9 * semantic_score + 0.1 * bm25_score  [for low BM25 quality, e.g., Korean]
  
Language-specific:
  For English queries: use equal weights (0.5/0.5)
  For Korean/CJK queries: downweight BM25 (0.9/0.1) due to tokenization issues
```

**Skill Rating on Fusion Methods**: 0/5

#### Gap 4: No Mixed-Language Corpus Debugging
**Problem**: Corpus contains unrelated papers (CRMB + coding papers) in different languages
- Increases chance of false positives across domains
- Cross-domain contamination (chemistry papers in neuroscience corpus)

**Debugging Workflow the Skill Should Provide**:
1. Analyze corpus composition: "What % of chunks are coding vs neuroscience vs chemistry?"
2. Analyze term distribution: "Does '확산' appear in chemistry papers more than neuroscience?"
3. Field-based filtering: "Restrict to papers tagged as 'boundary completion' related"
4. Document-level filtering: "Check if false positives come from specific papers"

**Current Skill State**: No corpus analysis guidance  
**Skill Rating on Corpus Debugging**: 0/5

---

### Summary: Mixed-Language BM25 False Positives Coverage

| Aspect | Skill Guidance | For Korean Queries | Score |
|--------|---|---|---|
| BM25 tuning guidance | None (re-ranking only) | Cannot tune BM25 without guidance | 0/5 |
| Language-aware tokenization | Assumes English | Korean queries fail silently | 0/5 |
| Hybrid fusion weighting | Not discussed | Cannot adjust RRF weights | 0/5 |
| False positive diagnosis | Generic troubleshooting | No language-specific debug steps | 0/5 |
| Corpus contamination analysis | None | Cannot identify mixed-domain issues | 0/5 |
| **Mixed-Language BM25 Coverage (Overall)** | **Negligible** | **No actionable guidance** | **0/5** |

---

## 3. Language-Specific Retrieval Debugging Support

### Current Skill Debugging Capabilities

The skill provides a "Troubleshooting" section with:
1. **Embedding quality issues**
   - Suggests: "Try a larger embedding model"
   - Relevant for Korean? No (model size doesn't solve language mismatch)

2. **Re-ranking quality**
   - Suggests: "Use cross-encoder re-ranking"
   - Relevant for Korean? No (cross-encoder won't fix BM25 false positives if they rank high)

3. **Database performance**
   - Suggests: "Add indexes, increase k value"
   - Relevant for Korean? Partially (but doesn't address language issues)

### What Language-Specific Debugging Requires

#### Debug Step 1: Identify Language-Specific Issues
**Not covered by skill**: How to determine if problem is language-specific or general

**Diagnostic Script Missing**:
```python
# Compare English vs Korean performance on same query
query_en = "How does diffusion equation work in boundary completion?"
query_ko = "경계 완성에서 확산 방정식이 어떻게 작동하나요?"

# Run both queries through same pipeline
results_en = search(query_en)
results_ko = search(query_ko)

# Diagnostic output:
print(f"English query - Top result score: {results_en[0]['score']}")
print(f"Korean query - Top result score: {results_ko[0]['score']}")
print(f"English MRR@10: {calculate_mrr(results_en, threshold=0.7)}")
print(f"Korean MRR@10: {calculate_mrr(results_ko, threshold=0.7)}")

# If Korean MRR << English MRR → language-specific issue
```

**Skill Rating**: 0/5 (no comparative diagnostics provided)

---

#### Debug Step 2: Analyze Embedding Quality by Language
**Not covered by skill**: How to measure embedding quality in different languages

**What's Needed**:
```python
# Test embedding model on Korean vs English
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-l6-v2')  # English-optimized

# Similar concepts in different languages
concept_en = "diffusion equation boundary"
concept_ko = "확산 방정식 경계"  # Korean equivalent
concept_ja = "拡散方程式境界"    # Japanese equivalent

emb_en = model.encode(concept_en)
emb_ko = model.encode(concept_ko)
emb_ja = model.encode(concept_ja)

# Measure similarity between language versions of same concept
from sklearn.metrics.pairwise import cosine_similarity
sim_en_ko = cosine_similarity([emb_en], [emb_ko])[0][0]
sim_en_ja = cosine_similarity([emb_en], [emb_ja])[0][0]

print(f"English-Korean similarity: {sim_en_ko:.3f}")  # Likely ~0.3-0.4 (poor)
print(f"English-Japanese similarity: {sim_en_ja:.3f}")

# Good multilingual model (BGE-M3):
model_multi = SentenceTransformer('BAAI/bge-m3')
# Would show similarity 0.8-0.9 across languages
```

**Skill Rating**: 0/5 (no language quality measurement guidance)

---

#### Debug Step 3: Decompose BM25 vs Semantic Contribution
**Not covered by skill**: How to isolate which component causes false positives

**Missing Diagnostic Workflow**:
```python
# Run query through both retrieval paths separately
query_ko = "경계 완성에서 확산 방정식이 어떻게 작동하나요?"

# Path A: Semantic search only
semantic_results = search(query_ko, method='semantic')
print("Semantic Top-5:")
for i, result in enumerate(semantic_results[:5]):
    print(f"  {i+1}. {result['doc_title']}: {result['semantic_score']:.3f}")

# Path B: BM25 only
bm25_results = search(query_ko, method='bm25')
print("BM25 Top-5:")
for i, result in enumerate(bm25_results[:5]):
    print(f"  {i+1}. {result['doc_title']}: {result['bm25_score']:.3f}")

# Diagnostic output:
# Semantic Top-5: [FCS papers] (correct)
# BM25 Top-5: [Chemistry papers] (false positives)
# → Problem identified: BM25 component causes false positives
# → Solution: Reduce BM25 weight in fusion or improve tokenization
```

**Skill Rating**: 0/5 (no component decomposition guidance)

---

#### Debug Step 4: Tokenization Analysis
**Not covered by skill**: How to verify correct tokenization for Korean queries

**Missing Analysis**:
```python
# Show how query is tokenized
from transformers import AutoTokenizer

# English model tokenizer
en_tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
query_en = "boundary completion diffusion equation"
tokens_en = en_tokenizer.tokenize(query_en)
print(f"English tokens: {tokens_en}")
# Output: ['boundary', 'completion', 'diffusion', 'equation']

# Korean query with English model (WRONG):
query_ko = "경계 완성에서 확산 방정식이 어떻게 작동하나요?"
tokens_ko_wrong = en_tokenizer.tokenize(query_ko)
print(f"Korean with EN tokenizer: {tokens_ko_wrong}")
# Output: ['[UNK]', '[UNK]', '[UNK]', '[UNK]', ...] or subword splits

# Korean query with Korean tokenizer (CORRECT):
from koNLPy.tag import Mecab
ko_tokenizer = Mecab()
tokens_ko_right = ko_tokenizer.morphs(query_ko)
print(f"Korean with KO tokenizer: {tokens_ko_right}")
# Output: ['경계', '완성', '에서', '확산', '방정식', '이', ...]
```

**Skill Rating**: 0/5 (no tokenization analysis guidance)

---

#### Debug Step 5: Corpus Composition Analysis
**Not covered by skill**: How to understand mixed-language corpus issues

**Missing Analysis**:
```python
# Analyze corpus by language, domain, and term distribution
import json
from collections import Counter

corpus_stats = {
    'by_language': Counter(),
    'by_domain': Counter(),
    'term_diffusion_by_domain': Counter(),
}

# Count "확산" (diffusion) occurrences by domain
for doc in corpus:
    if '확산' in doc['content']:
        corpus_stats['term_diffusion_by_domain'][doc['domain']] += 1

print("Corpus Analysis:")
print(f"  Documents by language: {dict(corpus_stats['by_language'])}")
print(f"  Documents by domain: {dict(corpus_stats['by_domain'])}")
print(f"  '확산' occurrences by domain: {dict(corpus_stats['term_diffusion_by_domain'])}")

# Diagnostic insight:
# If Chemistry domain has 80% of '확산' mentions, 
# then BM25 will rank chemistry papers high on Korean query
```

**Skill Rating**: 0/5 (no corpus analysis guidance)

---

### Summary: Multilingual Debugging Support

| Debug Component | Skill Coverage | For Korean Queries | Score |
|---|---|---|---|
| Language-specific issue detection | None | Cannot diagnose language vs algorithm issues | 0/5 |
| Embedding quality measurement | None | Cannot verify Korean embedding quality | 0/5 |
| BM25 vs semantic decomposition | None | Cannot isolate false positive source | 0/5 |
| Tokenization verification | None | Cannot check if Korean tokenization is correct | 0/5 |
| Corpus composition analysis | None | Cannot understand mixed-domain contamination | 0/5 |
| **Language-Specific Debugging (Overall)** | **Zero support** | **No diagnostic tools provided** | **0/5** |

---

## 4. Multilingual Robustness Score: 1-5

### Scoring Breakdown

#### Korean Query Handling: 0.25/5
- **Model Selection**: 1/5 (BGE-M3 mentioned but not recommended for multilingual)
- **Tokenization**: 0/5 (no Korean tokenization guidance)
- **Query Preprocessing**: 0/5 (assumes English)
- **Overall**: Would likely fail silently on Korean queries

#### Mixed-Language BM25 Issues: 0/5
- **BM25 Tuning**: 0/5 (no BM25 guidance provided)
- **Language-Aware Tokenization**: 0/5 (English-only)
- **Hybrid Fusion**: 0/5 (no discussion of fusion methods)
- **False Positive Handling**: 0/5 (no diagnosis or solution)
- **Overall**: No relevant guidance for mixed-language corpus

#### Language-Specific Debugging: 0/5
- **Comparative Analysis**: 0/5 (no multi-language testing tools)
- **Embedding Diagnostics**: 0/5 (no language quality measurement)
- **Component Decomposition**: 0/5 (no BM25/semantic split analysis)
- **Tokenization Analysis**: 0/5 (no tokenizer verification)
- **Corpus Analysis**: 0/5 (no mixed-language corpus tools)
- **Overall**: Complete absence of debugging infrastructure

#### **FINAL SCORE: 0.08/5** (Inadequate for multilingual robustness)

---

## 5. Concrete Improvements: Priority Summary

**Priority 1 (CRITICAL - 300 lines)**:
- Add "Multilingual Embedding Models" section
- Compare BGE-M3, multilingual-e5, language-specific models
- Explain why default model fails on Korean
- Provide selection algorithm by language coverage

**Priority 2 (HIGH - 200 lines)**:
- Add "Multilingual BM25 Tuning" section  
- Language-aware weighting (0.85/0.15 for Korean vs 0.5/0.5 for English)
- Phrase-based matching for CJK languages
- Configuration template for rag_config.json

**Priority 3 (HIGH - 250 lines)**:
- Add "Troubleshooting: Multilingual Issues" with diagnostic utilities
- Component decomposition (semantic vs BM25 analysis)
- Tokenization verification script
- Corpus composition analysis tool
- Comparative language version testing

**Priority 4 (MEDIUM - 150 lines)**:
- Create MULTILINGUAL_QUICKREF.md
- Quick reference table for model selection
- Hybrid weight cheat sheet by language
- Common Korean query examples with fixes

**Priority 5 (MEDIUM - 100 lines)**:
- Add Korean-specific setup section
- KoNLPy/Mecab installation instructions
- Korean configuration template
- Test Korean query support validation

---

## 6. Conclusion

### FINAL MULTILINGUAL ROBUSTNESS SCORE: **0.08/5**

The skill:
- ✓ Works well for English-only RAG (monolingual, homogeneous corpus)
- ✗ Completely fails for Korean queries (0.25/5)
- ✗ Cannot handle mixed-language BM25 issues (0/5)
- ✗ Provides zero multilingual debugging support (0/5)

A user deploying on CRMB + coding papers corpus with Korean queries would:
1. Experience silent failures on Korean queries (returns wrong results without errors)
2. See false positives from unrelated domains rank high (chemistry papers for neuroscience query)
3. Have no debugging tools to understand why
4. Need external research to solve Korean NLP + BM25 tuning independently

### Required Action
Add **800-1000 lines of multilingual guidance** to achieve 3.5-4.0/5 multilingual robustness.

---

**Evaluation Date**: 2026-04-14  
**File**: /tmp/csnl-skill-ecosystem/skills/rag-pipeline/evals/prompt3_eval.md  
**Status**: Complete
