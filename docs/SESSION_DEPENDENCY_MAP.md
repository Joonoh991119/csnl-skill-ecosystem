# Inter-Session Dependency Map (Updated)

## Ecosystem Status

```
Repository: csnl-skill-ecosystem @ 12bce6f
Mirror: CRMB_tutor @ e4cdbd0
Skills: 12 | Lines: 7911 | Validation: ALL PASS
Meta-review: AUDIT_v3 → 7.5/10
```

## Skill Inventory

| Skill | Lines | Evals | Best Score | Domain |
|-------|-------|-------|-----------|--------|
| equation-parser | 1206 | P1(4.5) P2(3.5) P3(0.7→patched) | 4.5 | parsing |
| db-pipeline | 1024 | P1(4.5) P2(1.5→patched) | 4.5 | infrastructure |
| rag-pipeline | 920 | P1-P2(patched) P3(0.08→patched) | 4.0 | retrieval |
| conversation-sim | 811 | P1(2.7→patched) | 3.5 | evaluation |
| eval-runner | 612 | P1-P2(patched) | 4.0 | evaluation |
| paper-processor | 589 | P1-P2(patched) | 4.0 | parsing |
| sci-viz | 560 | P1-P2(patched) | 4.0 | visualization |
| user-feedback | 545 | P1(2.0→patched) | 3.0 | feedback |
| ontology-rag | 480 | P1(4.3)+worked example | 4.3 | retrieval |
| sci-post-gen | 464 | P1(3.3)+worked example | 3.5 | generation |
| tutor-content-gen | 427 | P1-P2(patched) | 4.0 | generation |
| efficient-coding-domain | 273 | P1(4.3) | 4.3 | domain |

## Session → Skill Matrix

| Skill | DB개선 | Ontology RAG | Post Gen v2 | Addictive Conv | User Feedback |
|-------|--------|-------------|-------------|----------------|---------------|
| db-pipeline | **P0** | | | | |
| equation-parser | **P0** | P1 | P1 | P2 | |
| paper-processor | **P0** | P1 | | | |
| rag-pipeline | **P0** | **P0** | P2 | | P2 |
| ontology-rag | P1 | **P0** | | | |
| efficient-coding-domain | P1 | P2 | **P0** | P1 | |
| sci-post-gen | | | **P0** | | |
| tutor-content-gen | | P1 | P1 | P2 | |
| sci-viz | | | P1 | | |
| conversation-sim | | | | **P0** | |
| eval-runner | P1 | P1 | P1 | P1 | P1 |
| user-feedback | | | | | **P0** |

## Critical Path

```
[Layer 0: Infrastructure]
  db-pipeline → equation-parser → paper-processor
       ↓ produces: pgvector with raw+equations+figures (1024-dim BGE-M3)

[Layer 1: Retrieval]  
  ontology-rag → rag-pipeline (Korean multilingual hybrid search)
       ↓ produces: ranked chunks with citations + ontology expansion

[Layer 2: Generation]
  tutor-content-gen → sci-post-gen (bilingual, source-grounded)
       ↓ produces: educational content + blog posts

[Layer 3: Evaluation]
  eval-runner → conversation-sim (multi-seed, ART domain, strategy pivot)
       ↓ produces: quality metrics + engagement scores

[Layer 4: Feedback Loop]
  user-feedback → evolve.py (component routing, Korean sentiment)
       ↓ produces: parameter adjustments → back to Layer 0
```

## Interface Schemas (Unified)

```
equation-parser OUTPUT → EQUATION_OUTPUT_SCHEMA
  ↓ request_id, embedding_config, equations[], citation
rag-pipeline CITATION → CITATION_SCHEMA  
  ↓ ref_id, display_text, display_text_ko, bibtex_key
sci-post-gen INPUT → POST_INPUT_SCHEMA
  ↓ retrieved_chunks, equations, citations, post_config
```

## Cross-Domain Bridges (CRMB ↔ Efficient Coding)

| CRMB Concept | EC Concept | Bridge Type |
|---|---|---|
| ART vigilance (ρ) | Fisher information J(θ) | precision analogy |
| BCS orientation columns | Sparse coding basis (φ_i) | representation analogy |
| FCS diffusion | Efficient representation | efficiency analogy |
| LAMINART laminar circuits | Metabolic constraints | computational analogy |

## Robustness Status

| Skill | Robustness | Key Patch |
|-------|-----------|-----------|
| equation-parser | Checkpoint + cross-page stitch + Nougat retry + Unicode fix |
| db-pipeline | PipelineCheckpoint + mixed-dim detection + smart baseline |
| rag-pipeline | Korean hybrid weights (dense=0.70) + Mecab + language detection |

## Memory: Essential Facts

- CRMB = Grossberg's "Conscious Mind, Resonant Brain"
- BGE-M3: 1024-dim, MPS device, use_fp16=True
- RRF: en(0.50/0.30/0.20), ko(0.70/0.10/0.20), k=60
- SciSpark tutor persona, Korean primary
- M4 Pro 64GB, Apple Silicon MPS
- Self-evolution: evolve.py + blind evaluator
