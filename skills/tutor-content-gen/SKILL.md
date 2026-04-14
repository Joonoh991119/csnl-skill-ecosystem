# tutor-content-gen: Socratic Dialogue Generation for Neuroscience RAG Tutoring

Skill for generating contextually-grounded, publication-aligned Socratic dialogues in neuroscience education. Integrates with the CRMB (Computational Research Methods in Behavioral Neuroscience) source material corpus to ensure mechanistic accuracy and prevent hallucination.

## Core Purpose

Generate Socratic teaching dialogues that:
- Build conceptual understanding through graduated questioning (Socratic method)
- Ground explanations strictly in specified source materials (CRMB corpus)
- Support multilingual instruction (Korean primary, English technical terms inline)
- Scaffold from learner's existing mental models to target concepts
- Mark source citations and uncertainty boundaries explicitly

## Socratic Dialogue Structure

### Three-Phase Scaffold Pattern

**Phase 1: Diagnostic (Establish baseline understanding)**
- Probe learner's existing knowledge with open-ended questions
- Identify misconceptions without judgment
- Document learner profile (background, prerequisites met/unmet)

**Phase 2: Guided Discovery (Build toward target concept)**
- Ask questions that surface contradictions or gaps
- Guide attention toward relevant source mechanisms
- Use analogy/contrast with known concepts
- Maintain dialogue naturalness (avoid question-dumping)

**Phase 3: Consolidation (Verify and extend understanding)**
- Ask learner to explain key mechanisms in own words
- Probe boundary conditions and edge cases
- Connect to broader conceptual networks
- Mark confidence level of learner grasp

### Example: Neural Network Fundamentals

```
Tutor: You mentioned understanding backpropagation. In a feedforward network, 
       how does the network "know" which direction to adjust weights during training?

Learner: It uses the error signal... I think?

Tutor: Yes—there's an error. But here's what puzzles me: if the network can 
       measure error at the output, how does that information flow backward 
       through the hidden layers? What would need to happen?

[Learner reasons through mechanisms...]

Tutor: Exactly. Now, Grossberg's ART networks also have a mismatch signal, 
       but it triggers a different response than backprop error. Can you anticipate 
       why ART might not want to propagate error the same way?
```

## Source Grounding: CRMB Citation Framework

### Required Citation Pattern

Every mechanistic claim must map to a source in the learner's available corpus:

```
[MECHANISM]: Claim about neural process or learning rule
[SOURCE]: Exact reference (author, year, section, page if available)
[CONFIDENCE]: HIGH (directly stated) | MEDIUM (inferred from context) | LOW (analogous/extrapolated)
[RISK]: Flags if this goes beyond source material
```

### Example: ART Vigilance Parameter

```
[MECHANISM]: "High vigilance (ρ) restricts acceptable prototypes, forcing formation of fine-grained categories"
[SOURCE]: Grossberg (1976, Adaptive Resonance Theory section); Carpenter & Grossberg (1987, Neural Networks 1(1): 17-88)
[CONFIDENCE]: HIGH
[RISK]: None—directly stated in foundational papers

[MECHANISM]: "Vigilance can model attention-driven category refinement in human learning"
[SOURCE]: Inferred extension from Grossberg's mismatch-driven reset property
[CONFIDENCE]: MEDIUM
[RISK]: Requires empirical validation; grounded in theory but not yet demonstrated in CRMB corpus
```

### Preventing Hallucination: Explicit Uncertainty

When a query asks for content NOT in the source corpus:

1. **State the boundary clearly**: "The CRMB papers discuss ART vigilance in the context of unsupervised learning. Your question about vigilance in supervised learning goes beyond the available sources."

2. **Offer grounded alternatives**: "I can explain how vigilance operates in the unsupervised setting and ask you questions that help you predict how it might behave under supervision."

3. **Flag gaps for future inquiry**: "This would be an interesting extension to test empirically against the core ART mechanisms."

## Multilingual Scaffolding (Korean/English)

### Language Blending Pattern

For learners with Korean as primary language:

```
Korean concept explanation → English technical term (inline) → 
Example in learner's familiar context → English from source material

Example:
"신경망이 학습할 때 가중치를 조정하는 방향을 결정하는 신호를 
'오류 신호 (error signal)'라고 부릅니다. 
Grossberg의 이론에서는 이것을 '부정합 신호 (mismatch signal)'이라고 하는데,
차이가 무엇일까요?"
```

### Code Pattern: Bilingual Dialogue Template

```python
def generate_socratic_dialogue(
    learner_profile: dict,
    target_concept: str,
    source_corpus: list,
    max_turns: int = 8,
    language_primary: str = "ko"
) -> dict:
    """
    Args:
        learner_profile: {
            "background": "graduate student, basic neural networks",
            "language_primary": "ko",
            "target_concept": "Adaptive Resonance Theory (ART)",
            "prerequisite_knowledge": ["backprop", "unsupervised learning"]
        }
        source_corpus: List of source texts (Grossberg, Carpenter & Grossberg, etc.)
        max_turns: Dialogue length target
        language_primary: Primary language for explanation ("ko" or "en")
    
    Returns:
        {
            "phases": {
                "diagnostic": [{"speaker": "Tutor", "text": "...", "citations": [...]}, ...],
                "guided_discovery": [...],
                "consolidation": [...]
            },
            "citations_used": [
                {"mechanism": "...", "source": "...", "confidence": "HIGH", "risk": None}
            ],
            "hallucination_risk_flags": []
        }
    """
    pass
```

## Topic-Specific Patterns

### Adaptive Resonance Theory (ART) Dialogues

**Prerequisite Knowledge Required:**
- Competitive learning (Kohonen, Rumelhart & Zipser)
- Unsupervised learning motivation
- Bottom-up and top-down weight distinction
- Pattern matching concepts

**Key Mechanisms to Scaffold (in order):**
1. **Bottom-up/Top-down Architecture**: Input → Feature detection layer → Category layer → Template matching
2. **Matching Rule**: Template-input similarity threshold (vigilance ρ)
3. **Resonance**: Bidirectional agreement between bottom-up input and top-down template
4. **Mismatch Detection**: When similarity < ρ, trigger search phase
5. **Category Learning**: Weight update rules during resonance
6. **Vigilance Parameter**: How to control category granularity

**Risk Zones (where hallucination commonly occurs):**
- Confusing ART's mismatch-driven reset with backprop error correction
- Assuming vigilance ρ is directly analogous to supervised learning thresholds
- Overgeneralizing ART principles to domains not covered in CRMB papers
- Mixing ART/1, ART/2, ART/3 mechanisms without explicit distinction

**Source Priority Order (for grounding):**
1. Grossberg foundational papers (1976+)
2. Carpenter & Grossberg (1987) — formal ART/1 and ART/2
3. Grossberg & Mingolla — neural correlates and predictions
4. Later theoretical extensions (with CONFIDENCE: MEDIUM and RISK flags)

## Output Format Requirements

### Dialogue JSON Schema

```json
{
  "skill_name": "tutor-content-gen",
  "dialogue": {
    "title": "Socratic Dialogue: ART and Category Learning",
    "learner_profile": {
      "background": "Graduate student, understands neural networks and unsupervised learning",
      "language_primary": "Korean (ko)",
      "technical_languages": ["English"],
      "prerequisites": ["backpropagation", "competitive learning", "Kohonen maps"]
    },
    "phases": {
      "phase_1_diagnostic": [
        {
          "turn": 1,
          "speaker": "Tutor",
          "language": "ko",
          "text": "신경망이 새로운 범주(category)를 학습할 때, 언제 기존 범주를 수정하고 언제 새로운 범주를 만들어야 할까요?",
          "intent": "diagnostic",
          "citations": []
        },
        {
          "turn": 2,
          "speaker": "Learner",
          "language": "ko",
          "text": "글쎄... 아마 데이터가 기존 범주와 비슷하면 수정하고, 너무 다르면 새로운 범주를 만드는 건가요?"
        }
      ],
      "phase_2_guided_discovery": [
        {
          "turn": 3,
          "speaker": "Tutor",
          "language": "ko",
          "text": "좋은 직관이에요. 그런데 '비슷하다'는 기준은 뭘까요? 누가 그 기준을 정하는 걸까요?",
          "intent": "probe_mechanism",
          "citations": []
        }
      ],
      "phase_3_consolidation": [
        {
          "turn": 7,
          "speaker": "Tutor",
          "language": "ko",
          "text": "좋아요. 그럼 이제 Grossberg의 '경계 매개변수 (vigilance parameter ρ)'를 다시 생각해보세요. 이게 무엇의 역할을 한다고 했죠?",
          "intent": "consolidate",
          "citations": [
            {
              "mechanism": "Vigilance parameter controls category acceptance threshold",
              "source": "Grossberg (1976); Carpenter & Grossberg (1987)",
              "confidence": "HIGH",
              "risk": "None"
            }
          ]
        }
      ]
    },
    "source_citations": [
      {
        "mechanism": "Mismatch-driven reset in ART",
        "source": "Carpenter & Grossberg (1987). 'A Massively Parallel Architecture for a Self-Organizing Neural Pattern Recognition Machine.' IEEE Transactions on Computers, C-37(11): 1356-1369.",
        "confidence": "HIGH",
        "risk": "None"
      },
      {
        "mechanism": "Vigilance parameter determines category granularity",
        "source": "Grossberg (1976). 'Adaptive Pattern Classification and Universal Recoding.' Biological Cybernetics, 23(3-4): 121-134.",
        "confidence": "HIGH",
        "risk": "None"
      }
    ],
    "hallucination_risk_assessment": {
      "total_turns": 8,
      "mechanisms_grounded": 6,
      "mechanisms_flagged": 2,
      "risk_flags": [
        {
          "turn": 5,
          "mechanism": "Extending ART vigilance to continuous learning scenarios",
          "source_coverage": "CRMB papers focus on discrete category formation. Continuous learning extension is inferred.",
          "risk_level": "MEDIUM",
          "recommendation": "Can pose as a question for learner to hypothesize, but must mark as beyond core CRMB material."
        }
      ]
    }
  }
}
```

## Validation Checklist

Before generating dialogue output:

- [ ] Learner prerequisites map to your scaffolding sequence
- [ ] Every mechanism claim has a source (or explicit RISK: flag)
- [ ] Citations are primary sources, not summaries
- [ ] Socratic questions outnumber declarative statements (goal: 60% questions)
- [ ] Dialogue maintains conversational flow (no question-dumping)
- [ ] Technical terms appear with translation on first use
- [ ] Phase transitions are natural (not abrupt)
- [ ] Consolidation asks learner to explain (not tutor)
- [ ] Hallucination risk zones are pre-flagged

## Best Practices

### Do
- Ask open-ended questions that surface misconceptions
- Cite source page numbers and sections when available
- Use learner's prior knowledge as anchor for new concepts
- Mark confidence levels and uncertainty boundaries
- Check if claim is in source corpus before asserting

### Don't
- Assume learner's background without diagnostic questioning
- State mechanistic claims without citing CRMB source
- Blurt out answers (let learner discover via guided questions)
- Mix languages without translation on first technical term use
- Extrapolate source material without explicit RISK flag

## Integration with RAG Pipeline

This skill assumes:
1. **Source Corpus Available**: CRMB papers are indexed in vector DB
2. **Retrieval Before Generation**: Query source corpus for relevant passages before dialogue generation
3. **Citation Linking**: Generate links to source text for learner verification
4. **Iterative Grounding**: After dialogue generation, run QA against source material to verify claims

## Multilingual Term Glossary (Korean/English)

| English | Korean | Domain | CRMB Source |
|---------|--------|--------|-------------|
| Adaptive Resonance Theory (ART) | 적응적 공명 이론 | Neural networks | Grossberg (1976+) |
| Vigilance parameter | 경계 매개변수 | ART mechanism | Carpenter & Grossberg (1987) |
| Mismatch signal | 부정합 신호 | ART matching | Carpenter & Grossberg (1987) |
| Bottom-up processing | 상향식 처리 | ART architecture | Grossberg & Mingolla |
| Top-down template | 하향식 템플릿 | ART architecture | Grossberg & Mingolla |
| Category learning | 범주 학습 | Unsupervised learning | Grossberg foundational |
| Resonance | 공명 | ART dynamics | Carpenter & Grossberg (1987) |
| Pattern matching | 패턴 매칭 | ART matching rule | Carpenter & Grossberg (1987) |

---
Last Updated: 2026-04-14
Version: 1.0
Author: CSNL Neuroscience Tutoring Ecosystem


## Hallucination Prevention Workflow

Before including any mechanistic claim in generated dialogue:

1. **Search CRMB Corpus for Supporting Passage**
   - Query vector DB with claim's key terms
   - Retrieve top-3 ranked passages
   - If no passage found or relevance < 0.7: proceed to step 2

2. **Verify Against Retrieved Chunks**
   - Cross-reference claim against passage verbatim
   - Check equation numbers, figure numbers, page references
   - If claim contradicts passage: REJECT claim, reframe as question
   - If claim extends passage: mark as [MEDIUM CONFIDENCE] with RISK flag

3. **Never Generate Mechanism Descriptions Outside Retrieved Chunks**
   - Do not synthesize new mechanistic details not explicitly grounded
   - If mechanism requires synthesis: pose as Socratic question instead
   - Example: Instead of "ART then does X," ask "What would happen if vigilance reset triggered a search phase?"

4. **Flag Unverified Claims**
   - Mark claim as [UNVERIFIED] in dialogue JSON
   - Add to `hallucination_risk_flags` array with source_coverage: "NOT FOUND"
   - Recommendation: "Rephrase as learner question or omit from this dialogue"

---

## Graduate-Level Scaffolding Strategy

For learners with foundational knowledge (e.g., backprop, basic NNs):

1. **Identify Prerequisite Concepts Learner Already Knows**
   - Diagnostic phase: explicitly ask learner to explain their mental model
   - Map learner's vocabulary to CRMB sources (e.g., "error signal" ↔ "mismatch signal")
   - Use this as anchor point for contrast

2. **Build via Contrastive Examples**
   - Ask: "In standard backprop, weight changes are driven by error. In ART, what plays that role?"
   - Highlight what ART does differently: unsupervised, bidirectional matching, vigilance-gated reset
   - Use learner's existing neural network intuitions to forecast ART behavior

3. **Progress Complexity Within Dialogue Turns**
   - Turn 1-2: Diagnostic questions grounded in learner's prerequisite knowledge
   - Turn 3-5: Introduce new mechanism, contrast with known concepts
   - Turn 6-8: Apply mechanism to novel scenarios, extend to edge cases
   - Each turn adds one new constraint or dimension (avoid cognitive overload)

---

## Corpus Boundary Definition

**Primary Source: CRMB Chapters 1-20**
- Grossberg foundational papers (1976, 1980, 1987, 1995)
- Carpenter & Grossberg (1987, 1991) — ART/1, ART/2, ART/3 formal definitions
- Grossberg & Mingolla — neural correlates and visual predictions
- All mechanistic claims in dialogue must cite chapter/section/page

**Secondary Source: Published Grossberg Papers**
- Extensions and applications (e.g., ARTMAP, ART in vision/motor)
- Mark as [SECONDARY SOURCE] in citations
- Use only if CRMB corpus does not cover topic

**Out-of-Scope: Anything Beyond These Boundaries**
- Speculative extensions without peer-reviewed grounding
- Claims from other labs' reinterpretations of ART
- Applications not documented in listed sources
- **Must explicitly flag with [OUT-OF-SCOPE] and RISK: HIGH**

---

## Translation Validation Protocol

For Korean/English bilingual dialogues:

1. **Preserve Mechanistic Specificity in Translation**
   - Verify Korean technical term maps to exact English equivalent in CRMB source
   - Example: "부정합 신호" must translate to "mismatch signal" (not "error signal" or "conflict")
   - If no direct Korean equivalent exists, inline English term with parenthetical explanation

2. **Validate Term Consistency Across Dialogue**
   - Same mechanism always uses same Korean term throughout
   - Check glossary table (Korean/English) against dialogue output
   - If term varies (e.g., "범주" vs "카테고리"): standardize to table entry

3. **Review Translation Against Source Material**
   - After dialogue generation, cross-check Korean translations against CRMB source passages
   - Ensure no mechanistic nuance lost in translation
   - Flag any translation ambiguities for tutor review before dialogue delivery

---
