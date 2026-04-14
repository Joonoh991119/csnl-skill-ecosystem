# Inter-Session Dependency Map

## Ecosystem Overview

```
Total: 11 skills, 5885 lines
Status: All 11 PASS validation (YAML frontmatter + description ≤1024 chars)
Repos: csnl-skill-ecosystem (primary), CRMB_tutor (integration)
```

## Session → Skill Matrix

| Skill | DB개선 | Ontology RAG | Post Gen v2 | Addictive Conv | User Feedback |
|-------|--------|-------------|-------------|----------------|---------------|
| db-pipeline | **P0** | | | | |
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

## Critical Path (Unblocking Order)

```
db-pipeline + paper-processor (DB 개선)
    ↓ produces: raw chunks + equations in pgvector
ontology-rag (ontology 구축)
    ↓ produces: concept graph + chunk-concept links
rag-pipeline (hybrid search 연결)
    ↓ produces: query → ranked chunks
tutor-content-gen + sci-post-gen (콘텐츠 생성)
    ↓ produces: grounded educational content
conversation-sim + eval-runner (평가)
    ↓ produces: quality metrics + simulated dialogues
user-feedback (피드백 루프)
    ↓ produces: improvement signals → evolve.py
```

## Dependency Graph (Skill → Skill)

```
paper-processor ──→ rag-pipeline ──→ tutor-content-gen
       │                │                    │
       ↓                ↓                    ↓
  db-pipeline     ontology-rag        sci-post-gen
       │                │                    │
       └────────────────┴────────────────────┘
                        ↓
                   eval-runner ←── conversation-sim
                        ↓
                  user-feedback
                        ↓
                   evolve.py (self-improvement loop)
```

## DB 개선 세션 준비 현황

### 현재 DB 상태
- LanceDB: summaries only, 3072-dim (lance_store.py hardcode)
- 목표: raw text + equations, pgvector, 1024-dim (BGE-M3)

### DB 세션에서 사용할 스킬
1. **db-pipeline** (966L) — 전체 파이프라인 오케스트레이터
   - Current state audit → Marker → Nougat → figure extraction → pgvector migration → re-embed → eval
2. **paper-processor** (589L) — Marker integration + equation extraction + batch chapter processing
3. **rag-pipeline** (852L) — pgvector schema versioning + batch re-embedding MPS + before/after eval hook

### DB 세션 실행 순서
```
1. db-pipeline: audit_db()          — 현재 LanceDB 상태 확인
2. paper-processor: run_marker()     — 20챕터 Marker 변환
3. paper-processor: extract_equations() — Nougat fallback
4. paper-processor: extract_figures() — PyMuPDF figure extraction
5. rag-pipeline: migrate_v1_to_v2()  — pgvector 스키마 마이그레이션
6. rag-pipeline: batch_reembed_mps() — BGE-M3 재임베딩 (MPS)
7. eval-runner: before_after_eval()  — 품질 비교
8. db-pipeline: generate_report()    — 최종 리포트
```

## Efficient Coding 도메인 통합 경로

```
efficient-coding-domain (용어집 + concept graph + eval queries)
    ↓
paper-processor (Efficient Coding 논문 PDF 처리)
    ↓
ontology-rag (CRMB 온톨로지에 EC 노드 추가, cross-domain bridges)
    ↓
rag-pipeline (두 도메인 통합 검색)
    ↓
sci-post-gen / tutor-content-gen (두 도메인 콘텐츠 생성)
    ↓
conversation-sim (cross-domain 대화 시뮬레이션)
```

## Eval Coverage

| Skill | Prompt 1 | Prompt 2 | Score Range |
|-------|----------|----------|-------------|
| rag-pipeline | ✅ | ✅ (1.7→patched) | 1.7-4.0 |
| paper-processor | ✅ | ✅ (1.5→patched) | 1.5-4.0 |
| eval-runner | ✅ | ✅ (2.3→patched) | 2.3-4.0 |
| tutor-content-gen | ✅ | ✅ (2.7→patched) | 2.7-4.0 |
| sci-viz | ✅ | ✅ (1.3→patched) | 1.3-4.0 |
| ontology-rag | ✅ (4.3) | — | 4.3 |
| sci-post-gen | ✅ (3.3) | — | 3.3 |
| conversation-sim | ✅ (2.7) | — | 2.7 |
| user-feedback | ✅ (2.0) | — | 2.0 |
| efficient-coding-domain | ✅ (4.3) | — | 4.3 |
| db-pipeline | — | — | NEW |

## Memory: Key Facts (Pruned)

- CRMB = Grossberg's "Conscious Mind, Resonant Brain" (ART-focused)
- Embedding: BGE-M3 → 1024-dim (NOT 3072, NOT 1536)
- RRF weights: dense=0.50, sparse=0.30, colbert=0.20, k=60
- CRMB_tutor persona: SciSpark
- Korean primary, English terms inline
- Apple Silicon: M4 Pro, 64GB, MPS device
- Self-evolution: evolve.py + blind evaluator
