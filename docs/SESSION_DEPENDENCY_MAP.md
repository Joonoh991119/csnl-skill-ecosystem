# Inter-Session Dependency Map (v4)

## Ecosystem Status

```
Repository: csnl-skill-ecosystem @ HEAD
Mirror: CRMB_tutor @ HEAD
Skills: 14 | Lines: ~13500 | Validation: ALL PASS
Ground Truth: 85 queries (5/chapter × 17 chapters)
Eval Coverage: 36/36 (P1+P2+P3 × 12 core skills; corpus-manager & workflow-orchestrator new)
Meta-review: AUDIT_v4 → 72/100
Cross-skill integration: v3 → 7.5/10 (was 6/10 in v2)
```

## New in v4
- corpus-manager: lifecycle for CRMB chapters + external papers, SHA-256 versioning
- workflow-orchestrator: DAG executor with AutoRecoveryExecutor (4 handlers)
- db-pipeline: PreMigrationValidator (6 checks, blocks dim-mismatch class)
- user-feedback: ProfileAwareEvolutionBridge (prevents beginner→expert param cascade)

## Skill Inventory

| Skill | Lines | P1 | P2 | P3 | Domain |
|-------|-------|----|----|-----|--------|
| equation-parser | 1205 | 4.5 | 3.5 | patched | parsing |
| db-pipeline | 1023 | 4.5 | patched | 3.0 | infrastructure |
| ontology-rag | 1002 | 4.3 | 4.0 | 2→patched | retrieval |
| sci-viz | 952 | 5.0 | patched | 2→patched | visualization |
| rag-pipeline | 919 | 5.0 | patched | patched | retrieval |
| sci-post-gen | 882 | 3.3 | 4.0 | 2→patched | generation |
| conversation-sim | 871 | patched | patched | 3.5 | evaluation |
| eval-runner | 611 | 5.0 | patched | patched | evaluation |
| paper-processor | 631 | 5.0 | patched | patched | parsing |
| user-feedback | 544 | patched | 4.0 | 3.0 | feedback |
| tutor-content-gen | 463 | 4.0 | patched | patched | generation |
| efficient-coding-domain | 366 | 4.3 | 4.0 | 2→patched | domain |

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

| Skill | Key Patches |
|-------|-------------|
| equation-parser | Checkpoint + cross-page stitch + Nougat retry + Unicode fix |
| db-pipeline | PipelineCheckpoint + mixed-dim detection + smart baseline |
| rag-pipeline | Korean hybrid weights (dense=0.70) + Mecab + language detection |
| tutor-content-gen | Trap query detection + semantic chain check + uncertainty templates |
| paper-processor | Subfigure extraction + footnotes + table validation + appendix boundary |
| conversation-sim | ConversationLogger + diagnose() + AB test significance |
| sci-viz | NaN handling + outlier normalization + colorblind maps + LaTeX labels |
| efficient-coding-domain | Disambiguation table + validated bridges + notation conflicts |
| ontology-rag | Cycle detection + orphan nodes + multi-hop + SPARQL + Korean NLP |
| sci-post-gen | Cross-domain orchestration + equation validation + CuriosityModulator |
| user-feedback | EvolutionBridge v2 + Korean sentiment + feedback routing |
| eval-runner | Bootstrap ground truth v2 (85 queries) + ablation workflow |

## Memory: Essential Facts

- CRMB = Grossberg's "Conscious Mind, Resonant Brain"
- BGE-M3: 1024-dim, MPS device, use_fp16=True
- RRF: en(0.50/0.30/0.20), ko(0.70/0.10/0.20), k=60
- SciSpark tutor persona, Korean primary
- M4 Pro 64GB, Apple Silicon MPS
- Self-evolution: evolve.py + blind evaluator
