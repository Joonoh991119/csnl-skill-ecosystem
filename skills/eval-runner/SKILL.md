---
name: eval-runner
description: >
  Automated evaluation and quality assessment pipeline for RAG tutoring systems.
  Runs test suites against skills and pipeline components, measures retrieval quality
  (precision@k, recall, MRR), generation quality (factuality, relevance, completeness),
  and tutoring effectiveness. Generates HTML comparison reports and suggests improvements.
  MANDATORY TRIGGERS: Any request involving testing, evaluating, benchmarking, quality
  assessment, regression testing, comparing versions, measuring accuracy, "is this working
  well", "how good is the retrieval", "test the pipeline", "check quality", or any
  performance measurement of the RAG tutor system. Also trigger when user wants to
  compare before/after changes, run A/B tests, or diagnose why answers are poor.
---

# Evaluation Runner

You measure and improve the quality of the CSNL RAG tutor system through systematic
evaluation. Without measurement, improvement is guesswork.

## Why Evals Matter for a Tutor

A tutor that gives wrong answers is worse than no tutor. A tutor that retrieves irrelevant
papers wastes the student's time. Evals catch these problems before students encounter them.

## Evaluation Dimensions

### 1. Retrieval Quality (Does the pipeline find the right documents?)

| Metric | Formula | Target |
|---|---|---|
| Precision@5 | relevant_in_top5 / 5 | > 0.6 |
| Recall@10 | relevant_in_top10 / total_relevant | > 0.8 |
| MRR | 1/rank_of_first_relevant | > 0.5 |
| nDCG@10 | normalized discounted cumulative gain | > 0.7 |

```python
def eval_retrieval(test_queries: list, ground_truth: dict, retriever) -> dict:
    """Evaluate retrieval quality on a test set."""
    metrics = {'precision_at_5': [], 'recall_at_10': [], 'mrr': [], 'ndcg_at_10': []}

    for query_item in test_queries:
        query = query_item['query']
        relevant_ids = set(ground_truth[query])

        results = retriever.search(query, k=10)
        result_ids = [r['id'] for r in results]

        # Precision@5
        top5_relevant = len(set(result_ids[:5]) & relevant_ids)
        metrics['precision_at_5'].append(top5_relevant / 5)

        # Recall@10
        top10_relevant = len(set(result_ids[:10]) & relevant_ids)
        metrics['recall_at_10'].append(top10_relevant / len(relevant_ids) if relevant_ids else 0)

        # MRR
        for rank, rid in enumerate(result_ids, 1):
            if rid in relevant_ids:
                metrics['mrr'].append(1.0 / rank)
                break
        else:
            metrics['mrr'].append(0.0)

    return {k: sum(v)/len(v) for k, v in metrics.items()}
```

### 2. Generation Quality (Are the tutor's answers good?)

| Metric | Method | Target |
|---|---|---|
| Factuality | LLM-as-judge vs source docs | > 0.9 |
| Relevance | Query-answer cosine similarity | > 0.7 |
| Completeness | Key points coverage check | > 0.8 |
| Citation accuracy | Claims traceable to sources | > 0.85 |
| Korean fluency | LLM-as-judge (Korean native) | > 0.8 |

```python
def eval_generation_factuality(qa_pairs: list, source_docs: dict) -> dict:
    """Use LLM-as-judge to evaluate factual accuracy."""
    judge_prompt = """You are evaluating a tutor's answer for factual accuracy.

Source documents:
{sources}

Question: {question}
Tutor's answer: {answer}

Rate factuality on 1-5 scale:
5: All claims are supported by source documents
4: Minor unsupported details but core is accurate
3: Mix of supported and unsupported claims
2: Major unsupported claims
1: Contradicts source documents

Score: """

    scores = []
    for qa in qa_pairs:
        sources = source_docs.get(qa['query'], '')
        prompt = judge_prompt.format(
            sources=sources, question=qa['query'], answer=qa['answer']
        )
        # Call local model (Qwen2.5-32B via Ollama/MLX)
        score = call_local_llm(prompt)
        scores.append(parse_score(score))

    return {
        'mean_factuality': sum(scores) / len(scores),
        'scores': scores,
        'below_threshold': sum(1 for s in scores if s < 3)
    }
```

### 3. Tutoring Effectiveness (Does the student learn?)

| Metric | Method | Target |
|---|---|---|
| Explanation clarity | Readability score + LLM judge | > 0.7 |
| Concept coverage | Key concepts mentioned vs expected | > 0.8 |
| Difficulty calibration | Level match (undergrad/grad/PhD) | > 0.75 |
| Follow-up quality | Can answer follow-up questions | > 0.7 |

## Test Suite Management

### Creating Test Cases

```python
# test_suite.json
{
  "suite_name": "vwm_retrieval_v1",
  "created": "2026-04-14",
  "test_cases": [
    {
      "id": "vwm_001",
      "query": "What is the capacity limit of visual working memory?",
      "expected_topics": ["Cowan 2001", "slot model", "K estimate", "set size"],
      "relevant_paper_ids": ["cowan2001", "luck_vogel1997", "zhang_luck2008"],
      "difficulty": "undergraduate",
      "language": "en"
    },
    {
      "id": "vwm_002",
      "query": "시각적 작업 기억의 용량 한계는 무엇인가?",
      "expected_topics": ["Cowan 2001", "슬롯 모델", "K 추정", "세트 크기"],
      "relevant_paper_ids": ["cowan2001", "luck_vogel1997", "zhang_luck2008"],
      "difficulty": "undergraduate",
      "language": "ko"
    }
  ]
}
```

### Running a Full Evaluation

```python
def run_full_eval(test_suite_path: str, pipeline, output_dir: str) -> dict:
    """Run complete evaluation across all dimensions."""
    import json
    from datetime import datetime

    with open(test_suite_path) as f:
        suite = json.load(f)

    results = {
        'suite_name': suite['suite_name'],
        'timestamp': datetime.now().isoformat(),
        'retrieval': {},
        'generation': {},
        'tutoring': {},
        'summary': {}
    }

    # 1. Retrieval eval
    results['retrieval'] = eval_retrieval(suite['test_cases'], ground_truth, pipeline.retriever)

    # 2. Generation eval
    qa_pairs = []
    for tc in suite['test_cases']:
        answer = pipeline.generate(tc['query'])
        qa_pairs.append({'query': tc['query'], 'answer': answer, 'expected': tc['expected_topics']})
    results['generation'] = eval_generation_factuality(qa_pairs, source_docs)

    # 3. Summary
    results['summary'] = {
        'overall_score': compute_overall(results),
        'pass': results['retrieval']['precision_at_5'] > 0.6 and results['generation']['mean_factuality'] > 3.5,
        'recommendations': generate_recommendations(results)
    }

    # Save results
    output_path = f"{output_dir}/eval_{suite['suite_name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results
```

## HTML Report Generation

Generate a visual report comparing runs:

```python
def generate_html_report(current: dict, previous: dict = None, output_path: str = "eval_report.html"):
    """Generate visual HTML comparison report."""
    # Includes:
    # - Score dashboard (current vs previous)
    # - Per-query breakdown table
    # - Failure analysis (worst-performing queries)
    # - Improvement suggestions
    # - Trend charts if multiple historical runs available
```

## Improvement Suggestions Engine

```python
def generate_recommendations(results: dict) -> list:
    """Analyze eval results and suggest specific improvements."""
    recs = []

    if results['retrieval']['precision_at_5'] < 0.6:
        recs.append({
            'area': 'retrieval',
            'severity': 'high',
            'suggestion': 'Retrieval precision is low. Consider: (1) Re-embedding with a better model, '
                         '(2) Adding BM25 hybrid search, (3) Improving chunking to preserve context.'
        })

    if results['generation']['mean_factuality'] < 3.5:
        recs.append({
            'area': 'generation',
            'severity': 'high',
            'suggestion': 'Factuality is below threshold. Consider: (1) Increasing retrieved context, '
                         '(2) Adding citation enforcement in prompt, (3) Using chain-of-thought verification.'
        })

    # ... more diagnostic rules

    return recs
```

## Bootstrap: Creating the Ground Truth Dataset

Before evals can run, you need ground truth. This is manual work that cannot be skipped.

### Minimum viable test suite: 30 queries

```python
# bootstrap_ground_truth.py
# PhD student fills this in manually — no shortcuts here

GROUND_TRUTH = {
    "queries": [
        {
            "id": "gt_001",
            "query_en": "What is the capacity limit of visual working memory?",
            "query_ko": "시각적 작업 기억의 용량 한계는?",
            "relevant_papers": ["cowan2001", "luck_vogel1997", "zhang_luck2008"],
            "relevant_sections": ["results", "discussion"],
            "difficulty": "undergraduate",
            "domain": "visual_working_memory"
        },
        # ... 29 more entries (aim for 30 total, covering 5+ domains)
    ]
}

# Domains to cover (minimum 5 queries each):
# - visual working memory
# - perceptual decision making
# - attention
# - neural coding / efficient coding
# - fMRI methodology
# - psychophysics methods
```

### How to build this (realistic time: 2-3 days)
1. Export Zotero collection topics → list 30 testable questions
2. For each question, manually identify 3-5 relevant papers from Zotero
3. Mark which section of each paper contains the answer
4. Save as JSON → this becomes eval-runner's ground truth

**Why 30?** Fewer than 20 gives unreliable metrics (high variance). More than 50 is diminishing returns for initial bootstrap. 30 is the sweet spot.

## Optimization Workflow (Human-in-the-Loop, NOT Automated)

The eval → improve loop is manual at first. Don't pretend otherwise.

```
Step 1: Run eval-runner → get precision@5, factuality scores
Step 2: Human reads failure cases ("query X returned irrelevant docs")
Step 3: Human diagnoses root cause:
        - Bad chunking? → Adjust chunk_size/overlap in rag-pipeline
        - Wrong embedding? → Try different model
        - Missing papers? → Add to Zotero → re-index
Step 4: Apply fix
Step 5: Re-run eval-runner → measure improvement
Step 6: If improved, commit change. If not, revert.
```

### Future: DSPy Integration (Phase 2+, NOT included in this skill)

When the manual loop is stable and you have 50+ test queries with ground truth,
you can wrap the evaluation metrics as DSPy assertions:

```python
# FUTURE WORK — not implemented yet
# This requires a separate bridge layer between eval-runner metrics and DSPy Signatures
# See: https://dspy.ai/ for GEPA/MIPROv2 optimizer documentation
# The bridge would:
#   1. Convert SKILL.md prompt sections → DSPy Signature
#   2. Feed eval metrics as DSPy assertions
#   3. Use GEPA to generate prompt variants
#   4. Validate new SKILL.md syntax before deployment
# This is a Phase 2 goal, not a Phase 0-1 deliverable.
```

## Korean Language Evaluation

The tutor generates bilingual content. Korean output needs dedicated evaluation.

```python
def eval_korean_quality(qa_pairs_ko: list) -> dict:
    """Evaluate Korean content quality using LLM-as-judge."""
    judge_prompt = """다음 한국어 튜터링 답변의 품질을 평가하세요.

질문: {question}
답변: {answer}

평가 기준 (각 1-5점):
1. 한국어 자연스러움: 번역투가 아닌 자연스러운 한국어인가?
2. 전문 용어 정확성: 신경과학 용어가 정확하게 사용되었는가?
3. 영한 용어 일관성: TERM_GLOSSARY와 일치하는가?
4. 교육적 명확성: 해당 난이도 수준 학생이 이해할 수 있는가?

각 기준별 점수와 근거를 제시하세요."""

    scores = {'naturalness': [], 'terminology': [], 'consistency': [], 'clarity': []}
    for qa in qa_pairs_ko:
        prompt = judge_prompt.format(question=qa['query_ko'], answer=qa['answer_ko'])
        result = call_local_llm(prompt)  # Qwen2.5-32B supports Korean
        parsed = parse_korean_scores(result)
        for k in scores:
            scores[k].append(parsed.get(k, 0))

    return {k: sum(v)/len(v) for k, v in scores.items()}
```

### Korean-Specific Checks
- **번역투 탐지**: Flag sentences with Japanese-style passive constructions (되어지다, 이루어지다 overuse)
- **용어 일관성**: Cross-check against TERM_GLOSSARY from tutor-content-gen
- **혼용 비율**: Measure Korean vs English ratio in answers (target: >70% Korean for undergrad)

## Scheduled Evaluation (via schedule skill)

Set up on-demand evals first, then automate:
```
Phase 0-1: Run manually after each pipeline change
Phase 2+:  Schedule daily at 02:00 AM via schedule skill
           Output: JSON results → compare with previous run
           Alert: Slack notification if any metric drops > 10%
```

## Integration Points

- **rag-pipeline**: Primary evaluation target (retrieval quality)
- **tutor-content-gen**: Evaluate generated content quality (factuality, difficulty calibration)
- **paper-processor**: Ground truth quality depends on extraction quality
- **Slack MCP**: Alert on quality degradation (Phase 2+)
- **Notion MCP**: Store eval results for longitudinal tracking

## Known Limitations (Honest Assessment)

1. **LLM-as-judge is noisy**: Factuality scores from local Qwen2.5 have ~0.7 agreement with human judgment. Always spot-check.
2. **Ground truth is static**: As new papers are added, ground truth queries become stale. Re-review quarterly.
3. **Circular dependency**: If paper-processor extracts claims wrong, ground truth is contaminated. Always verify ground truth against raw PDFs, not processed output.
4. **Small test suites overfit**: With 30 queries, one flaky query swings precision@5 by 3%. Report confidence intervals.


## Diagnostic Frameworks for Metric Divergence

When individual metrics conflict, use this decision tree to isolate the root cause.

### Metric Divergence Patterns

**Pattern 1: High nDCG but Low MRR**
- Symptom: nDCG@10 > 0.7, MRR < 0.5
- Diagnosis: Relevant documents are ranked 6-10, not in top 5
- Root cause: Query ambiguity or multi-faceted relevance
- Fix: (1) Re-rank top-5 with diversity model, (2) Check if ground truth is overconstrained (mark multiple docs relevant), (3) Add query clarification step to retriever

**Pattern 2: Low nDCG but High MRR**
- Symptom: nDCG@10 < 0.6, MRR > 0.7
- Diagnosis: Top-1 result is correct but rest irrelevant (ignoring rank positions 2-10)
- Root cause: Query has single dominant answer; retriever lacks diversity
- Fix: (1) Ensemble with BM25 to surface alternative angles, (2) Apply diversity penalty, (3) Verify ground truth includes related documents, not just one answer

**Pattern 3: Both nDCG and MRR Low**
- Symptom: nDCG < 0.6 AND MRR < 0.5
- Diagnosis: Fundamental embedding/retrieval failure
- Root cause: Embedding model mismatch, chunking destroys context, or query reformulation needed
- Fix: (1) Swap embedding model, (2) Increase chunk overlap, (3) Try query expansion with LLM

```python
def diagnose_metric_divergence(results: dict) -> dict:
    """Decision tree for metric conflicts."""
    ndcg = results.get('ndcg_at_10', 0)
    mrr = results.get('mrr', 0)
    
    diagnosis = {
        'pattern': None,
        'root_cause': None,
        'fixes': []
    }
    
    if ndcg > 0.7 and mrr < 0.5:
        diagnosis['pattern'] = 'high_ndcg_low_mrr'
        diagnosis['root_cause'] = 'relevant_docs_ranked_6to10'
        diagnosis['fixes'] = [
            'apply_diversity_reranking',
            'check_ground_truth_overconstrained',
            'add_query_clarification'
        ]
    elif ndcg < 0.6 and mrr > 0.7:
        diagnosis['pattern'] = 'low_ndcg_high_mrr'
        diagnosis['root_cause'] = 'single_answer_lack_diversity'
        diagnosis['fixes'] = [
            'ensemble_bm25',
            'apply_diversity_penalty',
            'verify_gt_includes_alternates'
        ]
    elif ndcg < 0.6 and mrr < 0.5:
        diagnosis['pattern'] = 'both_low'
        diagnosis['root_cause'] = 'fundamental_retrieval_failure'
        diagnosis['fixes'] = [
            'swap_embedding_model',
            'increase_chunk_overlap',
            'try_query_expansion'
        ]
    
    return diagnosis
```

## Ablation Workflow: Isolating Failure Points

Use ablation to pinpoint whether failures stem from retrieval, generation, or language issues.

### Step 1: Test Retrieval Alone (Ground Truth Injection)

Replace the actual retriever with ground truth gold passages to isolate generation quality:

```python
def ablation_retrieval_only(test_cases: list, ground_truth_passages: dict, 
                            generator, output_file: str = 'ablation_retrieval.json'):
    """Inject ground truth documents and measure generation quality in isolation."""
    results = {'test_cases': []}
    
    for tc in test_cases:
        query = tc['query']
        gold_passages = ground_truth_passages[query]
        
        # Skip retrieval; use gold passages directly
        answer = generator(query, context=gold_passages)
        
        # Score against reference (oracle factuality)
        judge_score = call_llm_judge(query, answer, gold_passages)
        
        results['test_cases'].append({
            'query_id': tc['id'],
            'answer': answer,
            'factuality_score': judge_score,
            'retrieved_via': 'ground_truth'
        })
    
    # If factuality is still low here, problem is generation, not retrieval
    avg_score = sum(t['factuality_score'] for t in results['test_cases']) / len(results['test_cases'])
    results['summary'] = {
        'mean_factuality_with_gold': avg_score,
        'conclusion': 'generation_problem' if avg_score < 3.5 else 'retrieval_problem'
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results
```

### Step 2: Test Generation with Perfect Retrieval

Measure how much retrieval quality constrains generation:

```python
def ablation_generation_only(test_cases: list, actual_retriever, 
                             gold_generator, output_file: str = 'ablation_generation.json'):
    """Use actual retriever but compare against oracle generator on retrieved docs."""
    results = {'test_cases': []}
    
    for tc in test_cases:
        query = tc['query']
        retrieved = actual_retriever.search(query, k=10)
        context = '\n'.join([r['text'] for r in retrieved])
        
        # Use gold standard generator (e.g., Claude-3.5) instead of tutor
        gold_answer = gold_generator(query, context=context)
        actual_answer = actual_generator(query, context=context)
        
        # Compare quality
        gold_score = call_llm_judge(query, gold_answer, context)
        actual_score = call_llm_judge(query, actual_answer, context)
        
        results['test_cases'].append({
            'query_id': tc['id'],
            'gold_answer_score': gold_score,
            'actual_answer_score': actual_score,
            'gap': gold_score - actual_score
        })
    
    avg_gap = sum(t['gap'] for t in results['test_cases']) / len(results['test_cases'])
    results['summary'] = {
        'mean_generation_gap': avg_gap,
        'conclusion': 'generation_issue' if avg_gap > 0.5 else 'retrieval_sufficient'
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results
```

### Step 3: Language-Specific Ablation (Korean vs English)

Run parallel evals on English and Korean to isolate language issues:

```python
def ablation_language_comparison(test_cases_bilingual: list, pipeline, 
                                 output_file: str = 'ablation_language.json'):
    """Compare Korean and English performance on same queries."""
    results = {'en': [], 'ko': []}
    
    for tc in test_cases_bilingual:
        query_en = tc.get('query_en')
        query_ko = tc.get('query_ko')
        
        # Test English
        if query_en:
            answer_en = pipeline.generate(query_en)
            retrieval_en = pipeline.retriever.search(query_en, k=5)
            score_en = call_llm_judge(query_en, answer_en, retrieval_en)
            results['en'].append({'query_id': tc['id'], 'score': score_en})
        
        # Test Korean
        if query_ko:
            answer_ko = pipeline.generate(query_ko)
            retrieval_ko = pipeline.retriever.search(query_ko, k=5)
            score_ko = call_llm_judge(query_ko, answer_ko, retrieval_ko)
            results['ko'].append({'query_id': tc['id'], 'score': score_ko})
    
    avg_en = sum(r['score'] for r in results['en']) / len(results['en']) if results['en'] else 0
    avg_ko = sum(r['score'] for r in results['ko']) / len(results['ko']) if results['ko'] else 0
    
    results['summary'] = {
        'mean_en': avg_en,
        'mean_ko': avg_ko,
        'language_gap': avg_en - avg_ko,
        'worse_lang': 'korean' if avg_ko < avg_en else 'english'
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results
```

## Korean-Specific Diagnostics

When term consistency is low but naturalness is high, follow this checklist:

1. **TERM_GLOSSARY Coverage**: Check if Korean terminology matches tutor-content-gen's glossary
   - Run: `grep -F "$(answer_ko_terms)" TERM_GLOSSARY.json`
   - If missing: Add to glossary and re-index

2. **Generation Prompt Language Mixing**: Verify generation prompt is monolingual Korean
   - Check tutor-content-gen SKILL.md: prompt should be >95% Korean, examples should use Korean papers
   - If mixed: Regenerate with monolingual Korean examples

3. **Retrieval Language Mismatch**: Ensure queries and indexed documents are same language
   - Run: `detect_language(query_ko)` and `detect_language(doc_text)` on top-5 retrieved
   - If English docs returned for Korean query: Add language filter to retriever

```python
def diagnose_korean_issues(results_ko: dict) -> dict:
    """Korean-specific diagnostic checklist."""
    diagnosis = {}
    
    naturalness = results_ko.get('naturalness_score', 0)
    consistency = results_ko.get('consistency_score', 0)
    retrieval_lang_mismatch = results_ko.get('retrieval_lang_mismatch', False)
    
    # Pattern: high naturalness, low consistency
    if naturalness > 3.5 and consistency < 3.0:
        diagnosis['issue'] = 'terminology_inconsistency'
        diagnosis['checks'] = [
            'check_TERM_GLOSSARY_coverage',
            'verify_generation_prompt_korean_only',
            'inspect_top_5_retrieved_docs_language'
        ]
    elif retrieval_lang_mismatch:
        diagnosis['issue'] = 'retrieval_language_mismatch'
        diagnosis['action'] = 'add_language_filter_to_retriever'
    
    return diagnosis
```

