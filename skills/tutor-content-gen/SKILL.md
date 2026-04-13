---
name: tutor-content-gen
description: >
  Educational content generator for the CSNL scientific RAG tutoring system.
  Creates structured explanations, Q&A pairs, quizzes, concept maps, and adaptive
  learning modules from scientific papers and knowledge base content. Supports
  Korean and English bilingual output with difficulty scaling (undergraduate to PhD).
  This is the core content production skill for the RAG tutor.
  MANDATORY TRIGGERS: Any request involving creating educational content from papers,
  generating explanations of scientific concepts, making quizzes, creating study
  materials, tutoring content generation, Q&A pair creation, concept map generation,
  learning module design, "explain this paper to students", "make a quiz about X",
  "generate flashcards", "create a study guide", "what should students know about X",
  or any content destined for the tutoring interface. Also trigger when the user
  mentions "posting" or "content" for the tutor system.
---

# Tutor Content Generator

You generate high-quality educational content from scientific sources for the CSNL RAG
tutoring system. Every piece of content you create must be traceable to source documents
and calibrated to the target audience's level.

## Core Principle: Source Grounding

Every claim in generated content MUST be traceable to a source document. The tutor's
credibility depends on this. Never generate ungrounded explanations.

```
Source Paper → Structured Extraction (paper-processor) → Content Generation → Verification → Output
```

## Content Types

### 1. Conceptual Explanation (가장 기본 / Most Common)

Structure:
```markdown
## [Concept Name] / [개념명]

### One-Sentence Summary
[English] / [Korean]

### Core Explanation
[2-3 paragraphs, calibrated to difficulty level]

### Key Terms
- **Term 1**: Definition [Source: Author, Year]
- **Term 2**: Definition [Source: Author, Year]

### Visual Analogy
[Relatable metaphor or analogy for the concept]

### Connection to Other Concepts
- Related to: [Concept A] (how)
- Builds on: [Concept B] (how)
- Leads to: [Concept C] (how)

### Sources
[List of papers this explanation draws from]
```

Generation template:
```python
EXPLANATION_PROMPT = """You are creating an educational explanation for a {difficulty} level
student studying cognitive/systems neuroscience.

Topic: {topic}
Source material:
{retrieved_context}

Requirements:
1. Every factual claim must come from the source material
2. Use [Author, Year] inline citations
3. Difficulty level: {difficulty}
   - undergraduate: Define all technical terms, use analogies
   - master: Assume basic neuroscience knowledge, focus on mechanisms
   - phd: Assume deep background, focus on nuances and open questions
4. Language: {language}
5. Include at least one concrete example from a real experiment

Generate the explanation following this structure:
{structure_template}
"""
```

### 2. Q&A Pairs (튜터 대화 엔진용)

For feeding the conversation engine:

```python
QA_GENERATION_PROMPT = """Generate {n} question-answer pairs from the following paper content.

Source: {paper_title} ({year})
Content:
{paper_sections}

Requirements:
- Questions should test genuine understanding, not just recall
- Include the specific section/page the answer comes from
- Vary question types: factual, conceptual, application, analysis
- For each Q&A pair, provide:
  - question (in {language})
  - answer (in {language})
  - difficulty: undergraduate | master | phd
  - question_type: factual | conceptual | application | analysis | comparison
  - source_section: which part of the paper
  - key_terms: concepts the student needs to know

Output as JSON array.
"""
```

Output schema:
```json
[
  {
    "question": "Why does visual working memory capacity plateau at approximately 3-4 items?",
    "question_ko": "시각적 작업 기억 용량이 약 3-4개 항목에서 정체하는 이유는 무엇인가?",
    "answer": "According to Luck & Vogel (1997) and Cowan (2001), the capacity limit reflects a fixed number of discrete 'slots' in VWM...",
    "answer_ko": "Luck & Vogel (1997)과 Cowan (2001)에 따르면, 용량 한계는 VWM의 이산적 '슬롯'의 고정된 수를 반영합니다...",
    "difficulty": "undergraduate",
    "question_type": "conceptual",
    "source_section": "introduction",
    "source_paper": "luck_vogel1997",
    "key_terms": ["visual working memory", "capacity limit", "slot model", "K estimate"]
  }
]
```

### 3. Multiple Choice Quiz

```python
QUIZ_PROMPT = """Create a {n}-question multiple choice quiz on: {topic}

Source material:
{retrieved_context}

Requirements:
- Each question has 4 options (A, B, C, D)
- Exactly one correct answer
- Distractors should be plausible but wrong (common misconceptions preferred)
- Include explanation for why correct answer is correct AND why each distractor is wrong
- Bilingual: provide question and options in both English and Korean
- Difficulty: {difficulty}

Output format (JSON):
{{
  "quiz_title": "...",
  "questions": [
    {{
      "q_en": "...",
      "q_ko": "...",
      "options": {{
        "A": {{"en": "...", "ko": "..."}},
        "B": {{"en": "...", "ko": "..."}},
        "C": {{"en": "...", "ko": "..."}},
        "D": {{"en": "...", "ko": "..."}}
      }},
      "correct": "B",
      "explanation_en": "B is correct because... A is wrong because... C is wrong because... D is wrong because...",
      "explanation_ko": "...",
      "source": "Author (Year), Section X"
    }}
  ]
}}
"""
```

### 4. Concept Map (개념 맵)

For visualizing relationships between concepts:

```python
CONCEPT_MAP_PROMPT = """Analyze the following papers and extract a concept map.

Papers:
{paper_summaries}

Generate a concept map with:
- nodes: key concepts (with brief definition)
- edges: relationships between concepts (labeled with relationship type)

Relationship types: "causes", "correlates_with", "is_component_of", "contradicts",
"extends", "measures", "models", "is_example_of"

Output as JSON:
{{
  "nodes": [
    {{"id": "vwm_capacity", "label": "VWM Capacity", "definition": "...", "papers": ["cowan2001"]}}
  ],
  "edges": [
    {{"from": "set_size", "to": "vwm_capacity", "relationship": "measures", "evidence": "..."}}
  ]
}}
"""
```

This JSON can then be rendered by sci-viz as an interactive network diagram.

### 5. Study Guide / Reading Guide

```python
STUDY_GUIDE_PROMPT = """Create a study guide for reading: {paper_title}

The student is at {difficulty} level.

Pre-reading:
- What background knowledge is needed?
- Key terms to know before reading
- Guiding questions to keep in mind

During reading:
- Section-by-section focus points
- What to pay attention to in figures
- Common points of confusion

Post-reading:
- Summary of main contributions
- How this connects to the broader field
- Critical evaluation questions
- Suggested follow-up readings
"""
```

## Difficulty Calibration

| Level | Language | Assumed Knowledge | Focus |
|---|---|---|---|
| Undergraduate | Simple, analogies | Basic bio/psych | What & why |
| Master | Technical, precise | Core neuroscience | How & mechanisms |
| PhD | Nuanced, critical | Deep domain expertise | Limitations, open questions, methods details |

## Bilingual Generation Strategy

For Korean + English parallel content:

1. **Generate in primary language first** (usually English for scientific content)
2. **Translate with domain awareness** — scientific terms often stay in English even in Korean text
3. **Verify key terms** — maintain a terminology glossary (영한 용어집):

```python
TERM_GLOSSARY = {
    "visual working memory": "시각적 작업 기억",
    "set size": "세트 크기",
    "change detection": "변화 탐지",
    "capacity limit": "용량 한계",
    "slot model": "슬롯 모델",
    "resource model": "자원 모델",
    "BOLD signal": "BOLD 신호",
    "retinotopic map": "망막위상 지도",
    "psychometric function": "심리측정 함수",
    "orientation tuning": "방향 튜닝",
    # ... extend as needed
}
```

## Quality Checks (Self-Verification)

Before outputting any content, verify:

1. **Source grounding**: Every factual claim has a citation
2. **Difficulty match**: Language complexity matches target level
3. **Bilingual consistency**: Korean and English versions convey same information
4. **No hallucination**: Cross-check claims against provided source material
5. **Pedagogical value**: Content teaches, not just informs

### Quality Checklist (Concrete Verification Steps)

Run this checklist before finalizing ANY generated content:

```python
def verify_content_quality(content: dict, source_docs: list) -> dict:
    """Concrete quality gate — returns pass/fail with reasons."""
    issues = []
    
    # 1. Source grounding: every [Author, Year] must exist in source_docs
    citations = re.findall(r'\[([A-Z][a-z]+(?:\s+(?:&|and)\s+[A-Z][a-z]+)?,\s*\d{4})\]', content['text'])
    known_refs = {f"{d['authors']}, {d['year']}" for d in source_docs}
    for cite in citations:
        if cite not in known_refs:
            issues.append(f"UNGROUNDED CITATION: [{cite}] not in source docs")
    
    # 2. Difficulty calibration check
    from textstat import flesch_kincaid_grade
    grade = flesch_kincaid_grade(content['text_en'])
    expected = {'undergraduate': (10, 14), 'master': (14, 18), 'phd': (16, 22)}
    low, high = expected.get(content['difficulty'], (10, 22))
    if grade < low or grade > high:
        issues.append(f"DIFFICULTY MISMATCH: Grade {grade:.1f}, expected {low}-{high} for {content['difficulty']}")
    
    # 3. Bilingual term consistency
    for en_term, ko_term in TERM_GLOSSARY.items():
        if en_term.lower() in content['text_en'].lower():
            if ko_term not in content['text_ko']:
                issues.append(f"TERM INCONSISTENCY: '{en_term}' in EN but '{ko_term}' missing in KO")
    
    # 4. Retrieval failure guard
    if len(source_docs) < 3:
        issues.append("INSUFFICIENT SOURCES: <3 source docs. Halt and request more papers.")
    
    return {
        'pass': len(issues) == 0,
        'issues': issues,
        'citation_count': len(citations),
        'readability_grade': grade if 'grade' in dir() else None
    }
```

**If retrieval returns fewer than 3 relevant chunks**: HALT content generation. 
Ask the user to add more papers to the knowledge base rather than generating 
ungrounded content. Never fabricate to fill gaps.

## Integration Points

- **paper-processor**: Provides structured paper data as input
- **rag-pipeline**: Retrieves relevant context for content generation
- **eval-runner**: Evaluates content quality (factuality, clarity, difficulty calibration)
- **sci-viz**: Renders concept maps and explanatory figures
- **Notion MCP**: Publish generated content to lab knowledge base
- **Zotero MCP**: Link content back to source papers
