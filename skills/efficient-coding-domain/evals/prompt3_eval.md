# efficient-coding-domain — Prompt 3 Evaluation (Robustness/Edge Cases)

**Evaluation Date:** 2026-04-14  
**Skill File:** `/private/tmp/csnl-skill-ecosystem/skills/efficient-coding-domain/SKILL.md` (273 lines)  
**Focus:** Cross-domain bridge robustness — ambiguous concepts (e.g., "adaptation" across domains), hallucination in CRMB↔EC bridge, Korean terminology gaps, equation notation conflicts

---

## Test Scenarios

### 1. Ambiguous Concept: "Adaptation" Across Domains
**Scenario:** User asks: "How does neural adaptation relate to efficient coding principles?"

**Expected Behavior:**
- **EC interpretation:** Temporal whitening / predictability reduction (Laughlin 1981, Atick & Redlich 1992) — neurons adapt to stimulus statistics to optimize signal transmission
- **CRMB interpretation:** Adaptive resonance theory vigilance thresholds adjusting to attention levels / task demands
- Skill should disambiguate both meanings and clarify which domain applies
- Bridge should explain convergent mechanisms (both optimize representation given constraints)

**Actual Result:** ⚠️ **PARTIAL FAIL**
- Concept graph (lines 84–127) lists "adaptation" only in metabolic efficiency context
- No explicit entry for "neural adaptation" as a temporal coding phenomenon
- Cross-domain bridge (lines 129–149) addresses "Metabolic Efficiency ↔ LAMINART Laminar Circuits" but omits adaptation-to-whitening connection
- CRMB reference materials are not provided; skill cannot disambiguate ART vigilance vs. EC adaptation
- User invoking this skill with "adaptation" query would receive incomplete coverage

**Impact:** High — "adaptation" appears in dozens of neuroscience papers; ambiguity causes confusion.

---

### 2. Hallucination Risk: Invented CRMB ↔ EC Connections
**Scenario:** User queries: "Does BCS implement sparse coding principles through its boundary-contour computation?"

**Expected Behavior:**
- Skill acknowledges uncertainty if connection is theoretical vs. empirically validated
- Cites specific papers claiming/rejecting the connection
- Avoids claiming equivalence without source support

**Actual Result:** ❌ **FAILS**
- Section 4 (lines 129–149) makes bridge claims like: "BCS's boundary contour system is a form of sparse coding"
- No citation supporting this claimed equivalence
- SKILL.md provides no ground-truth validation mechanism (e.g., "bridges only claim connections from cited papers")
- RAG corpus preparation (section 5) advises chunking but does not enforce citation tracking
- Risk: Skill could generate plausible-sounding but unsupported connections (e.g., "LAMINART sparse representations optimize metabolic efficiency by pruning weak layer 4 signals")

**Impact:** Critical — False bridges undermine tutor credibility; users may propagate unfounded theories.

---

### 3. Korean Terminology Gap: "적응" Polysemy
**Scenario:** Korean-speaking user asks in Korean: "신경 적응(neural adaptation)이 효율적 부호화와 어떤 관계가 있나요?"

**Expected Behavior:**
- Glossary (lines 176–210) provides both domain-specific Korean terms
- Skill disambiguates "적응" in EC context (temporal filtering / whitening) vs. CRMB context (vigilance adjustment)
- Output clearly states which definition applies

**Actual Result:** ⚠️ **PARTIAL FAIL**
- Korean glossary is provided (lines 176–210)
- **BUT:** "adaptation" is not included in glossary; only covers base concepts (sparse coding, efficient coding, etc.)
- No guidance on polysemous terms or context-dependent translations
- If user asks in Korean, skill cannot disambiguate 적응 without English fallback
- Glossary is English ↔ Korean but lacks hierarchical organization by domain (EC vs. CRMB)

**Impact:** Medium — Korean users will encounter undefined terms; glossary feels incomplete.

---

### 4. Equation Notation Conflicts Between Domains
**Scenario:** User queries both:
- EC paper using: $\rho = \text{corr}(x_i, x_j)$ for redundancy correlation
- CRMB paper using: $\rho$ for vigilance parameter (match threshold)

**Expected Behavior:**
- Skill maintains separate equation symbol tables per domain
- When bridging, clearly maps EC $\rho$ → CRMB ρ with explanation (different meanings)
- Avoids conflating formalism

**Actual Result:** ❌ **FAILS**
- Section 5 (lines 151–169) describes equation extraction and "Preserve variable definitions"
- **BUT:** No formal symbol clash detection or domain-scoped equation registries
- Concept graph (lines 84–127) does not include equation metadata or variable definitions
- If RAG retrieves chunk with EC $\rho = \text{corr}(...)$ and CRMB $\rho$ threshold, tutor would display both without disambiguation
- Users could incorrectly map EC correlation threshold onto CRMB vigilance parameter

**Impact:** High — Notation conflict creates formal errors in user understanding.

---

### 5. Cross-Domain Query Hallucination: "Sparse Coding Vigilance"
**Scenario:** User asks: "Can sparse coding explain why ART's vigilance threshold prevents false matches?"

**Expected Behavior:**
- Skill recognizes this conflates two mechanisms: sparsity (EC) and match suppression (ART)
- Clarifies: Sparsity *could* inform vigilance threshold design but is not a direct mechanism
- Cites papers if connection exists; states "uncertain / not directly addressed" if not

**Actual Result:** ❌ **FAILS**
- Bridge section (lines 129–149) claims: "Sparse Coding ↔ ART Category Learning: Both achieve efficient representation through selective neuron activation"
- This is plausible but overstated; no citation validates that sparse coding *explains* vigilance
- Evaluation queries (section 7, lines 213–260) lack a "CRMB-EC interaction" query that would expose hallucination
- Ground-truth validation is absent; claims are assertions without empirical backing

**Impact:** Critical — Users will construct false causal narratives (sparse coding → ART vigilance mechanism).

---

### 6. Missing Domain Boundary Concepts
**Scenario:** User asks: "What is information bottleneck theory and how does it relate to CRMB?"

**Expected Behavior:**
- Skill recognizes information bottleneck (Tishby et al.) as an EC-domain concept
- States whether it appears in CRMB literature
- If bridge exists, cites sources

**Actual Result:** ❌ **FAILS**
- Concept graph (lines 84–127) lists "efficient_coding" with sparse coding, population coding, predictive coding, redundancy reduction, metabolic efficiency
- **Missing:** information bottleneck, rate-distortion theory, predictive information / deep learning connections
- These are foundational EC concepts but absent from knowledge base
- User asking about information bottleneck receives no coverage (skill triggered but insufficient ground truth)

**Impact:** Medium-High — Skill is incomplete for EC domain; critical modern EC concepts are absent.

---

### 7. Evaluation Query Coverage Gaps
**Scenario:** Tutor runs 15 evaluation queries (lines 213–260) to validate ground truth.

**Expected Behavior:**
- Each query tests one concept with clear expected coverage
- Queries capture multi-domain scenarios

**Actual Result:** ⚠️ **PARTIAL FAIL**
- Queries 1–7 test single-domain concepts; Queries 8–15 test bridges or specialized topics
- **Gaps:**
  - Q8 tests ART ↔ Predictive Coding but Q6 tested retinal efficient coding (narrow scope)
  - No query tests "information bottleneck" or rate-distortion theory
  - No query explicitly tests hallucination resistance (e.g., "Does sparse coding explain ART vigilance?")
  - Q12 (overcomplete bases) is EC-specific with no CRMB bridge attempt
- Evaluation set is ~70% EC-focused, ~20% CRMB, ~10% bridge — imbalanced for bridge robustness

**Impact:** Medium — Evaluation protocol does not stress-test cross-domain brittleness.

---

## Findings Summary

### What Works
1. ✓ EC domain fundamentals clearly defined (sparse coding, population coding, predictive coding, metabolic constraints)
2. ✓ Well-structured concept graph with hierarchical organization
3. ✓ Key papers cited (Barlow, Olshausen, Pouget, Rao & Ballard, Friston)
4. ✓ Korean glossary provided (English ↔ Korean translations)
5. ✓ RAG corpus preparation guidance is detailed and section-aware

### What Breaks
1. ❌ **Ambiguous concepts underdefined:** "adaptation" exists in both domains; skill provides no disambiguation logic
2. ❌ **Unsupported bridges:** Cross-domain claims lack citations; hallucination risk is high
3. ❌ **Korean terminology gaps:** Polysemous terms (적응) not handled; glossary incomplete for domain-specific usage
4. ❌ **Notation conflicts untracked:** Equation symbol collisions (ρ in EC vs. CRMB) would confuse users
5. ❌ **Missing EC concepts:** Information bottleneck, rate-distortion, predictive information absent from knowledge base
6. ❌ **Evaluation queries weak on cross-domain hallucination:** No explicit test for false bridges
7. ❌ **No ground-truth validation mechanism:** Bridges are assertions without empirical backing

### Root Causes
- **No formal bridge validation:** CRMB-EC connections are theoretical propositions, not grounded in cited empirical work
- **Incomplete EC knowledge base:** Core modern EC concepts (information bottleneck, rate-distortion) missing
- **Ambiguity in domain definitions:** Concepts like "adaptation," "selectivity," "efficiency" are used across domains without explicit scoping
- **Korean support is surface-level:** Glossary is English ↔ Korean mapping without domain-aware semantics
- **Evaluation protocol is EC-heavy:** Does not stress-test multi-domain robustness

---

## Score: 2/5

**Rationale:**
- **Relevance: 3/5** — Covers EC domain well; bridges are relevant but unsupported
- **Completeness: 2/5** — EC knowledge base is ~70% complete (missing IB, rate-distortion); CRMB integration is ~30%
- **Hallucination Resistance: 1/5** — Unsupported bridges pose high risk of false claims
- **Ground Truth Grounding: 2/5** — Evaluation queries exist but do not validate cross-domain claims
- **Multilingual Robustness: 2/5** — Korean glossary provided but incomplete and unambiguous for domain context
- **Cross-Domain Clarity: 1/5** — Ambiguous concepts not disambiguated; notation conflicts unmanaged

**Composite:** (3 + 2 + 1 + 2 + 2 + 1) / 6 = **1.83/5** → **2/5**

---

## Recommendations

### Critical Patches (Priority 1)

1. **Add ground-truth validation for bridges:**
   ```python
   VALIDATED_BRIDGES = {
       ("sparse_coding", "ART"): {
           "claim": "Both achieve efficient representation through selective neuron activation",
           "citations": ["Srinivasan_et_al_2000", "Olshausen_1996"],
           "confidence": "medium",  # low/medium/high based on evidence
       },
       ("predictive_coding", "ART_vigilance"): {
           "claim": "Predictive coding formalizes ART's top-down/bottom-up dynamics",
           "citations": ["Friston_2005"],
           "confidence": "low",  # speculative, not directly validated
       },
   }
   ```
   - Only serve bridges from VALIDATED_BRIDGES
   - Mark speculative bridges with low confidence
   - Require at least one citation per bridge

2. **Disambiguate polysemous concepts:**
   ```python
   DOMAIN_SPECIFIC_TERMS = {
       "adaptation": {
           "EC": {
               "definition": "Temporal filtering to whiten stimulus statistics (Laughlin 1981)",
               "key_papers": ["Laughlin_1981", "Atick_Redlich_1992"],
               "synonyms": ["gain control", "whitening", "decorrelation"],
           },
           "CRMB": {
               "definition": "Vigilance threshold adjustment to attention/task demands",
               "key_papers": ["Grossberg_CRMB_Ch3"],
               "synonyms": ["vigilance modulation", "category learning adjustment"],
           },
       },
   }
   ```

3. **Add notation registry with domain scoping:**
   ```python
   EQUATION_REGISTRY = {
       "rho": [
           {
               "domain": "efficient_coding",
               "definition": "Correlation coefficient: corr(x_i, x_j)",
               "context": "Redundancy reduction",
               "source": "Atick_Redlich_1992",
           },
           {
               "domain": "CRMB",
               "definition": "Vigilance parameter (match threshold)",
               "context": "ART pattern matching",
               "source": "Grossberg_CRMB_Ch3",
           },
       ],
   }
   ```
   - When rendering equations, flag symbol collisions
   - Auto-rename to ρ_EC vs. ρ_CRMB when both appear

### High-Priority Patches (Priority 2)

4. **Expand EC knowledge base:**
   - Add information bottleneck theory (Tishby et al. 1999+)
   - Add rate-distortion theory connections
   - Add predictive information / deep learning links
   - Extend concept graph to ~200 nodes (currently ~30)

5. **Enhance Korean glossary with domain context:**
   ```python
   KOREAN_GLOSSARY = {
       "적응": {
           "EC": "대사 효율성을 위한 시간적 필터링 (시간-영역 화이트닝)",
           "CRMB": "ART의 경계값 조정 (주의 기반 카테고리 학습)",
       },
       "선택성": {
           "EC": "희소 부호화에서 활성 뉴런 선택 (overfitting 방지)",
           "CRMB": "BCS 방향 선택성 (V1 기본 피처 검출)",
       },
   }
   ```

6. **Strengthen evaluation queries with hallucination tests:**
   - Q16: "Can sparse coding explain ART's vigilance mechanism? Provide evidence."
   - Q17: "What is information bottleneck theory and does it appear in CRMB?"
   - Q18: "Explain the notation ρ in both efficient coding and CRMB contexts."
   - These explicitly test cross-domain hallucination resistance

### Medium-Priority Patches (Priority 3)

7. **Add bridge confidence scoring:**
   - Evaluate each bridge with metrics: citation coverage, empirical support, theoretical plausibility
   - Return bridges ranked by confidence
   - Display confidence in tutor output

8. **Implement bridge-to-citation mapper:**
   - User queries bridge → skill returns: (claim, citations, confidence, alternative interpretations)
   - Tutor can surface "This connection is speculative; alternative views exist"

9. **Audit concept graph for CRMB coverage:**
   - Map CRMB chapters to EC concepts (currently implicit)
   - Create explicit CRMB concept graph matching EC structure
   - Test 1:1 mapping quality (should be ~70% matched)

---

## Testing Checklist for Next Eval

- [ ] Query "adaptation" → receive both EC (whitening) and CRMB (vigilance) definitions
- [ ] Query "Does sparse coding explain ART vigilance?" → receive low-confidence response with caveat
- [ ] Korean query about 적응 → receive domain-disambiguated responses
- [ ] Generate equation with ρ from EC paper + ρ from CRMB paper → verify collision detection
- [ ] Query "information bottleneck" → receive substantive coverage (not "not found")
- [ ] Run all 15 evaluation queries → verify ≥90% citation coverage per query
- [ ] Manually audit 5 bridge claims → verify ≥3 citations per claim
- [ ] Generate cross-domain post (ART + sparse coding) → verify no hallucinated connections

---

**Summary:** efficient-coding-domain is a well-researched EC knowledge base that fails when bridging to CRMB. Unsupported bridges pose hallucination risk; ambiguous concepts and notation conflicts would confuse users. Investment in ground-truth validation, domain-scoped terminology, and expanded EC knowledge base would elevate from 2/5 → 4/5.
