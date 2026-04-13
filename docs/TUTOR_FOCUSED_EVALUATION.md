# Tutor-Centric Skill Evaluation

**평가 기준 (J's directive)**:
1. 이 스킬이 설치되면 튜터 DB 품질이 올라가는가?
2. 이 스킬이 튜터의 답변 품질을 개선하는가?
3. 이 스킬이 파이프라인의 self-evolution을 가속하는가?

---

## 스킬 5개 재평가

### 1. `rag-pipeline` — **CRITICAL PATH**

| 기준 | 점수 | 근거 |
|---|---|---|
| DB 품질 ↑ | 10/10 | RAG 파이프라인 없이는 DB 자체가 존재하지 않음. chunking 품질이 retrieval 정확도를 직접 결정. |
| 답변 품질 ↑ | 10/10 | 검색 정확도가 답변 품질의 ceiling. garbage in = garbage out. |
| Self-evolution ↑ | 7/10 | 파이프라인 구조가 있어야 eval을 돌릴 수 있음. 간접적으로 필수. |
| **종합** | **9/10** | **첫 번째로 만들어야 함** |

**튜터에 대한 실질 기여**: 논문을 section-aware로 chunking → 임베딩 → 벡터DB 저장.
이게 없으면 튜터가 "어디서 답을 찾을지" 자체를 모름. 인프라 자체.

---

### 2. `paper-processor` — **DB 품질의 INPUT QUALITY**

| 기준 | 점수 | 근거 |
|---|---|---|
| DB 품질 ↑ | 9/10 | 논문에서 구조화된 정보(claims, sections, figures)를 추출해야 DB 품질이 올라감. raw text만 넣으면 DB 품질이 낮아짐. |
| 답변 품질 ↑ | 8/10 | 구조화된 데이터 → 더 정확한 retrieval → 더 정확한 답변. claims 추출이 핵심. |
| Self-evolution ↑ | 5/10 | 직접적 기여는 낮지만, 잘 구조화된 데이터가 eval의 ground truth 역할. |
| **종합** | **7.5/10** | **두 번째로 만들어야 함** |

**튜터에 대한 실질 기여**: PDF → "이 논문의 핵심 주장은 X이고, 방법론은 Y이고, Figure 3이 이걸 보여줌"
→ 이 구조가 rag-pipeline에 들어가면 "시각 작업 기억 용량"을 물었을 때 abstract가 아니라
정확히 results section의 관련 claim이 검색됨.

---

### 3. `tutor-content-gen` — **OUTPUT QUALITY**

| 기준 | 점수 | 근거 |
|---|---|---|
| DB 품질 ↑ | 6/10 | 생성된 Q&A, 설명이 DB에 추가되면 튜터의 커버리지 확장. 하지만 source quality에 의존. |
| 답변 품질 ↑ | 9/10 | 이 스킬이 직접 답변을 생성. 프롬프트 품질, 난이도 조절, 한영 병렬 생성 모두 여기서 결정. |
| Self-evolution ↑ | 6/10 | 생성된 콘텐츠가 eval의 대상. eval → feedback → 재생성 루프의 핵심 노드. |
| **종합** | **7/10** | **세 번째로 만들어야 함 (rag-pipeline + paper-processor가 먼저)** |

**튜터에 대한 실질 기여**: 검색된 context → "학부생이 이해할 수 있는 설명 + 퀴즈 + 개념맵"
→ 이게 없으면 RAG는 raw paper text를 그대로 보여주는 수준에 머묾.

**⚠️ 주의**: rag-pipeline과 paper-processor가 없으면 이 스킬의 입력 자체가 없음.
순서가 중요.

---

### 4. `eval-runner` — **SELF-EVOLUTION ENABLER**

| 기준 | 점수 | 근거 |
|---|---|---|
| DB 품질 ↑ | 5/10 | 간접적. eval이 "이 논문의 chunking이 나쁘다"를 발견하면 DB 품질 개선 가능. |
| 답변 품질 ↑ | 7/10 | 측정 없이 개선 없음. eval이 "이 쿼리에서 factuality 2점"을 발견하면 수정 가능. |
| Self-evolution ↑ | 10/10 | **이것 자체가 self-evolution의 핵심**. DSPy → eval → optimize → redeploy 루프의 시작점. |
| **종합** | **7.5/10** | **네 번째이지만, 장기적으로는 가장 가치 높음** |

**튜터에 대한 실질 기여**: "VWM capacity 질문에서 precision@5가 0.3밖에 안 됨"
→ chunking 전략 수정 → precision@5가 0.7로 상승 → 답변 품질 자동 개선.
이 루프가 없으면 문제를 모르는 채로 돌아감.

---

### 5. `sci-viz` — **CONDITIONAL VALUE**

| 기준 | 점수 | 근거 |
|---|---|---|
| DB 품질 ↑ | 2/10 | 시각화가 DB 품질에 직접 기여하지 않음. |
| 답변 품질 ↑ | 5/10 | 튜터가 figure를 생성해서 보여줄 수 있으면 교육 효과 상승. 하지만 텍스트 답변이 우선. |
| Self-evolution ↑ | 3/10 | eval 결과 시각화에 사용 가능하지만, Plotly/matplotlib 직접 사용으로도 가능. |
| **종합** | **3.5/10** | **후순위. 다른 4개가 안정화된 후에 추가** |

**솔직한 평가**: sci-viz는 "있으면 좋은" 스킬이지 "없으면 안 되는" 스킬이 아님.
튜터 DB 품질이나 답변 정확도에 직접 기여하지 않음. 포스팅 엔진에서 필요하긴 하지만,
핵심 파이프라인(DB 품질 + 답변 품질 + self-evolution) 관점에서는 후순위.

---

## 최종 우선순위 (튜터 중심)

```
MUST (없으면 튜터가 안 됨):
  1. rag-pipeline        ← DB 인프라 자체
  2. paper-processor     ← DB 입력 품질

SHOULD (없으면 튜터가 약함):
  3. tutor-content-gen   ← 출력 품질
  4. eval-runner         ← 자기 개선 능력

NICE-TO-HAVE (없어도 튜터는 됨):
  5. sci-viz             ← 보조 시각화
```

## 설치 순서 (Dependencies 고려)

```
Week 1: rag-pipeline + paper-processor (동시 진행 가능)
         └→ Ollama 설치, ChromaDB 설치, PyMuPDF 설치
         └→ Zotero library에서 10편 테스트 인덱싱

Week 2: tutor-content-gen (rag-pipeline 위에 구축)
         └→ 인덱싱된 10편으로 Q&A 생성 테스트
         └→ 한영 병렬 생성 검증

Week 3: eval-runner (전체 파이프라인 위에 구축)
         └→ 테스트 쿼리 20개 작성
         └→ retrieval + generation 품질 baseline 측정
         └→ 첫 번째 개선 루프 실행

Week 4+: sci-viz + 추가 개선
         └→ eval 결과 기반 chunking 전략 개선
         └→ 포스팅 엔진 연동
```

---

## 로컬 모델 설치: 튜터 관점 최소 필수

```bash
# 즉시 필요 (Week 1)
ollama pull nomic-embed-text          # 274MB, 임베딩용
pip install chromadb pymupdf --break-system-packages

# Week 2 (content generation 시작 시)
ollama pull qwen2.5:32b               # 17GB, 생성/추론용

# Week 3 (eval 시작 시)
pip install rank-bm25 sentence-transformers --break-system-packages
```

Qwen2.5-32B가 17GB이므로, 임베딩 모델(nomic 274MB) + ChromaDB와
동시에 48GB M4 Pro에서 충분히 구동 가능.

---

## MCP 서버: 튜터 관점 최소 필수

```
즉시 필요:
  - Zotero MCP (이미 연결됨) → 논문 소스
  - Notion MCP (이미 연결됨) → 지식 베이스

Week 2-3:
  - Paper Search MCP (openags/paper-search-mcp) → 새 논문 발견
  - Semantic Scholar MCP → citation network

불필요 (당분간):
  - LanceDB MCP (ChromaDB로 충분)
  - Plotly MCP (sci-viz 후순위)
  - arXiv LaTeX MCP (PDF 처리로 충분, LaTeX 파싱은 luxury)
```
