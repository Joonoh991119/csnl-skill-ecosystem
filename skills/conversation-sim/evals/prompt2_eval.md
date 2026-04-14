# Evaluation: conversation-sim Skill Against EVAL PROMPT 2 (Stress Test)

**Evaluation Date:** 2026-04-14  
**Skill File:** `/tmp/csnl-skill-ecosystem/skills/conversation-sim/SKILL.md` (810 lines)  
**Prompt:** Diagnose why 50 simulated conversations with intermediate-level profiles and ART topics show: avg session length 8 turns (target 15), aha moments 0.3/session (target 1.5), hook effectiveness 35% (target 60%), students don't re-engage after pivot (p=0.67 for A/B test). Root cause analysis: simulation flaw (unrealistic profiles)? Hook quality issue? Pivot strategy failure?

---

## 1. Can the Skill Help Diagnose the Root Cause?

### Short Answer
**Partially, but with critical blind spots.** The skill provides a testing framework and metrics collection, but lacks diagnostic instrumentation to isolate root causes. It cannot distinguish between:
- Profile realism vs. hook design vs. pivot strategy failure
- Without detailed logging, the skill cannot pinpoint why the pivot fires but doesn't re-engage.

### What the Skill Can Diagnose

1. **Hook Effectiveness by Type (lines 329–372)**
   - The `_assess_hook_effectiveness()` method scores each hook 0–1 based on type and recency.
   - **Diagnostic Value:** You can observe which hook types achieve 35% effectiveness and which would target 60%.
   - **Limitation:** Scores are hardcoded (MISCONCEPTION=0.9, PARADOX=0.85, etc.). Does not measure *actual student resonance* during the simulation—only assigned scores.

2. **Engagement Tracking (lines 193–200, 310–322)**
   - `UserState.engagement` updates after each turn with `engagement_delta`.
   - The skill tracks engagement floor by profile (beginner 40%, intermediate 60%, expert 75%).
   - **Diagnostic Value:** Can verify if intermediate users stay above 60% floor. If they don't, disengagement is confirmed.
   - **Limitation:** Engagement updates are formula-based (`delta = hook_effectiveness * 5`). Doesn't capture why students say "그냥 원래 주제로 돌아가요" (just go back to the original topic).

3. **Failure Detection & Recovery (lines 382–391)**
   - `_attempt_recovery()` increases hook frequency when engagement < 50.
   - **Diagnostic Value:** Can see if recovery was attempted (true/false flag).
   - **Limitation:** Binary flag only. Does not log:
     - Which turn triggered recovery?
     - What was the re-engagement response?
     - Did the pivot *content* match the student's expectation?

4. **Session Metrics Aggregation (lines 393–412, Batch Runner section)**
   - The skill computes `avg_engagement`, `misconceptions_resolved`, `total_xp`, `aha_moments`, `hook_distribution`.
   - **Diagnostic Value:** Run 50 seeds and aggregate to reproduce the stress test results (mean=0.3 aha moments, etc.).
   - **Limitation:** Aggregate metrics hide individual turn-by-turn behavior. Cannot see *why* turn 4 pivot fails.

### What the Skill Cannot Diagnose

1. **Student Profile Realism**
   - The skill generates questions with templates (lines 259–293). No validation that intermediate student behavior is realistic.
   - **Missing:** A "profile fidelity check" that compares simulated question depth, vocabulary usage, and misconception patterns against real intermediate Korean student data.
   - **Impact:** Cannot distinguish "is this an unrealistic profile?" from "is this a poor hook?"

2. **Pivot Strategy Failure Root Cause**
   - The skill has no strategy pivot mechanism (yet—see prompt1_eval recommendation).
   - The `_attempt_recovery()` only increases hook frequency; it does NOT switch domain or explain *why* the student rejects the pivot.
   - **Missing:** Logging of post-pivot re-engagement attempts and rejection patterns.
   - **Impact:** Cannot diagnose whether "students say 그냥 원래 주제로 돌아가요" is because:
     - The pivot was poorly timed (too abrupt)?
     - The new domain was too disconnected?
     - The explanation quality dropped post-pivot?
     - The student needed a re-negotiation of goals, not a pivot?

3. **Hook Quality vs. Hook-Student Fit**
   - The skill assigns fixed effectiveness scores to hook types (MISCONCEPTION=0.9, PARADOX=0.85, etc.).
   - No A/B testing of *hook content*, only configuration parameters (hook_frequency, challenge_level).
   - **Missing:** Ability to test whether hook type X works for profile Y or whether the *wording* of hooks is the issue.
   - **Impact:** Stress test shows A/B test is insignificant (p=0.67). The skill cannot diagnose whether this is because:
     - Hook content is universally weak?
     - Hooks match profiles well but problem is elsewhere (engagement floor too high)?
     - Configuration parameters don't matter because hooks are ignored post-pivot?

---

## 2. Scoring: Diagnostic Power, Metric Interpretation, Actionability

### Diagnostic Power: 2/5

**Rationale:**
- Provides engagement tracking, hook distribution, recovery flags—surface-level diagnostics.
- **Cannot isolate root cause** because:
  1. No student model validation (is the intermediate profile realistic?).
  2. No pivot content logging (what exactly is rejected and why?).
  3. No post-pivot engagement curve (engagement at turns 4, 5, 6, 7... post-pivot).
  4. No hook-student interaction logging (did IMPLICATION work for this student?).
- The skill is a **metrics reporter**, not a **root-cause analyzer**.

**What it would take to move to 4/5:**
- Add detailed turn-by-turn logging: `[turn, engagement, hook_type, hook_content, student_response, resonance_score, misconception_hit, re_engagement_success]`.
- Add post-pivot state dump: `[pivot_turn, pre_engagement, post_engagement_delta_t1, post_engagement_delta_t5, rejection_reason]`.

### Metric Interpretation: 2/5

**Rationale:**
- The skill outputs metrics (avg_engagement, aha_moments, hook_effectiveness %) but provides **minimal guidance on what they mean**.
- The testing checklist (lines 474–482) only validates that runs work, not that results are meaningful.
- **Example failure:** Stress test shows hook_effectiveness=35%, target=60%. The skill outputs this number but doesn't explain:
  - Is 35% low because hooks are weak, or because students reached engagement floor and stopped listening?
  - Is the 60% target achievable for the given profile and domain?
  - Does hook_effectiveness correlate with aha_moments? (Stress test suggests no: p=0.67 A/B test.)

**What it would take to move to 4/5:**
- Add diagnostic heuristics:
  - If hook_effectiveness is low AND recovery_success is low → "Pivot strategy failure."
  - If aha_moments are low AND misconceptions_resolved are high → "Hook quality issue: addressing misconceptions but not triggering insight."
  - If avg_engagement stays above floor → "Profile fidelity issue: engagement not dipping despite low hooks."
- Compute correlation matrices (hook_type vs aha_moments, engagement vs hook_effectiveness, etc.) to surface confounds.

### Actionability: 1/5

**Rationale:**
- The skill cannot directly answer the stress test questions:
  1. "Is this a simulation flaw (unrealistic user profiles)?" → **Cannot test.** No profile validation tool.
  2. "Is this a hook quality issue?" → **Cannot isolate.** Hook scores are fixed; would need A/B test of hook *content*, not configuration.
  3. "Is this a pivot strategy failure?" → **Cannot diagnose.** No detailed logging of pivot mechanics or rejection patterns.
- To use the skill for diagnosis, a developer would need to:
  1. Add extensive logging (~100 lines).
  2. Write post-hoc analysis scripts (~200 lines) to compare observed vs. expected correlations.
  3. Manually inspect turn-by-turn logs to find patterns.
- **Current state:** The skill is a black box. You run it, get metrics, but cannot answer "why?"

**What it would take to move to 4/5:**
- Add a `DiagnosticReport` class that generates a text report:
  ```
  === Diagnostic Report ===
  Stress Test Results:
  - avg_session_length=8 (target=15) → FAIL
  - aha_moments=0.3 (target=1.5) → FAIL
  - hook_effectiveness=35% (target=60%) → FAIL
  
  Root Cause Hypothesis:
  1. Pivot Strategy Failure (60% confidence)
     Evidence: Recovery flagged TRUE in 70% of runs, but re_engagement_success=FALSE in 65%.
     Implication: Pivot is triggered but ineffective.
  
  2. Hook Quality Issue (25% confidence)
     Evidence: hook_effectiveness low across all types. MISCONCEPTION (target 90%) averaging 45%.
     Implication: Hook content/timing weak, not configuration.
  
  3. Profile Realism (15% confidence)
     Evidence: Engagement floor (60%) rarely violated. All users stay engaged "artificially."
     Implication: Intermediate profile too robust; should fail more naturally.
  
  Recommended Debugging:
  - Log post-pivot engagement curve (turns 4–8). If flat/declining, pivot failed.
  - Compare hook effectiveness with real student data from pilot (if available).
  - Interview students: Did they understand the pivot explanation? Did it feel forced?
  ```
- Add methods to compute these confidence scores from raw metrics.

---

## 3. Gaps and Concrete Improvements

### Critical Gaps for Stress Test Diagnosis

#### Gap 1: No Turn-by-Turn Logging
**Problem:**
- The skill computes final metrics but discards intermediate turn data in logs.
- Cannot observe: "At what turn does engagement drop below 60? Does it recover post-pivot (turn 4)?"

**Recommendation:**
- Modify `Turn` dataclass (line 161) to include:
  ```python
  @dataclass
  class Turn:
      turn_num: int
      engagement_pre: float  # ADD
      engagement_post: float  # ADD
      resonance: float  # ADD
      hook_effectiveness_actual: float  # ADD (vs. fixed score)
      student_rejection: bool  # ADD
      re_engagement_success: bool  # ADD
  ```
- Write turn logs to JSON file for post-hoc analysis.
- **Implementation Scope:** ~30 lines.

#### Gap 2: No Profile Validation
**Problem:**
- Intermediate profile is hardcoded (lines 228–233). No check for realism against real student data.
- Stress test cannot answer "Is the profile unrealistic?"

**Recommendation:**
- Add a `ProfileValidator` class:
  ```python
  class ProfileValidator:
      def compare_to_baseline(profile: Profile, baseline_path: str) -> Dict:
          """Compare simulated vocabulary, question depth, misconceptions to real data."""
          baseline = load_baseline(baseline_path)
          return {
              "vocabulary_drift": abs(profile.vocab - baseline.vocab) / baseline.vocab,
              "depth_mismatch": abs(profile.depth - baseline.depth),
              "misconception_realism": similarity(profile.misconceptions, baseline.misconceptions),
          }
  ```
- Require `--baseline-profile <path>` flag for stress testing.
- Report validation results before running simulations.
- **Implementation Scope:** ~50 lines.

#### Gap 3: No Pivot Content Logging
**Problem:**
- Recovery is attempted (lines 382–391), but what was communicated to the student? Was it clear? Realistic?
- The skill modifies config (hook_frequency, challenge_level) but doesn't log what the student sees.

**Recommendation:**
- Add a `PivotLog` to track:
  ```python
  @dataclass
  class PivotEvent:
      turn_num: int
      fatigue_type: str
      pivot_explanation: str  # What was told to student
      engagement_pre: float
      engagement_post: float  # At turns 5, 6, 7 (post-pivot window)
      student_rejection: bool
      rejection_reason: str  # "Wrong topic", "Too simple", "Not explained", etc.
  ```
- During recovery, generate and log actual pivot dialogue (e.g., "이제 다른 주제로 전환해볼까요? 같은 원리를 다른 맥락에서...").
- **Implementation Scope:** ~40 lines.

#### Gap 4: No Hook-Student Interaction Model
**Problem:**
- Hook effectiveness is assigned statically (MISCONCEPTION=0.9) but doesn't depend on student state.
- A/B test shows p=0.67 (no significance). The skill cannot diagnose why.

**Recommendation:**
- Modify `_assess_hook_effectiveness()` (lines 359–372) to model fit:
  ```python
  def _assess_hook_effectiveness(self, hook: HookType, turn_num: int, 
                                 student_state: UserState) -> float:
      base_score = {...}  # As before
      
      # Hook-student fit: does this hook match student's curiosity profile?
      fit_bonus = 0.0
      if hook in student_state.preferred_hooks:
          fit_bonus = 0.15
      elif hook_conflicts_with_misconception(hook, student_state):
          fit_bonus = -0.10  # Hook ineffective if student doesn't see the misconception
      
      return max(0.0, base_score * recency_factor + fit_bonus)
  ```
- Track "hook hits" (effectiveness > 0.7) vs. "hook misses" for each student.
- This allows A/B test to compare hook_frequency against hook_fit.
- **Implementation Scope:** ~50 lines.

#### Gap 5: No Engagement Recovery Curve Analysis
**Problem:**
- Recovery is binary (success/fail). But intermediate metrics matter: engagement at turns 5, 6, 7?
- Stress test students don't re-engage. Is it immediate (turn 5) or delayed (turn 7)?

**Recommendation:**
- Add `engagement_trajectory` post-pivot:
  ```python
  @dataclass
  class SessionMetrics:
      # ... existing fields ...
      engagement_post_pivot_t0: float  # Turn 4 (pivot turn)
      engagement_post_pivot_t1: float  # Turn 5
      engagement_post_pivot_t3: float  # Turn 7
      re_engagement_latency: int  # Turns until recovery > 65%
      re_engagement_slope: float  # (eng_t7 - eng_t5) / 2: recovery rate
  ```
- Compute aggregate statistics: mean re-engagement latency, % that recover by turn 7, etc.
- This directly diagnoses: "Pivot is tried but recovery takes too long / never happens."
- **Implementation Scope:** ~30 lines.

#### Gap 6: No Hypothesis Testing for A/B Significance
**Problem:**
- Stress test reports p=0.67 for high_enthusiasm vs. balanced configs.
- The skill does not guide interpretation: "Is p=0.67 because configs are equivalent, or because the metric is noisy?"

**Recommendation:**
- Add statistical tests:
  ```python
  from scipy import stats
  
  def compare_configs(config_a_runs: List[SessionMetrics], 
                      config_b_runs: List[SessionMetrics]) -> Dict:
      eng_a = [r.avg_engagement for r in config_a_runs]
      eng_b = [r.avg_engagement for r in config_b_runs]
      
      t_stat, p_value = stats.ttest_ind(eng_a, eng_b)
      effect_size = (mean(eng_a) - mean(eng_b)) / std(eng_a + eng_b)
      
      if p_value > 0.05:
          confidence = "configs statistically equivalent"
      else:
          confidence = f"config_a better (effect size={effect_size:.2f})"
      
      return {"p_value": p_value, "confidence": confidence}
  ```
- Add interpretation guidance: if p > 0.05, the issue is not configuration—look elsewhere (hooks, profile, pivot).
- **Implementation Scope:** ~30 lines + scipy dependency.

### Secondary Gaps

7. **No Student Rejection Simulation**
   - The skill doesn't model student saying "그냥 원래 주제로 돌아가요."
   - Students always engage with tutor responses (no rejection logic).
   - Recommendation: Add a `student_rejection_probability()` function based on:
     - Hook surprise factor (surprise > 0.8 → higher rejection).
     - Context match (pivot explanation clarity).
     - Engagement floor (if floor is high, less likely to reject).

8. **No Domain Switch Cost**
   - If the skill ever implements pivot (domain switch), switching CRMB ↔ Coding should have a cognitive cost (turn to re-orient).
   - Currently no such penalty.
   - Recommendation: Add `re_orientation_cost = 2 turns of -10% engagement` when pivoting domains.

9. **No Misconception Depth Tracking**
   - Skill tracks "misconceptions_resolved" (count) but not severity.
   - A misconception about osmosis vs. enzyme kinetics may require different hooks.
   - Recommendation: Assign severity levels to misconceptions; track which hooks resolve severe vs. minor misconceptions.

---

## 4. Summary Table

| Criterion | Score | Reason |
|-----------|-------|--------|
| **Diagnostic Power** | 2/5 | Tracks metrics but cannot isolate root cause. No turn-by-turn logging or pivot diagnostics. |
| **Metric Interpretation** | 2/5 | Outputs raw metrics without guidance on causation. No correlation analysis. |
| **Actionability** | 1/5 | Cannot directly answer stress test questions. Requires extensive post-hoc analysis. |
| **Logging Depth** | 2/5 | Only final session metrics. No turn-level or event-level logging. |
| **Profile Validation** | 1/5 | No tool to validate intermediate profile realism. Hardcoded assumptions. |
| **Pivot Mechanism** | 0/5 | No strategy pivot implemented (see prompt1_eval). Cannot test pivot failure. |
| **Statistical Rigor** | 1/5 | Reports aggregates but no hypothesis testing or significance interpretation. |
| **Overall** | 1.3/5 | Skill is a simulator, not a diagnostic tool. Cannot answer stress test questions without major augmentation. |

---

## 5. Prioritized Improvements to Enable Stress Test Diagnosis

### Phase 1: Logging (Est. 60 lines) — **Must Have**
1. Add turn-by-turn logging (engagement_pre, engagement_post, resonance, student_rejection).
2. Write logs to JSON file for each run.
3. **Payoff:** Can replay simulations and see exactly when/why engagement drops.

### Phase 2: Profile Validation (Est. 50 lines) — **Critical**
1. Add `ProfileValidator` to compare against baseline real student data.
2. Report profile drift metrics before stress test.
3. **Payoff:** Can rule out "is the profile unrealistic?"

### Phase 3: Pivot Event Logging (Est. 40 lines) — **Critical**
1. Track pivot explanations, post-pivot engagement curve (turns 4–7), student rejection.
2. Compute re-engagement latency and slope.
3. **Payoff:** Can diagnose whether "pivot is attempted but fails" or "pivot is never accepted."

### Phase 4: Hook-Student Interaction (Est. 50 lines) — **Important**
1. Make hook effectiveness dependent on student state (preferred hooks, misconception awareness).
2. Track hook hits vs. misses per student.
3. **Payoff:** Can diagnose "is hook quality universal problem or student-specific fit issue?"

### Phase 5: Statistical Analysis (Est. 30 lines) — **Important**
1. Add t-tests and effect size computation for A/B test results.
2. Provide interpretation guidance (equivalent vs. significant difference).
3. **Payoff:** Stress test p=0.67 result is interpreted as "configs are equivalent; problem elsewhere."

### Phase 6: Diagnostic Report Generator (Est. 100 lines) — **Nice to Have**
1. Synthesize Phases 1–5 into a structured report with hypothesis confidence scores.
2. Recommend next debugging steps.
3. **Payoff:** Automation of the root-cause analysis workflow.

---

## 6. Root Cause Hypotheses for Stress Test (Given Current Skill)

Based on the skill design, here are plausible root causes for the stress test failure:

### Hypothesis 1: Pivot Strategy Failure (50% confidence)
**Evidence from Skill:**
- Recovery mechanism exists but only adjusts hook_frequency and challenge_level (lines 382–391).
- No domain pivot mechanism (gap—see prompt1_eval).
- **Implication:** When engagement dips, tutor tries more hooks but stays in same domain. Students feel repetition, say "그냥 원래 주제로 돌아가요."

**How to Test:**
- Implement domain pivot, re-run stress test, check if aha_moments > 1.5.

### Hypothesis 2: Hook Quality Issue (30% confidence)
**Evidence from Skill:**
- Hook effectiveness is hardcoded (MISCONCEPTION=0.9, etc.), not learned.
- A/B test compares configurations, not hook content. Both configs use same hook pool.
- Stress test: p=0.67 suggests configurations don't matter → problem is hook design itself, not frequency.
- **Implication:** The 6 hook types (PARADOX, CONNECTION, HISTORY, IMPLICATION, MISCONCEPTION, FRONTIER) may not resonate with Korean intermediate learners on ART topics.

**How to Test:**
- Collect pilot data: which hooks trigger aha moments in real conversations?
- Update skill with empirical hook effectiveness scores.
- Re-run stress test.

### Hypothesis 3: Profile Realism Issue (15% confidence)
**Evidence from Skill:**
- Intermediate profile has engagement floor = 60% (line 255), vocabulary = 4000 words (line 232).
- Stress test shows avg_engagement = 8 turns, aha_moments = 0.3. If floor is 60%, why isn't engagement higher?
- **Implication:** Either (a) profile's floor is too generous and doesn't match real students, or (b) students are declining engagement despite high floor (which means problem is hooks/pivot, not profile).

**How to Test:**
- Compare simulated vocabulary, question depth, misconceptions against real intermediate Korean student logs.
- If match is poor, adjust profile; re-run.
- If match is good, rule out this hypothesis.

### Hypothesis 4: Engagement Floor Too High (5% confidence)
**Evidence from Skill:**
- Intermediate floor = 60% (line 255). If students stay engaged artificially, hooks may seem to work when they don't.
- **Implication:** Stress test results (aha_moments=0.3) may be artificially suppressed because engagement never drops enough to trigger natural disengagement.

**How to Test:**
- Lower engagement floor to 40%, re-run stress test, check if aha_moments increase or if failure patterns emerge.

---

## 7. Conclusion

**Can the skill help diagnose the root cause of the stress test?**
- **Short answer:** No, not as-is. It provides a framework but lacks diagnostic instrumentation.

**What would enable diagnosis?**
- Turn-by-turn logging (Phase 1).
- Pivot event tracking (Phase 3).
- Profile validation (Phase 2).
- Statistical interpretation guidance (Phase 5).

**Estimated effort to full diagnostic capability:** ~250 lines of code + analysis scripts (6–8 hours for a developer familiar with the skill).

**Immediate next step:** Implement Phase 1 (logging) and Phase 2 (profile validation). With those, you can manually inspect logs and rule out hypothesis #3 (profile realism) within 2 hours.

**Longer-term:** Once domain pivot is implemented (from prompt1_eval recommendation), add Phases 3–5 to enable full automated root-cause analysis.
