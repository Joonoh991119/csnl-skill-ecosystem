# Meta-Review Audit Log

## Date: 2026-04-14, Initial Audit

### Methodology
- **Small Loop**: 각 SKILL.md를 blind 평가 (scout 컨텍스트 없이)
- **Big Loop**: 생태계 전체의 self-evolution 실현가능성 meta-review
- **Review 독립성**: Evaluator ≠ Scout, 독립 판정

---

## Big Loop: Self-Evolution Feasibility

### Phase 0 (Foundation, 3 weeks): **FEASIBLE**
- 인프라 설치 + 스킬 2개 + 부트스트랩 데이터셋 30개 = 현실적
- 병목: 부트스트랩 ground truth 수동 작성 (2-3일)

### Phase 1 (Manual Eval Loop, Week 4-7): **FEASIBLE → ASPIRATIONAL boundary**
- eval-runner metrics 계산 코드: 실제 동작 가능
- 수동 feedback loop: 가능
- DSPy 자동 최적화: **제거됨** (이 Phase에서는 하지 않음)

### Phase 2 (Semi-Automated, Week 8-15): **ASPIRATIONAL**
- DSPy GEPA → SKILL.md 직접 최적화: **FANTASY → 제거됨**
- 현실적 목표: "수동 루프를 더 빠르게 도는 것"으로 downgrade

### Phase 3 (Structured Evolution, Month 4-6+): **ASPIRATIONAL**
- Auto-skill-proposal: **FANTASY → 제거됨**
- 현실적 목표: Coverage map + gap detection + human decision

---

## Small Loop: SKILL.md Structural Audit

### Issue 1: rag-pipeline MLX embedding fantasy (FIXED)
- `mlx_lm.load`는 text generation 모델용, embedding 모델 아님
- **Fix**: sentence-transformers + MPS로 교체 (v2)
- **Fix**: PostgreSQL+pgvector로 전면 재설계 (v2)

### Issue 2: eval-runner DSPy bridge 부재 (FIXED)
- "DSPy GEPA로 SKILL.md 자동 최적화" 주장 → bridge layer 없이 불가능
- **Fix**: DSPy를 "Phase 2+ future work"로 재분류, bootstrap dataset 추가

### Issue 3: Bootstrap problem (FIXED)
- 테스트 쿼리 2개로는 eval 의미 없음
- **Fix**: 30개 ground truth 생성을 Phase 0의 필수 작업으로 추가

### Issue 4: Timeline 40% 과소 추정 (FIXED)
- 12주 → 15-20주로 현실 조정
- Phase 2/3를 downgrade

### Issue 5: Circular dependency (DOCUMENTED, NOT FIXED)
- paper-processor → rag-pipeline → tutor-content-gen → eval-runner → paper-processor
- Mitigation: ground truth는 raw PDF 대비 검증, paper-processor output에 의존하지 않도록

---

## Pending Issues (다음 루프에서 해결)

1. [ ] sci-viz가 tutor DB에 직접 기여하지 않음 — 스킬 유지 vs 제거 결정 필요
2. [ ] paper-processor의 section detection regex가 단순함 — 실제 논문 10편에 테스트 필요
3. [ ] tutor-content-gen의 bilingual 품질 검증 안 됨 — 한국어 출력 실사 필요
4. [ ] eval-runner의 LLM-as-judge noise level 미측정 — human agreement rate 필요
5. [ ] 각 SKILL.md를 skill-creator로 실제 생성 → 실패 지점 발견 필요

---

## Change Log

| Date | Change | Reason |
|---|---|---|
| 2026-04-14 | rag-pipeline v2: pgvector + OpenRouter | J directive: ChromaDB→PostgreSQL, 64GB |
| 2026-04-14 | eval-runner v2: bootstrap + DSPy removal | Meta-review: fantasy detection |
| 2026-04-14 | Blueprint timeline revised | Meta-review: 40% overoptimistic |
| 2026-04-14 | MLX embedding code removed | Blind audit: non-functional code |
