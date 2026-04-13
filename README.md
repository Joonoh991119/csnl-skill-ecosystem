# CSNL Skill Ecosystem

Scientific RAG Tutoring System skills for the Cognitive and Systems Neuroscience Laboratory (CSNL), Seoul National University.

## Skills

| Skill | SKILL.md | Validated | Packaged | Eval Iters | Tutor DB Contribution |
|---|---|---|---|---|---|
| **rag-pipeline** | v4 (pgvector, parameterized dim) | ✅ | ✅ | 1 (baseline + with-skill) | DIRECT: core retrieval |
| **paper-processor** | v2 (complete figure extraction) | ✅ | ✅ | 2 (baseline + with-skill + batch) | DIRECT: ingestion |
| **eval-runner** | v3 (Korean metrics added) | ✅ | ✅ | 1 (bootstrap 34 queries) | INDIRECT: validation |
| **tutor-content-gen** | v2 (quality checklist added) | ✅ | ✅ | 1 (VWM bilingual) | DIRECT: content gen |
| **sci-viz** | v1 | ✅ | ✅ | 0 | INDIRECT: visualization |

## Architecture

```
Zotero MCP → paper-processor → rag-pipeline (pgvector) → tutor-content-gen → Notion/UI
                                      ↑                         ↓
                               eval-runner ←──────────────── sci-viz
```

## Key Design Decisions

- **PostgreSQL + pgvector** over LanceDB/ChromaDB: production-grade, SQL joins, ACID
- **BGE-M3 1024d** as default embedding (OpenRouter API or local sentence-transformers)
- **Parameterized EMBEDDING_DIM**: supports model switching without schema breaks
- **No DSPy auto-optimization**: marked as Phase 2+ research, not promised
- **No MLX for embeddings**: MLX is text-gen only; embeddings use sentence-transformers + MPS
- **30+ ground truth queries**: bootstrap dataset for statistically meaningful eval

## QC Status

- Meta-review AUDIT_v2: All 5 skills PASS (0 blockers, 0 fantasy claims)
- All skills pass `quick_validate.py` and `package_skill.py`
- Cross-skill dependency matrix: no circular dependencies
- Bootstrap ground truth pushed to CRMB_tutor repo (34 queries, 17 chapters)

## Commits

| Hash | Description |
|---|---|
| `0659daf` | iteration-3: packaged .skill files + audit warning fixes |
| `4e5f690` | iteration-2: meta-review audit + EMBEDDING_DIM + quality checklist |
| `a2af1f4` | iteration-1: evals for paper-processor, eval-runner, tutor-content-gen |
| `ca39607` | rag-pipeline v3 + CRMB compat + baseline eval |

## Environment

- Mac Mini M4 Pro, 64GB RAM
- PostgreSQL 16 + pgvector
- Embedding: OpenRouter API (primary) or local BGE-M3 FP16 with MPS
- Local LLM: Qwen2.5-32B via Ollama (for eval judging)
