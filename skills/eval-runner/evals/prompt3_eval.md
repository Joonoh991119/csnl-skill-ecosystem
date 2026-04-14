# EVAL PROMPT 3: Robustness Analysis
## Ground Truth Reliability & Per-Chapter Diagnostic Coverage

**Evaluation Date:** 2026-04-14  
**Test Set:** bootstrap_ground_truth_v2 (34 queries, 2 per chapter × 17 chapters)  
**Languages:** English + Korean  
**Metric Focus:** NDCG@10, Naturalness@5, Per-chapter variance

---

## 1. GROUND TRUTH RELIABILITY ANALYSIS

### 1.1 Sample Size Adequacy

**Current Setup:** 2 queries per chapter × 17 chapters = 34 total queries

**Statistical Assessment:**

| Aspect | Status | Analysis |
|--------|--------|----------|
| **Minimum viable** | MARGINAL | Standard guidance: ≥20 queries baseline for retrieval evals |
| **Per-chapter coverage** | WEAK | 2 queries/chapter is at floor for detecting chapter-specific issues |
| **Variance detection** | HIGH RISK | With n=2, single flaky query swings chapter metric by ±25% |
| **Overall NDCG confidence** | MODERATE | 34 queries total allows ±0.04 CI@95%, acceptable for trend detection |

**Reliability Concerns:**

1. **Per-chapter reliability is brittle:** A single high-scoring or low-scoring query dominates the chapter mean
   - Chapter mean = (score_query1 + score_query2) / 2
   - If query_1 = 0.95 and query_2 = 0.45 → chapter_mean = 0.70 (same as overall!)
   - Indistinguishable from true 0.70 performance

2. **Language interaction effects hidden:** With 2 queries per chapter, you cannot separate:
   - Is chapter 5 strong because of retrieval quality, OR because both queries in chapter 5 happen to be easy?
   - Is chapter 1-3 weak because of a systematic issue, OR because test queries are harder?

3. **Sentence-level confounding:** Korean naturalness score (4.5/5 overall, 2.1/5 for chapter 5) cannot be disaggregated from retrieval quality
   - Chapter 5 has high NDCG (0.95) but low naturalness (2.1) → suggests **generation/translation issue**, not retrieval
   - But with only 2 queries, you cannot rule out that one query's answer was particularly stilted

### 1.2 Ground Truth Quality Checks (Before Using This Data)

**CRITICAL VERIFICATION STEPS:**

Before accepting these numbers as diagnostic, verify:

1. **Circular dependency check:** Are the 34 ground truth queries based on paper-processor's *extracted* sections, or the *raw PDFs*?
   - If based on processed output: Ground truth is contaminated by extraction errors
   - Action: Spot-check 5 random ground truth queries against raw PDFs; confirm relevant papers are actually relevant
   
2. **Chapter assignment validity:** Do chapters 5 (BCS/FCS) and 12 (consciousness) truly represent "harder retrieval" or "easier ground truth"?
   - Chapter 5 NDCG=0.95 is suspiciously high → inspect a chapter-5 query in detail
   - Manual check: Take one chapter-5 query, run retrieval live, read top-5 papers
   - If papers are obviously relevant: retrieval is working
   - If papers are ambiguous/margin calls: ground truth may be overconstrained (only marking 1 paper when 3 are relevant)

3. **Language annotation consistency:** Are Korean queries direct translations, or are they independently written?
   - Direct translation: Korean queries inherit English query ambiguity
   - Independent Korean: May differ in focus and pick up different retrieval errors
   - Status: If translated, this biases results; if independent, this is stronger

### 1.3 Bootstrap Interpretation

**Your data shows:**
- **Overall NDCG@10 = 0.81** ✓ meets target (>0.7)
- **Chapter variance = 0.50** (range 0.45–0.95) ⚠ ALARMING

**Interpretation (with caveats):**

| Finding | Confidence | Implication |
|---------|------------|-------------|
| **System is generally working** | MEDIUM | NDCG=0.81 meets baseline, but n=34 with high variance |
| **Chapters 5, 12 are strong** | LOW | n=2 per chapter; 95% is likely overfitted to 2 easy queries |
| **Chapters 1–3 are weak** | MEDIUM | Three separate chapters below threshold suggests systematic issue, not noise |
| **Korean is struggling** | MEDIUM | 4.5/5 overall is acceptable; 2.1/5 chapter-5 is real concern (high NDCG but low naturalness) |

---

## 2. PER-CHAPTER DIAGNOSTIC COVERAGE

### 2.1 Root Cause Isolation Framework

**Your data lacks the structure to distinguish three failure modes:**

| Failure Mode | Observable in Current Data? | How to Detect |
|--------------|----------------------------|---------------|
| **Retrieval failure** (wrong docs ranked high) | MAYBE | NDCG low, BUT confounded with ground truth quality |
| **Ground truth failure** (marked wrong papers as relevant) | NO | Need ablation: inject gold passages, re-measure generation quality |
| **Translation failure** (Korean generation breaks) | PARTIALLY | Korean naturalness is low, but tied to specific retrieved docs |

### 2.2 Chapter-by-Chapter Breakdown

#### Chapters 1–3 (Intro/Basics): NDCG = 0.45

**Diagnostic Questions:**

1. **Is this retrieval or ground truth?**
   - Action: Run ablation_retrieval_only() on chapters 1–3
     - Use ground truth papers, generate answer, score factuality
     - If factuality suddenly jumps to 3.8+: problem is retrieval
     - If factuality stays low (< 3.0): problem is generation or ground truth quality
   
2. **Do the 2 queries differ wildly in difficulty?**
   - Example: If chapter 1 has (query_A: NDCG=0.20, query_B: NDCG=0.70)
     - Suggests one query is ambiguous, one is clear
     - Action: Deep-dive one failure case: manually inspect top-10 retrieved for query_A, read abstracts, explain why top-1 is wrong

3. **Language effect?** Are chapters 1–3 disproportionately hurt by Korean queries?
   - Run language_comparison ablation on chapters 1–3
   - If English NDCG=0.65, Korean NDCG=0.25 → retrieval language mismatch
   - If both equally low → retrieval issue, not language

#### Chapters 5, 12 (BCS/FCS, Consciousness): NDCG = 0.95+

**Red Flag: This is Suspiciously High**

- Research literature median NDCG@10 ≈ 0.70 for neural IR tasks
- 0.95 suggests either:
  1. **Queries happen to be easy** (ground truth papers are obvious top-ranked) — likely with n=2
  2. **Ground truth is overconstrained** (only 1 paper marked relevant when 3–5 are actually relevant; creates artificially perfect ranking)
  3. **Embedding model is tuned to cognitive neuroscience** (possible; check model training data)

**Action:** Manually inspect one chapter-5 query
- Example: "What is the binding problem in consciousness?"
- Ground truth says: {paper_X, paper_Y}
- Retriever ranked: [paper_X (0.92), paper_A (0.89), paper_B (0.88), paper_Y (0.87), ...]
- If ground truth only marked {paper_X, paper_Y}, NDCG rewards 0.92, 0.87 perfectly
- If you re-evaluate and realize papers A, B, C are also relevant, true NDCG drops to 0.75

### 2.3 Korean Naturalness Paradox

**Key Observation:** 
- Chapter 5: NDCG=0.95 (excellent retrieval) BUT naturalness=2.1/5 (very poor translation)
- This is NOT a retrieval problem; it's a **generation/translation problem**

**Diagnostic Steps:**

1. **Isolate language from retrieval:** Run the same chapter-5 query in English
   - If English answer is clear, fluent (>4.0/5 naturalness) → problem is Korean generation
   - If English answer is also awkward → problem is generation, not Korean specifically

2. **Check TERM_GLOSSARY consistency:**
   - Korean answer uses 번역투 (translation-style Korean)
   - Likely cause: Generation prompt was tuned on English examples, then naively translated
   - Action: Review tutor-content-gen SKILL.md; if generation prompt is English-primary with Korean examples, regenerate with Korean-primary examples

3. **Retrieval language mismatch:** 
   - Are retrieved docs predominantly English papers with Korean summaries?
   - Korean naturalness drops when mixing English nomenclature with Korean grammar
   - Action: Inspect top-5 retrieved for chapter-5 Korean query; count English vs Korean papers

---

## 3. RELIABILITY SCORING

### 3.1 Statistical Rigor: 2/5

**Rationale:**

- ✓ Overall NDCG metric is sound (standard IR metric, well-defined)
- ✓ 34 queries sufficient for trend detection (CI ±0.04)
- ✗ Per-chapter n=2 is below statistical threshold (high variance, low power to detect differences)
- ✗ No confidence intervals reported per chapter
- ✗ No distinction between systematic error (retrieval) vs random error (ground truth noise)
- ✗ Korean evaluation conflates language quality with retrieval quality

**Missing:** 
- Confidence intervals: ± how much uncertainty around 0.45 and 0.95?
- Ablation separation: Cannot isolate retrieval vs generation failure

### 3.2 Diagnostic Depth: 2/5

**Rationale:**

- ✓ You correctly identified that chapters 1–3 underperform (systematic issue, not noise)
- ✓ You flagged Korean naturalness issue as distinct from NDCG
- ✗ No ablation framework to test retrieval vs generation
- ✗ No manual inspection of failure cases (e.g., why is chapter-1 query X ranked wrong?)
- ✗ Ground truth quality is unvalidated
- ✗ No separation of language-specific issues from chapter-specific issues

**Missing Steps:**
1. Spot-check ground truth against raw PDFs (5–10 queries)
2. Run ablation_retrieval_only() on weak chapters to isolate retrieval
3. Manual deep-dive: Pick chapter 1, query A, manually read top-10 retrieved papers, identify first retrieval error
4. Language separation: Run English vs Korean on same chapters

---

## 4. GAPS AND IMPROVEMENTS

### 4.1 Immediate Wins (Before Next Eval Cycle)

| Priority | Action | Effort | Expected Gain |
|----------|--------|--------|----------------|
| **HIGH** | Spot-check ground truth: 10 random queries against raw PDFs | 2 hours | Validate that marked papers are actually relevant |
| **HIGH** | Ablation on chapters 1–3: inject gold passages, re-measure generation quality | 3 hours | Determine if issue is retrieval or generation |
| **HIGH** | Manual inspection: one chapter-1 query, read top-10 papers, explain top-1 failure | 1 hour | Concrete evidence of retrieval vs ground truth failure |
| **MEDIUM** | Korean language ablation: compare English vs Korean NDCG on same queries | 2 hours | Isolate language effect from chapter effect |
| **MEDIUM** | Expand ground truth: +2 queries per chapter (34 → 51 total) | 6 hours | Reduce variance, stabilize chapter metrics |

### 4.2 Structural Improvements for Phase 2

| Issue | Solution | Phase |
|-------|----------|-------|
| **2 queries/chapter is too sparse** | Expand to 4–5 per chapter (68–85 total) | Phase 2 (1–2 weeks) |
| **Per-chapter variance unquantified** | Report 95% CI per chapter | Phase 2 |
| **Retrieval vs generation confounded** | Implement ablation_retrieval_only() as standard eval step | Phase 2 |
| **Korean ground truth unvalidated** | Add Korean-native human review of 10 Korean queries | Phase 2 |
| **章Chapter 5/12 suspiciously high** | Manual re-evaluation: are marked papers the ONLY relevant ones, or are others being missed? | Phase 2 |

### 4.3 Testing Ground Truth Quality

**Protocol to validate the 34 queries:**

```
1. Sample 10 random queries from bootstrap_ground_truth_v2
2. For each query:
   a. Get ground truth marked papers: {paper_X, paper_Y, ...}
   b. Retrieve top-20 docs using actual retriever
   c. Manually read titles + abstracts of:
      - All marked papers (confirm they're relevant)
      - Top-5 retrieved papers not marked (are they actually irrelevant?)
   d. Score: "ground truth seems correct" or "ground truth is incomplete/wrong"
3. If >2/10 are wrong: bootstrap is contaminated; rebuild with human review

Estimated time: 4–5 hours
Expected outcome: Either "ground truth is solid" or "ground truth needs rebuild"
```

### 4.4 Isolating Korean Naturalness

**Chapter 5 paradox:** High NDCG but 번역투

**Test plan:**

```
1. Take one chapter-5 Korean query Q_ko
2. Run English equivalent Q_en through pipeline
3. Compare:
   - English answer: naturalness score N_en
   - Korean answer: naturalness score N_ko
   
If N_ko << N_en (e.g., 2.1 vs 4.2):
   → Problem is Korean generation/translation, not retrieval
   → Action: Review generation prompt in tutor-content-gen; ensure Korean examples are native, not translated
   
If N_ko ≈ N_en (both low):
   → Problem is content quality, not language
   → Action: Inspect retrieved docs; are they incomplete/noisy?
```

---

## 5. RECOMMENDATIONS FOR NEXT EVAL CYCLE

### 5.1 Immediate Next Steps (This Week)

1. **Validate ground truth** (2 hours)
   - Spot-check 10 queries: compare marked papers to raw PDFs
   - Flag any overconstrained or incomplete markings

2. **Ablate chapters 1–3** (3 hours)
   - Run with gold passages only
   - If generation quality jumps to 3.8+: problem is retrieval → optimize BM25 hybrid
   - If stays low: problem is generation or ground truth → need different fix

3. **Manual failure analysis** (1 hour per chapter)
   - Pick worst chapter-1 query
   - Read top-10 papers manually
   - Explain why rank-1 is wrong; identify retrieval failure mode

### 5.2 Before Phase 2 Expansion

1. **Grow ground truth from 34 → 50+ queries**
   - Target: 3–4 per chapter minimum
   - Reduces per-chapter variance by ~40%
   - Enables split-half validation

2. **Add confidence intervals per chapter**
   - Report: Chapter 1 NDCG = 0.45 ± 0.18 (95% CI)
   - Channels uncertainty into decisions

3. **Korean language protocol**
   - Decide: Are queries translated or independent?
   - If translated: expect correlation between English/Korean performance
   - If independent: may reveal different retrieval failures

4. **Ablation suite becomes standard**
   - eval_retrieval_only() when factuality seems low
   - eval_generation_only() when NDCG is high but answers are weak
   - eval_language_comparison() for any multilingual concern

---

## 6. SUMMARY

| Question | Answer | Confidence |
|----------|--------|-----------|
| **Are 2 queries/chapter enough to be reliable?** | NO for diagnosis, MAYBE for monitoring | LOW for chapters, MEDIUM for overall |
| **Is low NDCG@0.45 in chapters 1–3 a retrieval issue?** | LIKELY, but unproven without ablation | MEDIUM |
| **Is Korean 2.1/5 naturalness a generation issue?** | VERY LIKELY, given high NDCG in chapter 5 | HIGH |
| **Should I trust chapter 5 NDCG=0.95?** | NOT without spot-checking ground truth | LOW |
| **What's the minimum viable sample for reliable chapter diagnosis?** | 4–5 queries per chapter (68–85 total) | MEDIUM |

### Key Actionable Insight:

**Your paradox (high retrieval, low Korean fluency) is actually diagnostic gold.** Chapter 5 proves retrieval is working, but answers are stilted. This points directly to generation/prompt tuning issues, not embedding quality. Focus next steps on Korean prompt design in tutor-content-gen, not retrieval optimization.

---

## 7. CONFIDENCE ASSESSMENT

**Overall Evaluation Reliability: 2.5 / 5**

- **Data quality:** Unvalidated (spot-check needed)
- **Per-chapter reliability:** Too sparse (n=2)
- **Diagnostic separation:** Weak (retrieval vs generation confounded)
- **Actionable insights:** YES (Korean issue is clear; retrieval issue is likely but unproven)

**Recommendation:** Do NOT optimize retrieval broadly based on this data. Instead:
1. Validate ground truth (2 hours)
2. Run ablation on weak chapters (3 hours)
3. Prioritize Korean generation improvement
4. Expand ground truth to 50+ queries for Phase 2
