# Downstream Session → Skill Requirements (Reverse Mapping)

## Session 1: 포스팅 엔진 (Content Posting Engine)
**Needs from skill ecosystem:**
- `paper-processor` → 논문에서 핵심 insight 추출
- `tutor-content-gen` → 추출된 insight를 교육 포스팅으로 변환
- `sci-viz` → 포스팅에 삽입할 figure 자동 생성
- `rag-pipeline` → 관련 논문/자료 자동 검색 및 컨텍스트 제공

## Session 2: 대화 디자인 (Conversation Engine)
**Needs from skill ecosystem:**
- `rag-pipeline` → 대화 중 실시간 지식 검색
- `tutor-content-gen` → 난이도별 설명 생성
- `eval-runner` → 대화 품질 자동 평가 (응답 정확도, 교육 효과)
- NEW: `conversation-flow` → 대화 흐름 설계 및 분기 관리

## Session 3: 피드백 시스템 (Feedback System)
**Needs from skill ecosystem:**
- `eval-runner` → 피드백 기반 성능 측정
- NEW: `quality-monitor` → 응답 품질 drift 감지
- NEW: `prompt-optimizer` → 피드백 → 프롬프트 개선 자동화
- `rag-pipeline` → 피드백에서 지식 gap 식별 → 인덱스 보강

## Session 4: UI 설계
**Needs from skill ecosystem:**
- `sci-viz` → UI에 삽입할 interactive visualization component
- NEW: `ui-component-gen` → React/HTML 컴포넌트 자동 생성
- `tutor-content-gen` → UI에 표시할 콘텐츠 포맷 표준화

## Session 5: 핵심 파이프라인 (Core Pipeline)
**Needs from skill ecosystem:**
- `rag-pipeline` → 파이프라인의 backbone
- `paper-processor` → ingestion stage
- `eval-runner` → 파이프라인 전체 E2E 테스트
- `sci-viz` → 파이프라인 모니터링 대시보드

---

## Priority Matrix (Downstream 역방향 기준)

| Skill | 포스팅 | 대화 | 피드백 | UI | 핵심 | **Total** | **Priority** |
|---|---|---|---|---|---|---|---|
| `rag-pipeline` | O | O | O | - | O | **4** | **P0** |
| `sci-viz` | O | - | - | O | O | **3** | **P0** |
| `paper-processor` | O | - | - | - | O | **2** | **P1** |
| `tutor-content-gen` | O | O | - | O | - | **3** | **P0** |
| `eval-runner` | - | O | O | - | O | **3** | **P0** |

**결론**: 5개 스킬 모두 downstream 3개 이상 세션에서 필요. 전부 P0-P1.
