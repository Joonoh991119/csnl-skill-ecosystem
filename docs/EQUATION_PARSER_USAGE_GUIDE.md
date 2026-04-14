# equation-parser: Downstream Session Usage Guide

## Quick Reference

```python
# Core import pattern for all sessions
from equation_parser import (
    parse_equation,           # 4-stage cascade: Marker → Nougat → LaTeX-OCR → pix2tex
    classify_equation,        # inline/display, numbering, cross-refs
    verify_latex,             # pdflatex compilation test
    convert_to_triple_format, # LaTeX + MathML + plain text
    annotate_grossberg_notation,  # ART/BCS/FCS/LAMINART notation
    tag_equation_domain,      # auto-classify domain
    store_equation_chunk,     # pgvector storage
    KOREAN_MATH_GLOSSARY,     # 60+ terms
    GROSSBERG_NOTATION,       # ART ρ, BCS B_ijk, FCS F_ij, etc.
)
```

---

## Session 1: CMRB Ontology-Augmented RAG (DB 개선)

**Priority**: P0 (equations are the primary content gap in current DB)

**Usage Flow**:
```
CRMB Chapter PDF → equation-parser → equation_chunks table → ontology-rag tags → rag-pipeline search
```

**Key Functions**:
- `process_all_chapters(pdf_dir, conn, embedder)` — batch all 20 chapters
- `store_equation_chunk(conn, eq, embedder)` — pgvector with 1024-dim BGE-M3
- `tag_equation_domain(latex, context)` — auto-tag ART/BCS/FCS/LAMINART

**Integration with db-pipeline**:
```python
# In db-pipeline orchestrator, after Marker step:
from equation_parser import process_chapter_equations

for chapter_num, pdf_path in enumerate(chapter_pdfs, 1):
    stats = process_chapter_equations(pdf_path, chapter_num, conn, embedder)
    print(f"Ch.{chapter_num}: {stats['total']} equations, {stats['verified']} verified")
```

**ontology-rag integration**:
```python
# Tag equation chunks with ontology concept IDs
for eq in equations:
    domain = tag_equation_domain(eq['latex'], eq.get('context_before', ''))
    annotations = annotate_grossberg_notation(eq['latex'])
    eq['semantic_tags'] = [a['name'] for a in annotations]
    eq['math_domain'] = domain
    # → ontology-rag can now filter by concept: "BCS boundary signal" 
```

---

## Session 2: Scientific Post Generation v2

**Priority**: P1 (equations embedded in blog posts)

**Usage Flow**:
```
equation-parser output → sci-post-gen template → Quarto .qmd with LaTeX blocks
```

**Key Functions**:
- `convert_to_triple_format(latex)` — get LaTeX for display, plain text for inline description
- `annotate_equation_korean(latex, plain_text)` — Korean term annotations for bilingual posts
- `KOREAN_MATH_GLOSSARY` — term consistency across posts

**In sci-post-gen template**:
```markdown
## ART 경계 조건 (Vigilance Condition)

적응적 공명 이론(Adaptive Resonance Theory)의 핵심 수식:

$$\rho \leq \frac{|X \wedge V^J|}{|X|}$$

여기서 $\rho$는 경계 매개변수(vigilance parameter), 
$X$는 입력 패턴(input pattern), $V^J$는 하향식 기대(top-down template)입니다.
```

**Cross-domain post (ART ↔ Fisher info)**:
```python
# equation-parser provides both equations
art_eq = convert_to_triple_format(r'\rho \leq \frac{|X \wedge V^J|}{|X|}')
fisher_eq = convert_to_triple_format(r'J(\theta) = E\left[\left(\frac{\partial}{\partial\theta} \log p(m|\theta)\right)^2\right]')

# sci-post-gen weaves them together in Quarto template
# Korean annotations: annotate_equation_korean() for both
```

---

## Session 3: Addictive Conversation

**Priority**: P2 (equation retrieval during tutoring dialogues)

**Usage Flow**:
```
student question → rag-pipeline retrieves equation_chunks → conversation-sim presents equation
```

**Key Functions**:
- `search_equations(conn, query_vector, filters={'math_domain': 'ART'})` — filtered equation search
- `generate_accessible_description(latex)` — for TTS/accessibility
- `GROSSBERG_NOTATION` — tutor can explain each symbol

**In conversation-sim**:
```python
# When student asks about a specific equation
if user_asks_about_equation:
    eq_results = search_equations(conn, query_vec, filters={'chapter': 5, 'math_domain': 'BCS'})
    for eq in eq_results:
        # Present with Korean annotation
        annotations = annotate_grossberg_notation(eq['latex'])
        korean_terms = annotate_equation_korean(eq['latex'], eq['plain_text'])
        # → CuriosityModulator can use equation as PARADOX hook:
        # "이 수식에서 ρ를 0에 가깝게 하면 어떻게 될까요? 모든 입력을 같은 범주로..."
```

---

## Session 4: User Feedback

**Priority**: P3 (equation difficulty feedback routing)

**Usage Flow**:
```
"수식이 어려워요" → user-feedback classifier → equation_type + difficulty → tutor param adjustment
```

**Key Functions**:
- `equation_completeness_check(latex)` — verify the equation shown wasn't truncated
- `classify_equation(latex)` — complexity indicator (display > inline)

**Feedback pattern**:
```python
# In user-feedback ComponentPatternMatcher:
EQUATION_FEEDBACK_PATTERNS = {
    "수식이 어려워요": {"component": "tutor_content_gen", "action": "simplify_math"},
    "수식 설명이 부족해요": {"component": "tutor_content_gen", "action": "add_variable_defs"},
    "수식이 깨져 보여요": {"component": "equation_parser", "action": "reparse_verify"},
}
```

---

## Common Patterns Across All Sessions

### Verify Before Use
```python
# Always verify parsed equations before downstream consumption
for eq in parsed_equations:
    if not verify_latex_fast(eq['latex']):
        eq['parse_quality'] = 'unverified'
        # Skip or flag for manual review
```

### Domain Detection
```python
domain = tag_equation_domain(eq['latex'], surrounding_context)
# Returns: 'ART', 'BCS', 'FCS', 'LAMINART', 'efficient_coding', or 'general'
```

### Korean Annotation
```python
ko_terms = annotate_equation_korean(eq['latex'], eq['plain_text'])
# Returns: {'vigilance': '경계 감지', 'integral': '적분', ...}
```

### M4 Pro Settings
```python
MPS_CONFIG = {
    "device": "mps", "use_fp16": True,
    "batch_size": 32,       # equation images are large
    "nougat_workers": 2,
    "pdflatex_timeout": 15,
}
```
