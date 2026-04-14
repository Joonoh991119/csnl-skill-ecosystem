---
name: sci-post-gen
description: Generate bilingual (Korean/English) scientific educational posts for CRMB (Conscious Mind, Resonant Brain) and Efficient Coding domains. Supports blog posts, social media threads, newsletters, and academic summaries with mandatory source grounding, citation verification, and Quarto rendering. Triggers on CRMB concepts (ART, BCS/FCS, LAMINART), Efficient Coding papers (Barlow, Olshausen, sparse/population coding), cross-domain connections, and post format requests.
---

# Scientific Post Generation v2 (sci-post-gen)

## Overview

The sci-post-gen skill generates peer-reviewed, source-grounded scientific educational content in Korean (primary) with inline English terminology. Built for the CRMB_tutor v2 session, this skill handles two knowledge domains:

- **CRMB Domain**: Grossberg's Conscious Mind, Resonant Brain theory (ART, BCS/FCS, LAMINART)
- **Efficient Coding Domain**: Barlow, Olshausen, sparse coding, population coding frameworks

Every claim is anchored to chapter/paper citations; hallucination prevention and Korean naturalness checks ensure quality.

## Core Features

### 1. Post Templates

Four template formats address different audience needs:

#### Blog Post Template
```markdown
---
title: "[KO Title]"
author: "CRMB_tutor v2"
date: YYYY-MM-DD
categories: [CRMB|EfficientCoding|Cross-Domain]
lang: ko
---

## 도입 (Introduction)
[Korean text with inline English terms]

## 핵심 개념 (Key Concepts)
- **개념1**: [설명] (Reference: CRMB Ch.X or Paper Y)
- **개념2**: [설명] (Reference: CRMB Ch.X or Paper Y)

## 연결고리 (Connections)
[Cross-domain links if applicable]

## 결론 (Conclusion)
[Synthesis with citations]

## 참고문헌 (References)
```

#### Social Media Thread Template
```
[Post 1/N] [Korean text + #hashtags]
Reference: CRMB Ch.X

[Post 2/N] [Follow-up concept]
Reference: Paper Y

[Post N/N] [Synthesis + call-to-action]
```

#### Newsletter Template
```
제목: [Title]
기간: [Period]

헤드라인 (Headline): [1-2 sentences, hook]
기사 (Article): [300-500 words, bilingual, citations]
팀 노트 (Team Note): [Internal reflection]
참고 (References): [Full citations]
```

#### Academic Summary Template
```
제목: [Formal Korean + English]
요약: [Structured abstract format]
배경: [Prior work with citations]
주요 발견: [Key findings or theorems]
응용: [Practical applications]
한계: [Limitations and open questions]
```

### 2. Two-Domain Handling Strategy

#### Domain Detection
```python
def detect_domain(query: str) -> List[str]:
    crmb_keywords = {
        'ART', 'Adaptive Resonance Theory',
        'BCS', 'Biased Competition',
        'FCS', 'Feature Contour System',
        'LAMINART', '3D LAMINART',
        'resonance', 'binding', 'attention',
        '어댑티브', '공명', '양극화'
    }
    
    ec_keywords = {
        'sparse coding', 'population coding',
        'Barlow', 'Olshausen',
        'redundancy reduction', 'efficient representation',
        '휴지 부호화', '모집단 부호화'
    }
    
    domains = []
    if any(kw.lower() in query.lower() for kw in crmb_keywords):
        domains.append('CRMB')
    if any(kw.lower() in query.lower() for kw in ec_keywords):
        domains.append('EfficientCoding')
    if len(domains) == 2:
        domains.append('CrossDomain')
    
    return domains if domains else ['General']
```

#### Cross-Domain Connection Examples
- **ART ↔ Sparse Coding**: Both address pattern recognition under noisy conditions; ART uses vigilance thresholds, sparse coding uses sparsity constraints
- **BCS/FCS ↔ Population Coding**: Both represent information across populations of neurons; FCS uses distributed feature signals
- **LAMINART ↔ Efficient Representations**: Laminar cortical circuits optimize hierarchical feature compression

### 3. Source Grounding & Hallucination Prevention

#### Mandatory Citation Format
```python
class Citation:
    def __init__(self, source_type: str, identifier: str, page: int = None):
        self.source_type = source_type  # 'CRMB_Chapter' | 'Paper' | 'Textbook'
        self.identifier = identifier    # e.g., "Grossberg_CRMB_Ch3" or "Olshausen_Nature_2003"
        self.page = page
    
    def to_string(self) -> str:
        base = f"{self.source_type}: {self.identifier}"
        return f"{base} (p.{self.page})" if self.page else base

# Every claim requires one of:
claim = "ART uses vigilance thresholds to prevent match suppression."
citations = [Citation('CRMB_Chapter', 'Grossberg_CRMB_Ch3_ART', page=125)]

# Pre-generate ALLOWED_CLAIMS from corpus
ALLOWED_CLAIMS = {
    "ART vigilance": Citation('CRMB_Chapter', 'Grossberg_CRMB_Ch3', 125),
    "BCS bottom-up": Citation('CRMB_Chapter', 'Grossberg_CRMB_Ch4', 187),
    "sparse coding efficiency": Citation('Paper', 'Olshausen_Nature_2003', 47),
}
```

#### Verification Checklist
```python
def verify_post(post: str, citations: List[Citation]) -> Dict[str, bool]:
    return {
        'has_citations': len(citations) > 0,
        'citations_valid': all(validate_citation(c) for c in citations),
        'no_hedging': 'probably' not in post and 'might' not in post,
        'domain_consistent': len(post.split()) > 100,  # Sufficient depth
        'korean_natural': korean_grammar_check(post),  # See quality checks
    }
```

### 4. Bilingual Generation (Korean Primary)

#### TERM_GLOSSARY (Consistency)
```yaml
# Maintain across all posts
CRMB_Terms:
  Adaptive Resonance Theory: 적응 공명 이론 (ART)
  Vigilance: 경계 (vigilance threshold)
  Match Suppression: 부호 억제
  Biased Competition: 편향된 경쟁 (BCS)
  Feature Contour: 특징 윤곽 (FCS)
  Binding: 결합 (binding problem)
  
EfficientCoding_Terms:
  Sparse Coding: 휴지 부호화 (sparse coding)
  Population Coding: 모집단 부호화
  Redundancy Reduction: 중복성 감소
  Receptive Field: 수용장 (receptive field)
  Selectivity: 선택성
```

#### Generation Pattern
```python
def generate_bilingual_sentence(concept: str, domain: str) -> str:
    korean = get_korean_text(concept, domain)
    english_terms = extract_inline_terms(korean)
    
    # Example output:
    # "ART (적응 공명 이론)는 경계(vigilance) 메커니즘을 통해..."
    return f"{korean} ({english_terms})"

# Post generation maintains Korean as primary with English parentheticals
```

### 5. Visual Integration

#### Figure Reference Scheme
When to invoke the sci-viz skill:

```python
def identify_figure_needs(post_content: str) -> List[FigureRequest]:
    requests = []
    
    if 'ART architecture' in post_content or 'network' in post_content:
        requests.append(FigureRequest(
            type='architecture_diagram',
            domain='CRMB',
            components=['STM', 'LTM', 'reset_signal'],
            format='quarto_include'
        ))
    
    if 'sparse coding' in post_content or 'basis' in post_content:
        requests.append(FigureRequest(
            type='concept_diagram',
            domain='EfficientCoding',
            elements=['signal', 'basis_set', 'weights'],
            format='svg_inline'
        ))
    
    return requests

# Equation rendering via Quarto math:
# Inline: $V = \sum_{i} w_i \phi_i$
# Display:
# $$V = \sum_{i} w_i \phi_i(x)$$
```

### 6. Quality Checks Pipeline

```python
class QualityScorer:
    def readability(self, text: str) -> float:
        """Flesch-Kincaid grade level (target: 10-12)"""
        words = len(text.split())
        sentences = text.count('।')
        syllables = sum(count_korean_syllables(w) for w in text.split())
        return (0.39 * words/sentences + 11.8 * syllables/words - 15.59)
    
    def citation_density(self, citations: List[Citation]) -> float:
        """Citations per 500 words"""
        return (len(citations) / (len(text.split()) / 500))
    
    def korean_naturalness(self, text: str) -> float:
        """Grammar scoring via morphological analysis"""
        # Check for natural conjunction use, particle agreement, etc.
        issues = validate_korean_grammar(text)
        return 1.0 - (len(issues) / len(text.split()))
    
    def coherence(self, post: str) -> float:
        """Semantic continuity check"""
        sentences = text.split('।')
        return average_semantic_similarity(sentences)
    
    def score_overall(self, post: Post) -> Dict[str, float]:
        return {
            'readability': self.readability(post.content),
            'citations': self.citation_density(post.citations),
            'korean_quality': self.korean_naturalness(post.content),
            'coherence': self.coherence(post.content),
            'composite': np.mean([...]),  # Weighted average
        }
    
    def suggest_improvements(self, scores: Dict) -> List[str]:
        suggestions = []
        if scores['readability'] < 9:
            suggestions.append("Simplify sentence structure")
        if scores['citations'] < 0.02:
            suggestions.append("Add more source citations")
        if scores['korean_quality'] < 0.90:
            suggestions.append("Review Korean grammar")
        return suggestions
```

### 7. Quarto Integration

The project uses Quarto for rendering. Posts are generated as `.qmd` files:

```yaml
# _quarto.yml references
project:
  type: website
  output-dir: _output

website:
  title: "CRMB_tutor v2 Posts"
  navbar:
    left:
      - text: "CRMB Posts"
        href: posts/crmb/
      - text: "Efficient Coding"
        href: posts/efficient-coding/

format:
  html:
    theme: cosmo
    code-fold: true
```

#### Post Generation for Quarto
```python
def generate_quarto_post(post_data: PostData) -> str:
    qmd = f"""---
title: "{post_data.title_ko}"
subtitle: "{post_data.title_en}"
author: "CRMB_tutor v2"
date: {post_data.date}
categories: {post_data.categories}
image: {post_data.image_path if post_data.image_path else 'featured.png'}
lang: ko
execute:
  echo: false
---

{post_data.content}

## 참고문헌
"""
    for citation in post_data.citations:
        qmd += f"\n- {citation.to_string()}"
    
    return qmd

# Render locally:
# quarto render posts/crmb/2026-04-14-art-vigilance.qmd
# Outputs to _output/posts/crmb/2026-04-14-art-vigilance.html
```

## Usage Workflow

1. **Trigger Recognition**: User mentions CRMB concept, Efficient Coding paper, or post format
2. **Domain Detection**: Classify as CRMB, EfficientCoding, or CrossDomain
3. **Template Selection**: Choose blog/social/newsletter/academic based on context
4. **Source Verification**: Look up citations in ALLOWED_CLAIMS and corpus
5. **Content Generation**: Generate Korean primary text with inline English terms
6. **Visual Planning**: Identify figures via sci-viz skill if needed
7. **Quality Scoring**: Run QualityScorer and suggest improvements
8. **Quarto Rendering**: Output as .qmd file for project integration

## Dependencies

- CRMB source: Grossberg's "Conscious Mind, Resonant Brain" (chapter references)
- EC papers: Barlow (1961), Olshausen & Field (2003, Nature)
- sci-viz skill: For architecture diagrams and concept visualizations
- Quarto: For rendering and publishing
- Korean language tools: For grammar validation and naturalness checking

## Success Criteria

- ✓ Zero hallucinated claims (100% citation coverage)
- ✓ Bilingual coherence (Korean primary, English consistent)
- ✓ Readability score 10-12 grade level
- ✓ Citation density ≥ 2 per 500 words
- ✓ Korean grammatical accuracy > 95%
- ✓ Quarto renders without errors


## Worked Example: ART ↔ Sparse Coding Blog Post

**Complete end-to-end walkthrough** demonstrating cross-domain composition:

1. **Domain Detection**
   - Input: "ART and sparse coding" → detects two computational neuroscience domains
   - ART → CRMB domain (Carpenter & Grossberg)
   - Sparse coding → efficient_coding domain (Olshausen & Field)
   - Classification: cross-domain composition required

2. **Template & Structure**
   - Selected: `blog_post_template` with cross-domain bridge section
   - Outline: (1) Intro, (2) ART basics, (3) Sparse coding basics, (4) Unified bridge, (5) Conclusion
   - Word budget: ~2000 words split 400/400/400/500/300

3. **Citation Placement**
   - ART section: Carpenter & Grossberg (CRMB Ch.3), Grossberg 1987
   - Sparse coding section: Olshausen & Field 1996, Lewicki & Sejnowski 2000
   - Bridge: Srinivasan et al. 2000 (efficient coding theory unifies both)

4. **Equation Embedding**
   - Inline for intuitive equations: "$\rho \leq 0.5$" (similarity threshold)
   - Display for key derivations: "$$J(\theta) = \|x - D\theta\|_2^2 + \lambda\|\theta\|_1$$" (sparse coding objective)
   - Quarto: wrap in `$...$` (inline) or `$$...$$` (display)

5. **Figure Request to sci-viz Skill**
   ```
   "Generate orientation tuning curve comparing ART selectivity vs sparse coding basis functions. 
   Style: publication-quality. Format: SVG. Caption: Figure 1: ART weight matrix selectivity 
   vs learned sparse basis for natural image patches."
   ```

6. **Quarto Output** (.qmd)
   ```markdown
   ---
   title: "Bridging ART and Sparse Coding"
   author: "sci-post-gen"
   format: html
   ---
   
   ## Introduction
   [400 words on complementary roles]
   
   ## Adaptive Resonance Theory
   [ART mechanics, $\rho$ threshold, vigilance parameter]
   
   [Figure: Orientation selectivity] <!-- sci-viz output -->
   
   ## Sparse Coding
   [Efficient coding hypothesis, $$J(\theta) = ...$$]
   
   ## Unified Bridge
   [How ART clustering + sparse coding optimization converge]
   
   ## Conclusion
   [Summary, future directions]
   ```

---

## sci-viz Skill Integration Protocol

**How to invoke sci-viz for figures within sci-post-gen:**

### Figure Request Structure
```python
figure_request = {
    "type": "orientation_tuning",           # plot type
    "data": {
        "art_selectivity": [...],           # numpy array or path
        "sparse_basis": [...],
        "stimulus_params": {"contrasts": [0.1, 0.5, 1.0]}
    },
    "style": "publication",                 # figstyle
    "format": "svg",                        # output format (svg/png/pdf)
    "dpi": 300,
    "caption": "Figure 1: Orientation selectivity comparison",
    "width_inches": 4,
    "height_inches": 3
}
```

### Invocation
1. Construct request dict with domain-specific data
2. Call sci-viz: `request_figure(figure_request)`
3. Receive SVG/PNG asset + caption metadata
4. Embed in Quarto: `![caption](figure-uuid.svg)`
5. Update references in bibliography if sci-viz generates citations
