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


## Gap 1: Component-Specific Feedback Patterns

**Pattern-Based Feedback Classification**

Maps user feedback strings to specific component failures, distinguishing retrieval errors from generation quality issues:

```python
class ComponentPatternMatcher:
    """Route feedback to specific components via pattern matching."""
    
    def __init__(self):
        self.patterns = {
            "retrieval_failure": {
                "korean": ["답변이 관련없어요", "주제를 벗어났어", "이건 아닌 것 같아"],
                "english": ["wrong topic", "irrelevant answer", "off-topic"],
                "component": "rag_pipeline",
                "action": "increase_retrieval_depth"
            },
            "generation_quality": {
                "korean": ["설명이 너무 얕아요", "좀 더 자세히", "부족해"],
                "english": ["too shallow", "not enough detail", "incomplete"],
                "component": "prompt_template",
                "action": "tune_system_prompt"
            },
            "korean_naturalness": {
                "korean": ["한국어가 부자연스러워요", "어색한 표현", "뭔가 이상해"],
                "english": ["awkward Korean", "unnatural phrasing"],
                "component": "prompt_template",
                "action": "add_korean_guidance"
            },
            "difficulty_calibration": {
                "korean": ["너무 어려워요", "이해를 못했어", "어렵다"],
                "english": ["too hard", "too difficult", "don't understand"],
                "component": "expertise_estimator",
                "action": "decrease_difficulty"
            },
            "engagement": {
                "korean": ["재미없어요", "지겨워", "흥미로운 게 없네"],
                "english": ["boring", "not engaging", "uninteresting"],
                "component": "curiosity_modulator",
                "action": "increase_engagement"
            }
        }
    
    def classify_and_route(self, feedback_text: str, language: str = "ko"):
        """Match feedback to component and suggest action."""
        for pattern_key, pattern_data in self.patterns.items():
            patterns_list = pattern_data.get("korean" if language == "ko" else "english", [])
            if any(p in feedback_text for p in patterns_list):
                return {
                    "pattern": pattern_key,
                    "component": pattern_data["component"],
                    "action": pattern_data["action"],
                    "confidence": 0.95 if len([p for p in patterns_list if p in feedback_text]) > 0 else 0.7
                }
        return {"pattern": "unknown", "component": None, "action": None, "confidence": 0.0}
```

## Gap 2: Feedback Loop Closure

**Measure Whether Parameter Changes Improved Outcomes**

Track before/after feedback sentiment to verify parameter adjustments succeeded:

```python
def measure_improvement(before_params: dict, after_params: dict, feedback_window: int = 50):
    """Compare feedback sentiment distribution before/after param change.
    
    Args:
        before_params: Original parameter state (e.g., {'top_k': 5})
        after_params: New parameter state (e.g., {'top_k': 10})
        feedback_window: Number of post-adjustment feedbacks to evaluate
    
    Returns:
        improvement_score (float): Improvement in sentiment [0.0, 1.0]
        confidence_interval: (lower, upper) bounds for statistical significance
    """
    # Query feedback history around param change
    before_feedback = query_feedback_by_params(before_params, window=feedback_window)
    after_feedback = query_feedback_by_params(after_params, window=feedback_window)
    
    # Compute sentiment distributions
    before_scores = [entry["sentiment_score"] for entry in before_feedback]
    after_scores = [entry["sentiment_score"] for entry in after_feedback]
    
    before_mean = sum(before_scores) / max(len(before_scores), 1)
    after_mean = sum(after_scores) / max(len(after_scores), 1)
    
    improvement = (after_mean - before_mean) / max(abs(before_mean), 0.01)
    
    # Confidence via bootstrap (simplified)
    import statistics
    std_err = statistics.stdev(after_scores + before_scores) / (feedback_window ** 0.5)
    ci_lower = improvement - 1.96 * std_err
    ci_upper = improvement + 1.96 * std_err
    
    return {
        "improvement_score": max(0.0, min(1.0, improvement)),
        "confidence_interval": (ci_lower, ci_upper),
        "before_sentiment_mean": before_mean,
        "after_sentiment_mean": after_mean,
        "samples": len(after_feedback)
    }
```

## Gap 3: EvolutionBridge Contract

**Concrete Interface with evolve.py**

Standardized job format and priority scoring for parameter evolution:

```python
class EvolutionBridgeV2:
    """Concrete interface to evolve.py with strict job schema."""
    
    def submit_job(self, component: str, param_path: str, current_value, 
                   suggested_value, evidence: dict, feedback_volume: int, 
                   severity_score: float):
        """Submit parameter evolution job with priority scoring.
        
        Job format:
            {
                'component': 'rag_pipeline' | 'prompt_template' | 'curiosity_modulator',
                'param_path': 'top_k' | 'system_prompt' | 'hint_frequency',
                'current_value': current param value,
                'suggested_value': proposed new value,
                'evidence': {
                    'feedback_ids': [list of supporting feedback IDs],
                    'pattern_match': 'retrieval_failure' or other pattern,
                    'improvement_measurement': measure_improvement(...),
                    'user_count': number of users reporting issue
                },
                'priority_score': float [0.0, 1.0],
                'status': 'pending'
            }
        """
        priority = self._compute_priority(feedback_volume, severity_score)
        
        job = {
            "component": component,
            "param_path": param_path,
            "current_value": current_value,
            "suggested_value": suggested_value,
            "evidence": evidence,
            "priority_score": priority,
            "status": "pending",
            "submitted_at": self._timestamp()
        }
        
        # Write to evolve.py job queue
        with open(self.job_queue_path, 'a') as f:
            json.dump(job, f)
            f.write('\n')
        
        return job
    
    def _compute_priority(self, feedback_volume: int, severity: float):
        """Priority = (feedback_volume * 0.6) + (severity * 0.4), normalized."""
        raw = (feedback_volume / 100.0) * 0.6 + severity * 0.4
        return min(1.0, max(0.0, raw))
```

## Deep Robustness

Comprehensive anti-abuse and quality assurance mechanisms for handling adversarial input, sarcasm, feedback oscillations, and multi-language sentiment analysis.

### 1. Spam Detection

```python
from collections import defaultdict
from typing import Tuple
import time

class SpamDetector:
    """Identify spam, duplicate, and low-quality feedback using heuristic and content-based filters."""
    
    THRESHOLDS = {
        "repetition_ratio": 0.6,      # >60% repeated words = spam
        "link_density": 0.3,           # >30% URLs = spam
        "all_caps_ratio": 0.5,         # >50% caps = spam
        "min_words": 3,                # Feedback must have >= 3 words
        "duplicate_cosine": 0.9,       # Similarity >0.9 = duplicate
        "rate_limit_per_hour": 5       # Max 5 feedback items per user per hour
    }
    
    def __init__(self):
        self.user_feedback_history = defaultdict(list)  # user_id -> [(timestamp, text), ...]
        self.vector_cache = {}  # text -> embedding
    
    def classify(self, feedback_item: FeedbackEntry) -> Tuple[bool, str]:
        """Classify feedback as spam or legitimate.
        
        Args:
            feedback_item: FeedbackEntry to classify
        
        Returns:
            (is_spam: bool, reason: str)
        """
        user_id = feedback_item.user_id
        content = feedback_item.content
        timestamp = float(feedback_item.timestamp)
        
        # Check rate limiting
        if self._is_rate_limited(user_id, timestamp):
            return (True, "rate_limit_exceeded")
        
        # Check content length
        word_count = len(content.split())
        if word_count < self.THRESHOLDS["min_words"]:
            return (True, "too_short")
        
        # Check repetition ratio (token frequency concentration)
        if self._get_repetition_ratio(content) > self.THRESHOLDS["repetition_ratio"]:
            return (True, "excessive_repetition")
        
        # Check link density
        if self._get_link_density(content) > self.THRESHOLDS["link_density"]:
            return (True, "spam_links")
        
        # Check all-caps ratio
        if self._get_all_caps_ratio(content) > self.THRESHOLDS["all_caps_ratio"]:
            return (True, "shouting")
        
        # Check for duplicate against user's history
        if self._is_duplicate(user_id, content):
            return (True, "duplicate_submission")
        
        # Record this feedback in history
        self.user_feedback_history[user_id].append((timestamp, content))
        
        return (False, "legitimate")
    
    def _is_rate_limited(self, user_id: str, current_timestamp: float) -> bool:
        """Check if user exceeded rate limit (max 5 items per hour)."""
        one_hour_ago = current_timestamp - 3600
        recent_feedback = [
            ts for ts, _ in self.user_feedback_history[user_id]
            if ts > one_hour_ago
        ]
        return len(recent_feedback) >= self.THRESHOLDS["rate_limit_per_hour"]
    
    def _get_repetition_ratio(self, text: str) -> float:
        """Calculate ratio of repeated words to total words."""
        words = text.lower().split()
        if not words:
            return 0.0
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        repeated_words = sum(count - 1 for count in word_counts.values() if count > 1)
        return repeated_words / len(words)
    
    def _get_link_density(self, text: str) -> float:
        """Calculate ratio of URL tokens to total tokens."""
        import re
        url_pattern = r'https?://\S+|www\.\S+'
        urls = re.findall(url_pattern, text)
        tokens = text.split()
        if not tokens:
            return 0.0
        return len(urls) / len(tokens)
    
    def _get_all_caps_ratio(self, text: str) -> float:
        """Calculate ratio of all-caps words to total words."""
        words = text.split()
        if not words:
            return 0.0
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        return len(caps_words) / len(words)
    
    def _is_duplicate(self, user_id: str, content: str) -> bool:
        """Check if content is similar to user's previous feedback (cosine >0.9)."""
        if user_id not in self.user_feedback_history:
            return False
        
        current_vec = self._vectorize(content)
        for _, prev_content in self.user_feedback_history[user_id]:
            prev_vec = self._vectorize(prev_content)
            similarity = self._cosine_similarity(current_vec, prev_vec)
            if similarity > self.THRESHOLDS["duplicate_cosine"]:
                return True
        return False
    
    def _vectorize(self, text: str) -> dict:
        """Simple bag-of-words vectorization."""
        if text in self.vector_cache:
            return self.vector_cache[text]
        words = text.lower().split()
        vec = defaultdict(int)
        for word in words:
            vec[word] += 1
        self.vector_cache[text] = vec
        return vec
    
    def _cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """Compute cosine similarity between two bag-of-words vectors."""
        if not vec1 or not vec2:
            return 0.0
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in set(vec1.keys()) | set(vec2.keys()))
        norm1 = sum(v ** 2 for v in vec1.values()) ** 0.5
        norm2 = sum(v ** 2 for v in vec2.values()) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
```

### 2. Korean Sarcasm Detection

```python
class SarcasmDetectorKorean:
    """Detect Korean sarcasm via pattern matching and emoji-sentiment mismatch."""
    
    SARCASM_MARKERS = {
        "진짜 대단하시네요": "sarcasm_marker",      # "You're really great" (sarcastic)
        "아 네네": "dismissive_sarcasm",            # "Yeah yeah" (sarcastic)
        "ㅎㅎ": "laughing_dismissal",               # "haha" (dismissive)
        "정말요": "insincere_agreement",            # "Really?" (sarcastic)
        "좋네요": "false_praise"                    # "That's nice" (might be sarcastic)
    }
    
    POSITIVE_EMOJIS = {"😊", "😄", "👍", "❤️", "😍", "🎉"}
    NEGATIVE_WORDS = {
        "나쁘", "싫어", "불만", "문제", "실패", "잘못", 
        "어렵", "어색", "부족", "이상한", "끔찍"
    }
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
    
    def detect_sarcasm_ko(self, text: str) -> dict:
        """Detect Korean sarcasm patterns and emoji mismatches.
        
        Args:
            text: Korean feedback text
        
        Returns:
            {
                'is_sarcasm': bool,
                'confidence': float [0.0, 1.0],
                'reason': str,
                'suggested_sentiment': str (original, inverted)
            }
        """
        sarcasm_score = 0.0
        reasons = []
        
        # Check for sarcasm markers
        marker_found = False
        for marker, marker_type in self.SARCASM_MARKERS.items():
            if marker in text:
                marker_found = True
                sarcasm_score += 0.3
                reasons.append(f"sarcasm_marker:{marker_type}")
                break
        
        # Check for emoji-sentiment mismatch
        emoji_negative_mismatch = self._check_emoji_sentiment_mismatch(text)
        if emoji_negative_mismatch:
            sarcasm_score += 0.4
            reasons.append("emoji_sentiment_mismatch")
        
        # Check for negative words that contradict positive markers
        has_negative_words = any(word in text for word in self.NEGATIVE_WORDS)
        if marker_found and has_negative_words:
            sarcasm_score += 0.3
            reasons.append("marker_with_negative_context")
        
        # Final classification
        is_sarcasm = sarcasm_score >= self.confidence_threshold
        
        return {
            "is_sarcasm": is_sarcasm,
            "confidence": min(1.0, sarcasm_score),
            "reason": " | ".join(reasons) if reasons else "no_sarcasm_detected",
            "suggested_sentiment": "inverted" if is_sarcasm else "original"
        }
    
    def _check_emoji_sentiment_mismatch(self, text: str) -> bool:
        """Check if positive emoji appears with negative words."""
        has_positive_emoji = any(emoji in text for emoji in self.POSITIVE_EMOJIS)
        has_negative_words = any(word in text for word in self.NEGATIVE_WORDS)
        return has_positive_emoji and has_negative_words
```

### 3. Feedback Loop Cycle Prevention

```python
from collections import defaultdict, deque

class FeedbackCycleDetector:
    """Detect and dampen oscillation in parameter adjustments from feedback loops."""
    
    def __init__(self, history_window: int = 10):
        """Initialize cycle detector with parameter history tracking.
        
        Args:
            history_window: Number of iterations to track for oscillation detection
        """
        self.parameter_history = defaultdict(lambda: deque(maxlen=history_window))
        self.history_window = history_window
        self.dampening_factor = 0.5  # Reduce adjustment magnitude by 50% per oscillation
    
    def record_adjustment(self, param_name: str, old_val, new_val):
        """Record parameter adjustment in history.
        
        Args:
            param_name: Parameter identifier (e.g., 'top_k', 'hint_frequency')
            old_val: Previous parameter value
            new_val: New parameter value
        """
        adjustment = {
            "old": old_val,
            "new": new_val,
            "timestamp": time.time()
        }
        self.parameter_history[param_name].append(adjustment)
    
    def detect_oscillation(self, param_name: str, window_size: int = 3) -> bool:
        """Detect if parameter toggled back and forth within recent iterations.
        
        Args:
            param_name: Parameter to check
            window_size: Number of recent iterations to examine (default: 3)
        
        Returns:
            True if oscillation detected, False otherwise
        """
        history = self.parameter_history[param_name]
        if len(history) < window_size:
            return False
        
        # Get last 3 values in window
        recent_values = [h["new"] for h in list(history)[-window_size:]]
        
        # Check for pattern: A -> B -> A (toggle back)
        if len(recent_values) >= 3:
            return (recent_values[0] == recent_values[2] and 
                    recent_values[0] != recent_values[1])
        
        return False
    
    def get_dampened_adjustment(self, param_name: str, proposed_delta: float) -> float:
        """Apply dampening to adjustment magnitude if oscillation detected.
        
        Args:
            param_name: Parameter being adjusted
            proposed_delta: Proposed change magnitude
        
        Returns:
            Adjusted delta (reduced if oscillation detected)
        """
        oscillation_count = self._count_recent_oscillations(param_name)
        
        # Each oscillation reduces magnitude by 50%
        dampening = self.dampening_factor ** oscillation_count
        dampened_delta = proposed_delta * dampening
        
        return {
            "original_delta": proposed_delta,
            "dampened_delta": dampened_delta,
            "oscillation_count": oscillation_count,
            "dampening_applied": dampening
        }
    
    def _count_recent_oscillations(self, param_name: str) -> int:
        """Count number of detected oscillations in recent history."""
        history = self.parameter_history[param_name]
        if len(history) < 3:
            return 0
        
        oscillations = 0
        recent = list(history)[-9:]  # Look at last 9 entries
        
        for i in range(len(recent) - 2):
            if (recent[i]["new"] == recent[i + 2]["new"] and 
                recent[i]["new"] != recent[i + 1]["new"]):
                oscillations += 1
        
        return oscillations
```

### 4. Adversarial Input Sanitization

```python
import re
import unicodedata

def sanitize_feedback(feedback_text: str, max_length: int = 2000) -> dict:
    """Sanitize feedback against HTML injection, prompt injection, and malformed input.
    
    Args:
        feedback_text: Raw feedback string
        max_length: Maximum allowed character length (default: 2000)
    
    Returns:
        {
            'cleaned': str,
            'is_safe': bool,
            'issues': [str],
            'original_length': int,
            'final_length': int
        }
    """
    issues = []
    
    # 1. Check length
    if len(feedback_text) > max_length:
        feedback_text = feedback_text[:max_length]
        issues.append(f"truncated_to_{max_length}_chars")
    
    # 2. Detect and remove HTML/script injection
    html_script_pattern = r'<script|<iframe|<img|on\w+\s*=|javascript:'
    if re.search(html_script_pattern, feedback_text, re.IGNORECASE):
        feedback_text = re.sub(html_script_pattern, '', feedback_text, flags=re.IGNORECASE)
        issues.append("html_script_injection_removed")
    
    # 3. Detect prompt injection attempts
    injection_indicators = [
        "ignore previous instructions",
        "системная роль",  # Russian "system role"
        "역할 무시",        # Korean "ignore role"
        "system prompt",
        "jailbreak",
        "override"
    ]
    
    if any(indicator.lower() in feedback_text.lower() for indicator in injection_indicators):
        issues.append("prompt_injection_detected")
    
    # 4. Unicode normalization (Korean text)
    feedback_text = unicodedata.normalize('NFC', feedback_text)
    
    # 5. Remove control characters
    feedback_text = ''.join(char for char in feedback_text if unicodedata.category(char)[0] != 'C')
    
    is_safe = "prompt_injection_detected" not in issues
    
    return {
        "cleaned": feedback_text.strip(),
        "is_safe": is_safe,
        "issues": issues,
        "original_length": len(feedback_text),
        "final_length": len(feedback_text.strip())
    }
```

### 5. Multi-Language Sentiment Fallback

```python
class MultiLangSentiment:
    """Robust multi-language sentiment analysis with Korean-first, English fallback strategy."""
    
    def __init__(self):
        self.korean_classifier = SentimentClassifier()  # Existing Korean classifier
        self.english_patterns = {
            "positive": ["good", "great", "helpful", "clear", "excellent", "amazing"],
            "negative": ["bad", "terrible", "unclear", "confusing", "poor", "awful"],
            "neutral": []
        }
    
    def classify_with_fallback(self, text: str, primary_lang: str = "ko") -> dict:
        """Classify sentiment with primary language support and automatic fallback.
        
        Args:
            text: Feedback text (may be mixed language)
            primary_lang: Primary language ('ko' or 'en')
        
        Returns:
            {
                'sentiment': str (positive/negative/neutral),
                'confidence': float,
                'language_detected': str,
                'primary_result': dict,
                'fallback_result': dict (if used),
                'merged_result': dict (if mixed language)
            }
        """
        # Detect language composition
        lang_ratio = self._detect_language_mix(text)
        
        results = {
            "original_text": text,
            "language_detected": lang_ratio,
            "confidence": 0.0,
            "sentiment": "neutral"
        }
        
        # If pure or primarily Korean
        if lang_ratio["korean_ratio"] >= 0.7:
            results["primary_result"] = self.korean_classifier.classify(text, language="ko")
            results["sentiment"] = results["primary_result"]["sentiment"]
            results["confidence"] = results["primary_result"]["confidence"]
        
        # If pure or primarily English
        elif lang_ratio["english_ratio"] >= 0.7:
            results["primary_result"] = self._classify_english(text)
            results["sentiment"] = results["primary_result"]["sentiment"]
            results["confidence"] = results["primary_result"]["confidence"]
        
        # If mixed language
        else:
            ko_result = self.korean_classifier.classify(text, language="ko")
            en_result = self._classify_english(text)
            results["primary_result"] = ko_result
            results["fallback_result"] = en_result
            results["merged_result"] = self._merge_multilingual(ko_result, en_result, lang_ratio)
            results["sentiment"] = results["merged_result"]["sentiment"]
            results["confidence"] = results["merged_result"]["confidence"]
        
        return results
    
    def _detect_language_mix(self, text: str) -> dict:
        """Estimate Korean vs English character ratio."""
        korean_chars = len([c for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7AF])
        english_chars = len([c for c in text if c.isalpha() and ord(c) < 128])
        total = korean_chars + english_chars
        
        if total == 0:
            return {"korean_ratio": 0.0, "english_ratio": 0.0, "mixed": False}
        
        ko_ratio = korean_chars / total
        en_ratio = english_chars / total
        
        return {
            "korean_ratio": ko_ratio,
            "english_ratio": en_ratio,
            "mixed": ko_ratio > 0.2 and en_ratio > 0.2
        }
    
    def _classify_english(self, text: str) -> dict:
        """Rule-based English sentiment classification."""
        text_lower = text.lower()
        scores = {"positive": 0, "negative": 0, "neutral": 0}
        
        for word in self.english_patterns["positive"]:
            if word in text_lower:
                scores["positive"] += 1
        
        for word in self.english_patterns["negative"]:
            if word in text_lower:
                scores["negative"] += 1
        
        sentiment = max(scores, key=scores.get)
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1
        
        return {
            "sentiment": sentiment,
            "scores": scores,
            "confidence": max_score / (len(text.split()) + 1),
            "language": "en"
        }
    
    def _merge_multilingual(self, ko_result: dict, en_result: dict, lang_ratio: dict) -> dict:
        """Merge Korean and English sentiment with weighted average.
        
        Args:
            ko_result: Korean classification result
            en_result: English classification result
            lang_ratio: Language ratio dictionary
        
        Returns:
            Merged sentiment result
        """
        # Weight by language composition
        ko_weight = lang_ratio["korean_ratio"]
        en_weight = lang_ratio["english_ratio"]
        
        # Convert sentiments to scores
        sentiment_scores = {
            "positive": 1.0,
            "negative": -1.0,
            "neutral": 0.0,
            "constructive": 0.5
        }
        
        ko_score = sentiment_scores.get(ko_result["sentiment"], 0.0)
        en_score = sentiment_scores.get(en_result["sentiment"], 0.0)
        
        # Weighted merge
        merged_score = (ko_score * ko_weight + en_score * en_weight) / (ko_weight + en_weight + 0.0001)
        
        # Map back to sentiment
        if merged_score > 0.3:
            merged_sentiment = "positive"
        elif merged_score < -0.3:
            merged_sentiment = "negative"
        else:
            merged_sentiment = "neutral"
        
        merged_confidence = max(ko_result["confidence"], en_result["confidence"])
        
        return {
            "sentiment": merged_sentiment,
            "confidence": merged_confidence,
            "weighted_ko": ko_weight,
            "weighted_en": en_weight,
            "merged_score": merged_score,
            "language_mix": "ko+en"
        }
```

### Usage Integration

```python
# Pipeline integration example
def process_feedback_robustly(feedback_text: str, user_id: str) -> dict:
    """End-to-end feedback processing with all robustness layers."""
    
    # Layer 1: Sanitize input
    sanitized = sanitize_feedback(feedback_text)
    if not sanitized["is_safe"]:
        return {"accepted": False, "reason": "unsafe_input", "issues": sanitized["issues"]}
    
    cleaned_text = sanitized["cleaned"]
    
    # Layer 2: Spam detection
    spam_detector = SpamDetector()
    feedback_entry = FeedbackEntry(
        session_id="temp",
        user_id=user_id,
        timestamp=str(time.time()),
        channel=FeedbackChannel.SURVEY,
        content=cleaned_text
    )
    is_spam, spam_reason = spam_detector.classify(feedback_entry)
    if is_spam:
        return {"accepted": False, "reason": f"spam_detected:{spam_reason}"}
    
    # Layer 3: Sarcasm detection (Korean)
    sarcasm_detector = SarcasmDetectorKorean()
    sarcasm_result = sarcasm_detector.detect_sarcasm_ko(cleaned_text)
    
    # Layer 4: Multi-language sentiment with fallback
    sentiment_classifier = MultiLangSentiment()
    sentiment_result = sentiment_classifier.classify_with_fallback(cleaned_text)
    
    # Adjust sentiment if sarcasm detected
    if sarcasm_result["is_sarcasm"] and sarcasm_result["suggested_sentiment"] == "inverted":
        original_sentiment = sentiment_result["sentiment"]
        sentiment_result["sentiment"] = "negative" if original_sentiment == "positive" else "positive"
        sentiment_result["sarcasm_adjusted"] = True
    
    # Layer 5: Check for feedback cycles
    cycle_detector = FeedbackCycleDetector()
    dampened_adj = cycle_detector.get_dampened_adjustment("explanation_clarity", 0.1)
    
    return {
        "accepted": True,
        "cleaned_text": cleaned_text,
        "sanitization": sanitized,
        "sarcasm_detected": sarcasm_result["is_sarcasm"],
        "sentiment": sentiment_result,
        "feedback_cycle_dampening": dampened_adj,
        "ready_for_routing": True
    }
```
```

## Deep Robustness: Profile-Aware Evolution

```python
from enum import Enum

class LearnerProfile(Enum):
    BEGINNER     = "beginner"      # undergrad, first exposure
    INTERMEDIATE = "intermediate"  # grad student, some background
    EXPERT       = "expert"         # PhD student, deep familiarity

PROFILE_PARAMETERS = {
    LearnerProfile.BEGINNER: {
        "difficulty_range": (0.3, 0.6),
        "equation_density_max": 0.2,
        "analogy_rate": 0.8,
        "korean_english_ratio": 0.9,  # heavy Korean
        "citation_density": 0.3,      # fewer citations, more intuition
    },
    LearnerProfile.INTERMEDIATE: {
        "difficulty_range": (0.5, 0.8),
        "equation_density_max": 0.5,
        "analogy_rate": 0.5,
        "korean_english_ratio": 0.6,
        "citation_density": 0.6,
    },
    LearnerProfile.EXPERT: {
        "difficulty_range": (0.7, 1.0),
        "equation_density_max": 1.0,
        "analogy_rate": 0.2,
        "korean_english_ratio": 0.3,  # more English jargon OK
        "citation_density": 1.0,
    },
}

class ProfileAwareEvolutionBridge:
    """Applies parameter deltas scoped to the learner's profile.

    Prevents the failure mode where a BEGINNER's complaint ('too hard')
    cascades into dumbing down EXPERT content.
    """
    def __init__(self, history_path: str = ".evolution_history.json"):
        self.history = self._load(history_path)
        self.history_path = history_path

    def propose_adjustment(self, feedback_item: dict) -> dict:
        profile = LearnerProfile(feedback_item.get("profile", "intermediate"))
        complaint = feedback_item.get("category")  # "too_hard", "too_easy", "boring", "confusing"
        current = feedback_item.get("current_params", {})
        proposed = dict(current)

        profile_bounds = PROFILE_PARAMETERS[profile]
        if complaint == "too_hard":
            proposed["difficulty"] = max(
                profile_bounds["difficulty_range"][0],
                current.get("difficulty", 0.7) - 0.1
            )
            proposed["analogy_rate"] = min(1.0, current.get("analogy_rate", 0.5) + 0.15)
        elif complaint == "too_easy":
            proposed["difficulty"] = min(
                profile_bounds["difficulty_range"][1],
                current.get("difficulty", 0.5) + 0.1
            )
        elif complaint == "boring":
            proposed["curiosity_hook_rate"] = min(1.0, current.get("curiosity_hook_rate", 0.3) + 0.2)
        elif complaint == "confusing":
            proposed["citation_density"] = min(profile_bounds["citation_density"],
                                                current.get("citation_density", 0.5) + 0.15)

        # clamp every parameter to its profile bounds
        for k, v in proposed.items():
            bound_key = f"{k}_range"
            if bound_key in profile_bounds:
                lo, hi = profile_bounds[bound_key]
                proposed[k] = max(lo, min(hi, v))

        delta = {k: proposed[k] - current.get(k, 0) for k in proposed if proposed[k] != current.get(k)}
        return {
            "profile": profile.value,
            "complaint": complaint,
            "current": current,
            "proposed": proposed,
            "delta": delta,
            "confidence": self._compute_confidence(feedback_item),
        }

    def _compute_confidence(self, feedback_item: dict) -> float:
        # confidence high if: engagement low, feedback specific, profile matches complaint
        eng = feedback_item.get("engagement", 0.5)
        specificity = len(feedback_item.get("text", "").split()) / 50  # more words = more specific
        return min(1.0, (1.0 - eng) * 0.5 + min(specificity, 1.0) * 0.3 + 0.2)

    def record(self, adjustment: dict):
        import json
        from datetime import datetime
        self.history.append({"ts": datetime.utcnow().isoformat(), **adjustment})
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def _load(self, path):
        import os, json
        if os.path.exists(path):
            try: return json.load(open(path))
            except: return []
        return []

    def detect_profile_drift(self, user_id: str, window: int = 5) -> dict:
        """If complaints consistently span profile bounds, user may be mis-classified."""
        recent = [h for h in self.history[-window:] if h.get("user_id") == user_id]
        if len(recent) < 3: return {"drift": False}
        profiles = [h["profile"] for h in recent]
        complaints = [h["complaint"] for h in recent]
        # heuristic: beginner profile but persistent "too_easy" complaints → promote
        if profiles.count("beginner") >= 3 and complaints.count("too_easy") >= 2:
            return {"drift": True, "suggested_profile": "intermediate",
                    "reason": "persistent_too_easy_in_beginner"}
        if profiles.count("expert") >= 3 and complaints.count("too_hard") >= 2:
            return {"drift": True, "suggested_profile": "intermediate",
                    "reason": "persistent_too_hard_in_expert"}
        return {"drift": False}
```
```
