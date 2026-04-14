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
