# CSNL Skill Ecosystem

**Cognitive & Systems Neuroscience Laboratory — AI Knowledge System Skills**

Scientific RAG tutoring system을 위한 Cowork 스킬 생태계.  
Seoul National University, Department of Brain and Cognitive Sciences.

## Architecture

```
skills/
├── rag-pipeline/       ← P0: PostgreSQL+pgvector 기반 RAG 파이프라인
├── paper-processor/    ← P0: 논문 구조 추출 (sections, claims, figures)
├── tutor-content-gen/  ← P1: 교육 콘텐츠 생성 (한영 병렬, 난이도별)
├── eval-runner/        ← P1: 평가 파이프라인 (precision@k, factuality)
└── sci-viz/            ← P2: 과학 시각화 자동 생성

docs/
├── BLUEPRINT.md        ← 전체 설계 + 로드맵 + 인프라 전략
├── TUTOR_FOCUSED_EVALUATION.md  ← 튜터 DB 기여도 기준 스킬 재평가
└── DOWNSTREAM_REQUIREMENTS.md   ← 세션별 역방향 의존성 분석

meta-review/
└── AUDIT.md            ← QC 결과: 실현가능성 판정 + 수정 이력
```

## Environment

- **Hardware**: Mac Mini M4 Pro, 64GB unified memory
- **DB**: PostgreSQL + pgvector (primary), ChromaDB (dev fallback)
- **Embedding**: OpenRouter API (production) / BGE-M3 or Qwen3-Embedding-8B (local)
- **LLM**: Qwen2.5-32B Q5_K_M via MLX (local) / Claude via API
- **MCP**: Zotero, Notion, Slack, Gmail, Google Calendar, Desktop Commander, Chrome

## Status

| Skill | SKILL.md | QC Pass | skill-creator Test | Deployed |
|---|---|---|---|---|
| rag-pipeline | ✅ v2 (pgvector) | 🔄 Auditing | ⏳ Pending | ❌ |
| paper-processor | ✅ v1 | 🔄 Auditing | ⏳ Pending | ❌ |
| tutor-content-gen | ✅ v1 | 🔄 Auditing | ⏳ Pending | ❌ |
| eval-runner | ✅ v2 (bootstrap added) | 🔄 Auditing | ⏳ Pending | ❌ |
| sci-viz | ✅ v1 | 🔄 Auditing | ⏳ Pending | ❌ |

## Development Loop

```
push SKILL.md → skill-creator test → review failures → fix → push again
```

완료 선언 금지. 루프는 계속된다.
