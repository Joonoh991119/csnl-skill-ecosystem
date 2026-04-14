# Conversation Simulator — Prompt 3 Evaluation (Robustness/Edge Cases)

## Test Scenarios

### Test 1: User Dropout Mid-Conversation Edge Case
**Input Query:** "Simulate beginner user with 15 scheduled turns; user drops out after turn 7. Verify engagement score collapse detection and recovery attempt logging."

**Evaluation Criteria:**
- Does FailureDetector identify sudden engagement drop (e.g., turn 7-8 delta > 20%)?
- Does the simulation log dropout event with timestamp and turn number?
- Does the session metrics reflect incomplete conversation (7/15 turns)?
- Can the system quantify engagement loss at dropout point?

**Expected Findings:** Dropout should trigger FailureDetector warning; session should be marked as incomplete with recovery attempt documented.

---

### Test 2: Contradictory User Persona Edge Case
**Input Query:** "Create user profile with contradictory settings: vocabulary_level=beginner (1000 words) but question_depth=expert (synthesis questions). Simulate conversation and observe behavior."

**Evaluation Criteria:**
- Does the system detect contradictory persona parameters at initialization?
- How does ExpertiseEstimator handle mismatch (beginner vocab, expert questions)?
- Does the tutor adjust scaffolding (simplify vocabulary? defer complex questions?)?
- Are contradictions logged for session review?

**Expected Findings:** Contradiction should trigger warning; system should default to conservative (beginner) assumptions or request clarification.

---

### Test 3: Engagement Score Collapse
**Input Query:** "Run intermediate profile conversation with hook_frequency=0.8, track engagement per turn. Inject repeated boredom signals (negative hook feedback). Verify engagement collapses and measure."

**Evaluation Criteria:**
- Does engagement_delta accumulate correctly (additive or multiplicative across turns)?
- At what engagement level does FailureDetector trigger re-engagement intervention?
- Does engagement score ever go negative (or saturate at 0)?
- Can recovery interventions restore engagement (measure recovery trajectory)?

**Expected Findings:** Engagement collapse should be measurable (e.g., 100% → 20% over 3-5 turns); recovery should take 2-4 turns with correct intervention.

---

### Test 4: Strategy Pivot Failure (Hook Type Mismatch)
**Input Query:** "Expert profile prefers FRONTIER hooks (cutting-edge topics). Simulate conversation where CuriosityModulator uses PARADOX hooks instead (wrong type). Measure engagement penalty."

**Evaluation Criteria:**
- Does ExpertiseEstimator track hook preference by profile (FRONTIER for expert)?
- If wrong hook used, does engagement drop?
- How large is the penalty (5%, 10%, 20%)?
- Does CuriosityModulator detect mismatch and correct in next turn?

**Expected Findings:** Wrong hook type should reduce engagement; self-correction should occur by turn N+1; expert-level engagement floor should apply (≥75%).

---

### Test 5: Misconception Not Addressed (Persistence)
**Input Query:** "Beginner profile: introduce misconception 'X=Y'. User feedback indicates misconception not resolved. Simulate turn N+1 without addressing. Verify engagement penalty and logging."

**Evaluation Criteria:**
- Does FailureDetector identify unresolved misconception in feedback?
- Is the same misconception tracked across turns (persistence data)?
- What is the engagement penalty for repeated misconception?
- Does the system force address in turn N+2, or allow repeated failure?

**Expected Findings:** Unresolved misconceptions should accumulate; repeated failures should trigger intervention; penalty should increase with repetition.

---

### Test 6: Context Drift Across Domain Switch
**Input Query:** "Run CRMB conversation (ART, resonance) for 5 turns, then abruptly switch to Efficient Coding domain (sparse coding). Measure coherence drop."

**Evaluation Criteria:**
- Does context tracking maintain prior turns in session history?
- When domain switches, is prior context retained or lost?
- What is coherence score before/after switch?
- Does tutor acknowledge the switch (e.g., 'Let's now explore efficient coding in parallel')?

**Expected Findings:** Coherence should drop 20-40% on abrupt switch; system should recognize and bridge domains; recovery turn N+3.

---

### Test 7: Spaced Repetition Failure (Review Timing)
**Input Query:** "Simulate expert profile over 3 sessions (day 1, day 5, day 30). Track if SpacedRepetition scheduler proposes review at optimal delays. If delays wrong, measure retention loss."

**Evaluation Criteria:**
- Does SpacedRepetition track session intervals (1 day, 5 days, 30 days)?
- Are review windows calculated correctly (proposed at D, 3D, 7D, etc.)?
- If review comes too early (day 2 instead of day 5), is retention loss measured?
- Can the system recover from mistimed reviews (retry at corrected interval)?

**Expected Findings:** Correct spacing should maximize retention; mistimed reviews should show measurable loss; system should auto-correct next interval.

---

## Findings

### Strengths Observed
- **Comprehensive Failure Mode Taxonomy (Section 1):** Boredom, confusion, frustration, context drift identified as distinct failure modes with different intervention strategies.
- **Multi-Module Architecture:** CuriosityModulator, ExpertiseEstimator, FailureDetector, SpacedRepetition, Gamification provide independent failure points and recovery paths.
- **User Profile Abstraction:** Beginner/intermediate/expert profiles with vocabulary, question depth, misconceptions, and engagement floor provide realistic variance for edge case testing.
- **Metrics Tracking:** SessionMetrics (avg_engagement, hook_distribution, misconceptions_resolved, xp, streaks, aha_moments) enable detailed post-hoc analysis.

### Gaps & Robustness Risks
- **Dropout Handling Unspecified:** No definition of dropout detection threshold (e.g., >5 seconds without response?); recovery attempt strategy not documented.
- **Contradictory Persona Validation Missing:** System doesn't validate profile consistency at initialization; conflicts between vocabulary_level and question_depth could cause tutor malfunction.
- **Engagement Score Semantics Unclear:** Is engagement additive, multiplicative, or time-decayed? Does it saturate (0-100)? Can it go negative? No specification.
- **Hook Type Matching Algorithm Missing:** ExpertiseEstimator has hook preference mapping, but no algorithm for "select hook matching profile" or penalty for mismatch.
- **Misconception Tracking Incomplete:** collect_misconceptions() identified but not implemented; no graph of misconception relationships or persistence across turns.
- **Context Drift Metric Undefined:** "Coherence drop" mentioned but not quantified; no specification of coherence scoring (embedding similarity? entity continuity?).
- **SpacedRepetition Integration Stubbed:** Framework mentioned but no concrete implementation of review scheduling or timing validation.

### Failure Mode Coverage
✓ Boredom: Easy hook repetition → engagement spike (conceptually clear)  
⚠ Confusion: Complex explanation without scaffolding → dropout (no scaffolding algorithm)  
⚠ Frustration: Unresolved misconception → mini-failures (tracking incomplete)  
⚠ Context Drift: Abrupt domain switch → coherence drop (metric undefined)  

### Edge Case Robustness
**Dropout Detection:** ❌ Threshold undefined (response latency? turn absence?)  
**Contradictory Profiles:** ❌ No validation logic  
**Engagement Collapse:** ⚠ Accumulation semantics unclear  
**Hook Type Mismatch:** ⚠ Penalty defined informally ("might reduce engagement")  
**Misconception Persistence:** ⚠ Tracking incomplete  
**Context Drift Recovery:** ❌ Coherence metric undefined  
**Spaced Repetition Timing:** ❌ No implementation  

### Implicit Assumptions (Risks)
- Engagement score is 0-100 and monotonic (unclear if multi-modal possible)
- All failure modes are independent (no cascade effects)
- Recovery is always possible (no "hard failure" state)
- User profiles don't change mid-conversation (dynamic profile updates not handled)
- A/B test configs are orthogonal (no interaction effects between hook_frequency and challenge_level)

---

## Score: 3.5/5

### Justification
The skill provides **good conceptual framework for conversation simulation** with clear user profiles and failure mode taxonomy. However, **significant P3 robustness gaps** prevent higher score:

1. **Dropout Detection Unspecified (-0.5):** No threshold definition or recovery attempt algorithm; critical for real-world reliability.
2. **Engagement Score Semantics Missing (-0.4):** Accumulation rules, saturation behavior, and negative value handling not defined; could cause divergent results across test runs.
3. **Contradictory Persona Validation Missing (-0.3):** System allows conflicting profiles; could cause undefined behavior in ExpertiseEstimator or CuriosityModulator.
4. **Context Drift Metric Undefined (-0.3):** Coherence drop mentioned but not quantified; impossible to validate recovery or measure impact.
5. **Misconception Tracking Incomplete (-0.25):** No persistence mechanism; impossible to test edge cases with repeated misconceptions.
6. **SpacedRepetition Not Implemented (-0.25):** Only mentioned in metrics; no timing validation or recovery testing possible.

### Integration Readiness
**For CRMB_tutor v2:** Skill is **60% ready** for production testing. Implementation tasks:
1. Define engagement score semantics: 0-100 scale, additive per-turn deltas, floor by profile (40%, 60%, 75%), saturation at 0 and 100.
2. Implement dropout detection: latency threshold (e.g., >30 sec no response) + turn skip detection; log dropout with recovery attempt.
3. Add persona validation: check vocabulary_level ≤ question_depth; flag contradictions; use conservative defaults if conflict.
4. Define coherence metric: embedding similarity between consecutive turns (target 0.7-0.9; drop to 0.3-0.5 on domain switch).
5. Implement misconception tracking: graph of misconceptions per turn; accumulation rule (unresolved = +1 per turn); penalty function.
6. Implement SpacedRepetition: Leitner scheduler (review at 1D, 3D, 7D, 14D); validate timing; measure retention loss for mistimed reviews.

---

## Recommendations

### High Priority (Robustness Blockers)
1. **Engagement Score Specification:** Propose formal definition:
   - Range: [0, 100]
   - Per-turn delta: -20 to +15 (bounded to prevent whiplash)
   - Accumulation: `new_engagement = max(0, min(100, engagement + delta))`
   - Floor by profile: beginner ≥40, intermediate ≥60, expert ≥75
   - Document with examples: turn 1 (100) + negative hook (delta=-10) → turn 2 (90)
2. **Dropout Detection Algorithm:** Specify trigger conditions:
   - No response for >30 seconds → mark as dropout candidate
   - If turn skipped (turn N+1 never starts) → confirm dropout
   - Log: {timestamp, turn_num, engagement_at_dropout, reason}
   - Recovery: repeat last explanation with different hook type
3. **Persona Validation at Init:** Implement check:
   ```python
   assert vocabulary_level <= question_depth  # E.g., beginner vocab with expert questions invalid
   assert misconceptions >= 0
   assert engagement_floor in [40, 60, 75]
   ```

### Medium Priority (Quality Improvements)
4. **Misconception Persistence Tracking:** Create per-session graph:
   - Track introduced misconceptions: {turn_num, concept, description}
   - Mark resolved: {turn_num_resolved, explanation}
   - Accumulation: unresolved_count += 1 per turn if not addressed
   - Penalty: engagement -= 2 * unresolved_count per turn
5. **Hook Type Matching Algorithm:** Formalize selection:
   - Profile → preferred_hook_types mapping (FRONTIER for expert, PARADOX for beginner)
   - Random selection weighted by profile preference: 70% preferred, 30% alternatives
   - Mismatch penalty: engagement -= 5 if wrong type used
   - Self-correction: next turn attempts preferred type
6. **Context Drift Coherence Metric:** Define as embedding similarity:
   - Turn N embedding vs Turn N+1 embedding (use sentence-transformers)
   - Within-domain coherence target: 0.7-0.9
   - Cross-domain coherence target: 0.3-0.5 initially (should recover to 0.6+ by turn N+3)
   - Measure recovery trajectory and penalize slow recovery

### Low Priority (Polish)
7. **A/B Test Interaction Analysis:** Verify configs are orthogonal:
   - Run high_enthusiasm + balanced combinations
   - Measure interactions between hook_frequency and challenge_level
   - Identify synergies or conflicts
8. **Dynamic Profile Updates:** Allow profile.vulnerability to increase with failed intervention attempts:
   - Track intervention success rate per user
   - Update profile priors for future sessions
9. **Multi-Domain Conversation Validation:** Generate CRMB + Efficient Coding conversations in same session:
   - Measure coherence loss on domain switch
   - Validate bridge concepts (sparse coding ↔ ART) are used for context preservation

### Testing Checklist for P3 Readiness
- [ ] Dropout detection triggers at latency threshold (>30 sec) and logs recovery attempt
- [ ] Contradictory profiles rejected at init with specific error message
- [ ] Engagement score stays in [0, 100] after all operations (no out-of-bounds)
- [ ] Engagement floor enforced for each profile (beginner >40, etc.)
- [ ] Hook type mismatch identified; penalty applied; correction attempted next turn
- [ ] Misconceptions tracked across turns; unresolved count incremented; penalty applied
- [ ] Context drift detected on domain switch; coherence drops 20-40%; recovery by turn N+3
- [ ] Spaced repetition review timing validated (±1 day tolerance); retention loss measured if mistimed
- [ ] A/B test configs (high_enthusiasm, balanced, adaptive) produce different engagement curves
- [ ] SessionMetrics accurately summarizes: total turns, avg engagement, hook distribution, misconceptions resolved, xp, streaks, aha moments
- [ ] Edge case sessions complete without crashes (dropout, contradictory profile, domain switch, misconception loop)

---

**Robustness Status:** ⚠ Partial (framework present; edge case handling incomplete)  
**Dropout Handling:** ❌ Unimplemented (threshold and recovery missing)  
**Persona Validation:** ❌ Missing (contradictory profiles allowed)  
**Engagement Score:** ⚠ Semantics unclear (accumulation and saturation undefined)  
**Hook Type Matching:** ⚠ Informal (preference mapping present; selection algorithm missing)  
**Misconception Tracking:** ⚠ Framework only (persistence mechanism missing)  
**Context Coherence:** ❌ Metric undefined (concept referenced but not measured)  
**SpacedRepetition:** ❌ Not implemented (mentioned in metrics only)  
**Failure Recovery:** ⚠ Partial (FailureDetector present; intervention logic incomplete)
