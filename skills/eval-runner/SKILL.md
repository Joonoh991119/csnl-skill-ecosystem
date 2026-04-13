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
