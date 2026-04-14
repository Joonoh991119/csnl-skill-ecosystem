# tutor-content-gen — Prompt 1 Evaluation (Foundational)

## Test Scenarios

### Test 1: Socratic Dialogue Generation
**Scenario**: Can the skill generate Socratic dialogues with proper three-phase structure (Diagnostic → Guided Discovery → Consolidation)?

**Criterion**:
- Phase 1 probes baseline knowledge with open-ended questions
- Phase 2 guides discovery via contrasting examples
- Phase 3 consolidates via learner explanation (not tutor explanation)
- Maintains dialogue naturalness (not question-dumping)

**Finding**: SKILL.md provides three-phase structure with clear examples. Phase 1: diagnostic questions ("You mentioned understanding backpropagation...") that probe without judgment. Phase 2: guided discovery ("What would need to happen?") with analogy/contrast (ART vigilance vs backprop error). Phase 3: consolidation ("Can you explain in your own words?") asking learner to explain. Example dialogue shows natural conversational flow across 8 turns, not rapid-fire questions.

### Test 2: Hallucination Prevention
**Scenario**: Does the skill prevent claims outside CRMB corpus?

**Criterion**:
- Specifies corpus boundaries (CRMB Ch 1-20, primary sources only)
- Provides mechanism for flagging ungrounded claims [UNGROUNDED], [MEDIUM CONFIDENCE], [OUT-OF-SCOPE]
- Includes "trap query detection" for semantic leap errors
- Provides dialog templates for honest uncertainty (Korean)

**Finding**: SKILL.md defines corpus boundary explicitly: CRMB Chapters 1-20 + Grossberg foundational papers (1976+) + Carpenter & Grossberg (1987) + Grossberg & Mingolla. Secondary sources marked [SECONDARY SOURCE]. Out-of-scope claims flagged [OUT-OF-SCOPE] with RISK: HIGH. Trap query detection section includes `check_semantic_chain()` verifying explicit source linkage (NOT inferring "nonlinear dynamics" → "chaos theory"). Uncertainty templates in Korean: "CRMB에서 직접 다루지 않아요", "제가 확실히 말하기 어려워요".

### Test 3: Korean Tutoring Format
**Scenario**: Is bilingual dialogue correctly formatted with Korean-primary, English technical terms?

**Criterion**:
- Primary language Korean (ko), technical terms English inline with parenthetical translation
- Term consistency across dialogue (same concept = same Korean term)
- Translation validation against CRMB source material
- TERM_GLOSSARY mapping (English ↔ Korean)

**Finding**: SKILL.md specifies language blending: Korean concept → English technical term (inline) → example → English from source. Example: "신경망이 학습할 때 가중치를 조정하는 방향을 결정하는 신호를 'error signal'이라고 부릅니다. Grossberg의 이론에서는 이것을 'mismatch signal'이라고 하는데, 차이가 무엇일까요?" TERM_GLOSSARY table includes 8 entries (Adaptive Resonance Theory / 적응적 공명 이론, Vigilance / 경계 매개변수, Mismatch signal / 부정합 신호, etc.). Translation validation protocol specifies checking Korean terms against CRMB sources.

### Test 4: Source Grounding with Citation Schema
**Scenario**: Does every mechanistic claim have [MECHANISM], [SOURCE], [CONFIDENCE], [RISK] metadata?

**Criterion**:
- Every claim tagged with source (author, year, section, page if available)
- Confidence level specified: HIGH (directly stated) | MEDIUM (inferred) | LOW (analogous)
- Risk assessment: None | MEDIUM | HIGH
- Complete dialogue JSON includes citations_used array

**Finding**: SKILL.md provides citation schema with [MECHANISM], [SOURCE], [CONFIDENCE], [RISK] tags. Example: [MECHANISM] "Vigilance (ρ) restricts acceptable prototypes", [SOURCE] "Carpenter & Grossberg (1987, Neural Networks 1(1): 17-88)", [CONFIDENCE] HIGH, [RISK] None. Output JSON schema includes citations_used array with full source metadata. Unverified claims flagged with source_coverage: "NOT FOUND" and recommendation to rephrase or omit.

### Test 5: Hallucination Prevention Workflow
**Scenario**: Is the 4-step hallucination prevention workflow complete?

**Criterion**:
- Step 1: Search CRMB corpus for supporting passage
- Step 2: Verify against retrieved chunks (verbatim, equations, figures)
- Step 3: Never synthesize mechanisms outside retrieved chunks
- Step 4: Flag unverified claims in output JSON

**Finding**: SKILL.md provides explicit 4-step workflow. (1) Query vector DB with claim terms, retrieve top-3 passages, reject if relevance < 0.7. (2) Cross-reference against passage (verbatim, equation numbers, page refs). If contradicts: REJECT. If extends: [MEDIUM CONFIDENCE] + RISK flag. (3) Never generate mechanisms outside chunks; pose as question instead. Example: "Instead of ART then does X, ask What would happen if...?" (4) Mark as [UNVERIFIED] in JSON with source_coverage: "NOT FOUND" and recommendation.

## Findings

**Strengths:**
- Three-phase Socratic structure (Diagnostic → Guided Discovery → Consolidation) clearly specified
- Hallucination prevention explicit with corpus boundary definition and trap query detection
- Korean-primary format with English technical terms inline; language blending specified
- Citation schema [MECHANISM], [SOURCE], [CONFIDENCE], [RISK] applied to all claims
- Validation checklist (8 items) ensures dialogue quality before delivery
- Multilingual term glossary with 8+ English/Korean pairs for domain
- ART-specific scaffolding sequence (prerequisites, key mechanisms in order, risk zones)

**Gaps:**
- Socratic dialogue generation algorithm not provided (template-only, not implementation)
- LLM selection for dialogue generation not specified (assumption: Claude or Qwen2.5)
- Learner profile structure defined but no automatic learner assessment algorithm
- Vector DB integration assumed but not detailed (assumes RAG pipeline already built)
- Phase transition detection not algorithmic (no guidance on when to move Phase 1→2→3)
- Corpus boundary enforcement relies on manual flagging (no automated check)

**Quality Assessment:**
- Socratic structure is pedagogically sound (based on Bloom's taxonomy progression)
- Hallucination prevention workflow is rigorous and practical
- Korean format matches target learner (CSNL neuroscience students)
- Citation schema is verifiable and repeatable
- ART topic coverage is complete for P1 (prerequisites → mechanics → edge cases)
- Validation checklist provides objective quality gates

## Score: 4/5

**Rationale:**
- Socratic dialogue generation works (three phases with clear progression)
- Hallucination prevention workflow is explicit and comprehensive
- Korean tutoring format correctly specified with term consistency
- Citation schema [MECHANISM], [SOURCE], [CONFIDENCE], [RISK] applied throughout
- Validation checklist ensures dialogue quality
- ART-specific scaffolding with risk zones identified
- **Limitation for 4/5**: Dialogue generation algorithm not provided (template-only). Implementation requires LLM integration, which is deferred to skill invocation. For P1, structural specification is sufficient, but end-to-end code example would elevate to 5/5.

## Recommendations

1. **Provide dialogue generation algorithm** (pseudocode or full implementation) using Claude/Qwen2.5
2. **Add learner assessment function** to automatically construct learner_profile from diagnostic Q&A
3. **Implement corpus boundary enforcement** with automated [OUT-OF-SCOPE] detection
4. **Document phase transition heuristics** (turn count, learner response patterns)
5. **Provide vector DB integration example** (assumes rag-pipeline already running)
6. **Add dialogue quality metrics** (Socratic ratio, coverage of risk zones, misconception handling)
7. **Expand TERM_GLOSSARY** from 8 to 20+ terms for broader coverage beyond ART
