# eval-runner — Prompt 1 Evaluation (Foundational)

## Test Scenarios

### Test 1: Metric Definition and Coverage
**Scenario**: Can the skill define all required retrieval metrics with correct formulas and targets?

**Criterion**: 
- Defines Precision@5, Recall@10, MRR, nDCG@10 with mathematical formulas
- Sets realistic threshold targets (P@5 > 0.6, Recall > 0.8, MRR > 0.5, nDCG > 0.7)
- Provides executable Python code for metric computation

**Finding**: SKILL.md covers all four retrieval metrics with formulas, clear target thresholds, and working `eval_retrieval()` function. Formulas are correct. Python implementation uses proper scoring logic (e.g., 1/rank for MRR).

### Test 2: Bootstrap Ground Truth Schema
**Scenario**: Is the ground truth structure clearly specified for building a 30-query test suite?

**Criterion**:
- Specifies JSON schema for ground truth with: id, query (EN/KO), relevant_papers, relevant_sections, difficulty level, domain
- Recommends 30-query minimum with 5+ domains
- Provides realistic time estimate (2-3 days) and step-by-step bootstrap instructions

**Finding**: SKILL.md provides complete `GROUND_TRUTH` schema with bilingual queries (en/ko), relevant_papers list, sections, difficulty, and domain. Explicitly states 30-query minimum rationale. Bootstrap workflow is concrete: export Zotero → list questions → identify papers → mark sections → save JSON. Time estimate included.

### Test 3: Generation Quality Metrics
**Scenario**: Does the skill cover generation quality (factuality, relevance, completeness, citation accuracy)?

**Criterion**:
- Defines at least 4 generation metrics beyond retrieval
- Provides LLM-as-judge prompts with rating scales
- Addresses Korean language quality separately

**Finding**: SKILL.md defines 5 generation metrics: Factuality (LLM judge vs docs, >0.9), Relevance (cosine similarity, >0.7), Completeness (key points coverage, >0.8), Citation accuracy (>0.85), Korean fluency (LLM judge, >0.8). Includes full judge prompt with 1-5 scale. Korean-specific eval section with naturalness, terminology, consistency, clarity checks.

### Test 4: Ablation & Diagnostic Workflows
**Scenario**: Can the skill isolate retrieval vs generation vs language failures?

**Criterion**:
- Provides ablation method: ground truth injection to test generation alone
- Provides parallel language comparison (KO vs EN)
- Includes diagnostic decision tree for metric divergence patterns

**Finding**: SKILL.md provides 3 ablation workflows: (1) Test generation with gold passages only, (2) Test generation with actual retriever, (3) Language-specific ablation comparing KO/EN on same queries. Includes diagnostic decision tree for 3 metric patterns (high nDCG/low MRR, low nDCG/high MRR, both low).

### Test 5: Korean-Specific Diagnostics
**Scenario**: Does the skill provide Korean language-specific diagnostic checks?

**Criterion**:
- Defines diagnostic checks for Korean terminology consistency
- Detects 번역투 (translation-like) errors
- Specifies Korean vs English mixing ratio target

**Finding**: SKILL.md includes Korean diagnostic checklist: (1) TERM_GLOSSARY coverage verification, (2) Generation prompt monolingual Korean check (>95%), (3) Retrieval language mismatch detection. Flags 번역투 patterns (되어지다, 이루어지다 overuse). Targets >70% Korean for undergrad content.

## Findings

**Strengths:**
- All core retrieval metrics (recall@k, precision@k, MRR, NDCG) fully specified with formulas and code
- Bootstrap ground truth workflow is practical and achievable (30-query minimum justified)
- Generation quality evaluation uses LLM-as-judge with explicit scoring scales and Qwen2.5-32B local model
- Ablation workflow clearly separates retrieval/generation/language failure modes
- Korean language evaluation is thorough (naturalness, terminology consistency, clarity)
- Metric divergence patterns include diagnostic decision tree for root cause analysis
- Citation accuracy metric (>0.85) explicitly included

**Gaps:**
- No mention of confidence intervals or variance reporting for small test suites (30 queries acknowledged as tight)
- DSPy integration deferred to Phase 2+ (acknowledged limitation, acceptable for P1)
- HTML report generation spec mentioned but no implementation code
- Korean terminology glossary referenced but not included inline (external file assumed)

**Quality Assessment:**
- Metric definitions are mathematically sound and directly testable
- Code examples are complete and runnable (eval_retrieval, eval_generation_factuality, ablation functions)
- Ground truth schema is JSON-parseable and domain-aware
- Handles 2 languages (EN/KO) with explicit term consistency checks
- Diagnostic depth covers retrieval anomalies (Pattern 1-3) with explicit fixes

## Score: 5/5

**Rationale:**
- All required components for foundational evaluation capability present and well-specified
- Metric coverage includes recall@k, precision@k, MRR, NDCG as required
- Bootstrap workflow provides clear path from concept to 30-query suite
- Generation quality metrics exceed baseline (5 metrics including language-specific)
- Ablation + diagnostic workflows provide strong failure isolation capability
- Korean language support integrated throughout, not bolted on
- Code examples are production-grade (not pseudocode)
- P1 scope focused on definable metrics and repeatable workflows; Phase 2+ defers LLM optimization

## Recommendations

1. **Add confidence interval reporting** for small test suites: Report 95% CI alongside point estimates
2. **Implement HTML report generation** code (currently just a stub comment)
3. **Provide TERM_GLOSSARY example** with 20+ Korean/English term pairs for domain
4. **Add eval scheduling template** for manual-then-automated Phase 1→2 transition
5. **Document Qwen2.5-32B setup** for local LLM-as-judge (MLX/Ollama instructions)
