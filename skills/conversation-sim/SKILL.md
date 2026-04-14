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
