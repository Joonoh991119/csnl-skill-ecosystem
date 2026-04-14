# ontology-rag — Prompt 3 Evaluation (Robustness/Edge Cases)

**Evaluation Date:** 2026-04-14  
**Skill File:** `/private/tmp/csnl-skill-ecosystem/skills/ontology-rag/SKILL.md` (480 lines)  
**Focus:** Graph traversal edge cases — cycles, orphan nodes, multi-hop queries (3+ hops), conflicting hierarchies, SPARQL-like query failures, Korean ontology coverage

---

## Test Scenarios

### 1. Cyclic Relations in Ontology
**Scenario:** Ontology contains cycle: ART → BCS/FCS → LAMINART → ART (via feedback loop).

**Expected Behavior:**
- Multi-hop query (lines 109–128) should detect and break cycles
- Avoid infinite traversal; cap results at max_hops
- Document cycle in output (e.g., "cycle detected between ART and LAMINART")

**Actual Result:** ⚠️ **PARTIAL FAIL**
- `multi_hop_query()` uses DFS with `visited` set (lines 114–127) to prevent infinite loops
- **BUT:** `visited` is local to the DFS within each level iteration; cycles across levels may not be fully detected
- If LAMINART → ART creates back-edge, second iteration might re-traverse ART
- No explicit cycle detection or reporting to user
- Graph visualization would show cycle without highlighting it

**Impact:** Medium — Cycles are common in neuronal hierarchies (recurrent feedback); silent traversal confusion is risky.

---

### 2. Orphan Nodes Without Hierarchy
**Scenario:** Concept "adaptive resonance" exists in ontology but has no is-a parents and no part-of children; it appears in text but is disconnected.

**Expected Behavior:**
- Query expansion (lines 136–174) should handle orphan nodes gracefully
- Return the orphan concept with flag "no hierarchy" or "isolated concept"
- Do not crash or exclude it from results

**Actual Result:** ❌ **FAILS**
- `QueryExpander.expand_query()` (lines 136–174) calls `get_ancestors()` and checks `self.builder.graph.predecessors()`
- If concept is not in graph (orphan), `concept in self.builder.graph` is False (line 149)
- Orphan concept is silently skipped; no attempt to retrieve its text description
- If "adaptive resonance" is mentioned in a chapter but not linked, user query "Tell me about adaptive resonance" would fail to expand that concept

**Impact:** Medium-High — Chunks mentioning isolated concepts would be missed in hybrid search.

---

### 3. Multi-Hop Query Beyond 3 Hops (Explosion)
**Scenario:** Request: "Find all concepts related to ART in 5 hops" with a dense ontology (20 CRMB concepts × 3 relations each = ~60 edges).

**Expected Behavior:**
- Gracefully handle large result sets
- Return top-K most relevant concepts by centrality or distance
- Avoid combinatorial explosion in graph traversal

**Actual Result:** ⚠️ **PARTIAL FAIL**
- `multi_hop_query()` caps at `max_hops=3` by default (line 109)
- Each hop expands concepts linearly
- **BUT:** No deduplication across hops; same concept can appear multiple times
- With dense ontology, result set grows exponentially: hop 1 (5 concepts) → hop 2 (25) → hop 3 (125+)
- No sorting/ranking; results are unordered
- User receives overwhelmingly long "expansion" dict with duplicates and low-relevance nodes

**Impact:** Medium — Large graphs cause poor usability; users need ranked, deduplicated results.

---

### 4. Conflicting Hierarchies (Multiple Parents)
**Scenario:** Ontology has two conflicting trees:
- Tree A: Sparse Coding → Efficient Coding (EC parent)
- Tree B: Sparse Coding → ART Competition (CRMB parent)

**Expected Behavior:**
- Recognize sparse coding as multi-parentage node
- Represent both is-a paths in graph
- When bridging, explain why sparse coding appears in both trees

**Actual Result:** ⚠️ **PARTIAL FAIL**
- NetworkX DiGraph supports multi-parent (multiple incoming edges)
- `extract_relations()` (lines 56–81) correctly adds edges for both paths
- **BUT:** `get_ancestors()` (lines 90–107) performs simple DFS; doesn't track or report multiple is-a paths to root
- If user queries "What is sparse coding?" and skill traverses both EC and CRMB parents, results are merged without noting conflict
- No mechanism to say "sparse coding is both a form of EC and related to ART competition" clearly

**Impact:** Medium — Multi-parent concepts are semantically important; merging paths without clarity is misleading.

---

### 5. SPARQL-like Query Failure: Complex Traversal Predicates
**Scenario:** User requests: "Find all concepts that are part-of ART AND cause activation"

**Expected Behavior:**
- Support boolean query logic: (part-of ART) ∩ (causes activation)
- Return intersection of two graph traversals

**Actual Result:** ❌ **FAILS**
- Skill provides only single-relation traversal (lines 90–107: `get_ancestors(..., relation="is_a")`)
- No API for complex queries combining multiple relations with AND/OR/NOT
- Multi-hop query (lines 109–128) traverses all relations indiscriminately; no relation filtering in output
- User cannot express "part-of AND causes" predicates; must post-process results externally

**Impact:** High — SPARQL-like queries are standard in knowledge graph tools; absence limits expressivity.

---

### 6. SPARQL Failure: Path-Based Queries
**Scenario:** User wants to find "shortest path from ART to metabolic efficiency" or "all paths of length 3 from BCS to LAMINART."

**Expected Behavior:**
- Compute shortest path(s) between concepts
- Return path explanation (e.g., "ART → sparse coding → efficient coding → metabolic efficiency")

**Actual Result:** ❌ **FAILS**
- No shortest-path API provided
- No path enumeration or explanation
- `multi_hop_query()` returns all reachable nodes at each level but not the paths themselves
- User would have to manually trace NetworkX graph using external code

**Impact:** Medium — Path queries are interpretable; lack of path explanation reduces user understanding.

---

### 7. Korean Ontology Term Coverage
**Scenario:** Build ontology with Korean terms: 적응 공명 이론 (ART), 경계 윤곽 체계 (BCS), 희소 부호화 (sparse coding).

**Expected Behavior:**
- Ontology supports both English and Korean node names
- Queries work in both languages (e.g., "적응 공명 이론의 상위개념은?" → "Efficient Coding")
- Multilingual graph traversal

**Actual Result:** ❌ **FAILS**
- `OntologyBuilder.extract_relations()` extracts English concepts via regex (lines 56–81)
- No language detection or Korean NLP support
- `QueryExpander._extract_concepts()` (lines 167–173) matches node names case-insensitively but only in English
- Korean queries would not match any concepts; expansion would fail silently
- No bilingual node support (e.g., "ART (적응 공명 이론)" as single node)

**Impact:** High — CSNL skill ecosystem targets Korean researchers; lack of Korean ontology support is critical.

---

### 8. Ontology Extraction Failure: Ambiguous Relations
**Scenario:** Text contains: "Boundary completion is how the BCS works to integrate partial features."

**Expected Behavior:**
- Regex pattern matching should extract "boundary completion" is-a relation or parse as part-of BCS
- Skill should disambiguate between is-a and part-of

**Actual Result:** ⚠️ **PARTIAL FAIL**
- `extract_relations()` uses three regex patterns (lines 60, 68, 75) for is-a, part-of, causes
- The example sentence contains "is how" (not "is-a"); it would not match is-a pattern
- It could match "part_of" pattern ("is how the BCS works") but "boundary completion" vs. "completion" parsing is fuzzy
- Results: Relations are extracted but with low precision; false negatives are common

**Impact:** Medium — Real text uses varied phrasing; rigid regex misses many relations, leading to incomplete ontologies.

---

## Findings Summary

### What Works
1. ✓ Cycle detection via visited set in DFS traversal
2. ✓ NetworkX integration for graph construction and manipulation
3. ✓ Basic multi-hop query expansion up to 3 hops
4. ✓ Chunk-to-ontology linking with embedding-based concept matching
5. ✓ LanceDB integration for hybrid vector + graph re-ranking
6. ✓ Efficient Coding domain extension (integrated cleanly)

### What Breaks
1. ❌ **Cyclic relations underdocumented:** Cycles are detected but not highlighted to user
2. ❌ **Orphan nodes excluded:** Disconnected concepts silently fail to expand
3. ❌ **Multi-hop explosion:** Large result sets lack ranking or deduplication; poor UX
4. ❌ **Multi-parent ambiguity:** Conflicting hierarchies merged without explanation
5. ❌ **No SPARQL-like boolean queries:** Cannot express (relation1 AND relation2) predicates
6. ❌ **No path-based queries:** Shortest path, path enumeration absent; low interpretability
7. ❌ **No Korean ontology support:** Korean term extraction and queries fail; regex is English-only
8. ❌ **Low-precision relation extraction:** Regex patterns miss varied phrasing in real text

### Root Causes
- **Limited query expressivity:** Only single-relation traversal; no boolean logic or path queries
- **No language support:** Ontology builder is English-only; no Korean NLP integration
- **Weak relation extraction:** Regex is brittle; should use NER + dependency parsing
- **Limited node handling:** Orphans and disconnected subgraphs are treated as errors, not edge cases
- **No interpretability layer:** Results show node labels; no path explanations or reasoning traces

---

## Score: 2/5

**Rationale:**
- **Relevance: 3/5** — Addresses ontology-augmented RAG core concept; graph structure is sound
- **Robustness: 2/5** — Breaks on orphan nodes, cycles, multi-hop explosion; lacks edge case handling
- **Query Expressivity: 1/5** — No SPARQL support; limited to single-hop, single-relation traversal
- **Multilingual: 1/5** — English-only; Korean ontology support absent
- **Relation Extraction: 2/5** — Regex-based; misses varied phrasing, low precision
- **Interpretability: 2/5** — Returns node labels; no path explanations or reasoning traces

**Composite:** (3 + 2 + 1 + 1 + 2 + 2) / 6 = **1.83/5** → **2/5**

---

## Recommendations

### Critical Patches (Priority 1)

1. **Add cycle detection and reporting:**
   ```python
   def detect_cycles(self) -> List[List[str]]:
       """Return all cycles in the ontology graph."""
       try:
           cycles = list(nx.simple_cycles(self.graph))
           return cycles
       except nx.NetworkXError:
           return []
   
   def multi_hop_query_safe(self, concept: str, max_hops: int = 3) -> Dict:
       """Expand with cycle awareness."""
       result = self.multi_hop_query(concept, max_hops)
       cycles_in_path = [c for c in self.detect_cycles() if concept in c]
       if cycles_in_path:
           result["_warning"] = f"Cycles detected: {cycles_in_path}"
       return result
   ```

2. **Handle orphan nodes:**
   ```python
   def expand_query_with_orphans(self, query: str, max_terms: int = 10) -> Dict:
       """Expand including orphan nodes."""
       concepts = self._extract_concepts(query)
       expanded = {"original": query, "concepts": {}, "orphans": []}
       
       for concept in concepts:
           if concept in self.builder.graph:
               # Standard expansion
               expanded["concepts"][concept] = {...}
           else:
               # Concept not in graph; treat as orphan
               expanded["orphans"].append(concept)
       
       return expanded
   ```

3. **Add deduplication and ranking to multi-hop results:**
   ```python
   def multi_hop_query_ranked(self, concept: str, max_hops: int = 3) -> Dict:
       """Return deduplicated, centrality-ranked results."""
       result = self.multi_hop_query(concept, max_hops)
       
       # Deduplicate
       all_concepts = set()
       for rel_type, concepts_list in result["expansion"].items():
           all_concepts.update(concepts_list)
       
       # Rank by betweenness centrality
       centrality = nx.betweenness_centrality(self.builder.graph)
       ranked = sorted(all_concepts, key=lambda c: centrality.get(c, 0), reverse=True)
       
       return {"original": concept, "expansion_ranked": ranked[:max_terms]}
   ```

### High-Priority Patches (Priority 2)

4. **Implement SPARQL-like boolean queries:**
   ```python
   def sparql_like_query(self, query_spec: Dict) -> Set[str]:
       """Execute boolean queries over ontology.
       
       query_spec: {
           "subject": "ART",
           "predicates": [
               {"relation": "part-of", "target": None},  # part-of anything
               {"relation": "causes", "target": "activation"}  # AND causes activation
           ],
           "operator": "AND"  # or "OR"
       }
       """
       results = []
       for predicate in query_spec["predicates"]:
           relation = predicate["relation"]
           target = predicate["target"]
           
           nodes = self.builder.get_ancestors(query_spec["subject"], relation)
           if target:
               nodes = [n for n in nodes if target in n.lower()]
           results.append(set(nodes))
       
       if query_spec["operator"] == "AND":
           return set.intersection(*results) if results else set()
       else:  # OR
           return set.union(*results) if results else set()
   ```

5. **Add path-based queries with explanation:**
   ```python
   def find_paths(self, source: str, target: str, max_length: int = 5) -> List[List[str]]:
       """Find all paths between source and target concepts."""
       try:
           paths = list(nx.all_simple_paths(self.builder.graph, source, target, cutoff=max_length))
           return paths
       except nx.NetworkXNoPath:
           return []
   
   def explain_path(self, path: List[str]) -> str:
       """Generate human-readable explanation of a path."""
       explanation = f"{path[0]}"
       for i in range(len(path) - 1):
           edge_data = self.builder.graph[path[i]][path[i+1]]
           relation = edge_data.get("relation", "related-to")
           explanation += f" --[{relation}]--> {path[i+1]}"
       return explanation
   ```

6. **Add Korean NLP support:**
   ```python
   from konlpy.tag import Kkma
   
   class KoreanOntologyExtractor:
       def __init__(self):
           self.kkma = Kkma()
       
       def extract_relations_ko(self, chapter_text: str, chapter_name: str) -> Dict:
           """Extract relations from Korean text using dependency parsing."""
           # Tokenize and POS tag
           pos_tagged = self.kkma.pos(chapter_text)
           
           # Pattern: NP1-이(가) NP2-이다 (is-a relation)
           # Pattern: NP1-이(가) NP2-의 부분-이다 (part-of)
           # ... implement Korean-specific patterns
           
           return relations
       
       def support_bilingual_nodes(self, en_concept: str, ko_concept: str):
           """Register bilingual concept pair."""
           self.bilingual_map[en_concept] = ko_concept
   ```

### Medium-Priority Patches (Priority 3)

7. **Improve relation extraction with NER + dependency parsing:**
   - Replace regex with spaCy NER + dependency parser
   - Extract concepts more accurately from varied phrasings
   - Support Korean via KoNLPy integration

8. **Add interpretability layer:**
   - Track reasoning path in each query
   - Return "path_explanation" alongside results
   - Log which concepts matched which patterns

9. **Benchmark on CRMB chapter corpus:**
   - Extract 100 relations from CRMB text manually
   - Compare regex precision/recall vs. NER-based extraction
   - Measure ontology coverage (% of key concepts extracted)

---

## Testing Checklist for Next Eval

- [ ] Create ontology with cycle (ART ↔ BCS feedback) → verify no infinite loop; check cycle detection output
- [ ] Query concept not in graph → verify orphan handling (not silent skip)
- [ ] Request 5-hop expansion on dense ontology → verify results are ranked and deduplicated
- [ ] Build ontology with sparse coding having two parents (EC + CRMB) → verify both paths are preserved
- [ ] Execute SPARQL query: "(part-of ART) AND (causes activation)" → verify boolean intersection works
- [ ] Find shortest path from BCS to metabolic efficiency → verify path is returned with explanation
- [ ] Extract relations from Korean text "경계 윤곽은 BCS의 일부이다" → verify Korean extraction works
- [ ] Create query in Korean → verify concepts match and expansion succeeds

---

**Summary:** ontology-rag provides a solid knowledge graph foundation but fails on real-world complexity (cycles, orphans, Korean language, complex queries). Regex-based extraction is low-precision. Investment in NLP-based relation extraction, SPARQL support, and Korean language integration would elevate from 2/5 → 4/5.
