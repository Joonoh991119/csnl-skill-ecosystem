# EVAL_PROMPT1: User Feedback System for SciSpark Tutor
## Comprehensive Feedback Pipeline → Automatic Improvement

**Evaluation Date:** 2026-04-14  
**Prompt:** Students using SciSpark tutor are giving mixed feedback — some love the curiosity hooks but find explanations too shallow, others say the Korean is unnatural. Need to: (1) collect feedback systematically, (2) classify by component (retrieval, generation, engagement, language), (3) route to improvement targets, (4) connect to evolve.py for auto-adjustment.

---

## 1. SUFFICIENCY OF GUIDANCE BY SECTION

### 1.1 Collection Architecture (Strong)
The skill provides **concrete, implementable code** for multi-modal feedback collection:
- **Channels covered:** thumbs reactions, emoji sentiment, post-session surveys, implicit signals (session length, return rate)
- **Data structure:** `FeedbackEntry` dataclass with fields for session_id, user_id, timestamp, channel, content, language, anonymization flag
- **Implementation details:** Buffer-and-flush pattern for persistence, explicit timestamp/user tracking
- **Guidance quality:** Clear enough that a developer could implement the `FeedbackCollector` class without external references

**Gap:** No concrete storage backend specified (file format, database schema, cloud storage integration). The `_persist()` method is a stub.

---

### 1.2 Sentiment Classification (Good for Korean, Limited for Component Routing)
**Strengths:**
- Explicitly recognizes Korean sentiment markers (좋아요, 이해됐어, 어렵다, 어려다, 필요없다)
- Korean pattern dictionary maps to actionable categories (positive, negative, constructive)
- Fallback English patterns provided
- `extract_targets()` hints at mapping feedback to improvement areas (explanation_clarity, pacing, content_relevance)

**Critical Gap:** The skill **does NOT adequately map sentiment to the four requested components:**
- **Retrieval (RAG quality)**: No explicit guidance on detecting retrieval failures in feedback. The code checks "관련" (relevant) generically but doesn't teach how to distinguish "I found the wrong context" vs. "the context was useless"
- **Generation (explanation quality):** Conflates with clarity. No guidance on detecting hallucination, factual errors, or missing domain knowledge
- **Engagement (curiosity hooks, pacing):** Only mentions "빠르다" (fast) and generic pacing. No framework for classifying hook effectiveness (did it motivate? Was it patronizing?)
- **Language (Korean naturalness):** Completely absent. No patterns for detecting unnatural Korean (formal register when casual expected, translationese artifacts, etc.)

**Actionability score:** 2/5 for component-specific routing; 4/5 for general sentiment.

---

### 1.3 Feedback → Improvement Routing (Partial)
**What's Present:**
- `FeedbackRouter` class with a `routing_map` that connects targets to components, actions, and parameters
- Example: "explanation_clarity" → prompt_template tuning with params ["explanation_depth", "example_count"]
- Priority assignment (high for negative, normal for positive)

**Critical Gaps:**
1. **Incomplete mapping:** The routing_map has ~5 targets (explanation_clarity, retrieval_quality, pacing, return_rate). The prompt asks for feedback on retrieval, generation, engagement, AND language — but only ~2 of these are explicitly covered (pacing ≈ engagement, some clarity ≈ generation).

2. **No language-specific routing:** No routing path for "Korean is unnatural" feedback. What action should be taken? Which parameters adjusted? No guidance.

3. **No retrieval-specific metrics:** The "retrieval_quality" target mentions reranking but doesn't explain how to infer from user feedback that retrieval failed (vs. the student not understanding the retrieved content).

4. **Parameter mapping is vague:** "explanation_depth" and "example_count" are reasonable, but:
   - What are the ranges? How much to adjust per negative feedback?
   - Should adjustments be global (affects all students) or personalized?
   - How do we avoid overcorrecting?

**Actionability score:** 2/5. Developers would struggle to implement this routing in production without trial-and-error.

---

### 1.4 Self-Evolution Loop Integration (Skeleton Only)
**What's Present:**
- `EvolutionBridge` class that:
  - Queues feedback-driven jobs with `submit_evolution_job()`
  - Tracks status with `get_evolution_status()`
  - Wraps jobs with source="user_feedback" metadata

**Critical Gaps:**
1. **No actual connection to evolve.py:** The `_write_job_queue()` and `_query_applied_jobs()` methods are stubs. How does the queue get written? Where does evolve.py pick it up?

2. **No feedback loop closure:** After evolve.py adjusts parameters, how does the system measure improvement? No guidance on:
   - A/B testing adjusted params vs. baseline
   - Collecting new feedback post-adjustment
   - Detecting if an adjustment made things worse

3. **No example job structure:** A developer implementing this would need to know:
   - Expected job format that evolve.py consumes
   - What parameters can actually be tuned
   - How to encode "increase explanation depth" into evolve.py's API

**Actionability score:** 1/5 for actual integration; the bridge is a stub begging for implementation details.

---

### 1.5 Dashboard Metrics (Skeletal)
`FeedbackMetrics.get_dashboard_payload()` returns hardcoded JSON with sentiment trends and evolution_impact metrics. No guidance on:
- How to compute "avg_metric_improvement" (improvement in what? Student correctness? Session retention?)
- How to aggregate data across time (rolling window? daily snapshots?)
- Real-time vs. batch metric updates

**Actionability score:** 2/5.

---

### 1.6 Privacy & Ethics (Good Coverage)
The skill provides:
- Anonymization pattern (hashing user_id)
- Consent checking (`check_consent()`)
- Right-to-deletion framework (`delete_user_feedback()`)
- Data retention tiers (90-day raw, 365-day aggregated, permanent audit trail)

**Gap:** Stub implementations; no guidance on encryption, secure deletion, or compliance testing.

---

## 2. SCORING

### Relevance (Does it address the eval prompt?) **2/5**
- **Collects feedback systematically:** Yes (strong architecture)
- **Classifies by component:** Partial (good for sentiment, weak for retrieval/generation/language/engagement as distinct categories)
- **Routes to improvement targets:** Partial skeleton
- **Connects to evolve.py auto-adjustment:** Stub only

The skill addresses ~50% of the prompt directly; the rest requires substantial engineering beyond the guidance provided.

### Completeness (How much of the pipeline is specified?) **2/5**
- Collection: 85% (missing storage backend)
- Sentiment analysis: 60% (Korean-aware but missing component-specific patterns)
- Routing: 40% (map exists but incomplete and unmapped to language feedback)
- Evolution bridge: 20% (skeleton only)
- Feedback loop closure: 0%

Missing entirely: Korean language naturalness detection patterns, retrieval failure inference, generation error patterns, actual evolve.py integration, A/B testing framework.

### Actionability (Can a developer use this?) **2/5**
A developer could:
- Implement `FeedbackCollector` from the code (copy-paste ready)
- Understand the sentiment classification approach
- See the routing architecture conceptually

A developer would struggle to:
- Detect language-specific issues
- Differentiate retrieval vs. generation problems
- Implement the EvolutionBridge without inventing the evolve.py contract
- Measure whether adjustments actually improved outcomes
- Deploy end-to-end without significant interpolation

---

## 3. GAPS & IMPROVEMENT RECOMMENDATIONS

### Gap 1: Component-Specific Feedback Patterns (Critical)
**Problem:** The skill doesn't teach how to detect retrieval, generation, engagement, or language issues in feedback.

**Solution:**
Add a new section "Component-Specific Patterns" with patterns for each:

```python
class ComponentPatternDetector:
    """Map feedback signals to specific tutor components."""
    
    def detect_retrieval_failure(self, feedback: str, language: str = "ko") -> bool:
        """Identify signs of poor context retrieval."""
        retrieval_patterns_ko = {
            "wrong_context": ["관련없다", "다른 주제", "전혀"],
            "missing_info": ["없었어", "못 찾았어", "빠졌어"],
            "shallow_context": ["표면적", "깊이 없", "기초만"]
        }
        # Return True if patterns match
    
    def detect_generation_failure(self, feedback: str, language: str = "ko") -> bool:
        """Identify hallucination, factual errors, or missing domain knowledge."""
        generation_patterns_ko = {
            "hallucination": ["틀렸어", "잘못된", "없는 내용"],
            "domain_gap": ["과학적 아니", "원리가", "이상한"],
            "missing_depth": ["피상적", "더 자세히", "왜인지"]
        }
    
    def detect_engagement_failure(self, feedback: str, language: str = "ko") -> bool:
        """Identify issues with curiosity hooks, pacing, or motivation."""
        engagement_patterns_ko = {
            "hook_miss": ["지루했어", "흥미없", "왜 배워야"],
            "pacing_fast": ["너무 빠르", "따라가기 힘", "시간 부족"],
            "pacing_slow": ["너무 느려", "뻔했어", "빨리"],
            "patronizing": ["아기 취급", "쉬운 거만", "너무 간단"]
        }
    
    def detect_language_issue(self, feedback: str, language: str = "ko") -> bool:
        """Identify Korean naturalness, register mismatch, or translationese."""
        language_patterns = {
            "formal_register": ["합니다", "입니다"],  # If student uses informal, formal in tutor is jarring
            "translationese": ["것이다", "직역 느낌", "어색"],
            "register_mismatch": ["존댓말", "반말 섞임"],
            "phonetic_unnatural": ["어투 이상", "한국인 아닌 느낌"]
        }
```

### Gap 2: Retrieval-Specific Metrics (Critical)
**Problem:** No way to distinguish "the retrieved context was bad" from "the student misunderstood the context."

**Solution:** Add context quality feedback collection:

```python
def collect_context_quality(self, session_id: str, retrieval_results: List[str], 
                           student_understanding: bool) -> FeedbackEntry:
    """Separate context quality from comprehension."""
    entry = FeedbackEntry(
        session_id=session_id,
        channel=FeedbackChannel.IMPLICIT,
        content=json.dumps({
            "retrieval_quality": "high" if student_understanding else "low",
            "context_relevance": "relevant" if any("key_term" in r for r in retrieval_results) else "tangential",
            "depth_matched": "yes" if all(len(r) > 100 for r in retrieval_results) else "no"
        })
    )
```

### Gap 3: Generation Error Detection (Critical)
**Problem:** No patterns for detecting hallucination, factual errors, or domain mismatches.

**Solution:** Add generation-specific feedback:

```python
def collect_generation_quality(self, session_id: str, explanation: str, 
                              student_feedback: str = "") -> FeedbackEntry:
    """Capture generation-specific signals."""
    entry = FeedbackEntry(
        session_id=session_id,
        channel=FeedbackChannel.SURVEY,
        content=json.dumps({
            "factuality": student_feedback if "잘못" in student_feedback else "ok",
            "depth_level": "shallow" if "더 자세" in student_feedback else "adequate",
            "examples_count": "insufficient" if "예시" in student_feedback else "adequate"
        })
    )
```

### Gap 4: Language-Specific Feedback Path (Critical)
**Problem:** Korean naturalness feedback has no routing path.

**Solution:** Add language tuning target:

```python
# In FeedbackRouter.routing_map:
"language_naturalness": {
    "component": "generation",
    "action": "tune_korean_generation",
    "params": ["register_level", "honorific_usage", "formality_index"]
}

# In SentimentClassifier.extract_targets():
if "어색" in text or "자연스럽지" in text or "어투" in text:
    targets.append("language_naturalness")
```

### Gap 5: Evolve.py Integration Contract (Critical)
**Problem:** EvolutionBridge is a stub; no specification of the job queue contract.

**Solution:** Specify the exact job format and evolve.py API:

```python
# Example: What does evolve.py expect?
evolution_job = {
    "job_id": "ev_abc123",
    "source": "user_feedback",
    "target_component": "prompt_template",  # Matches evolve.py's component names
    "action": "tune_system_prompt",
    "params": {
        "explanation_depth": {"current": 2, "adjustment": "+1", "rationale": "shallow per feedback"},
        "example_count": {"current": 1, "adjustment": "+1"}
    },
    "feedback_signal_count": 12,
    "feedback_confidence": 0.75,
    "evaluation_metric": "student_correctness",  # How to measure success
    "holdout_pct": 0.1  # A/B test 10% of students
}

# Actual queue mechanism:
def _write_job_queue(self, job: Dict) -> str:
    """Write to evolve.py's job queue (specify actual implementation)."""
    queue_path = f"{self.evolve_path}/queue/feedback_jobs.jsonl"
    with open(queue_path, 'a') as f:
        f.write(json.dumps(job) + '\n')
    return job["job_id"]
```

### Gap 6: Feedback Loop Closure & Measurement (Critical)
**Problem:** No guidance on how to measure whether adjustments helped.

**Solution:** Add a feedback-effect tracker:

```python
class FeedbackEffectTracker:
    """Measure impact of feedback-driven adjustments."""
    
    def measure_adjustment_impact(self, job_id: str, metric: str = "student_correctness") -> Dict:
        """Compare control vs. adjusted group."""
        return {
            "job_id": job_id,
            "metric": metric,
            "control_baseline": 0.65,
            "adjusted_group": 0.72,
            "improvement_pct": 10.8,
            "statistical_significance": "p=0.03",
            "recommendation": "deploy" if improvement_pct > 5 else "revert"
        }
```

### Gap 7: Korean Naturalness Detection (Critical)
**Problem:** Completely absent. Students report "Korean is unnatural" but skill doesn't help detect or fix it.

**Solution:** Add Korean-specific language quality module:

```python
class KoreanLanguageQuality:
    """Detect and route Korean naturalness issues."""
    
    def detect_register_mismatch(self, generated_text: str, student_context: str) -> bool:
        """Check if tutor's formal register clashes with student's casual style."""
        formal_markers = ["입니다", "합니다", "되었습니다"]
        informal_markers = ["야", "어", "해"]
        
        has_formal = any(m in generated_text for m in formal_markers)
        has_informal = any(m in student_context for m in informal_markers)
        return has_formal and has_informal
    
    def detect_translationese(self, text: str) -> bool:
        """Identify word-for-word English translations."""
        # Patterns like "것이다" (too literal), missing particles, etc.
        translationese_patterns = ["것이다", "이다+동사", "빠진 조사"]
        return any(p in text for p in translationese_patterns)
```

### Gap 8: Missing Evaluation Metrics (Critical)
**Problem:** No specification of how to measure success of feedback system itself.

**Solution:** Add evaluation framework:

```python
class FeedbackSystemMetrics:
    """Measure feedback system health."""
    
    def get_feedback_coverage(self) -> Dict:
        """What % of sessions generate feedback?"""
        return {
            "sessions_with_feedback": 487,
            "total_sessions": 612,
            "coverage_pct": 79.6,
            "target": 0.8
        }
    
    def get_routing_accuracy(self) -> Dict:
        """What % of routed jobs led to improvement?"""
        return {
            "jobs_evaluated": 24,
            "jobs_improved_metric": 18,
            "accuracy_pct": 75,
            "target": 0.7
        }
```

---

## 4. CONCRETE IMPLEMENTATION ROADMAP

To make the skill fully actionable for the eval prompt, prioritize in this order:

1. **(Week 1)** Implement Gap 1 (component-specific patterns) + Gap 7 (Korean naturalness). These are required to properly classify feedback.
2. **(Week 1)** Implement Gap 5 (evolve.py contract). Without this, no routing happens.
3. **(Week 2)** Implement Gap 6 (feedback loop closure). Without this, you can't measure whether the system works.
4. **(Week 2)** Implement Gap 2 + 3 (retrieval/generation-specific feedback). This enables component-specific routing.
5. **(Week 3)** Implement Gap 8 (system-level evaluation metrics). This lets you iterate on the feedback system itself.

---

## SUMMARY

| Dimension | Score | Status |
|-----------|-------|--------|
| **Relevance** | 2/5 | Partial — addresses collection & routing but weak on components & language |
| **Completeness** | 2/5 | Skeleton — collection code ready, everything else needs work |
| **Actionability** | 2/5 | Developers can start with `FeedbackCollector` but will hit walls on routing & integration |

**Verdict:** The skill provides a **solid foundation for feedback collection and a useful template for routing architecture**, but falls short of being a **complete end-to-end pipeline** for the eval prompt. The biggest gaps are:
- No component-specific classification (retrieval vs. generation vs. engagement vs. language)
- No Korean language naturalness detection
- Incomplete evolve.py integration
- No feedback loop closure or improvement measurement

**To meet the eval prompt fully, the skill needs 6-8 weeks of implementation work beyond the guidance provided.**
