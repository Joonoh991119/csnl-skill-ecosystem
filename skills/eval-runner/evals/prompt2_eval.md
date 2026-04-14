# Evaluation Report: eval-runner Skill vs. EVAL PROMPT 2 (Edge Cases)

## Executive Summary

The eval-runner SKILL.md provides a **solid foundation** for diagnostic evaluation workflows but falls short on **multi-metric interpretation and cross-domain debugging** for complex, realistic failure scenarios. The skill succeeds in metric definitions and ground-truth setup but **lacks systematic guidance** on how to synthesize results across retrieval, generation, and language-specific dimensions when signals conflict.

---

## Query Under Test

User scenario: Multi-metric, multi-language evaluation with contradictory signals
- NDCG@10=0.72 (decent) but MRR@5=0.45 (poor)
- Korean naturalness=4.2/5 (good) but term consistency=2.8/5 (poor)
- Question: Is this retrieval, generation, or Korean-specific?

---

## Analysis: Does the Skill Provide Sufficient Guidance?

### STRENGTHS: What the Skill Covers Well

| Aspect | Coverage | Evidence |
|--------|----------|----------|
| **Metric definitions** | ⭐⭐⭐⭐⭐ | Clear formulas for Precision@5, Recall@10, MRR, nDCG@10 with target thresholds (>0.5 for MRR) |
| **Retrieval evaluation code** | ⭐⭐⭐⭐⭐ | Complete working Python function `eval_retrieval()` showing step-by-step ranking analysis |
| **Generation quality assessment** | ⭐⭐⭐⭐ | Factuality and Korean LLM-as-judge implementations provided with example prompts |
| **Bootstrap ground truth process** | ⭐⭐⭐⭐⭐ | Pragmatic guidance: 30 queries minimum, 5 domains, manual annotation approach |
| **Korean language evaluation** | ⭐⭐⭐⭐ | Dedicated section with LLM-as-judge prompt in Korean, specific checks for 번역투 and term consistency |
| **Known limitations** | ⭐⭐⭐⭐ | Honest assessment of LLM-as-judge noise (~0.7 agreement), circular dependency risks, ground truth staleness |

### CRITICAL GAPS: Where the Skill Fails for This Query

#### Gap 1: Metric Interpretation & Reconciliation
**Problem**: The skill defines metrics but does NOT explain how to interpret conflicting signals.

User's situation:
- NDCG@10 = 0.72 (above 0.7 target) → suggests overall ranking is acceptable
- MRR@5 = 0.45 (well below 0.5 target) → suggests first relevant doc is in position 5+

**What the skill provides**: Individual metric formulas
```python
# MRR = 1/rank_of_first_relevant
# nDCG@10 = normalized discounted cumulative gain
```

**What the skill SHOULD provide but doesn't**:
- A decision tree: "If MRR < 0.5 but nDCG@10 > 0.7, then: relevant docs exist but are ranked too low"
- Guidance: "Check rank distribution of relevant docs (6-10 vs 1-5)"
- Root cause hypothesis: "This pattern suggests: (1) embedding similarity is weak for top positions, (2) re-ranker is underperforming, or (3) ground truth is wrong"

**Actionability: 2/5** — User must infer the diagnosis themselves.

---

#### Gap 2: Cross-Language Diagnosis Framework
**Problem**: Korean metrics (naturalness vs. term consistency gap) are evaluated in isolation.

User's situation:
- Naturalness = 4.2/5 (suggests LLM generation works)
- Term consistency = 2.8/5 (suggests translation quality or glossary alignment fails)

**What the skill provides**:
```python
def eval_korean_quality(qa_pairs_ko: list) -> dict:
    scores = {'naturalness': [], 'terminology': [], 'consistency': [], 'clarity': []}
    # ... computes averages
```

**What the skill SHOULD provide but doesn't**:
- Upstream/downstream diagnosis: "Is term consistency failing because:
  - (Upstream) Retrieved papers have inconsistent Korean terminology in source PDFs?
  - (Generation) The LLM is translating incorrectly despite good naturalness?
  - (Config) TERM_GLOSSARY is incomplete or misaligned?"
- Concrete next step: "Run retrieval eval on Korean queries separately to check if Korean document retrieval quality < English quality"

**Actionability: 1/5** — Skill reports metrics but no diagnostic pathway.

---

#### Gap 3: Retrieval vs. Generation Attribution
**Problem**: No systematic way to isolate the source of failure when both retrieval and generation could be responsible.

Example from user query:
- Could the NDCG/MRR gap be caused by:
  1. **Retrieval problem**: Embedding model doesn't rank relevant Korean papers in top-5?
  2. **Generation problem**: LLM generates good naturalness but ignores retrieved Korean terminology?
  3. **Both**: Retriever returns low-confidence matches → LLM compensates with generic Korean?

**What the skill provides**: Separate `eval_retrieval()` and `eval_generation_factuality()` functions.

**What's missing**:
- Ablation suggestions: "Run retrieval eval on ONLY Korean queries; compare precision@5_ko vs precision@5_en"
- Pipeline instrumentation: "Log which retrieved documents were used for each generation; check if high-quality Korean docs ranked low"
- Failure propagation analysis: "If precision@5_ko < precision@5_en, fix retrieval first. Otherwise, debug generation."

**Actionability: 2/5** — Can run evals in isolation but no guidance on correlation analysis.

---

#### Gap 4: Metric Confidence & Variance
**Problem**: The skill mentions ~0.7 LLM-as-judge agreement but doesn't address confidence thresholds for this specific query.

User has:
- Term consistency = 2.8/5 (between 2 and 3)
- Uncertainty: Is this a real problem (means LLM is genuinely confused) or judge noise?

**What the skill says**:
"LLM-as-judge is noisy: Factuality scores from local Qwen2.5 have ~0.7 agreement with human judgment. Always spot-check."

**What's missing**:
- Confidence interval guidance: "With N=30 Korean queries, score 2.8 has ±0.3 margin of error. Spot-check 5-10 cases manually."
- Threshold interpretation: "Scores 2-3 need manual review; scores <2 or >4 are more confident"
- Replication logic: "Run LLM judge twice on same sample; if agreement <0.6, the metric is too noisy to diagnose"

**Actionability: 1/5** — User doesn't know if 2.8 is a real signal or noise.

---

## Specific Sections: What Helps vs. What's Missing

### Helps: Retrieval Evaluation Code
**Location**: Section "1. Retrieval Quality"
**Code**: `eval_retrieval()` function computes all four metrics

**Why it helps for this query**: If user runs this function separately on Korean vs. English queries, they can compute:
- `precision@5_en` vs. `precision@5_ko`
- If gap is >0.1, Korean retrieval is the bottleneck

**Still missing**: Guide on how to interpret the gap once computed.

---

### Helps: Korean Evaluation Prompt
**Location**: Section "Korean Language Evaluation"
**Code**: Full LLM-as-judge prompt in Korean with 4-point evaluation rubric

**Why it helps**: User can run this exact prompt to re-evaluate a sample of Korean outputs with finer granularity.

**Still missing**: Instructions on sample size, confidence thresholds, and how to use results diagnostically.

---

### Helps (Partially): Improvement Suggestions Engine
**Location**: Section "Improvement Suggestions Engine"
**Code**: `generate_recommendations()` function with example checks

**Limitation**: Only addresses retrieval precision < 0.6 and generation factuality < 3.5. Does NOT cover:
- MRR < 0.5 with nDCG > 0.7 (the exact pattern in this query)
- Language-specific metric divergence
- Ranked list position analysis

**Example of what's in the code**:
```python
if results['retrieval']['precision_at_5'] < 0.6:
    recs.append({
        'area': 'retrieval',
        'severity': 'high',
        'suggestion': 'Retrieval precision is low. Consider: (1) Re-embedding with a better model, ...'
    })
```

**What's needed**: Rules like:
```python
if results['retrieval']['mrr'] < 0.5 and results['retrieval']['ndcg_at_10'] > 0.7:
    recs.append({
        'area': 'retrieval_ranking',
        'severity': 'medium',
        'suggestion': 'Relevant docs exist but ranked low. Check: (1) Are top-5 results high-confidence? '
                     '(2) Does re-ranker function? (3) Is ground truth correct?'
    })
```

**Actionability: 2/5**

---

### Gaps: No Ablation/Diagnostic Workflows

**Missing entirely**: Step-by-step diagnostic trees

Example of what SHOULD be in SKILL.md:

```
## Diagnostic Workflow: Metric Divergence

IF MRR@5 < threshold AND nDCG@10 >= threshold:
  Hypothesis: Relevant documents exist but are ranked 6-10
  
  Step 1: Analyze rank distribution
    - Count how many relevant docs are in [1-5] vs [6-10]
    - If >50% in [6-10], proceed to Step 2
  
  Step 2: Debug ranking stage
    a) Check retriever confidence scores → Are top-5 low-confidence?
    b) If re-ranker exists, disable it → Does MRR improve?
    c) Check ground truth → Are "relevant" docs actually relevant?
  
  Step 3: Root cause assignment
    - If confidence scores are the issue → Re-embed or fine-tune retriever
    - If re-ranker is failing → Check re-ranker training data
    - If ground truth is wrong → Correct annotations
```

**Current state**: SKILL.md jumps to generic "Consider: (1) Re-embedding (2) Adding BM25..." without diagnostic prerequisite.

---

### Gaps: Korean-English Comparison

**Missing entirely**: Guidance for multi-language evaluation

What's needed:
```
## Multilingual Evaluation Strategy

When metrics diverge by language (e.g., naturalness_ko ≠ naturalness_en):

Step 1: Isolate retrieval quality by language
  eval_retrieval(queries_en, ...) → precision@5_en = X
  eval_retrieval(queries_ko, ...) → precision@5_ko = Y
  If abs(X-Y) > 0.1, retrieval is language-specific
  
Step 2: Isolate generation quality by language
  eval_generation_factuality(qa_pairs_en, ...) → mean_factuality_en = A
  eval_generation_factuality(qa_pairs_ko, ...) → mean_factuality_ko = B
  If abs(A-B) > 0.2, generation is language-specific
  
Step 3: Interpret term consistency degradation
  If naturalness_ko > 4.0 but term_consistency_ko < 3.0:
    Likely cause: TERM_GLOSSARY incomplete or LLM ignoring it
    Check: Does glossary contain Korean equivalents for domain terms?
    Test: Add glossary enforcement to prompt → Re-run eval
```

**Current state**: SKILL.md has Korean evaluation in isolation; no comparative framework.

---

## Scoring: Relevance, Completeness, Actionability

### 1. Relevance: 4/5
✅ **Strengths**:
- Metric definitions directly match user's metrics (NDCG, MRR, naturalness, consistency)
- Ground truth bootstrap process is appropriate for the RAG system
- Korean evaluation section is well-designed

❌ **Gaps**:
- Diagnostic frameworks are missing (not directly relevant to this complex scenario)
- Multi-language comparison is mentioned but not actionable

**Score**: 4/5

---

### 2. Completeness: 2/5
✅ **Strengths**:
- Full code implementations for metric computation
- Comprehensive Korean prompt with 4-point rubric
- Honest limitations section

❌ **Major gaps**:
- No workflows for interpreting conflicting metrics
- No ablation/diagnostic procedures
- No guidance for root-cause attribution (retrieval vs. generation)
- No confidence interval or replication logic
- No multi-language comparative evaluation
- Improvement suggestions only cover 2 basic cases; this query requires deeper diagnosis

**Score**: 2/5

---

### 3. Actionability: 1/5
**For the specific user query**, the user would need to:

1. ✅ Can run code to get NDCG@10 and MRR@5 (skill provides this)
2. ✅ Can get naturalness and term consistency scores (skill provides Korean eval)
3. ❌ Cannot interpret why MRR@5 = 0.45 while nDCG@10 = 0.72 (skill doesn't explain)
4. ❌ Cannot diagnose the Korean term consistency drop (skill reports metric, no diagnostic)
5. ❌ Cannot determine retrieval vs. generation vs. Korean-specific (skill doesn't guide attribution)
6. ❌ Cannot run targeted experiments to isolate root cause (no ablation workflows)

**Example of what user would have to do on their own**:
"I guess I should check if Korean retrieval is bad? Maybe? Let me write my own script to test that."

**Score**: 1/5

---

## Concrete Improvement Recommendations for SKILL.md

### Recommendation 1: Add Diagnostic Decision Trees (HIGH PRIORITY)

**Location**: New section after "Improvement Suggestions Engine"

**Content**: 
```
## Diagnostic Workflows for Complex Scenarios

### Scenario A: MRR < threshold but nDCG > threshold

Pattern: Relevant documents exist but ranked 6-10 instead of 1-5

Decision tree:
1. Check rank distribution: Count [1-5] vs [6-10] relevant documents
2. If >50% are in [6-10]:
   a. Is retriever producing low confidence scores in top-5?
      → Test: Log score(top-5_relevant_doc) vs score(top-5_irrelevant_doc)
      → Fix: Re-embed with stronger model or fine-tune on in-domain data
   b. Is re-ranker degrading top-5 ordering?
      → Test: Disable re-ranker; re-run MRR
      → Fix: Retrain re-ranker or use different ranking model
   c. Is ground truth wrong?
      → Fix: Manually review 10 cases marked "relevant"; correct if needed
3. If <50% are in [6-10], something else is wrong (check "Overall retrieval debugging")

Expected outcome: MRR should improve to >0.5 after root cause is fixed
```

**Why**: User immediately knows what to check and in what order.

---

### Recommendation 2: Add Multilingual Comparative Evaluation (HIGH PRIORITY)

**Location**: Expand "Korean Language Evaluation" section

**Content**:
```
## Multilingual Evaluation: Comparing Language Performance

When the system supports multiple languages (English + Korean), 
evaluate retrieval and generation SEPARATELY per language to isolate language-specific issues.

### Step 1: Language-Specific Retrieval Metrics

```python
def eval_retrieval_by_language(test_suite, ground_truth, retriever) -> dict:
    """Evaluate retrieval separately for each language."""
    results = {}
    for lang in ['en', 'ko']:
        lang_queries = [tc for tc in test_suite if tc['language'] == lang]
        results[lang] = eval_retrieval(lang_queries, ground_truth, retriever)
    return results
```

After running:
- If precision@5_en = 0.7 but precision@5_ko = 0.5, retriever is language-biased
  - Diagnosis: Embedding model may be undertrained on Korean
  - Fix: Use multilingual embeddings (e.g., mE5-base) or fine-tune on Korean domain corpus
  
- If metrics are similar by language, retriever is not the bottleneck

### Step 2: Language-Specific Generation Metrics

```python
def eval_generation_by_language(qa_pairs_en, qa_pairs_ko, source_docs) -> dict:
    results = {}
    results['en'] = eval_generation_factuality(qa_pairs_en, source_docs)
    results['ko'] = eval_korean_quality(qa_pairs_ko)
    return results
```

Interpreting language-specific divergence:
- naturalness_ko > 4.0 but consistency_ko < 3.0 indicates:
  - LLM *generates fluent Korean* (naturalness high)
  - LLM *ignores or lacks domain terminology* (consistency low)
  - Fix: Add glossary to prompt, or fine-tune LLM on Korean neuroscience corpus

### Step 3: Root Cause Attribution

| Scenario | Retrieval | Generation | Primary Fix |
|----------|-----------|------------|-------------|
| precision@5_ko << precision@5_en, factuality_ko low | Language-specific | - | Re-embed or fine-tune retriever |
| precision@5_en ≈ precision@5_ko, but naturalness_ko > consistency_ko | - | Language-specific generation | Glossary enforcement in prompt |
| All metrics low by language | Both | Both | Start with retrieval (upstream fix) |
```

**Why**: User can now run retrieval and generation evals separately and correlate them to language to pinpoint the source of degradation.

---

### Recommendation 3: Add Ablation & Instrumentation Guide (MEDIUM PRIORITY)

**Location**: New section "Debugging Through Ablation"

**Content**:
```
## Ablation Workflows: Isolating Root Causes

When metrics suggest a problem, ablate components to isolate the source.

### Test 1: Retriever Quality (vs. Re-ranker, vs. Embedding)

Run these in sequence:

```python
# Baseline: Full pipeline
results_full = eval_retrieval(queries, ground_truth, pipeline.full_retriever)

# Without re-ranker (if exists)
results_no_rerank = eval_retrieval(queries, ground_truth, pipeline.dense_only)

# Without BM25 (if using hybrid)
results_no_bm25 = eval_retrieval(queries, ground_truth, pipeline.dense_only)
```

Interpretation:
- If mrr(full) << mrr(no_rerank), re-ranker is degrading precision@5
  - Fix: Check re-ranker training data or model quality
- If mrr(full) ≈ mrr(dense_only), re-ranker is not the issue
  - Fix: Look at dense retriever embedding quality

### Test 2: Ground Truth Quality

```python
def audit_ground_truth(ground_truth, retriever):
    """Check if ground truth is correct."""
    errors = []
    for query, relevant_ids in ground_truth.items():
        results = retriever.search(query, k=20)
        result_ids = [r['id'] for r in results]
        
        # Check: Are non-relevant docs actually non-relevant?
        for rank, rid in enumerate(result_ids[:5], 1):
            if rid not in relevant_ids:
                errors.append({
                    'query': query,
                    'rank': rank,
                    'doc_id': rid,
                    'note': 'Mark relevant if truly relevant; skip if false positive'
                })
    return errors
```

Run this when metrics are suspiciously low; it catches ground truth annotation errors.

### Test 3: Generation Quality Under Different Retrieved Context

```python
def eval_generation_given_retrieval_quality(queries, retriever, gen_model):
    """Check if generation quality improves with better retrieved context."""
    results = []
    for query in queries:
        # Scenario A: Use retrieved results as-is
        retrieved = retriever.search(query, k=5)
        answer_a = gen_model.generate(query, context=retrieved)
        
        # Scenario B: Use only the top-1 result
        answer_b = gen_model.generate(query, context=retrieved[:1])
        
        # Scenario C: Manually provide ground truth documents
        gt_docs = ground_truth[query]
        answer_c = gen_model.generate(query, context=gt_docs)
        
        results.append({
            'query': query,
            'quality_with_retrieved': eval_factuality(answer_a, retrieved),
            'quality_with_top1': eval_factuality(answer_b, retrieved[:1]),
            'quality_with_gt': eval_factuality(answer_c, gt_docs)
        })
    return results
```

If quality_with_gt >> quality_with_retrieved, generation is NOT the bottleneck; retrieval is.

**Why**: These ablations systematically eliminate potential root causes.

---

### Recommendation 4: Add Confidence & Variance Guidance (MEDIUM PRIORITY)

**Location**: Expand "Known Limitations" section

**Content**:
```
## Interpreting Score Confidence & Variance

### Confidence by Test Suite Size

| Test Suite Size | Metric | Confidence Interval | Interpretation |
|---|---|---|---|
| 30 queries | MRR = 0.45 | ±0.08 | Score could range [0.37, 0.53]; improvement of +0.05 is within noise |
| 30 queries | naturalness_ko = 4.2/5 | ±0.3 | Roughly 60% confidence; should spot-check 5-10 cases manually |
| 50 queries | MRR = 0.45 | ±0.06 | Tighter; +0.05 improvement is becoming meaningful |

### Spot-Check Protocol for Low-Confidence Metrics

When a score is in the uncertain range (e.g., 2-3 out of 5, or 0.4-0.6 for proportions):

1. Sample 5-10 cases uniformly across the test set
2. Manually evaluate using the same rubric as the LLM judge
3. Compute human-judge agreement with LLM scores
   - If agreement > 0.8: metric is reliable; trust the score
   - If agreement < 0.6: metric is too noisy; additional engineering needed

Example:
```python
def spot_check_consistency(qa_pairs_sample, judge_scores_sample):
    """Manual evaluation to verify LLM judge accuracy."""
    human_scores = []
    for qa in qa_pairs_sample:
        # Human manually rates Korean term consistency
        score = input(f"Term consistency for '{qa['answer_ko']}' [1-5]: ")
        human_scores.append(int(score))
    
    agreement = sum(1 for h, l in zip(human_scores, judge_scores_sample) if abs(h-l) <= 1) / len(human_scores)
    print(f"Human-LLM agreement: {agreement:.2%}")
    return agreement > 0.7  # Threshold for reliable metric
```

### Reporting Metrics with Confidence

Always report as:
- "Naturalness: 4.2 ± 0.3 (n=30 Korean queries, confidence=medium, spot-checked 7 cases)"

Instead of:
- "Naturalness: 4.2"

**Why**: Users understand the uncertainty and know when to trust the result or re-run.

---

### Recommendation 5: Add Multi-Metric Reconciliation Rules (MEDIUM PRIORITY)

**Location**: Expand "Improvement Suggestions Engine"

**Content**:
```python
def generate_recommendations_advanced(results: dict) -> list:
    """Diagnostic recommendations based on metric patterns."""
    recs = []

    # Pattern A: High nDCG but low MRR (your exact case)
    if results['retrieval']['ndcg_at_10'] > 0.7 and results['retrieval']['mrr'] < 0.5:
        recs.append({
            'area': 'retrieval_ranking',
            'severity': 'high',
            'pattern': 'relevant_docs_ranked_low',
            'hypothesis': 'Relevant documents are retrieved but ranked 6-10 instead of 1-5',
            'debug_steps': [
                '1. Analyze rank distribution: count relevant docs in [1-5] vs [6-10]',
                '2. If >50% in [6-10]: Check retriever confidence scores in top-5',
                '3. Disable re-ranker (if exists) and re-run MRR',
                '4. Verify ground truth is correct (manual spot-check)',
            ],
            'fixes_by_likelihood': [
                '(MOST LIKELY) Re-embed with stronger model (e.g., bge-large-en-v1.5)',
                '(2nd) Fine-tune retriever on in-domain queries',
                '(3rd) Disable broken re-ranker',
                '(LEAST LIKELY) Ground truth annotation errors',
            ]
        })

    # Pattern B: Naturalness high but consistency low (your Korean case)
    if (results.get('korean_metrics', {}).get('naturalness', 0) > 4.0 and
        results.get('korean_metrics', {}).get('consistency', 0) < 3.0):
        recs.append({
            'area': 'korean_generation',
            'severity': 'medium',
            'pattern': 'fluent_korean_but_wrong_terms',
            'hypothesis': 'LLM generates fluent Korean but ignores or lacks domain terminology',
            'debug_steps': [
                '1. Check TERM_GLOSSARY: Are Korean neuroscience terms included?',
                '2. Add glossary enforcement to LLM prompt',
                '3. Re-run eval_korean_quality() on 10 test cases',
                '4. If consistency still <3: Fine-tune LLM on Korean domain corpus',
            ],
            'fixes_by_likelihood': [
                '(MOST LIKELY) Update TERM_GLOSSARY with missing Korean terms',
                '(2nd) Add glossary enforcement to generation prompt',
                '(3rd) Fine-tune LLM on Korean neuroscience training data',
            ]
        })

    # Pattern C: All metrics low by language
    if (results['retrieval']['precision_at_5_ko'] < 0.5 and
        results['generation']['factuality_ko'] < 3.0):
        recs.append({
            'area': 'korean_overall',
            'severity': 'critical',
            'pattern': 'language_wide_degradation',
            'hypothesis': 'Korean language support is poorly calibrated; fix retrieval first',
            'debug_steps': [
                '1. Check: Is embedding model multilingual? (e.g., mE5-base)',
                '2. Compare precision@5_en vs precision@5_ko; if diff > 0.15, re-embed',
                '3. After fixing retrieval, re-run generation eval',
            ]
        })

    return recs
```

**Why**: This transforms generic suggestions into pattern-specific, prioritized diagnostics.

---

## Summary Table: Improvements Needed

| Gap | Severity | Effort | Impact |
|-----|----------|--------|--------|
| **Decision trees for metric divergence** | 🔴 HIGH | Medium | Users can diagnose MRR/nDCG patterns immediately |
| **Multilingual comparative evaluation** | 🔴 HIGH | Medium | Users can isolate language-specific problems |
| **Ablation workflows** | 🟡 MEDIUM | Medium | Users can systematically eliminate root causes |
| **Confidence & variance guidance** | 🟡 MEDIUM | Low | Users know when to trust scores and when to re-check |
| **Multi-metric reconciliation rules** | 🟡 MEDIUM | Low | Recommendations become pattern-specific instead of generic |

---

## Conclusion

**Current state**: SKILL.md is an **excellent metric computation library** with solid code, but a **poor diagnostic guide** for the realistic troubleshooting scenarios that RAG system builders encounter.

**For this eval prompt specifically**:
- ✅ User can compute all reported metrics (NDCG, MRR, naturalness, consistency)
- ❌ User cannot diagnose why MRR < threshold while nDCG > threshold
- ❌ User cannot determine if the Korean consistency issue is retrieval or generation
- ❌ User cannot design experiments to isolate root causes

**Recommendation**: Expand SKILL.md with Sections 1-5 above (prioritize 1 & 2), then the skill will guide realistic debugging workflows instead of just reporting numbers.

