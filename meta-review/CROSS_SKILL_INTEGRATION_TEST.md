# CROSS-SKILL INTEGRATION TEST: CRMB_tutor Pipeline
**Date:** 2026-04-14  
**Test Query:** "How does boundary completion in the FCS relate to sparse coding in efficient coding theory?"  
**Project:** CRMB_tutor (10-skill neuroscience tutoring system)

---

## EXECUTIVE SUMMARY

**Current Status:** 2/10 skills implemented (sci-viz, rag-pipeline partial)  
**Overall Integration Score: 2/10 (INCOMPLETE)**

The CRMB_tutor ecosystem is in early-stage development. Only the visualization and RAG pipeline foundations exist. The nine remaining skills—critical to query understanding, content generation, and pedagogy—are absent. This document traces the **intended** pipeline architecture and identifies integration gaps.

---

## SKILL-BY-SKILL INTEGRATION ANALYSIS

### 1. PAPER-PROCESSOR

**PURPOSE:** Extract CRMB paper sections, equations, and structured data for downstream skills.

**EXPECTED FLOW:**
```
Input:  CRMB PDF (Carpenter & Grossberg neuroscience papers)
Process: → Boundary Completion Section (BCS) ↔ FCS equations
         → Population coding models
         → Sparse coding references
Output: JSON with {chapter, section, equation_id, formula, context_window}
```

**WORKS (if implemented):**
- Extracts equations in LaTeX with MathML conversion
- Identifies FCS/BCS mathematical model definitions
- Maps population coding ↔ efficient coding theory references

**GAPS:**
- **MISSING:** No implementation exists
- **CRITICAL:** Without this, RAG system has no structured CRMB paper access
- **EQUATION EXTRACTION:** No pipeline for symbolic math extraction
- **CROSS-REFERENCE:** Cannot yet identify "sparse coding" citations that relate to BCS

**DEPENDENCIES:**
- Requires: PDF loader (PyPDF2 or pdfplumber)
- Produces: JSON graph for ontology-rag to ingest
- Interfaces: ontology-rag (concept boundaries), rag-pipeline (chunk indexing)

---

### 2. ONTOLOGY-RAG

**PURPOSE:** Build concept graph linking BCS → FCS → LAMINART → efficient coding domain.

**EXPECTED FLOW:**
```
Input: "boundary completion"
  ↓
Expand: BCS definition → FCS model (related) → Cortical architecture (LAMINART)
  ↓
Cross-domain link: "sparse coding in efficient coding theory"
  ↓
Output: [concept_node, relationships, similarity_scores, evidence_chunks]
```

**WORKS (if implemented):**
- Concept expansion: boundary-completion → BCS → FCS ✓ (likely)
- LAMINART bridging (laminar cortex layer model) ✓ (expected)
- Sparse coding concept graph linkage (population coding ↔ efficiency)

**GAPS:**
- **MISSING:** No implementation exists
- **CROSS-DOMAIN BRIDGE:** Cannot yet determine population-coding ↔ sparse-coding alignment
- **SEMANTIC EXPANSION:** Depends on pre-built ontology (not present)
- **QUALITY METRIC:** No evaluation of expansion relevance

**DEPENDENCIES:**
- Requires: paper-processor output (structured CRMB content)
- Requires: Ontology definition (YAML/JSON: concepts + edges)
- Produces: Concept expansion graph for rag-pipeline
- Interfaces: rag-pipeline (query expansion), tutor-content-gen (grounding)

---

### 3. RAG-PIPELINE

**PURPOSE:** Retrieve relevant content from papers using hybrid search (BM25 + BGE-M3 embeddings).

**CURRENT STATUS:** ⚠️ PARTIAL IMPLEMENTATION EXISTS

**WORKING COMPONENTS:**
- ✓ Embedding pipeline (BGE-M3 for dense retrieval)
- ✓ RRF (Reciprocal Rank Fusion) combining BM25 + embedding scores
- ✓ Query expansion framework (ready for ontology-rag input)

**EXPECTED FLOW:**
```
Input: query = "boundary completion + sparse coding" (expanded by ontology-rag)
  ↓
BM25 Search: Match "boundary completion", "FCS", "sparse" → top-20 chunks
BGE-M3 Embedding: Dense similarity to query → top-20 chunks
  ↓
RRF Fusion: Reciprocal rank score = 1/(BM25_rank+1) + 1/(embed_rank+1)
  ↓
Output: Sorted [chunk_id, text, source_section, similarity_score]
```

**WORKS:**
- ✓ BM25 baseline tuning present (tested in evals)
- ✓ Embedding model selection (BGE-M3 optimized for cross-lingual)
- ✓ RRF fusion logic implemented
- ✓ Query preprocessing (lowercasing, tokenization)

**GAPS:**
- **FALSE POSITIVES:** BM25 "boundary" may match unrelated sections
- **SPARSE CODING RECALL:** No semantic filtering for efficient-coding context
- **EVAL COVERAGE:** Evals show single-skill config; no cross-domain test cases
- **HALLUCINATION DETECTION:** No validation of retrieved chunk relevance

**DEPENDENCIES:**
- Requires: paper-processor output (chunked CRMB content)
- Requires: ontology-rag expansions (for query augmentation)
- Produces: Top-K retrieved chunks for tutor-content-gen
- Interfaces: tutor-content-gen (content grounding), eval-runner (metrics)

---

### 4. EFFICIENT-CODING-DOMAIN

**PURPOSE:** Bridge between CRMB neural models and efficient-coding theory.

**EXPECTED FLOW:**
```
Input: Retrieved chunks on "BCS" + "sparse coding"
  ↓
Domain Bridge:
  - BCS population coding → sparsity metric (% neurons active)
  - FCS feature selectivity → sparse basis (information theory)
  ↓
Output: Domain-specific explanations + cross-theory alignment
```

**WORKS (if implemented):**
- Population coding ↔ BCS orientation columns mapping
- Sparsity = 1 - (active_neurons / total_neurons)
- Information-efficient codes (low redundancy)

**GAPS:**
- **MISSING:** No implementation exists
- **CRITICAL BRIDGE:** Without this, tutor cannot explain BCS-sparse-coding relationship
- **QUANTIFICATION:** No equations linking population sparsity to information efficiency
- **VALIDATION:** No test showing population-coding alignment

**DEPENDENCIES:**
- Requires: rag-pipeline retrieved chunks (context)
- Requires: Domain ontology (efficient coding concepts)
- Produces: Domain-bridged explanations for tutor-content-gen
- Interfaces: tutor-content-gen (content composition), eval-runner (accuracy)

---

### 5. TUTOR-CONTENT-GEN

**PURPOSE:** Compose multi-part answer combining retrieved content, domain bridges, and pedagogical structure.

**EXPECTED FLOW:**
```
Input: 
  - Retrieved chunks [BCS definition, sparse coding, equations]
  - Domain bridge [population coding ↔ sparse coding]
  ↓
Compose:
  1. Intro: "Boundary completion relates to sparse coding through..."
  2. Explanation: Retrieved + domain-bridged content
  3. Equations: LaTeX with intuitive descriptions
  4. Verification: Claims checked against CRMB chapters
  ↓
Output: Structured answer {intro, body, equations, summary}
```

**WORKS (if implemented):**
- Multi-part templating (intro → explanation → examples → summary)
- Hallucination prevention (claim verification against paper chunks)
- LaTeX equation formatting + intuitive paraphrasing

**GAPS:**
- **MISSING:** No implementation exists
- **HALLUCINATION PREVENTION:** No mechanism to verify generated claims
- **EQUATION RENDERING:** Depends on paper-processor structured equations
- **PEDAGOGICAL ADAPTATION:** No student-level detection

**DEPENDENCIES:**
- Requires: rag-pipeline chunks (content grounding)
- Requires: efficient-coding-domain bridges (cross-theory links)
- Produces: Tutor answer for sci-post-gen + conversation-sim
- Interfaces: sci-post-gen (blog adaptation), conversation-sim (response), user-feedback (routing)

---

### 6. SCI-POST-GEN

**PURPOSE:** Adapt tutor answer into blog post with appropriate template and cross-domain detection.

**EXPECTED FLOW:**
```
Input: Tutor answer {intro, body, equations, summary}
  ↓
Template Selection:
  - Query about cross-domain topic? → "Bridging neural theory + coding theory"
  - Neuroscience-only? → "CRMB model explanation"
  - Theory-only? → "Efficient coding principles"
  ↓
Cross-Domain Detection: (boundary completion + sparse coding) → YES
  ↓
Adapt:
  - Add domain-neutral intro for mixed audience
  - Highlight connection diagram
  - Separate sections by domain
  ↓
Output: Blog post with {structure, emphasis, visual_placeholders}
```

**WORKS (if implemented):**
- Template framework (sci-viz shows journal-specific configs → blog analogy)
- Cross-domain detection (keyword overlap detection)
- Structure adaptation (sections separated by domain)

**GAPS:**
- **MISSING:** No implementation exists
- **TEMPLATE LIBRARY:** No blog templates defined
- **CROSS-DOMAIN DETECTION:** Would need heuristic or ML classifier
- **VISUAL PLACEHOLDERS:** Cannot auto-suggest sci-viz figures

**DEPENDENCIES:**
- Requires: tutor-content-gen output (answer structure)
- Requires: sci-viz skill (for figure suggestions)
- Produces: Blog template + adapted content
- Interfaces: sci-viz (figure insertion), eval-runner (post quality)

---

### 7. EVAL-RUNNER

**PURPOSE:** Evaluate answer quality across multiple dimensions.

**CURRENT STATUS:** ⚠️ PARTIAL (evaluation framework exists in rag-pipeline evals)

**EXPECTED EVALUATION:**
```
Input: Generated answer + ground-truth queries
  ↓
Metrics:
  1. CORRECTNESS: Semantic match (answer claims ↔ CRMB chapters)
  2. RECALL: Did answer address all key concepts?
  3. CLARITY: Is mathematical notation explained?
  4. HALLUCINATION: Are there unsupported claims?
  ↓
Output: Scores {correctness, recall, clarity, hallucination_flag}
```

**WORKS (if implemented):**
- ✓ Metric framework exists (evals/evals.json structure)
- ✓ Iteration-based improvement tracking

**GAPS:**
- **MISSING:** Only 2 skills evaluated; no integration tests
- **GROUND TRUTH:** No labeled dataset for boundary-completion + sparse-coding
- **HALLUCINATION METRIC:** No automatic false-claim detection
- **CROSS-DOMAIN ACCURACY:** No multi-domain answer quality tests

**DEPENDENCIES:**
- Requires: tutor-content-gen output (answer to evaluate)
- Requires: Ground-truth labels (hand-labeled correct answers)
- Requires: paper-processor chunks (for hallucination checking)
- Produces: Evaluation scores for improvement iteration
- Interfaces: All skills (metric feedback)

---

### 8. CONVERSATION-SIM

**PURPOSE:** Simulate student responses to tutor answers using learned profiles.

**EXPECTED FLOW:**
```
Input: Tutor answer + Student profile {level, learning_style, language}
  ↓
Profile Types:
  - BEGINNER: Confused by equations → "좋은 설명이지만 수식이 어려워요"
  - INTERMEDIATE: Wants deeper connections
  - ADVANCED: Checks cross-domain rigor
  ↓
Generate student response based on profile
  ↓
Output: Simulated response {text, language, profile_type, confidence}
```

**WORKS (if implemented):**
- Multilingual response generation (Korean example given)
- Profile-based response variation

**GAPS:**
- **MISSING:** No implementation exists
- **PROFILE DATABASE:** No student profiles trained on conversation data
- **RESPONSE GENERATION:** Would need template + LLM fine-tuning
- **LANGUAGE DETECTION:** No heuristic for language switching

**DEPENDENCIES:**
- Requires: tutor-content-gen output (answer to respond to)
- Produces: Simulated feedback for user-feedback routing
- Interfaces: user-feedback (how to route Korean response), tutor-content-gen (adaptive re-gen)

---

### 9. USER-FEEDBACK

**PURPOSE:** Route student feedback back into the pipeline for iterative improvement.

**EXPECTED FLOW:**
```
Input: Simulated student response OR real student message
  "좋은 설명이지만 수식이 어려워요" (Korean: good explanation but equations are hard)
  ↓
Parsing:
  - Language: Korean detected
  - Sentiment: Positive + Confused
  - Topic: Equations
  ↓
Routing:
  IF confusion_about_equations:
    → tutor-content-gen (regenerate with simpler math)
    → sci-viz (add intuitive diagram)
  ↓
Feedback Loop:
  - Log: User confusion on BCS equations
  - Improve: Next similar query → prioritize conceptual explanation
  ↓
Output: Routing decisions + logging
```

**WORKS (if implemented):**
- Multilingual parsing (Korean feedback routing)
- Sentiment analysis (appreciation vs. confusion)
- Topic extraction (equations, complexity, etc.)

**GAPS:**
- **MISSING:** No implementation exists
- **LANGUAGE PARSING:** No Korean NLP pipeline
- **FEEDBACK CLASSIFICATION:** No taxonomy of student confusion types
- **CLOSED LOOP:** No mechanism to improve tutor-content-gen from feedback

**DEPENDENCIES:**
- Requires: conversation-sim output OR real student input
- Produces: Routing signals for tutor-content-gen (regeneration)
- Produces: Feedback logs for eval-runner (metric improvement)
- Interfaces: tutor-content-gen (re-generation), conversation-sim (profile updates)

---

### 10. SCI-VIZ

**PURPOSE:** Generate publication-quality figures to accompany explanations.

**CURRENT STATUS:** ✓ IMPLEMENTED (9.6 KB SKILL.md)

**WORKING COMPONENTS:**
- ✓ Publication-quality figure generation (300 DPI, journal specs)
- ✓ Psychometric function plotting (TOJ sigmoid curves)
- ✓ Neuroimaging visualization (FreeSurfer surfaces, fMRI)
- ✓ Multi-subject panel layouts
- ✓ Citation-ready output (PNG + SVG formats)

**EXPECTED FOR CROSS-SKILL INTEGRATION:**
```
Input: Answer to "boundary completion + sparse coding"
  ↓
Figure Types:
  1. BCS Architecture: Laminar cortex diagram (LAMINART)
  2. Population Coding: Neuron tuning curves (orientation, sparse)
  3. Sparse Coding: Dictionary basis visualization
  4. Connection: BCS activation pattern → sparse code analogy
  ↓
Output: {bcs_architecture.png, population_coding.svg, sparse_coding.png}
```

**WORKS:**
- ✓ Figure generation framework (matplotlib + nibabel)
- ✓ Style configurations (journal-specific: JNeurosci, etc.)
- ✓ Multi-panel layouts (group averages, subject comparisons)

**GAPS:**
- **MISSING FIGURE TYPES:** No CRMB-specific diagram templates
  - No laminar cortex cross-section (BCS/FCS layers)
  - No sparse basis dictionary visualization
  - No population coding tuning curve plots
- **AUTO-FIGURE SELECTION:** Cannot choose which figures fit an answer
- **ANNOTATION:** No automatic labeling of conceptual elements

**DEPENDENCIES:**
- Requires: tutor-content-gen output (topic determination)
- Requires: paper-processor data (for anatomical diagrams if available)
- Produces: Figures for sci-post-gen + conversation-sim context
- Interfaces: sci-post-gen (figure insertion), tutor-content-gen (visual grounding)

---

## INTEGRATION ARCHITECTURE: THE FULL PIPELINE

```
STUDENT QUESTION
"How does boundary completion relate to sparse coding?"
  ↓
ONTOLOGY-RAG [MISSING]
Expand to: BCS, FCS, sparse coding, population coding
  ↓
RAG-PIPELINE [PARTIAL]
Retrieve chunks: [BCS_section, sparse_theory, ...]
  ↓
EFFICIENT-CODING-DOMAIN [MISSING]
Bridge: population code ↔ sparse code
  ↓
TUTOR-CONTENT-GEN [MISSING]
Compose + verify answer
  ↓
├─ SCI-VIZ [EXISTS]
│  Generate figures
│
├─ SCI-POST-GEN [MISSING]
│  Adapt to blog format
│
├─ EVAL-RUNNER [PARTIAL]
│  Score answer quality
│
├─ CONVERSATION-SIM [MISSING]
│  "좋은 설명이지만 수식이 어려워요"
│
└─ USER-FEEDBACK [MISSING]
   Route response back
```

---

## INTEGRATION GAPS SUMMARY

| Skill | Status | Critical | Blocker |
|-------|--------|----------|---------|
| paper-processor | ✗ Missing | YES | RAG has no content |
| ontology-rag | ✗ Missing | YES | Cannot expand query |
| rag-pipeline | ⚠️ Partial | YES | Blocked by paper-processor |
| efficient-coding-domain | ✗ Missing | YES | Cannot bridge concepts |
| tutor-content-gen | ✗ Missing | YES | Cannot compose answer |
| sci-post-gen | ✗ Missing | NO | Optional (blog output) |
| eval-runner | ⚠️ Partial | MEDIUM | No integration metrics |
| conversation-sim | ✗ Missing | NO | Optional (pedagogy) |
| user-feedback | ✗ Missing | NO | Optional (iteration) |
| sci-viz | ✓ Exists | NO | Ready (but needs CRMB templates) |

**CRITICAL BLOCKERS FOR TEST QUERY:**
1. **paper-processor** → RAG has nothing to retrieve
2. **ontology-rag** → Cannot expand boundary-completion
3. **efficient-coding-domain** → Cannot explain the relationship
4. **tutor-content-gen** → Cannot compose answer

---

## DEPENDENCY GRAPH

```
paper-processor
  ↓
ontology-rag ← required by rag-pipeline
  ↓
rag-pipeline (PARTIAL)
  ├─→ tutor-content-gen (MISSING)
  │     ├─→ efficient-coding-domain (MISSING)
  │     ├─→ sci-post-gen (MISSING)
  │     └─→ eval-runner (PARTIAL)
  │
  ├─→ sci-viz (READY)
  │     └─→ sci-post-gen (MISSING)
  │
  └─→ eval-runner (PARTIAL)
        └─→ conversation-sim (MISSING)
              └─→ user-feedback (MISSING)
```

---

## INTEGRATION SCORE: 2/10

### SCORING BREAKDOWN

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Implementation Completeness** | 1/10 | 2/10 skills implemented |
| **Cross-Skill Coordination** | 1/10 | No shared data formats |
| **Test Coverage** | 1/10 | Single-skill evals only |
| **Dependency Resolution** | 2/10 | rag-pipeline blocked by paper-processor |
| **Query Handling (Test)** | 1/10 | Cannot handle test query |
| **Hallucination Prevention** | 1/10 | No verification |
| **Pedagogy & Adaptation** | 0/10 | No student-level support |
| **Feedback Loop** | 0/10 | No iteration |
| **Code Quality** | 3/10 | sci-viz well-structured |
| **Documentation** | 2/10 | sci-viz documented |

**OVERALL: 2/10 (CRITICAL STAGE)**

---

## WHAT WORKS, WHAT'S MISSING, WHAT'S BLOCKED

### WORKS
- **sci-viz:** Publication-quality figure generation framework
- **rag-pipeline:** RRF fusion, embedding models, query preprocessing
- **evals structure:** Basic iteration framework for single skills

### GAPS (Missing entirely)
- paper-processor (no PDF extraction)
- ontology-rag (no concept graph)
- efficient-coding-domain (no theory bridging)
- tutor-content-gen (no answer composition)
- sci-post-gen (no blog templates)
- conversation-sim (no profile simulation)
- user-feedback (no routing system)

### BLOCKED (Waiting on other skills)
- rag-pipeline: Blocked on paper-processor (needs chunked CRMB content)
- tutor-content-gen: Blocked on ontology-rag + efficient-coding-domain
- sci-viz: Can visualize, but no CRMB figure templates
- eval-runner: No cross-skill test cases

---

## CRITICAL PATH TO FUNCTIONAL SYSTEM

### Phase 1: FOUNDATION (Weeks 1-2)
1. **paper-processor** (unblocks all downstream)
2. **ontology-rag** (enables query expansion)
3. **efficient-coding-domain** (enables content bridging)

### Phase 2: CONTENT GENERATION (Weeks 3-4)
4. **tutor-content-gen** (core answer generation)
5. Hallucination prevention mechanism

### Phase 3: EVALUATION & OUTPUT (Weeks 5-6)
6. **eval-runner** (cross-skill metrics)
7. **sci-post-gen** (blog adaptation)
8. **sci-viz** (add CRMB templates)

### Phase 4: PEDAGOGY (Weeks 7-8)
9. **conversation-sim** (student simulation)
10. **user-feedback** (routing + iteration)

---

## TEST CASE RESULT: CANNOT EXECUTE

**Query:** "How does boundary completion in the FCS relate to sparse coding?"

**EXPECTED ANSWER (if all skills functional):**
```
[sci-viz would generate figures here]
[tutor-content-gen would compose:]
Boundary completion in the Boundary Contour System (BCS) 
relates to sparse coding through population coding efficiency. 
The BCS uses approximately 20% neuron activity (sparse) to 
code orientation boundaries, compared to 60% in the 
Feature Contour System (FCS). This sparsity enables 
efficient information representation with reduced redundancy, 
aligning with efficient coding theory principles that show 
neurons minimize information cost through selective activation.
```

**ACTUAL RESULT (current system):**
```
✗ Cannot execute
  - paper-processor: No content extracted from CRMB PDF
  - ontology-rag: No query expansion to related concepts
  - efficient-coding-domain: No theory bridge computed
  - tutor-content-gen: No answer composed
  - eval-runner: Cannot verify claim accuracy
  
System is non-functional for test query.
```

---

## CONCLUSION

The CRMB_tutor cross-skill integration pipeline is **20% complete** by implementation (2 of 10 skills) but **functionally 0%** for the test query (cannot answer).

**For the test query to work, these 4 skills MUST be implemented:**
1. paper-processor (content → RAG)
2. ontology-rag (expand query)
3. efficient-coding-domain (bridge concepts)
4. tutor-content-gen (compose answer)

**Sci-viz is excellent** and ready to produce figures.  
**Rag-pipeline has good foundations** but is blocked.  
**Everything else is missing.**

**Estimated effort to functional system:** 6-8 weeks with dedicated team.

---

**Generated:** 2026-04-14  
**Status:** System incomplete; non-functional for test query  
**Next Step:** Implement paper-processor to unblock pipeline
