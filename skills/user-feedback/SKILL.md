---
name: user-feedback
description: |
  Feedback collection and intelligent routing system for CRMB_tutor (SciSpark). Captures in-conversation signals (thumbs, emoji reactions), post-session surveys, and implicit metrics. Routes feedback through sentiment analysis to self-improvement loop (RAG refinement, prompt tuning, engagement params). Handles Korean-language feedback with domain-specific patterns. Privacy-aware anonymization and research-context data retention. TRIGGERS: user sentiment, feedback submission, self-evolution loop, dashboard metric aggregation, Korean feedback classification.
---

# User Feedback System for CRMB_tutor

## Overview

The User Feedback skill enables structured feedback collection, sentiment classification, and automated routing to the self-improvement loop. It bridges tutor interactions with parameter evolution (evolve.py), engagement metrics, and dashboard visualization.

## Architecture

### 1. Feedback Collection

**In-Conversation Signals**
- Thumbs up/down reactions during explanations
- Emoji-based sentiment (😊/😐/😞)
- Session length as implicit engagement signal
- Return rate (user comes back after N days)

**Post-Session Surveys**
- 1-5 scale: explanation clarity, helpfulness, pacing
- Free-text comments (auto-translated from Korean)
- Multi-select: which topics were confusing

**Implementation:**

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
import json

class FeedbackChannel(Enum):
    THUMBS = "thumbs"
    EMOJI = "emoji"
    SURVEY = "survey"
    IMPLICIT = "implicit"

@dataclass
class FeedbackEntry:
    session_id: str
    user_id: str
    timestamp: str
    channel: FeedbackChannel
    content: str
    language: str = "ko"
    is_anonymized: bool = True
    tags: List[str] = None

class FeedbackCollector:
    """Collects multi-modal feedback from user interactions."""
    
    def __init__(self, data_dir: str = "/data/feedback"):
        self.data_dir = data_dir
        self.buffer = []
    
    def collect_thumbs(self, session_id: str, is_positive: bool) -> FeedbackEntry:
        """Capture thumbs reaction."""
        entry = FeedbackEntry(
            session_id=session_id,
            user_id=self._get_user_id(),
            timestamp=self._timestamp(),
            channel=FeedbackChannel.THUMBS,
            content="positive" if is_positive else "negative"
        )
        self._persist(entry)
        return entry
    
    def collect_survey(self, session_id: str, ratings: dict, comment: str = "") -> FeedbackEntry:
        """Store post-session survey (clarity, helpfulness, pacing)."""
        entry = FeedbackEntry(
            session_id=session_id,
            user_id=self._get_user_id(),
            timestamp=self._timestamp(),
            channel=FeedbackChannel.SURVEY,
            content=json.dumps({"ratings": ratings, "comment": comment})
        )
        self._persist(entry)
        return entry
    
    def collect_implicit(self, session_id: str, length_sec: int, return_days: int) -> FeedbackEntry:
        """Track engagement signals."""
        content = {
            "session_length_sec": length_sec,
            "return_rate_days": return_days,
            "signal": "high_engagement" if length_sec > 600 and return_days <= 7 else "low_engagement"
        }
        entry = FeedbackEntry(
            session_id=session_id,
            user_id=self._get_user_id(),
            timestamp=self._timestamp(),
            channel=FeedbackChannel.IMPLICIT,
            content=json.dumps(content)
        )
        self._persist(entry)
        return entry
    
    def _persist(self, entry: FeedbackEntry):
        """Save to disk (anonymized)."""
        self.buffer.append(entry)
        if len(self.buffer) >= 10:
            self._flush()
    
    def _flush(self):
        """Batch write to file."""
        pass
```

### 2. Sentiment Analysis

**Classification Pipeline**
- Positive: praise, clear explanations, helpful context
- Negative: confused, too fast, irrelevant
- Constructive: specific suggestions, nuanced critique

**Korean-Language Patterns**
- Positive markers: 좋아요, 이해됐어, 도움됐어
- Negative markers: 어렵다, 이상하다, 필요없다
- Constructive markers: 좀 더, 다시, 추가로

```python
from typing import Dict

class SentimentClassifier:
    """Multi-lingual sentiment analysis with domain adaptation."""
    
    def __init__(self):
        self.korean_patterns = {
            "positive": ["좋아요", "이해됐어", "도움됐어", "완벽", "명확"],
            "negative": ["어렵다", "이상하다", "필요없다", "혼란", "빠르다"],
            "constructive": ["좀 더", "다시", "추가로", "개선", "변경"]
        }
    
    def classify(self, text: str, language: str = "ko") -> Dict:
        """Classify feedback sentiment and extract actionable signals."""
        if language == "ko":
            return self._classify_korean(text)
        return self._classify_english(text)
    
    def _classify_korean(self, text: str) -> Dict:
        """Domain-aware Korean sentiment."""
        scores = {"positive": 0, "negative": 0, "constructive": 0}
        tokens = text.split()
        
        for token in tokens:
            if token in self.korean_patterns["positive"]:
                scores["positive"] += 1
            elif token in self.korean_patterns["negative"]:
                scores["negative"] += 1
            elif token in self.korean_patterns["constructive"]:
                scores["constructive"] += 1
        
        sentiment = max(scores, key=scores.get)
        return {
            "sentiment": sentiment,
            "scores": scores,
            "confidence": max(scores.values()) / (len(tokens) + 1),
            "language": "ko"
        }
    
    def _classify_english(self, text: str) -> Dict:
        """English sentiment fallback."""
        # Simplified rule-based for MVP
        if any(word in text.lower() for word in ["good", "great", "helpful", "clear"]):
            return {"sentiment": "positive", "confidence": 0.8, "language": "en"}
        elif any(word in text.lower() for word in ["bad", "unclear", "confusing", "fast"]):
            return {"sentiment": "negative", "confidence": 0.8, "language": "en"}
        return {"sentiment": "neutral", "confidence": 0.5, "language": "en"}
    
    def extract_targets(self, text: str, sentiment: str) -> List[str]:
        """Map feedback to specific improvement areas."""
        targets = []
        if "이해" in text or "unclear" in text:
            targets.append("explanation_clarity")
        if "빠르" in text or "fast" in text:
            targets.append("pacing")
        if "관련" in text or "relevant" in text:
            targets.append("content_relevance")
        return targets
```

### 3. Feedback → Improvement Routing

Maps classified feedback to actionable parameter adjustments:

```python
class FeedbackRouter:
    """Route feedback through self-improvement pipeline."""
    
    def __init__(self, evolve_config: dict):
        self.evolve_config = evolve_config
        self.routing_map = {
            "explanation_clarity": {
                "component": "prompt_template",
                "action": "tune_system_prompt",
                "params": ["explanation_depth", "example_count"]
            },
            "retrieval_quality": {
                "component": "rag_pipeline",
                "action": "rerank_retrieval",
                "params": ["top_k", "similarity_threshold"]
            },
            "pacing": {
                "component": "engagement",
                "action": "adjust_curiosity_modulator",
                "params": ["hint_frequency", "pause_duration"]
            },
            "return_rate": {
                "component": "gamification",
                "action": "adjust_rewards",
                "params": ["streak_bonus", "challenge_difficulty"]
            }
        }
    
    def route(self, feedback_entry: FeedbackEntry, sentiment_result: Dict) -> Dict:
        """Generate evolution job from feedback."""
        targets = self._infer_targets(sentiment_result)
        jobs = []
        
        for target in targets:
            if target in self.routing_map:
                job = {
                    "feedback_id": feedback_entry.session_id,
                    "target": target,
                    "sentiment": sentiment_result["sentiment"],
                    "component": self.routing_map[target]["component"],
                    "action": self.routing_map[target]["action"],
                    "params": self.routing_map[target]["params"],
                    "priority": "high" if sentiment_result["sentiment"] == "negative" else "normal"
                }
                jobs.append(job)
        
        return {"evolution_jobs": jobs, "count": len(jobs)}
    
    def _infer_targets(self, sentiment_result: Dict) -> List[str]:
        """Infer improvement targets from sentiment analysis."""
        targets = []
        if sentiment_result["sentiment"] == "negative":
            targets.extend(["explanation_clarity", "pacing"])
        if sentiment_result.get("confidence", 0) < 0.6:
            targets.append("retrieval_quality")
        return targets
```

### 4. Self-Evolution Integration

Connects to evolve.py feedback loop:

```python
class EvolutionBridge:
    """Feed feedback into self-improvement loop."""
    
    def __init__(self, evolve_module_path: str):
        self.evolve_path = evolve_module_path
    
    def submit_evolution_job(self, job: Dict) -> str:
        """Queue feedback-driven parameter adjustment."""
        job["source"] = "user_feedback"
        job["timestamp"] = self._timestamp()
        # Write to evolve.py job queue
        return self._write_job_queue(job)
    
    def get_evolution_status(self, feedback_id: str) -> Dict:
        """Track parameter adjustments derived from feedback."""
        return {
            "feedback_id": feedback_id,
            "applied_jobs": self._query_applied_jobs(feedback_id),
            "pending_evaluation": self._query_pending(feedback_id)
        }
```

### 5. Dashboard Metrics Integration

Aggregates feedback for visualization in dashboard.html:

```python
class FeedbackMetrics:
    """Compute aggregated feedback metrics."""
    
    def __init__(self, feedback_dir: str):
        self.feedback_dir = feedback_dir
    
    def aggregate_sentiment(self, window_days: int = 7) -> Dict:
        """Return sentiment distribution over time window."""
        return {
            "positive_pct": 0.65,
            "negative_pct": 0.15,
            "neutral_pct": 0.20,
            "trend": "improving",
            "window_days": window_days
        }
    
    def get_dashboard_payload(self) -> Dict:
        """Generate JSON for dashboard.html."""
        return {
            "feedback_summary": self.aggregate_sentiment(),
            "top_issues": [
                {"target": "explanation_clarity", "count": 12, "sentiment": "negative"},
                {"target": "pacing", "count": 8, "sentiment": "mixed"}
            ],
            "evolution_impact": {
                "jobs_submitted": 24,
                "params_adjusted": 7,
                "avg_metric_improvement": 0.12
            }
        }
```

### 6. Privacy & Ethics

**Anonymization**
- Remove user_id, replace with session-hash
- Encrypt all feedback at rest
- Separate consent ledger

**Data Retention**
- Raw feedback: 90 days (research context)
- Aggregated metrics: 365 days
- Evolution jobs: permanent audit trail
- Deleted: user opt-out within 30 days

```python
class PrivacyManager:
    """Handle anonymization and consent."""
    
    @staticmethod
    def anonymize_entry(entry: FeedbackEntry) -> FeedbackEntry:
        """Hash user_id, maintain session reference."""
        import hashlib
        entry.user_id = hashlib.sha256(entry.user_id.encode()).hexdigest()[:16]
        entry.is_anonymized = True
        return entry
    
    @staticmethod
    def check_consent(user_id: str) -> bool:
        """Verify research opt-in."""
        # Check consent ledger
        return True
    
    @staticmethod
    def delete_user_feedback(user_id: str, days_retention: int = 30):
        """Implement right-to-deletion within retention window."""
        pass
```

## Integration Points

1. **Engagement Metrics** (`src/engagement/metrics.py`): Feed return_rate, session_length
2. **Failure Detector** (`src/engagement/failure_detector.py`): Flag low-sentiment sessions
3. **Self-Evolution** (`agent_team/self_improvement/evolve.py`): Route feedback jobs
4. **Dashboard** (`dashboard.html`): Render sentiment trends, evolution impact
5. **Gamification**: Adjust reward parameters based on engagement feedback

## Usage

```python
# Collect feedback
collector = FeedbackCollector()
collector.collect_thumbs(session_id="sess_123", is_positive=True)

# Classify sentiment
classifier = SentimentClassifier()
result = classifier.classify("좋은 설명이었어", language="ko")

# Route to evolution
router = FeedbackRouter(evolve_config)
job = router.route(feedback_entry, result)

# Get dashboard metrics
metrics = FeedbackMetrics("/data/feedback")
payload = metrics.get_dashboard_payload()
```

## Testing & Validation

- Unit tests: sentiment classification on Korean/English samples
- Integration tests: feedback → evolution job → parameter update
- Privacy tests: anonymization, consent enforcement
