# Evaluation: ontology-rag Skill Against EVAL PROMPT 1

**Evaluator**: Claude Agent  
**Date**: 2026-04-14  
**Focus**: Core use case - CRMB ontology construction + concept-driven traversal + improved retrieval

---

## Prompt 1 Summary

User has CRMB chapters 1-20 parsed into markdown chunks in LanceDB. Goal:
1. Extract is-a, part-of, and causes relations between concepts (ART, BCS, FCS, LAMINART, CogEM)
2. Build concept ontology from these chunks
3. Use ontology to improve retrieval: when student asks "boundary completion", automatically traverse FCS→BCS→LAMINART and retrieve chunks from all related concepts
4. Show the **full pipeline**

---

## Section-by-Section Guidance Assessment

### Strengths - Sections That Help

#### 1. **Overview + Key Components (Structure)**
- Clear roadmap of 5 components: Ontology Construction → Query Expansion → Hybrid Retrieval → Chunk Linking → LanceDB Pipeline
- Explicitly lists expected inputs (CRMB chapters) and outputs (concept graph, re-ranked results)
- Sets expectations for domain extension (efficient coding)
- **Helps**: Gives user immediate overview of what they need to do

#### 2. **OntologyBuilder Class (Core Implementation)**
- Provides working regex patterns for all three relation types (is-a, part-of, causes)
- Uses NetworkX DiGraph: appropriate choice for directed relations
- `get_ancestors()` and `multi_hop_query()` methods directly support graph traversal (FCS→BCS→LAMINART)
- `multi_hop_query()` returns structured dict with all relation types per hop
- **Helps**: User can extract relations and traverse the graph without reinventing patterns

#### 3. **QueryExpander Class**
- `expand_query()` retrieves parents and children from ontology
- Flattens expansion into search_terms list
- Concept extraction stub with `_extract_concepts()` using graph node matching
- **Helps**: Shows how to expand "boundary completion" to find related concepts

#### 4. **ChunkOntologyLinker Class**
- Dual linking approach: (a) text-match for explicit mentions, (b) BGE-M3 embeddings for semantic relevance
- Returns matched_concepts and embedding_top_concepts with scores
- Produces ontology metadata per chunk (chunk_id, source_chapter, concept_ids, concept_scores)
- **Helps**: Solves the linking problem - which chunks belong to which ontology node

#### 5. **LanceDBOntologyPipeline Class**
- `create_table()` demonstrates adding ontology_boost column (centrality-based weighting)
- `hybrid_search()` shows re-ranking: vector distance + ontology_boost
- Explicitly combines expanded search terms (from ontology) with vector search
- **Helps**: Shows complete integration into LanceDB for improved retrieval

#### 6. **Example Usage**
- Step-by-step walkthrough: build ontology → extend with efficient coding → expand query → link chunks → hybrid search
- Output shown for each step
- **Helps**: Concrete execution flow that directly matches user's request

#### 7. **Integration with CRMB_tutor Project**
- Maps components to existing project structure
- Shows where each piece lives (concept_graph/, src/rag/, LanceDB store)
- **Helps**: Practical guidance for actually deploying in existing codebase

---

## Score Assessment (1-5 scale)

### 1. **Relevance: 5/5**
- Directly addresses all three required relation types (is-a, part-of, causes)
- Explicitly mentions target concepts (ART, BCS, FCS, LAMINART)
- Traversal logic (multi_hop_query) matches "traverse FCS→BCS→LAMINART" requirement
- Chunk-to-ontology linking directly solves the "retrieve chunks from all related concepts" problem
- Efficient coding extension shows adaptability beyond CRMB

### 2. **Completeness: 4/5**
- **Has**: All functional components (builder, expander, linker, pipeline) with working code
- **Has**: Query expansion, hybrid re-ranking, chunk metadata linking
- **Missing**: Concrete walkthrough of the EXACT scenario from prompt (user asks "boundary completion" → system traverses FCS→BCS→LAMINART → shows retrieved chunks)
- **Missing**: Actual CRMB chapter examples (uses placeholder text like "Adaptive Resonance Theory is-a competitive...")
- **Missing**: Performance benchmarks with real chapters 1-20 (only generic latency estimates)
- **Missing**: Error handling for relation extraction (what if chapter text has no relation patterns?)
- **Partial**: Concept extraction stub is lightweight; production NER/embedding-based matching not detailed

### 3. **Actionability: 4/5**
- **Excellent**: Can copy OntologyBuilder directly and run on user's chapters
- **Excellent**: Regex patterns are real and testable
- **Good**: LanceDB pipeline code is executable with minor changes (db_path, table name)
- **Good**: Example Usage section can run as-is (with mock embeddings_model)
- **Minor friction**: 
  - BGE-M3 embeddings require FlagEmbedding library (not called out explicitly)
  - _embed_text() in LanceDB pipeline uses model loading inline (inefficient in production)
  - Concept extraction _extract_concepts() is a stub; user needs to implement or integrate NER
  - ChunkOntologyLinker embedding code assumes embeddings_model has specific API (return_dense, return_sparse)

---

## Critical Gaps & Concrete Improvements

### Gap 1: Concept Extraction (⚠️ High Impact)
**Problem**: _extract_concepts() uses naive substring matching on graph nodes. For real CRMB, this misses synonyms, abbreviations, and context.

**Example**: User asks "What about the laminar model?" but ontology has "LAMINART" (not "laminar"). Naive extraction returns empty.

**Recommendation**:
- Add semantic concept matching using embeddings (embed query, find closest K ontology nodes by cosine similarity)
- Include a concept alias table: {"laminar": "LAMINART", "ART-inspired": "ART", "boundary map": "BCS"}
- Code snippet:
```python
def expand_query_semantic(self, query: str, top_k: int = 5) -> Dict:
    query_emb = self.embeddings_model.encode(query, return_dense=True)
    concept_scores = {}
    for concept in self.builder.graph.nodes():
        concept_emb = self.embeddings_model.encode(concept, return_dense=True)
        sim = cosine_similarity(query_emb["dense_vecs"], concept_emb["dense_vecs"])
        concept_scores[concept] = sim
    return sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
```

### Gap 2: Missing Walkthrough of Prompt 1 Scenario (⚠️ Medium Impact)
**Problem**: Skill shows all components but never demonstrates the exact flow: "boundary completion" → expand to [BCS, FCS, LAMINART] → traverse graph → retrieve chunks.

**Recommendation**: Add a "Worked Example" section showing:
```python
# User query
student_query = "How does boundary completion work?"

# 1. Expand via ontology
expanded = expander.expand_query(student_query)
# Output: concepts = {BCS: {parents: [visual_processing], children: [...]}, FCS: {...}}

# 2. Traverse to find related concepts
traversal = builder.multi_hop_query("BCS", max_hops=2)
# Output: expansion = {is_a: [FCS, LAMINART], part_of: [...], causes: [...]}

# 3. Hybrid search with all related concepts
results = pipeline.hybrid_search(student_query, expander, k=10)
# Output: [chunk_1 (BCS, score=0.95), chunk_2 (FCS, score=0.88), chunk_3 (LAMINART, score=0.81), ...]
```

### Gap 3: Relation Extraction Quality (⚠️ Medium Impact)
**Problem**: Regex patterns in extract_relations() are brittle. Real CRMB chapters likely have varied phrasing ("X constitutes Y", "X is fundamental to Y", "X enables Y").

**Recommendation**:
- Expand regex with alternatives: part_pattern should also match "contains", "composed of", "made up of"
- Add NLP-based extraction as fallback: use dependency parsing to find SBJ-pred-OBJ patterns
- Example:
```python
def extract_relations_nlp(self, chapter_text: str) -> Dict:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(chapter_text)
    
    relations = {"is_a": [], "part_of": [], "causes": []}
    for token in doc:
        if token.dep_ == "nsubj" and token.head.lemma_ in ["be", "comprise", "trigger"]:
            subject = token.text
            obj = [t.text for t in token.head.children if t.dep_ == "attr" or t.dep_ == "amod"]
            # ... structure extraction
```

### Gap 4: Missing Link Validation (⚠️ Medium Impact)
**Problem**: chunk.link_chunk() assigns concepts based on text match + embedding similarity, but no validation that assignments are correct. Incorrect chunk-concept links will poison retrieval.

**Recommendation**:
- Add confidence thresholding: only link if embedding similarity > 0.7 (tune on validation set)
- Add manual review step: show top 10 misaligned chunks (low text match but high embedding score)
- Code:
```python
def link_chunk_validated(self, chunk_id: str, chunk_text: str, min_sim: float = 0.7) -> Dict:
    # ... existing embedding matching ...
    top_concepts = [(c, s) for c, s in sorted_concepts if s > min_sim]
    return {
        "chunk_id": chunk_id,
        "linked_concepts": [c for c, _ in top_concepts],
        "confidence_scores": {c: float(s) for c, s in top_concepts},
        "low_confidence_alert": len(top_concepts) == 0,  # Warn if no concepts match
    }
```

### Gap 5: Performance with Full Dataset (⚠️ Low-Medium Impact)
**Problem**: Skill gives generic latency estimates ("~10-50ms per chapter") but user has 20 CRMB chapters. No guidance on batch processing, caching, or incremental updates.

**Recommendation**:
- Show batch ontology building: `for chapter in chapters: builder.add_chapter(chapter_name, text)`
- Cache embeddings to avoid recomputing (use pickle or embedding store)
- Incremental updates: `builder.add_chapter("Ch21", new_text)` without rebuilding entire graph
- Code:
```python
# Batch + caching
import pickle

ontology_cache = "ontology.pkl"
if os.path.exists(ontology_cache):
    with open(ontology_cache, "rb") as f:
        builder = pickle.load(f)
else:
    builder = OntologyBuilder()
    for ch_name, ch_text in chapters.items():
        builder.add_chapter(ch_name, ch_text)
    with open(ontology_cache, "wb") as f:
        pickle.dump(builder, f)
```

### Gap 6: Chunk Linking at Scale (⚠️ Low-Medium Impact)
**Problem**: `link_chunk()` encodes each chunk once. If user has 1000 chunks and 50 concepts, that's 1050 embedding calls. No batching strategy shown.

**Recommendation**:
```python
def link_chunks_batch(self, chunks: List[Dict]) -> List[Dict]:
    """Batch encode all chunks + concepts for efficiency."""
    chunk_texts = [c["text"] for c in chunks]
    concept_names = list(self.builder.graph.nodes())
    
    # Batch encode
    chunk_embeddings = self.embeddings_model.encode(
        chunk_texts, return_dense=True, return_sparse=True
    )
    concept_embeddings = self.embeddings_model.encode(
        concept_names, return_dense=True, return_sparse=True
    )
    
    # Compute similarity matrix once
    import numpy as np
    sims = np.dot(chunk_embeddings["dense_vecs"], concept_embeddings["dense_vecs"].T)
    
    results = []
    for chunk_idx, chunk in enumerate(chunks):
        top_concept_idx = np.argsort(sims[chunk_idx])[-5:]
        results.append({
            "chunk_id": chunk["id"],
            "linked_concepts": [concept_names[i] for i in top_concept_idx],
            "scores": sims[chunk_idx][top_concept_idx].tolist(),
        })
    return results
```

### Gap 7: Integration Testing (⚠️ Low Impact)
**Problem**: No test cases showing successful end-to-end flow with real or realistic mock data.

**Recommendation**: Add a "Test & Validate" section with small CRMB excerpt:
```python
# Minimal CRMB test chapters
test_chapters = {
    "ART": "Adaptive Resonance Theory is a neural network model. ART is-a competitive learning mechanism.",
    "BCS/FCS": "The Boundary Contour System is part of visual processing. BCS is-a form of feature detection.",
}

# Run pipeline
builder = OntologyBuilder()
for name, text in test_chapters.items():
    builder.add_chapter(name, text)

# Verify graph
assert ("Adaptive Resonance Theory", "competitive learning mechanism") in builder.graph.edges()
```

---

## Summary

| Dimension | Score | Comment |
|-----------|-------|---------|
| **Relevance** | 5/5 | Directly addresses core use case (ontology + traversal + retrieval) |
| **Completeness** | 4/5 | All components present; missing worked example of prompt scenario, real chapter examples, validation |
| **Actionability** | 4/5 | Code is executable; concept extraction stub, embedding batching, validation logic need user work |

---

## Recommended Improvements Priority

1. **High**: Add worked example showing "boundary completion" query → FCS/BCS/LAMINART traversal → chunk retrieval (directly addresses prompt scenario)
2. **High**: Implement semantic concept matching (embed query, find nearest concepts) to replace naive substring matching
3. **Medium**: Expand regex patterns and add NLP fallback for relation extraction
4. **Medium**: Add confidence-based linking validation to avoid poisoning retrieval
5. **Medium**: Show batch embedding for chunks to avoid 1000x encode calls
6. **Low**: Add test fixtures with realistic CRMB excerpts

---

## Verdict

The skill provides **solid scaffolding** for the ontology-RAG pipeline. Components are well-structured and largely actionable. However, it reads more as a **template than a complete guide**. A user following this skill would successfully build a working system but would need to:
- Implement semantic concept extraction (not just regex)
- Validate chunk-concept linking quality
- Handle embedding at scale (batch processing)
- Test on actual CRMB chapters

The missing **worked example of the exact prompt scenario** (boundary completion → BCS/FCS/LAMINART traversal) is the biggest gap. Adding that would move the skill from "reference implementation" to "complete pipeline."
