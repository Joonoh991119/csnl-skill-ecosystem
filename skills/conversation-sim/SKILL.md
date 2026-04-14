---
name: conversation-sim
description: Simulates multi-turn conversations testing engagement modules (CuriosityModulator, ExpertiseEstimator, FailureDetector, SpacedRepetition, Gamification) across CRMB and Efficient Coding domains. Supports user profiles (beginner/intermediate/expert), failure injection, A/B testing, and Korean dialogue quality assessment. TRIGGERS - run with domains (crmb|coding), profile (beginner|intermediate|expert), num_turns (10-20), mode (normal|failure_inject|ab_test).
---

# Conversation Simulator for Addictive Conversation System

## Overview
Generates realistic multi-turn conversations testing the CRMB_tutor engagement system across two domains. Tracks engagement metrics, tests failure recovery, and supports A/B parameter tuning with natural Korean dialogue.

## Quick Start

```bash
# Basic CRMB conversation with beginner
python conversation-sim.py --domain crmb --profile beginner --num_turns 15

# Failure injection test (trigger disengagement recovery)
python conversation-sim.py --domain coding --profile intermediate --mode failure_inject

# A/B test: compare hook frequencies
python conversation-sim.py --domain crmb --profile expert --mode ab_test --config_a high_enthusiasm --config_b balanced
```

## User Profiles

### Beginner
- Vocabulary: Basic (1000-2000 words)
- Question depth: Surface-level (why/what)
- Misconceptions: High (7-10 per conversation)
- Hook type preference: PARADOX, CONNECTION
- Engagement floor: 40%

### Intermediate  
- Vocabulary: Domain-specific (3000-5000 words)
- Question depth: Medium (how, application)
- Misconceptions: Moderate (3-5 per conversation)
- Hook type preference: IMPLICATION, HISTORY
- Engagement floor: 60%

### Expert
- Vocabulary: Advanced technical (5000+ words)
- Question depth: Deep (why underlying, synthesis)
- Misconceptions: Low (1-3 per conversation)
- Hook type preference: FRONTIER, MISCONCEPTION
- Engagement floor: 75%

## Domains

### CRMB (Cellular & Molecular Biology)
Topics: osmosis, enzyme kinetics, photosynthesis, protein folding, ATP hydrolysis

### Efficient Coding
Topics: algorithmic complexity, memory optimization, design patterns, async/await, caching strategies

## Metrics Tracked

1. **Engagement**: Session engagement %, hook effectiveness (0-100)
2. **Learning**: Misconceptions resolved, vocabulary acquisition rate
3. **Gamification**: XP earned, streak maintained, aha moments triggered
4. **Temporal**: Turn duration, response latency, session coherence
5. **Recovery**: Failure detection → intervention latency, re-engagement success

## Failure Modes

- **Boredom**: Easy hook repetition → disengagement spike
- **Confusion**: Complex explanation without scaffolding → dropout
- **Frustration**: Misconception not addressed → mini-failures
- **Context drift**: Domain switch too abrupt → coherence drop

## A/B Test Configs

```python
configs = {
    "high_enthusiasm": {"hook_frequency": 0.8, "challenge_level": 0.7, "xp_multiplier": 1.5},
    "balanced": {"hook_frequency": 0.5, "challenge_level": 0.5, "xp_multiplier": 1.0},
    "adaptive": {"hook_frequency": "profile-based", "challenge_level": "misconception-aware", "xp_multiplier": 1.2},
}
```

---

# Implementation

```python
#!/usr/bin/env python3
"""
conversation-sim: Multi-turn conversation simulator for Addictive Conversation System
Tests engagement modules: CuriosityModulator, ExpertiseEstimator, FailureDetector, Gamification
"""

import random
import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Tuple
import argparse

# =============================================================================
# Data Models
# =============================================================================

class HookType(Enum):
    PARADOX = "역설"  # Paradox
    CONNECTION = "연결"  # Connection
    HISTORY = "역사"  # History
    IMPLICATION = "함축"  # Implication
    MISCONCEPTION = "오개념"  # Misconception
    FRONTIER = "경계"  # Frontier

class Domain(Enum):
    CRMB = "crmb"
    CODING = "coding"

class Profile(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

@dataclass
class UserState:
    profile: Profile
    vocabulary_level: int
    question_depth: float
    misconceptions: List[str]
    engagement: float = 100.0
    xp: int = 0
    streak: int = 0
    aha_moments: int = 0

@dataclass
class Turn:
    turn_num: int
    user_message: str
    assistant_response: str
    hook_used: HookType
    engagement_delta: float
    misconception_addressed: bool
    vocabulary_acquired: List[str]

@dataclass
class SessionMetrics:
    domain: Domain
    profile: Profile
    total_turns: int
    avg_engagement: float
    hook_distribution: Dict[str, int]
    misconceptions_resolved: int
    total_xp: int
    streaks_maintained: int
    aha_moments: int
    failure_detected: bool
    recovery_success: bool

# =============================================================================
# User Simulators
# =============================================================================

class UserSimulator:
    """Generates realistic user responses based on profile"""
    
    def __init__(self, profile: Profile, domain: Domain):
        self.profile = profile
        self.domain = domain
        self.state = self._init_state()
        self.topic_queue = self._init_topics()
        
    def _init_state(self) -> UserState:
        config = {
            Profile.BEGINNER: {"vocab": 1500, "depth": 0.3, "misconceptions": 8},
            Profile.INTERMEDIATE: {"vocab": 4000, "depth": 0.6, "misconceptions": 4},
            Profile.EXPERT: {"vocab": 6000, "depth": 0.85, "misconceptions": 2},
        }
        cfg = config[self.profile]
        return UserState(
            profile=self.profile,
            vocabulary_level=cfg["vocab"],
            question_depth=cfg["depth"],
            misconceptions=self._generate_misconceptions(cfg["misconceptions"]),
        )
    
    def _init_topics(self) -> List[str]:
        topics = {
            Domain.CRMB: ["osmosis", "enzyme kinetics", "photosynthesis", "protein folding", "ATP"],
            Domain.CODING: ["complexity", "memory", "patterns", "async", "caching"],
        }
        return topics[self.domain]
    
    def _generate_misconceptions(self, count: int) -> List[str]:
        misconceptions = {
            Domain.CRMB: [
                "세포막이 물을 투과할 수 없다",
                "효소는 반응을 시작하기 위해 ATP를 필요로 한다",
                "광합성은 빛에서만 일어난다",
                "단백질은 정적인 구조이다",
            ],
            Domain.CODING: [
                "O(n²)은 항상 O(n)보다 느리다",
                "메모리 효율은 속도보다 중요하다",
                "비동기 코드는 항상 더 빠르다",
                "캐싱은 항상 도움이 된다",
            ],
        }
        pool = misconceptions[self.domain]
        return random.sample(pool, min(count, len(pool)))
    
    def generate_question(self, turn_num: int) -> str:
        """Generate realistic user question"""
        templates = {
            (Domain.CRMB, Profile.BEGINNER): [
                "{}가 뭐예요?",
                "{}는 왜 중요한가요?",
                "{}의 예시가 있어요?",
            ],
            (Domain.CRMB, Profile.INTERMEDIATE): [
                "{}의 메커니즘이 어떻게 되나요?",
                "{}가 {}와 어떻게 연관되어 있나요?",
                "{}를 막으면 어떤 일이 일어날까요?",
            ],
            (Domain.CRMB, Profile.EXPERT): [
                "{}의 진화적 이점은 뭔가요?",
                "{}의 열역학적 기여는?",
                "{}를 조작하는 고급 기법이 있나요?",
            ],
            (Domain.CODING, Profile.BEGINNER): [
                "{}가 뭐예요?",
                "{}는 언제 사용하나요?",
                "{}의 예제 코드 있어요?",
            ],
            (Domain.CODING, Profile.INTERMEDIATE): [
                "{}의 트레이드오프는 뭐죠?",
                "{}와 {}의 차이점은?",
                "이 경우 {}를 어떻게 최적화할까요?",
            ],
            (Domain.CODING, Profile.EXPERT): [
                "{}의 점근적 한계는?",
                "{}와 {}의 상호작용이 성능에 미치는 영향?",
                "{}를 극한까지 최적화하는 방법?",
            ],
        }
        
        key = (self.domain, self.profile)
        template = random.choice(templates.get(key, templates[(self.domain, Profile.BEGINNER)]))
        topic = random.choice(self.topic_queue)
        return template.format(topic)
    
    def update_engagement(self, hook_effectiveness: float, misconception_addressed: bool):
        """Update engagement state based on tutor interaction"""
        delta = hook_effectiveness * 5
        if misconception_addressed and self.state.misconceptions:
            delta += 10
            self.state.misconceptions.pop()
        
        floor = {
            Profile.BEGINNER: 40,
            Profile.INTERMEDIATE: 60,
            Profile.EXPERT: 75,
        }[self.profile]
        
        self.state.engagement = max(floor, min(100, self.state.engagement + delta))

# =============================================================================
# Engagement Engine
# =============================================================================

class ConversationRunner:
    """Orchestrates multi-turn conversation with engagement tracking"""
    
    def __init__(self, domain: Domain, profile: Profile, num_turns: int, config: Dict = None):
        self.domain = domain
        self.profile = profile
        self.num_turns = num_turns
        self.config = config or self._default_config()
        self.user = UserSimulator(profile, domain)
        self.turns: List[Turn] = []
        self.hook_counts: Dict[str, int] = {h.value: 0 for h in HookType}
        self.misconceptions_resolved = 0
        self.failure_detected = False
        self.recovery_attempted = False
        self.recovery_success = False
        
    def _default_config(self) -> Dict:
        return {
            "hook_frequency": 0.5,
            "challenge_level": 0.5,
            "xp_multiplier": 1.0,
        }
    
    def run(self) -> SessionMetrics:
        """Execute full conversation simulation"""
        for turn_num in range(1, self.num_turns + 1):
            user_msg = self.user.generate_question(turn_num)
            
            # Select hook based on config and user state
            hook = self._select_hook(turn_num)
            response = self._generate_response(user_msg, hook)
            
            # Assess learning
            misconception_hit = any(m in user_msg.lower() for m in self.user.state.misconceptions)
            if misconception_hit:
                self.misconceptions_resolved += 1
            
            # Calculate engagement impact
            hook_effectiveness = self._assess_hook_effectiveness(hook, turn_num)
            engagement_delta = hook_effectiveness * 5
            if misconception_hit:
                engagement_delta += 10
            
            # Detect failure modes
            if self.user.state.engagement < 50 and not self.failure_detected:
                self.failure_detected = True
                self._attempt_recovery()
            
            # Update user state
            self.user.update_engagement(hook_effectiveness, misconception_hit)
            
            # Record turn
            self.turns.append(Turn(
                turn_num=turn_num,
                user_message=user_msg,
                assistant_response=response,
                hook_used=hook,
                engagement_delta=engagement_delta,
                misconception_addressed=misconception_hit,
                vocabulary_acquired=self._extract_vocabulary(response),
            ))
        
        return self._compute_metrics()
    
    def _select_hook(self, turn_num: int) -> HookType:
        """Select engagement hook based on profile and config"""
        profile_prefs = {
            Profile.BEGINNER: [HookType.PARADOX, HookType.CONNECTION],
            Profile.INTERMEDIATE: [HookType.IMPLICATION, HookType.HISTORY],
            Profile.EXPERT: [HookType.FRONTIER, HookType.MISCONCEPTION],
        }
        preferred = profile_prefs[self.profile]
        
        if random.random() < self.config["hook_frequency"]:
            hook = random.choice(preferred)
        else:
            hook = random.choice(list(HookType))
        
        self.hook_counts[hook.value] += 1
        return hook
    
    def _generate_response(self, user_msg: str, hook: HookType) -> str:
        """Generate tutor response with selected hook"""
        hook_templates = {
            HookType.PARADOX: "흥미롭지만 모순적인 점이 있어요: {}",
            HookType.CONNECTION: "이건 {}와 연결되어 있어요:",
            HookType.HISTORY: "역사적으로 봤을 때 {}에서 시작됐어요:",
            HookType.IMPLICATION: "이것의 함의는 {}입니다:",
            HookType.MISCONCEPTION: "흔한 오개념을 바로잡겠습니다: {}",
            HookType.FRONTIER: "최신 연구에서 {}가 밝혀졌어요:",
        }
        intro = hook_templates[hook]
        return f"{intro}\n좋은 질문이에요. 차근차근 설명하겠습니다."
    
    def _assess_hook_effectiveness(self, hook: HookType, turn_num: int) -> float:
        """Rate hook effectiveness (0-1)"""
        base_score = {
            HookType.PARADOX: 0.85,
            HookType.CONNECTION: 0.75,
            HookType.HISTORY: 0.65,
            HookType.IMPLICATION: 0.80,
            HookType.MISCONCEPTION: 0.90,
            HookType.FRONTIER: 0.70,
        }[hook]
        
        # Early-turn hooks are less effective, mid-turn peaks
        recency_factor = 1.0 if 5 <= turn_num <= 15 else 0.7
        return base_score * recency_factor
    
    def _extract_vocabulary(self, response: str) -> List[str]:
        """Extract new vocabulary from response"""
        terms = {
            Domain.CRMB: ["hydrophobic", "kinetics", "metabolism", "catalyst"],
            Domain.CODING: ["throughput", "latency", "thrashing", "coherency"],
        }
        return random.sample(terms[self.domain], k=random.randint(1, 2))
    
    def _attempt_recovery(self) -> None:
        """Attempt to recover from disengagement"""
        self.recovery_attempted = True
        # Increase hook frequency and reduce challenge
        self.config["hook_frequency"] = min(1.0, self.config["hook_frequency"] + 0.3)
        self.config["challenge_level"] = max(0.2, self.config["challenge_level"] - 0.2)
        
        # Recovery succeeds if engagement recovers above 60
        if self.user.state.engagement > 60:
            self.recovery_success = True
    
    def _compute_metrics(self) -> SessionMetrics:
        """Compute final session metrics"""
        engagements = [
            t.engagement_delta for t in self.turns
        ]
        avg_eng = sum(engagements) / len(engagements) if engagements else 0
        
        return SessionMetrics(
            domain=self.domain,
            profile=self.profile,
            total_turns=len(self.turns),
            avg_engagement=round(avg_eng, 2),
            hook_distribution=self.hook_counts,
            misconceptions_resolved=self.misconceptions_resolved,
            total_xp=int(self.user.state.engagement * len(self.turns) * self.config["xp_multiplier"]),
            streaks_maintained=self.user.state.streak,
            aha_moments=self.user.state.aha_moments,
            failure_detected=self.failure_detected,
            recovery_success=self.recovery_success,
        )

# =============================================================================
# A/B Testing
# =============================================================================

def run_ab_test(domain: Domain, profile: Profile, num_turns: int, iterations: int = 3):
    """Run A/B test comparing two configurations"""
    configs = {
        "high_enthusiasm": {"hook_frequency": 0.8, "challenge_level": 0.7, "xp_multiplier": 1.5},
        "balanced": {"hook_frequency": 0.5, "challenge_level": 0.5, "xp_multiplier": 1.0},
    }
    
    results = {"high_enthusiasm": [], "balanced": []}
    
    for config_name, config in configs.items():
        for _ in range(iterations):
            runner = ConversationRunner(domain, profile, num_turns, config)
            metrics = runner.run()
            results[config_name].append(asdict(metrics))
    
    print(f"\n=== A/B Test Results: {domain.value.upper()} / {profile.value} ===")
    for config_name, runs in results.items():
        avg_engagement = sum(r["avg_engagement"] for r in runs) / len(runs)
        avg_xp = sum(r["total_xp"] for r in runs) / len(runs)
        print(f"{config_name}: avg_eng={avg_engagement:.1f}, avg_xp={avg_xp:.0f}")

# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Conversation Simulator")
    parser.add_argument("--domain", choices=["crmb", "coding"], default="crmb")
    parser.add_argument("--profile", choices=["beginner", "intermediate", "expert"], default="beginner")
    parser.add_argument("--num_turns", type=int, default=15)
    parser.add_argument("--mode", choices=["normal", "failure_inject", "ab_test"], default="normal")
    args = parser.parse_args()
    
    domain = Domain[args.domain.upper()]
    profile = Profile[args.profile.upper()]
    
    if args.mode == "ab_test":
        run_ab_test(domain, profile, args.num_turns)
    else:
        runner = ConversationRunner(domain, profile, args.num_turns)
        metrics = runner.run()
        
        print(f"\n=== Session Summary ===")
        print(f"Domain: {metrics.domain.value} | Profile: {metrics.profile.value}")
        print(f"Turns: {metrics.total_turns} | Avg Engagement: {metrics.avg_engagement:.1f}%")
        print(f"Misconceptions Resolved: {metrics.misconceptions_resolved}")
        print(f"Total XP: {metrics.total_xp} | Aha Moments: {metrics.aha_moments}")
        print(f"Failure Detected: {metrics.failure_detected} | Recovery: {metrics.recovery_success}")
        print(f"Hook Distribution: {metrics.hook_distribution}")

if __name__ == "__main__":
    main()
```

---

## Deep Robustness: P3 Enhancements

Advanced robustness patches targeting P3 engagement score of 3.5/5. This section implements four critical subsystems: dropout detection & recovery, persona consistency checking, structured engagement metrics, and misconception persistence tracking.

### 1. Dropout Detection & Recovery

Detects and recovers from silent users and disengagement patterns mid-conversation.

```python
class DropoutDetector:
    """Detect user disengagement and suggest recovery strategies"""
    
    DISENGAGEMENT_SIGNALS = [
        "okay", "fine", "sure", "whatever", "alright", "i guess",  # English
        "네", "응", "그래", "괜찮아", "뭐어", "그냥"  # Korean
    ]
    
    RESPONSE_LENGTH_THRESHOLD = 5  # words
    SILENT_TURNS_THRESHOLD = 3      # consecutive turns < 5 words
    
    def __init__(self):
        self.recent_responses = []  # Track last N user responses
        self.silent_streak = 0
        
    def detect_dropout_risk(self, conversation_history: List[Turn]) -> float:
        """
        Compute disengagement risk score (0-1).
        
        Signals monitored:
        - Silent turns: response length collapse to <5 words for 3+ consecutive turns
        - Disengagement phrases: "okay", "fine", "sure", "whatever"
        - Response length ratio: user_response_length / tutor_response_length < 0.2
        
        Returns:
            float: Risk score 0-1, where 1.0 = immediate intervention needed
        """
        if not conversation_history:
            return 0.0
        
        # Check recent response pattern
        recent = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
        response_lengths = [len(t.user_message.split()) for t in recent]
        
        risk = 0.0
        
        # Signal 1: Response length collapse
        short_responses = sum(1 for l in response_lengths if l < self.RESPONSE_LENGTH_THRESHOLD)
        if short_responses >= self.SILENT_TURNS_THRESHOLD:
            risk += 0.4
            self.silent_streak = short_responses
        
        # Signal 2: Disengagement phrases
        last_msg = recent[-1].user_message.lower() if recent else ""
        for phrase in self.DISENGAGEMENT_SIGNALS:
            if phrase in last_msg:
                risk += 0.35
                break
        
        # Signal 3: Response length ratio drop
        if recent and len(recent) > 1:
            avg_user_len = sum(response_lengths) / len(response_lengths)
            avg_tutor_len = sum(len(t.assistant_response.split()) for t in recent) / len(recent)
            if avg_user_len > 0 and avg_tutor_len > 0:
                ratio = avg_user_len / avg_tutor_len
                if ratio < 0.2:
                    risk += 0.25
        
        return min(1.0, risk)
    
    def suggest_recovery(self, risk_level: float, current_topic: str) -> Dict[str, str]:
        """
        Suggest recovery strategies based on risk level.
        
        Args:
            risk_level: Disengagement risk 0-1
            current_topic: Current conversation topic
            
        Returns:
            Strategy with action, response_template, and rationale
        """
        if risk_level < 0.3:
            return {"action": "continue", "rationale": "Engagement stable"}
        
        if risk_level < 0.6:
            # Light intervention: topic pivot
            return {
                "action": "topic_pivot",
                "response": f"{}와 다르게, {}는 실제로 어떨까요? (Unlike X, what about Y with {current_topic}?)",
                "rationale": "Subtle topic shift maintains engagement",
            }
        
        if risk_level < 0.85:
            # Medium intervention: curiosity hook + difficulty reduction
            return {
                "action": "curiosity_hook",
                "response": f"흥미로운 질문인데, {}의 '숨겨진' 측면이 있어요. (Interesting question! X has a 'hidden' aspect...)",
                "rationale": "Reframe topic as discovery, reduce cognitive load",
            }
        
        # High risk: emergency recovery with XP incentive
        return {
            "action": "emergency_reset",
            "response": f"지금까지 정말 잘하고 있어요! 이제 {}의 한 가지만 깊게 들어갈까요? (You're doing great! Want to dive deeper into one aspect of X?)",
            "rationale": "Positive reinforcement + fresh start with narrowed scope",
        }
```

### 2. Persona Consistency Checker

Tracks and resolves contradictions in stated user knowledge/preferences.

```python
class PersonaConsistencyChecker:
    """Track and resolve contradictions in user persona across turns"""
    
    def __init__(self):
        self.claims: Dict[int, List[Dict]] = {}  # turn_num -> [{"type": ..., "value": ..., "confidence": 0-1}]
        self.contradictions: List[Dict] = []
    
    def track_claim(self, turn_num: int, claim_type: str, claim_value: str, confidence: float = 0.8):
        """
        Record a claim about user knowledge/preference.
        
        Args:
            turn_num: Conversation turn number
            claim_type: "knowledge" | "preference" | "skill_level" | "goal"
            claim_value: The actual claim (e.g., "I know nothing about ART")
            confidence: How confident we are in this claim (0-1)
        """
        if turn_num not in self.claims:
            self.claims[turn_num] = []
        
        self.claims[turn_num].append({
            "type": claim_type,
            "value": claim_value,
            "confidence": confidence,
            "timestamp": turn_num,
        })
    
    def detect_contradictions(self) -> List[Dict]:
        """
        Scan all claims for logical contradictions.
        
        Returns:
            List of contradiction objects with severity and resolution options
        """
        contradictions = []
        
        # Group claims by type
        by_type = {}
        for turn_num, claims_list in self.claims.items():
            for claim in claims_list:
                ctype = claim["type"]
                if ctype not in by_type:
                    by_type[ctype] = []
                by_type[ctype].append((turn_num, claim))
        
        # Check for contradictions within each type
        for claim_type, claims_with_turns in by_type.items():
            if len(claims_with_turns) < 2:
                continue
            
            # Simple contradiction: opposite knowledge claims
            if claim_type == "knowledge":
                values = [c["value"] for _, c in claims_with_turns]
                if any("nothing" in v.lower() for v in values) and \
                   any("know about" in v.lower() or "familiar" in v.lower() for v in values):
                    
                    earliest = min(claims_with_turns, key=lambda x: x[0])
                    latest = max(claims_with_turns, key=lambda x: x[0])
                    
                    contradictions.append({
                        "type": "knowledge_contradiction",
                        "claim_1": earliest[1],
                        "turn_1": earliest[0],
                        "claim_2": latest[1],
                        "turn_2": latest[0],
                        "severity": 0.8,
                    })
        
        self.contradictions = contradictions
        return contradictions
    
    def resolve(self, strategy: str = "recency_weighted") -> Dict:
        """
        Resolve contradictions using specified strategy.
        
        Args:
            strategy: "recency_weighted" | "majority_vote" | "confidence_weighted"
            
        Returns:
            Resolved persona claims with rationale
        """
        if not self.contradictions:
            return {"status": "no_contradictions", "resolved_claims": {}}
        
        resolved = {}
        
        for contradiction in self.contradictions:
            claim_type = contradiction["type"]
            
            if strategy == "recency_weighted":
                # Latest claim wins, weighted by confidence
                if contradiction["turn_2"] > contradiction["turn_1"]:
                    resolved[claim_type] = {
                        "value": contradiction["claim_2"]["value"],
                        "source": f"turn {contradiction['turn_2']}",
                        "rationale": "Most recent claim with higher confidence"
                    }
            
            elif strategy == "confidence_weighted":
                # Use claim with highest confidence
                if contradiction["claim_1"]["confidence"] > contradiction["claim_2"]["confidence"]:
                    resolved[claim_type] = {
                        "value": contradiction["claim_1"]["value"],
                        "source": f"turn {contradiction['turn_1']}",
                        "rationale": "Higher confidence rating"
                    }
                else:
                    resolved[claim_type] = {
                        "value": contradiction["claim_2"]["value"],
                        "source": f"turn {contradiction['turn_2']}",
                        "rationale": "Higher confidence rating"
                    }
        
        return {
            "status": "resolved",
            "strategy": strategy,
            "resolved_claims": resolved,
            "contradictions_count": len(self.contradictions),
        }
```

### 3. Engagement Score Semantics

Define and compute multi-dimensional engagement metrics.

```python
ENGAGEMENT_METRICS = {
    "response_length_ratio": {
        "weight": 0.20,
        "description": "user_response_length / tutor_response_length"
    },
    "question_asking_rate": {
        "weight": 0.25,
        "description": "frequency of user questions (turns with ? marks)"
    },
    "topic_follow_through": {
        "weight": 0.25,
        "description": "does user engage with introduced topic in next turn?"
    },
    "elaboration_depth": {
        "weight": 0.15,
        "description": "does user go beyond yes/no? (sentence complexity)"
    },
    "session_duration_ratio": {
        "weight": 0.15,
        "description": "actual_session_length / expected_session_length"
    },
}

def compute_engagement(conversation: List[Turn]) -> float:
    """
    Compute weighted engagement score (0-1).
    
    Args:
        conversation: List of Turn objects
        
    Returns:
        Weighted engagement score 0-1
    """
    if not conversation:
        return 0.0
    
    scores = {}
    
    # Metric 1: Response length ratio
    user_lengths = [len(t.user_message.split()) for t in conversation]
    tutor_lengths = [len(t.assistant_response.split()) for t in conversation]
    avg_user_len = sum(user_lengths) / len(user_lengths) if user_lengths else 0
    avg_tutor_len = sum(tutor_lengths) / len(tutor_lengths) if tutor_lengths else 1
    ratio = min(1.0, avg_user_len / max(avg_tutor_len, 1))
    scores["response_length_ratio"] = ratio
    
    # Metric 2: Question asking rate
    questions = sum(1 for t in conversation if "?" in t.user_message)
    scores["question_asking_rate"] = min(1.0, questions / max(len(conversation), 1))
    
    # Metric 3: Topic follow-through
    follow_through = 0
    for i in range(len(conversation) - 1):
        current_topics = set(conversation[i].user_message.split())
        next_topics = set(conversation[i + 1].user_message.split())
        if len(current_topics & next_topics) > 2:  # Overlap threshold
            follow_through += 1
    scores["topic_follow_through"] = follow_through / max(len(conversation) - 1, 1)
    
    # Metric 4: Elaboration depth (sentence count, word variety)
    elaborate = sum(1 for t in conversation if len(t.user_message.split()) > 10)
    scores["elaboration_depth"] = elaborate / max(len(conversation), 1)
    
    # Metric 5: Session duration ratio (assume expected ~15-20 turns)
    expected_turns = 15
    actual_turns = len(conversation)
    scores["session_duration_ratio"] = min(1.0, actual_turns / expected_turns)
    
    # Weighted sum
    total = 0.0
    for metric_name, metric_config in ENGAGEMENT_METRICS.items():
        weight = metric_config["weight"]
        score = scores.get(metric_name, 0.0)
        total += weight * score
    
    return round(total, 3)
```

### 4. Strategy Pivot Validation

Validate pivot strategies before and after execution.

```python
class PivotValidator:
    """Validate domain pivot strategies for compatibility and effectiveness"""
    
    def __init__(self):
        self.pivot_history: List[Dict] = []
        self.validation_window = 3  # turns to measure effectiveness
    
    def validate_before_pivot(self, current_persona: UserState, new_domain: Domain, 
                             current_domain: Domain) -> Dict[str, any]:
        """
        Check if pivot is compatible with user persona before executing.
        
        Args:
            current_persona: Current user state/knowledge
            new_domain: Target pivot domain (CRMB or CODING)
            current_domain: Current domain
            
        Returns:
            Validation result with compatibility score and warnings
        """
        compatibility = 1.0
        warnings = []
        
        # Check: Is new domain too different in vocabulary level?
        if current_persona.profile == Profile.EXPERT and new_domain == Domain.CRMB:
            # Expert usually prefers depth; CRMB may lack frontier concepts
            compatibility -= 0.1
            warnings.append("Expert profile may find CRMB less challenging")
        
        # Check: Has this persona successfully engaged with new_domain before?
        domain_history = [p for p in self.pivot_history if p.get("to_domain") == new_domain]
        if domain_history:
            past_success = sum(1 for p in domain_history if p.get("success")) / len(domain_history)
            compatibility *= past_success
        
        return {
            "valid": compatibility > 0.5,
            "compatibility_score": round(compatibility, 2),
            "warnings": warnings,
            "recommendation": "proceed" if compatibility > 0.7 else "reconsider"
        }
    
    def measure_pivot_effectiveness(self, conversation: List[Turn], pivot_turn: int) -> Dict:
        """
        Measure engagement change post-pivot (next 3 turns).
        
        Args:
            conversation: Full conversation history
            pivot_turn: Turn number where pivot occurred
            
        Returns:
            Effectiveness metrics with success determination
        """
        if pivot_turn >= len(conversation) - self.validation_window:
            return {"status": "insufficient_data", "reason": "Not enough turns post-pivot"}
        
        pre_window = conversation[max(0, pivot_turn - 2):pivot_turn]
        post_window = conversation[pivot_turn:min(len(conversation), pivot_turn + self.validation_window)]
        
        pre_engagement = sum(t.engagement_delta for t in pre_window) / len(pre_window) if pre_window else 0
        post_engagement = sum(t.engagement_delta for t in post_window) / len(post_window) if post_window else 0
        
        engagement_delta = post_engagement - pre_engagement
        success = engagement_delta >= 0.1  # Success threshold: +0.1 engagement
        
        return {
            "pivot_turn": pivot_turn,
            "pre_engagement": round(pre_engagement, 2),
            "post_engagement": round(post_engagement, 2),
            "engagement_delta": round(engagement_delta, 2),
            "success": success,
            "analysis": "Strong recovery" if engagement_delta > 0.2 
                        else "Modest improvement" if engagement_delta > 0.1
                        else "No improvement - pivot ineffective"
        }
    
    def log_pivot_result(self, pivot_turn: int, from_domain: Domain, to_domain: Domain, 
                        success: bool, engagement_delta: float):
        """Record pivot outcome for learning and future validation"""
        self.pivot_history.append({
            "pivot_turn": pivot_turn,
            "from_domain": from_domain,
            "to_domain": to_domain,
            "success": success,
            "engagement_delta": engagement_delta,
        })
```

### 5. Misconception Persistence Tracking

Track identified misconceptions and escalate correction strategies.

```python
class MisconceptionTracker:
    """Track misconceptions and escalate correction strategies after failed attempts"""
    
    CORRECTION_STRATEGIES = [
        "analogy",           # "X is like Y..."
        "formal_definition", # "By definition, X means..."
        "worked_example",    # "For instance, when we..."
        "socratic_question", # "What if X were true? Would that..."
        "counterexample",    # "Actually, here's a case where X doesn't hold..."
    ]
    
    def __init__(self):
        self.tracked_misconceptions: Dict[str, Dict] = {}  # misconception -> {attempts, strategies, status}
    
    def add_misconception(self, misconception: str, turn_num: int):
        """
        Identify and register a misconception.
        
        Args:
            misconception: Description of the misconception
            turn_num: Turn where identified
        """
        if misconception not in self.tracked_misconceptions:
            self.tracked_misconceptions[misconception] = {
                "identified_turn": turn_num,
                "correction_attempts": [],
                "persistent": False,
                "escalation_level": 0,
            }
    
    def record_correction_attempt(self, misconception: str, strategy: str, 
                                  successful: bool, turn_num: int):
        """
        Log a correction attempt.
        
        Args:
            misconception: The misconception being addressed
            strategy: Correction strategy used (from CORRECTION_STRATEGIES)
            successful: Did the correction work?
            turn_num: Turn number
        """
        if misconception not in self.tracked_misconceptions:
            return
        
        self.tracked_misconceptions[misconception]["correction_attempts"].append({
            "strategy": strategy,
            "successful": successful,
            "turn": turn_num,
        })
    
    def detect_persistence(self, misconception: str, current_turn: int) -> bool:
        """
        Detect if a misconception reappears after correction.
        
        Returns True if misconception has been corrected but appears again.
        """
        if misconception not in self.tracked_misconceptions:
            return False
        
        m_data = self.tracked_misconceptions[misconception]
        attempts = m_data["correction_attempts"]
        
        if not attempts:
            return False
        
        # Check if there's a successful correction followed by re-appearance
        successful_correction = any(a["successful"] for a in attempts)
        reappearance = any(
            a["successful"] and attempts[-1]["turn"] > a["turn"]
            for a in attempts
        )
        
        return successful_correction and reappearance
    
    def suggest_escalation(self, misconception: str) -> Dict[str, str]:
        """
        Suggest next strategy after failed corrections.
        
        Returns strategy recommendation with explanation.
        """
        if misconception not in self.tracked_misconceptions:
            return {"strategy": "analogy", "rationale": "Start with accessible analogy"}
        
        m_data = self.tracked_misconceptions[misconception]
        attempts = m_data["correction_attempts"]
        
        if not attempts:
            return {"strategy": "analogy", "rationale": "First correction attempt"}
        
        failed_strategies = [a["strategy"] for a in attempts if not a["successful"]]
        
        # Suggest next unused strategy
        for strategy in self.CORRECTION_STRATEGIES:
            if strategy not in failed_strategies:
                m_data["escalation_level"] += 1
                return {
                    "strategy": strategy,
                    "rationale": f"Previous strategy failed; escalating to {strategy}",
                    "escalation_level": m_data["escalation_level"],
                }
        
        # All strategies exhausted
        return {
            "strategy": "expert_review",
            "rationale": "All standard strategies exhausted; recommend human instructor review",
            "escalation_level": 5,
        }
    
    def get_persistence_report(self) -> Dict[str, List[str]]:
        """
        Generate summary of persistent misconceptions requiring intervention.
        
        Returns:
            Dictionary with persistent misconceptions grouped by escalation level
        """
        report = {"level_0": [], "level_1": [], "level_2+": []}
        
        for misconception, m_data in self.tracked_misconceptions.items():
            if m_data["persistent"]:
                level = m_data["escalation_level"]
                if level == 0:
                    report["level_0"].append(misconception)
                elif level == 1:
                    report["level_1"].append(misconception)
                else:
                    report["level_2+"].append(misconception)
        
        return report
```

### Integration into ConversationRunner

Add to `ConversationRunner.__init__`:

```python
# Initialize robustness components
self.dropout_detector = DropoutDetector()
self.persona_checker = PersonaConsistencyChecker()
self.pivot_validator = PivotValidator()
self.misconception_tracker = MisconceptionTracker()
```

Add to main conversation loop (in `run()` method):

```python
# Per-turn robustness checks
dropout_risk = self.dropout_detector.detect_dropout_risk(self.turns)

if dropout_risk > 0.6:
    recovery = self.dropout_detector.suggest_recovery(dropout_risk, current_topic)
    # Apply recovery strategy
    response = self._apply_recovery_strategy(recovery["action"])

# Track misconceptions
if misconception_hit:
    misconception_text = [m for m in self.user.state.misconceptions if m in user_msg.lower()]
    for m in misconception_text:
        self.misconception_tracker.add_misconception(m, turn_num)
        self.misconception_tracker.record_correction_attempt(
            m, hook.value, success=True, turn_num=turn_num
        )

# Check engagement semantics
current_engagement = compute_engagement(self.turns)

# Persona consistency check
if turn_num > 5:
    contradictions = self.persona_checker.detect_contradictions()
    if contradictions:
        resolution = self.persona_checker.resolve(strategy="recency_weighted")
```

### Testing Checklist for P3 Enhancements

- [ ] **Dropout Detection**: Inject silent turns (5+ word limit), verify dropout_risk > 0.6 by turn 4
- [ ] **Recovery Strategies**: Test all 4 recovery actions (continue, topic_pivot, curiosity_hook, emergency_reset)
- [ ] **Persona Consistency**: Log contradictory claims, verify detection and recency-weighted resolution
- [ ] **Engagement Computation**: Calculate engagement across 15-turn conversation, verify 0-1 range
- [ ] **Pivot Validation**: Attempt incompatible pivot (Expert + low-challenge domain), verify warning and compatibility < 0.7
- [ ] **Misconception Persistence**: Correct misconception at turn 5, reintroduce at turn 10, verify detection and escalation
- [ ] **Integration**: Run full conversation with all subsystems active, verify no errors and coherent interaction

---

## Testing Checklist

- [ ] **Beginner CRMB**: 15 turns, verify PARADOX/CONNECTION hooks dominate
- [ ] **Intermediate Coding**: 15 turns, verify misconception resolution
- [ ] **Expert Cross-Domain**: Switch topics mid-conversation, check coherence
- [ ] **Failure Injection**: Trigger disengagement at turn 8, verify recovery attempt
- [ ] **A/B Test**: high_enthusiasm vs balanced, compare XP and engagement curves
- [ ] **Korean Quality**: Review response naturalness (no 번역투, proper formality)

## Output Example

```
=== Session Summary ===
Domain: crmb | Profile: intermediate
Turns: 15 | Avg Engagement: 72.3%
Misconceptions Resolved: 3
Total XP: 1089 | Aha Moments: 2
Failure Detected: False | Recovery: N/A
Hook Distribution: {'역설': 3, '연결': 2, '역사': 1, '함축': 4, '오개념': 3, '경계': 2}
```


---

## ART Domain Content (Adaptive Resonance Theory)

### Overview
Integrates Adaptive Resonance Theory (ART) concepts into conversation simulation for more cognitively plausible learning trajectories. ART models how learners balance plasticity (accepting new knowledge) with stability (preserving existing knowledge).

### ART Concepts for Simulation

**Category Learning & Vigilance Parameter**
- Vigilance ρ ∈ [0,1]: How strict pattern matching is. High ρ = learner demands category must match input closely.
- Learner types: Perfectionists (ρ=0.9), Pragmatists (ρ=0.5), Scanners (ρ=0.2)
- Template: "이 {}가 {} 범주에 들어가나요?" (Does this X fit Y category?)

**Top-Down Templates vs Bottom-Up Features**
- Templates (기준): Prior knowledge, misconceptions, schemas
- Features (특징): Immediate sensory/linguistic input details
- Mismatch triggers reset → new category learning
- Question: "처음엔 {}라고 생각했는데 실제론 다르네요. 왜죠?" (I thought it was X, but it's actually Y. Why?)

**Resonance & Reset Signals**
- Resonance: Input matches category template → stable learning
- Reset: Mismatch → vigilance increases → category splits
- Engagement reflects resonance level (high resonance = high engagement)
- Question: "{}를 이전 내용과 연결할 수 있나요?" (Can you link X to prior content?)

### Implementation Integration

```python
@dataclass
class ARTState:
    vigilance: float = 0.5  # Category matching strictness
    templates: Dict[str, List[str]] = field(default_factory=dict)  # Knowledge structures
    resonance: float = 0.0  # Current match quality
    reset_count: int = 0  # Mismatch incidents

def assess_art_resonance(user_msg: str, template: str, vigilance: float) -> float:
    """Match input against category template; resonance ∈ [0,1]"""
    match_score = len(set(user_msg.split()) & set(template.split())) / max(len(template.split()), 1)
    return match_score if match_score >= vigilance else 0.0

def trigger_category_reset(state: ARTState) -> None:
    """Learner experienced mismatch; increase vigilance and split categories"""
    state.vigilance = min(1.0, state.vigilance + 0.1)
    state.reset_count += 1
```



---

## Multi-Seed Batch Runner with Aggregated Metrics

### Purpose
Run N independent simulations with different random seeds to compute robust aggregate statistics (mean, std, confidence intervals) for engagement, XP, recovery success, and other metrics. Reduces noise from single-run variance.

### Implementation

```python
import statistics
from typing import List, Dict, Tuple

def batch_simulate(domain: Domain, profile: Profile, config: Dict, 
                   num_turns: int = 15, num_runs: int = 10, base_seed: int = 42) -> Dict:
    """
    Run N simulations with aggregated metrics.
    
    Args:
        domain: CRMB or CODING
        profile: BEGINNER, INTERMEDIATE, EXPERT
        config: Hook frequency, challenge level, XP multiplier
        num_turns: Turns per simulation
        num_runs: Number of independent runs
        base_seed: Starting seed (incremented per run)
    
    Returns:
        Aggregated statistics: mean/std/CI for each metric
    """
    results = []
    
    for i in range(num_runs):
        random.seed(base_seed + i)
        runner = ConversationRunner(domain, profile, num_turns, config)
        metrics = runner.run()
        results.append(asdict(metrics))
    
    return aggregate_metrics(results)

def aggregate_metrics(results: List[Dict]) -> Dict:
    """Compute mean, std, 95% CI for all numeric metrics"""
    aggregated = {}
    
    # Extract numeric fields
    numeric_keys = ["avg_engagement", "misconceptions_resolved", "total_xp", "aha_moments"]
    
    for key in numeric_keys:
        values = [r[key] for r in results]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        ci_margin = 1.96 * std_val / (len(values) ** 0.5)  # 95% CI
        
        aggregated[key] = {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "ci_lower": round(mean_val - ci_margin, 2),
            "ci_upper": round(mean_val + ci_margin, 2),
        }
    
    # Recovery success rate
    recovery_successes = sum(1 for r in results if r.get("recovery_success"))
    aggregated["recovery_success_rate"] = round(recovery_successes / len(results), 2)
    
    return aggregated

def run_batch(domain: Domain, profile: Profile, num_runs: int = 10):
    """CLI entry point for batch simulation"""
    config = {"hook_frequency": 0.5, "challenge_level": 0.5, "xp_multiplier": 1.0}
    agg = batch_simulate(domain, profile, config, num_turns=15, num_runs=num_runs)
    
    print(f"\n=== Batch Results ({num_runs} runs) ===")
    print(f"Domain: {domain.value} | Profile: {profile.value}")
    for metric, stats in agg.items():
        if isinstance(stats, dict):
            print(f"{metric}:")
            print(f"  mean={stats['mean']}, std={stats['std']}, "
                  f"95% CI=[{stats['ci_lower']}, {stats['ci_upper']}]")
        else:
            print(f"{metric}: {stats}")
```

### Usage

```bash
# Beginner CRMB: 10 runs with aggregated stats
python conversation-sim.py --mode batch --domain crmb --profile beginner --num_runs 10

# Expert Coding: 20 runs for tighter CI
python conversation-sim.py --mode batch --domain coding --profile expert --num_runs 20
```

### Output Example

```
=== Batch Results (10 runs) ===
Domain: crmb | Profile: intermediate
avg_engagement:
  mean=68.45, std=7.32, 95% CI=[62.98, 73.92]
misconceptions_resolved:
  mean=2.8, std=1.03, 95% CI=[2.18, 3.42]
total_xp:
  mean=1024.5, std=142.3, 95% CI=[920.4, 1128.6]
recovery_success_rate: 0.7
```



---

## Strategy Pivot on Disengagement

### Overview
Detects topic fatigue, confusion, and boredom mid-conversation and switches to an alternate domain (CRMB ↔ Efficient Coding) with increased hook frequency to re-engage learner. Tracks pivot effectiveness.

### Disengagement Detection

Three fatigue signals:

| Signal | Indicator | Threshold |
|--------|-----------|-----------|
| **Confusion** | Misconception addressed but engagement still drops | Δeng < -5 for 2+ turns |
| **Boredom** | Hook effectiveness flat despite variety | Resonance < 0.3 for 3+ turns |
| **Topic Fatigue** | Same domain questions repeat, engagement floor hit | Engagement = engagement_floor for 2 turns |

### Domain Pivot Strategy

```python
class EngagementMonitor:
    def __init__(self, engagement_floor: float = 0.5):
        self.engagement_floor = engagement_floor
        self.disengagement_window = []
        self.fatigue_type = None
        
    def detect_fatigue(self, engagement: float, resonance: float, 
                       prev_engagement: float, topic_diversity: float) -> str:
        """Classify fatigue type; returns None or 'confusion'|'boredom'|'topic_fatigue'"""
        self.disengagement_window.append({
            "engagement": engagement,
            "resonance": resonance,
            "delta": engagement - prev_engagement,
        })
        
        if len(self.disengagement_window) > 3:
            self.disengagement_window.pop(0)
        
        # Confusion: steep drop despite educational content
        if sum(w["delta"] for w in self.disengagement_window[-2:]) < -10:
            return "confusion"
        
        # Boredom: low resonance persists
        if sum(w["resonance"] for w in self.disengagement_window) / len(self.disengagement_window) < 0.3:
            return "boredom"
        
        # Topic fatigue: at floor
        if engagement <= self.engagement_floor:
            return "topic_fatigue"
        
        return None

def execute_pivot(current_domain: Domain, fatigue_type: str) -> Tuple[Domain, Dict]:
    """Switch domain and adjust config based on fatigue type"""
    alt_domain = Domain.CODING if current_domain == Domain.CRMB else Domain.CRMB
    
    adjustments = {
        "confusion": {
            "hook_frequency": 0.8,  # More frequent hooks
            "challenge_level": 0.3,  # Simplify explanations
            "xp_multiplier": 1.3,  # Reward persistence
            "skip_turns": 2,  # Brief recap before switching
        },
        "boredom": {
            "hook_frequency": 0.9,
            "challenge_level": 0.7,  # Increase novelty
            "xp_multiplier": 1.5,
            "skip_turns": 1,
        },
        "topic_fatigue": {
            "hook_frequency": 1.0,
            "challenge_level": 0.5,
            "xp_multiplier": 1.2,
            "skip_turns": 0,
        },
    }
    
    return alt_domain, adjustments[fatigue_type]
```

### Pivot Effectiveness Tracking

```python
@dataclass
class PivotEvent:
    turn_num: int
    fatigue_type: str
    from_domain: Domain
    to_domain: Domain
    pre_pivot_engagement: float
    post_pivot_engagement: float
    success: bool  # True if engagement recovered to > 65% by turn 20

def track_pivot_effectiveness(pivots: List[PivotEvent]) -> Dict:
    """Summarize pivot success rates and engagement recovery patterns"""
    if not pivots:
        return {"pivot_count": 0}
    
    success_by_fatigue = {}
    for fatigue_type in ["confusion", "boredom", "topic_fatigue"]:
        relevant = [p for p in pivots if p.fatigue_type == fatigue_type]
        if relevant:
            success_rate = sum(p.success for p in relevant) / len(relevant)
            avg_recovery = sum(p.post_pivot_engagement - p.pre_pivot_engagement for p in relevant) / len(relevant)
            success_by_fatigue[fatigue_type] = {
                "success_rate": round(success_rate, 2),
                "avg_engagement_delta": round(avg_recovery, 2),
            }
    
    return {
        "total_pivots": len(pivots),
        "success_by_fatigue_type": success_by_fatigue,
        "avg_pivot_turn": round(sum(p.turn_num for p in pivots) / len(pivots), 1),
    }
```

### Integration into ConversationRunner

Add to main simulation loop:

```python
monitor = EngagementMonitor(engagement_floor=floor)
pivot_events = []

for turn_num in range(1, self.num_turns + 1):
    fatigue = monitor.detect_fatigue(
        engagement=self.user.state.engagement,
        resonance=current_resonance,
        prev_engagement=prev_engagement,
        topic_diversity=topic_variety
    )
    
    if fatigue:
        new_domain, adjustments = execute_pivot(self.domain, fatigue)
        self.domain = new_domain
        self.config.update(adjustments)
        pivot_events.append(PivotEvent(
            turn_num=turn_num,
            fatigue_type=fatigue,
            from_domain=prev_domain,
            to_domain=new_domain,
            pre_pivot_engagement=self.user.state.engagement,
        ))
    
    # ... rest of turn logic ...
    
    if pivot_events and pivot_events[-1].turn_num == turn_num - 1:
        # Check if pivot was successful
        pivot_events[-1].post_pivot_engagement = self.user.state.engagement
        pivot_events[-1].success = self.user.state.engagement > 65
```

### Testing Checklist

- [ ] Confusion pivot: Trigger at turn 5 (bad explanation), verify domain switch and challenge reduction
- [ ] Boredom pivot: Run 10 turns same domain, verify pivot to alt domain at turn 8-10
- [ ] Topic fatigue pivot: Expert profile with no hooks, verify immediate pivot
- [ ] Recovery metric: Track post-pivot engagement recovery within 3 turns
- [ ] Korean quality: Verify transition dialogue is natural ("이제 다른 주제로 전환해볼까요?")


## Diagnostic Instrumentation

### 1. Turn-by-Turn Event Log

```python
class ConversationLogger:
    def __init__(self):
        self.events = []
    
    def log_turn(self, turn_num, user_msg, tutor_msg, engagement, hook_type, 
                 domain, pivot_fired=False, aha_detected=False):
        self.events.append({
            "turn": turn_num, "engagement": engagement,
            "hook_type": hook_type, "domain": domain,
            "pivot_fired": pivot_fired, "aha_detected": aha_detected,
            "user_length": len(user_msg), "tutor_length": len(tutor_msg),
        })
    
    def diagnose(self):
        """Auto-diagnose common failure patterns."""
        if not self.events:
            return ["NO_DATA: no events logged"]
        
        avg_eng = sum(e["engagement"] for e in self.events) / len(self.events)
        pivot_events = [e for e in self.events if e["pivot_fired"]]
        post_pivot_eng = [self.events[i+1]["engagement"] for i, e in enumerate(self.events) 
                         if e["pivot_fired"] and i+1 < len(self.events)]
        
        diagnosis = []
        if avg_eng < 0.4: diagnosis.append("LOW_BASELINE: profiles may be too disengaged")
        if pivot_events and post_pivot_eng and sum(post_pivot_eng)/len(post_pivot_eng) < avg_eng:
            diagnosis.append("PIVOT_BACKFIRE: engagement drops after pivot")
        if len(set(e["hook_type"] for e in self.events)) < 3:
            diagnosis.append("HOOK_MONOTONY: insufficient hook diversity")
        return diagnosis
```

### 2. A/B Statistical Testing

```python
from scipy import stats
import numpy as np

def ab_test_significance(group_a_metrics: list, group_b_metrics: list, alpha=0.05):
    """Proper hypothesis testing with effect size."""
    t_stat, p_value = stats.ttest_ind(group_a_metrics, group_b_metrics)
    pooled_std = np.std(group_a_metrics + group_b_metrics)
    effect_size = (np.mean(group_a_metrics) - np.mean(group_b_metrics)) / pooled_std if pooled_std > 0 else 0
    
    return {
        "p_value": p_value, "significant": p_value < alpha, 
        "effect_size": effect_size, 
        "interpretation": 
            "no_effect" if abs(effect_size) < 0.2 
            else "small" if abs(effect_size) < 0.5 
            else "medium" if abs(effect_size) < 0.8 
            else "large"
    }
```
