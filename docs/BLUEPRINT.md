# CSNL AI Knowledge System: Skill Ecosystem Blueprint & Self-Evolution Roadmap

**Author**: CSNL AI Research Orchestrator  
**Date**: 2026-04-14  
**Status**: Strategic Planning Document  
**Target**: Mac Mini M4 Pro (48GB) + Cowork Skill Ecosystem

---

## 1. Current State Assessment

### Connected MCP Infrastructure
| MCP Server | Status | Capability |
|---|---|---|
| Zotero | Connected | Semantic search, annotations, full-text, write ops |
| Notion | Connected | Pages, databases, views, search |
| Slack (Official + CSNL Bot) | Connected | Channels, DMs, search, scheduling |
| Gmail | Connected | Search, read, draft |
| Google Calendar | Connected | Events, scheduling, free time |
| Google Drive | Connected | Search, fetch |
| Desktop Commander | Connected | File ops, process management, search |
| Chrome (Claude in Chrome) | Connected | Web browsing, DOM interaction |
| Figma | Connected | Design context, screenshots |
| PowerPoint (Anthropic) | Connected | Slide creation/editing |
| bioRxiv/medRxiv | Connected | Preprint search |

### Current Cowork Skills (Built-in)
docx, pptx, xlsx, pdf, mcp-builder, skill-creator, b-time-analysis, doc-coauthoring, schedule

### Critical Gaps Identified
1. **시각화 파이프라인** - interactive plot 자동 생성 불가
2. **RAG 파이프라인** - chunking/embedding/retrieval 자동화 부재
3. **과학 논문 처리** - LaTeX 파싱, figure 추출, citation graph 부재
4. **코드 생성/실행** - Python/MATLAB 분석 스크립트 자동 생성 미흡
5. **Self-evaluation** - 성능 측정 → 병목 진단 → 개선 제안 루프 없음
6. **로컬 모델 통합** - Ollama/MLX 경량 모델 MCP 연동 부재

---

## 2. Skill Ecosystem Map

### Layer 1: Foundation Infrastructure (즉시 설치/구축)

```
┌─────────────────────────────────────────────────────────┐
│                    FOUNDATION LAYER                      │
├─────────────────┬───────────────────┬───────────────────┤
│  Vector DB MCP  │  Local LLM MCP   │  Visualization    │
│  (LanceDB/      │  (Ollama MCP)    │  MCP (Plotly)     │
│   ChromaDB)     │                  │                   │
├─────────────────┼───────────────────┼───────────────────┤
│  Paper Search   │  arXiv LaTeX     │  Semantic Scholar │
│  MCP (unified)  │  MCP             │  MCP              │
└─────────────────┴───────────────────┴───────────────────┘
```

**Recommended MCP Servers to Install:**

| Priority | MCP Server | GitHub | Purpose |
|---|---|---|---|
| P0 | LanceDB MCP | lancedb/lancedb-mcp-server | Vector DB for RAG pipeline |
| P0 | Paper Search MCP | openags/paper-search-mcp | Unified arXiv/PubMed/bioRxiv/Semantic Scholar |
| P0 | Plotly MCP | arshlibruh/plotly-mcp-cursor | 50+ chart types, interactive HTML |
| P1 | Semantic Scholar MCP | zongmin-yu/semantic-scholar-fastmcp-mcp-server | 200M+ papers, citation networks |
| P1 | arXiv LaTeX MCP | takashiishida/arxiv-latex-mcp | LaTeX source → equations/figures extraction |
| P1 | Ollama MCP | (build via mcp-builder) | Local model inference endpoint |
| P2 | Qdrant MCP | qdrant/mcp-server-qdrant | Alternative vector DB |
| P2 | mcp-rag-server | kwanLeeFrmVi/mcp-rag-server | Full RAG pipeline (chunk→embed→retrieve) |

**NOTE**: Anthropic 공식 MCP Registry에는 과학/RAG/시각화 커넥터가 아직 없음. 모두 커뮤니티 서버 또는 자체 구축 필요.

### Layer 2: Domain Skills (커스텀 스킬 구축)

```
┌─────────────────────────────────────────────────────────┐
│                    DOMAIN SKILLS                         │
├────────────────┬────────────────┬────────────────────────┤
│ sci-viz        │ rag-pipeline   │ paper-processor        │
│ (시각화 자동화) │ (RAG 파이프라인)│ (논문 처리 자동화)      │
├────────────────┼────────────────┼────────────────────────┤
│ neuro-analysis │ code-gen       │ tutor-engine           │
│ (신경과학 분석) │ (코드 생성)     │ (교육 콘텐츠 생성)      │
└────────────────┴────────────────┴────────────────────────┘
```

### Layer 3: Meta/Evolution Skills (자기 진화)

```
┌─────────────────────────────────────────────────────────┐
│                  META-EVOLUTION LAYER                     │
├───────────────┬─────────────────┬────────────────────────┤
│ eval-runner   │ prompt-optimizer│ quality-monitor        │
│ (평가 자동화)  │ (DSPy 기반)     │ (데이터 품질 감시)      │
├───────────────┼─────────────────┼────────────────────────┤
│ ab-tester     │ skill-evolver   │ pipeline-debugger      │
│ (A/B 테스트)   │ (스킬 자동 개선) │ (병목 진단)            │
└───────────────┴─────────────────┴────────────────────────┘
```

---

## 3. Model & Infrastructure Strategy (M4 Pro 64GB + OpenRouter)

### Dual Strategy: OpenRouter API + Local 64GB

| Role | Primary (API) | Local Fallback | RAM (local) |
|---|---|---|---|
| **Embedding** | OpenRouter: text-embedding-3-large | BGE-M3 FP16 (sentence-transformers) | 1.1GB |
| **Embedding (heavy)** | OpenRouter: voyage-3-large | Qwen3-Embedding-8B FP16 | 16GB |
| **Main LLM** | Claude/GPT via API | Qwen2.5-32B Q5_K_M (higher quant now!) | 21GB |
| **Code Gen** | Same | Same | - |
| **Korean** | Same (multilingual) | Same | - |
| **Lightweight** | - | Qwen2.5-14B Q5_K_M | 10GB |
| **DB** | PostgreSQL+pgvector | Same (local) | ~2GB service |

> **64GB changes everything**: Q5_K_M instead of Q4_K_M (better quality, still fits).
> Can run Qwen3-Embedding-8B (16GB) + Qwen2.5-32B (21GB) simultaneously with 27GB free.

### Runtime Selection: MLX > llama.cpp > Ollama

| Framework | Speed (14B) | Advantage | Use Case |
|---|---|---|---|
| **MLX** | 230 tok/sec | 20-87% faster, unified memory native | Interactive tutoring |
| **llama.cpp** | ~150 tok/sec | Broad model support | Batch processing |
| **Ollama** | 43 tok/sec | Easiest setup, HTTP API | Development/testing |

### Quantization Strategy (64GB)
- **Default**: Q5_K_M (98.8% quality, 1.5x speed) ← upgraded from Q4_K_M
- **Maximum quality**: Q6_K or Q8 now feasible for 32B models
- **For 70B+ models**: Q4_K_M (still required at 64GB, ~37GB)

### Installation Commands
```bash
# 1. PostgreSQL + pgvector (PRIMARY DB)
brew install postgresql@16 pgvector
brew services start postgresql@16
createdb csnl_rag && psql csnl_rag -c "CREATE EXTENSION vector;"

# 2. Python stack
pip install psycopg2-binary pgvector sentence-transformers pymupdf rank-bm25 --break-system-packages

# 3. MLX Framework
pip install mlx mlx-lm

# 4. Ollama (local model serving)
brew install ollama && ollama serve
ollama pull qwen2.5:32b           # 17GB Q4_K_M (or pull Q5 GGUF manually)
ollama pull nomic-embed-text      # 274MB lightweight embed

# 5. Korean NLP
pip install konlpy mecab-python3

# 6. Visualization
pip install plotly matplotlib seaborn
```

### Memory Budget (64GB)
```
PostgreSQL service:             2GB
Qwen2.5-32B (Q5_K_M):        21GB
Qwen3-Embedding-8B (FP16):   16GB
OS + Apps + Buffer:           10GB
──────────────────────────────────
Used:                         49GB
Free:                         15GB (headroom for batch/context)

Alternative: OpenRouter for embedding → save 16GB → 31GB free
```

---

## 4. Self-Evolution Roadmap

### Phase 0: Foundation (Week 1-3) ← REVISED from 2 weeks

**Goal**: 인프라 설치 + 커스텀 스킬 2개 배포 + **부트스트랩 데이터셋 30개 생성**

```
[Install Deps] → [Build Skills] → [Index 10 Papers] → [Write 30 Ground Truth Queries]
```

Actions:
- Ollama + ChromaDB + sentence-transformers 설치 (Day 1-2)
- `rag-pipeline`, `paper-processor` 스킬 생성 via skill-creator (Day 3-5)
- Zotero에서 10편 테스트 인덱싱 (Day 6-7)
- **부트스트랩: 30개 테스트 쿼리 + ground truth 수동 작성 (Day 8-14)** ← 이게 병목
- 수동 테스트로 baseline precision@5 측정 (Day 15-21)

> **Why 3 weeks?** Meta-review 결과, 부트스트랩 데이터셋 생성이 2-3일 소요되며 이를 
> 무시하면 Phase 1 eval이 의미 없음. 30개 쿼리 없이 eval을 돌리면 overfitting.

### Phase 1: Manual Eval Loop (Week 4-7) ← REVISED: "자동화" 삭제

**Goal**: 수동 평가 루프 구축 + 첫 번째 개선 사이클 3회 실행

```
[Run Eval] → [Human Reviews Failures] → [Diagnose Root Cause] → [Fix] → [Re-eval]
```

**이 Phase에서 하는 것:**
- eval-runner 스킬 배포 (skill-creator 통해)
- 30개 쿼리로 precision@5, recall@10, factuality 측정
- **수동으로** 실패 케이스 분석: "왜 이 쿼리에서 엉뚱한 논문이 검색됐는가?"
- 원인별 수정: chunking 전략, 임베딩 모델, 프롬프트
- tutor-content-gen 스킬 배포 + 생성 품질 평가

**이 Phase에서 하지 않는 것:**
- ~~DSPy 자동 최적화~~ (아직 아님)
- ~~Braintrust/Langfuse A/B 테스트~~ (오버엔지니어링)
- ~~자동 배포~~ (수동 commit으로 충분)

Key Metrics (same):
- RAG retrieval precision@5 > 0.6, recall@10 > 0.8
- Generation factuality > 3.5/5 (LLM-as-judge)
- 한국어 응답 자연스러움 > 3.5/5

### Phase 2: Semi-Automated Optimization (Week 8-15) ← REVISED from 4 weeks

**Goal**: 수동 루프를 반자동화 + 테스트 쿼리 50개로 확장

```
[Eval Results JSON] → [Human identifies pattern] → [Systematic fix]
                                                        ↓
                                                [Re-eval all 50 queries]
                                                        ↓
                                                [Commit if improved, revert if not]
```

**구체적 작업:**
1. 테스트 쿼리 30→50개 확장 (새 도메인: attention, neural coding 추가)
2. eval-runner를 schedule skill로 주간 자동 실행
3. Slack 알림: "이번 주 precision@5가 0.58→0.52로 하락" (threshold 기반)
4. **DSPy 탐색 시작** (기존 루프가 안정된 후에만):
   - DSPy Signature 래핑 실험 (rag-pipeline의 retrieval 부분만)
   - GEPA 1회 실험 → 결과 비교 → 수동 루프 대비 개선 여부 판단
   - **주의: GEPA는 SKILL.md를 직접 최적화할 수 없음. DSPy Signature와 SKILL.md 사이의 bridge layer가 필요하며, 이건 별도 엔지니어링.**

> **Meta-review 결론 반영**: DSPy GEPA → SKILL.md 자동 반영은 bridge layer 없이 불가능.
> Phase 2의 현실적 목표는 "수동 루프를 더 빠르게 도는 것"이지 "완전 자동화"가 아님.

### Phase 3: Structured Self-Evolution (Month 4-6+) ← REVISED: "Full" → "Structured"

**Goal**: 데이터 기반 개선 의사결정 체계 + gap detection

```
[Eval History DB] → [Trend Analysis] → [Gap Report] → [Human Decision] → [Build/Fix]
```

**Phase 3에서 현실적으로 가능한 것:**
- Coverage Map: 어떤 토픽이 잘 커버되고 어떤 토픽이 약한지 시각화
- Gap Detection: 실패 쿼리 패턴 분석 → "ion channel 관련 쿼리가 반복 실패"
- Quality Trend: 주간 eval 결과 longitudinal 추적
- Skill Proposal: Gap 기반으로 **사람에게** 새 스킬 필요성 보고

**Phase 3에서 비현실적인 것 (솔직하게):**
- ~~자동 스킬 생성~~ — skill-creator는 사람의 input이 필수
- ~~자동 배포~~ — validation 없는 auto-deploy는 위험
- ~~자동 진단~~ — "왜 precision이 떨어졌는가"의 자동 답변은 아직 연구 수준

> **Meta-review 핵심**: 자기 진화는 "측정 → 분석 → 수정 → 재측정" 루프의 반복이며,
> 그 루프의 속도를 높이는 것이 목표. 루프 자체를 자동화하는 건 6개월 이후 목표.

---

## 5. 즉시 생성할 커스텀 스킬 5개

### Skill 1: `sci-viz` (Scientific Visualization Generator)

```yaml
---
name: sci-viz
description: >
  Scientific data visualization generator. Creates publication-quality plots
  using Plotly, matplotlib, or D3 from data descriptions or CSV/DataFrame inputs.
  MANDATORY TRIGGERS: Any request involving plots, charts, graphs, figures,
  data visualization, heatmaps, scatter plots, bar charts, brain maps,
  timeseries plots, raster plots, psychometric functions, tuning curves,
  or any mention of "figure" in a scientific context. Even if the user just
  says "plot this" or "visualize the results", use this skill.
---
```

**Core capabilities**:
- Input: CSV path, DataFrame description, or natural language data description
- Processing: Auto-detect chart type → generate Plotly/matplotlib code → render to HTML/PNG/SVG
- Output: Interactive HTML (Plotly) or publication PNG (matplotlib)
- Neuroscience presets: orientation tuning curves, BOLD timecourses, psychometric functions, retinotopic maps, spike raster plots

**Structure**:
```
sci-viz/
├── SKILL.md
├── references/
│   ├── plotly-templates.md      # Neuroscience-specific templates
│   ├── matplotlib-templates.md  # Publication-quality presets
│   └── chart-selection-guide.md # Data type → chart type mapping
└── scripts/
    └── render_plot.py           # Headless rendering pipeline
```

### Skill 2: `rag-pipeline` (RAG Pipeline Builder)

```yaml
---
name: rag-pipeline
description: >
  End-to-end RAG pipeline builder for scientific document retrieval.
  Handles document ingestion, intelligent chunking, embedding generation,
  vector storage, and retrieval with re-ranking. Supports local models
  (Ollama/MLX) and cloud APIs. MANDATORY TRIGGERS: Any mention of RAG,
  retrieval augmented generation, document search, semantic search,
  knowledge base, embedding, chunking, vector database, similarity search,
  or building a search system over documents. Also trigger when user says
  "find papers about X" or "search my library for Y" if Zotero alone
  isn't sufficient.
---
```

**Core capabilities**:
- Chunking strategies: semantic, sliding window, section-aware (for papers)
- Embedding: Qwen3-Embedding (MLX) / BGE-M3 / Nomic-embed
- Vector DB: LanceDB (primary) / ChromaDB (fallback)
- Retrieval: Dense + Sparse (BM25) hybrid → cross-encoder re-ranking
- Special: LaTeX equation preservation during chunking, figure caption linking

### Skill 3: `paper-processor` (Scientific Paper Processing Pipeline)

```yaml
---
name: paper-processor
description: >
  Scientific paper processing and analysis pipeline. Extracts structured
  information from academic papers including abstracts, methods, results,
  figures, equations, and citations. Supports PDF, LaTeX, and arXiv sources.
  MANDATORY TRIGGERS: Any request involving paper analysis, literature review,
  paper summarization, extracting methods/results from papers, citation
  extraction, figure extraction, reading scientific PDFs, parsing LaTeX,
  or creating structured summaries of academic articles. Trigger when user
  says "summarize this paper", "extract the methods", "what are the key
  findings", or "process these papers".
---
```

**Core capabilities**:
- Input: PDF path, arXiv ID, DOI, or Zotero item
- Processing: PDF → structured sections → key claims extraction → citation graph
- Output: Structured JSON, Notion page, or markdown summary
- Integration: Zotero MCP (library), arXiv LaTeX MCP (source), Semantic Scholar MCP (citations)

### Skill 4: `eval-runner` (Automated Evaluation Pipeline)

```yaml
---
name: eval-runner
description: >
  Automated evaluation pipeline for testing and benchmarking AI skill outputs.
  Runs test suites against skills, collects metrics, generates comparison
  reports, and suggests improvements. MANDATORY TRIGGERS: Any request
  involving testing skills, evaluating outputs, benchmarking performance,
  comparing versions, running evals, quality assessment, regression testing,
  or "how well does X skill work". Also trigger for prompt optimization
  requests or when user says "is this better than before".
---
```

**Core capabilities**:
- Test suite management: Create, edit, run test cases per skill
- Metrics: Factuality, relevance, completeness, format compliance, execution success
- Comparison: A/B between skill versions, blind comparison mode
- Reporting: HTML report with pass/fail, scores, failure analysis
- Integration: DSPy assertions for programmatic quality gates

### Skill 5: `tutor-content-gen` (RAG Tutor Content Generator)

```yaml
---
name: tutor-content-gen
description: >
  Educational content generator for the CSNL scientific RAG tutoring system.
  Creates explanations, Q&A pairs, quizzes, and interactive learning modules
  from scientific papers and knowledge bases. Supports Korean and English
  bilingual output. MANDATORY TRIGGERS: Any request involving creating
  educational content, generating explanations of scientific concepts,
  making quizzes from papers, creating study materials, tutoring content,
  Q&A generation, concept maps, or learning modules. Also trigger for
  "explain this paper to students" or "make a quiz about X".
---
```

**Core capabilities**:
- Input: Paper (via paper-processor) or topic + knowledge base
- Content types: Conceptual explanation, Q&A pairs, multiple-choice quiz, concept map, worked examples
- Bilingual: Korean + English parallel generation
- Difficulty scaling: Undergrad → Master → PhD level
- Feedback integration: Student response analysis → adaptive content refinement

---

## 6. Community Resources to Leverage

### GitHub Skill Collections (Star-worthy)

| Repository | Stars | Contents | Action |
|---|---|---|---|
| K-Dense-AI/claude-scientific-skills | 133+ skills | Brain imaging, spike sorting, Neuropixels, fMRI | **Clone & adapt** |
| alirezarezvani/claude-skills | 232+ | Multi-domain enterprise skills | Browse for patterns |
| daymade/claude-code-skills | 48 production | Enhanced dev workflows | Reference architecture |
| jeremylongshore/claude-code-plugins-plus-skills | 340+1367 | CCPI package manager | Install tool |
| VoltAgent/awesome-agent-skills | 1000+ | Cross-platform agent skills | Browse for ideas |
| anthropics/skills | Official | Baseline implementations | Foundation reference |

### MCP Server Registries

| Registry | URL | Use Case |
|---|---|---|
| PulseMCP | pulsemcp.com | 12,520+ servers, best discovery |
| LobeHub | lobehub.com/mcp | User-friendly interface |
| mcp.so | mcp.so | Community-driven |
| mcpmarket.com | mcpmarket.com | Curated skills marketplace |
| Official MCP Registry | registry.modelcontextprotocol.io | ~2,000 entries, API v0.1 |

---

## 7. Immediate Action Checklist

### Today (30 minutes)

- [ ] `ollama pull qwen2.5:32b` (17GB download)
- [ ] `ollama pull nomic-embed-text` (274MB)
- [ ] `pip install mlx mlx-lm chromadb plotly --break-system-packages`

### This Week

- [ ] Clone K-Dense-AI/claude-scientific-skills → adapt neuroscience-relevant skills
- [ ] Install Paper Search MCP (openags/paper-search-mcp)
- [ ] Install LanceDB MCP or build Ollama MCP via mcp-builder
- [ ] Use skill-creator to build `sci-viz` skill (highest impact)
- [ ] Use skill-creator to build `rag-pipeline` skill
- [ ] Test Qwen2.5-32B on scientific paper summarization (Korean + English)

### This Month

- [ ] Build `paper-processor` skill with Zotero + arXiv LaTeX integration
- [ ] Build `eval-runner` skill with DSPy assertion framework
- [ ] Build `tutor-content-gen` skill (core product)
- [ ] Set up LanceDB vector index for Zotero library (~50K papers target)
- [ ] Create scheduled evaluation task (daily quality metrics)
- [ ] Build Notion dashboard for pipeline monitoring

### Next Quarter (Self-Evolution)

- [ ] DSPy integration: wrap all skills as DSPy Signatures
- [ ] GEPA optimizer: auto-tune prompt variants
- [ ] A/B testing framework: Langfuse or Braintrust integration
- [ ] Gap detector: analyze user queries → propose new skills
- [ ] Pipeline debugger: error pattern → auto-diagnosis
- [ ] Skill evolver: low-score skill → auto-redesign loop

---

## 8. Architecture Diagram

```
USER QUERY (Korean/English)
    │
    ▼
┌─────────────────────────────┐
│     COWORK SKILL ROUTER     │  ← skill description matching
│  (built-in Claude routing)  │
└─────────────┬───────────────┘
              │
    ┌─────────┼─────────┬──────────┬──────────┐
    ▼         ▼         ▼          ▼          ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│sci-viz ││rag-    ││paper-  ││tutor-  ││eval-   │
│        ││pipeline││process ││content ││runner  │
└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
    │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────┐
│              MCP SERVER LAYER                    │
├──────┬──────┬──────┬──────┬──────┬──────┬──────┤
│Zotero│Notion│Lance │Paper │Plotly│arXiv │Seman-│
│  MCP │ MCP  │DB MCP│Search│ MCP  │LaTeX │tic   │
│      │      │      │ MCP  │      │ MCP  │Scholar│
└──────┴──────┴──┬───┴──────┴──────┴──────┴──────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│           LOCAL MODEL LAYER (MLX)                │
├─────────────────┬───────────────────────────────┤
│ Qwen3-Embed-4B  │ Qwen2.5-32B (Q4_K_M)         │
│ (2GB, embedding) │ (17GB, inference/code/Korean)  │
├─────────────────┼───────────────────────────────┤
│ BGE-M3 (sparse) │ Qwen2.5-7B (lightweight)      │
│ (1GB, re-rank)  │ (5GB, fast summarization)      │
└─────────────────┴───────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│          SELF-EVOLUTION LAYER                    │
├──────────┬──────────┬──────────┬────────────────┤
│ DSPy     │ Eval     │ Quality  │ Skill          │
│ Optimizer│ Pipeline │ Monitor  │ Evolver        │
│ (GEPA)   │ (daily)  │ (drift)  │ (auto-improve) │
└──────────┴──────────┴──────────┴────────────────┘
```

---

## 9. Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| M4 Pro 48GB 메모리 부족 (복수 모델 동시) | HIGH | Sequential loading, Q4_K_M default, 7B fallback |
| 커뮤니티 MCP 서버 불안정 | MED | Docker 컨테이너화, fallback to direct API |
| DSPy 최적화 overfitting | MED | Holdout test set, human-in-the-loop approval |
| 한국어 embedding 품질 | MED | Qwen3 multilingual + domain-specific fine-tune |
| 스킬 간 의존성 충돌 | LOW | Modular design, skill isolation, version pinning |

---

*This blueprint is designed to be iteratively refined. Start with Phase 0 actions and let each phase's learnings inform the next.*
