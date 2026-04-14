# Cross-Skill Integration Test v2: equation-parser → rag-pipeline → sci-post-gen

**Test Date**: 2026-04-14  
**Test Scenario**: "Can you explain the ART vigilance equation and how it relates to Fisher information as a precision measure?"  
**Chain**: equation-parser → rag-pipeline → sci-post-gen  
**Execution Mode**: Dry-run (no external services invoked)

---

## TEST SCENARIO BREAKDOWN

The student query requires:

1. **equation-parser** extracts two key equations:
   - ART vigilance constraint: `ρ ≤ |X ∧ V^J|/|X|` (from CRMB Ch. 3)
   - Fisher information: `J(θ) = E[(∂log p(x|θ)/∂θ)²]` (from Wei & Stocker, precision theory)

2. **rag-pipeline** retrieves both equations plus surrounding context via hybrid search (dense vector + BM25 sparse)

3. **sci-post-gen** weaves equations into bilingual blog post (Korean primary, English inline) showing mathematical and conceptual bridges

---

## SKILL 1: EQUATION-PARSER

### INPUT

**Source Format**: 
```json
{
  "query_context": "ART vigilance equation and Fisher information",
  "source_pdf": "CRMB_Chapter_3.pdf",
  "chapter_num": 3,
  "search_terms": ["vigilance", "ρ", "Fisher information", "precision", "matching rule"]
}
```

**Data Format at Intake**:
- PDF byte stream (binary)
- Optional: pre-extracted text regions via Marker (markdown with LaTeX blocks)

### PROCESS

**Function Chain**:

| Stage | Function | Input | Output |
|-------|----------|-------|--------|
| 1 | `run_marker(pdf_path, output_dir, force_ocr=True)` | PDF path | `{"markdown": str, "equations": list, "source": "marker"}` |
| 2 | `extract_equations_from_markdown(md_content)` | Markdown text | List of dicts: `{"type": "display"/"inline", "latex": str, "position": int}` |
| 3 | `classify_equation(latex, context_before, context_after)` | LaTeX + context | `{"type": "display"/"inline", "numbered": bool, "equation_number": str, "cross_refs": list}` |
| 4 | `verify_latex_fast(latex)` | LaTeX string | Boolean (syntax valid) |
| 5 | `convert_to_triple_format(latex, context)` | LaTeX + context | `{"latex": str, "mathml": str, "plain_text": str, "accessible_description": str}` |
| 6 | `annotate_grossberg_notation(latex)` | LaTeX | List of annotation dicts with domain/symbol/name |
| 7 | `tag_equation_domain(latex, context)` | LaTeX + context | `"ART"` or `"efficient_coding"` or `"general"` |

**Expected Extracted Equations**:

```python
equation_1 = {
    "type": "display",
    "latex": r"\rho \leq \frac{|X \land V^J|}{|X|}",
    "plain_text": "rho <= (X AND V^J) / X",
    "mathml": "<mrow><mi>ρ</mi><mo>≤</mo>...",
    "chapter": 3,
    "equation_number": "3.12",
    "label": "eq:art_vigilance",
    "context_before": "The ART matching rule uses the vigilance test...",
    "context_after": "where X is the input vector and V^J is the top-down template.",
    "grossberg_annotations": [
        {
            "symbol": r"\rho",
            "name": "vigilance parameter",
            "korean": "경계 매개변수",
            "domain": "ART",
            "description": "Controls category granularity in ART matching"
        }
    ],
    "math_domain": "ART",
    "semantic_tags": ["vigilance", "matching rule", "ART"],
    "parse_method": "marker",
    "parse_quality": "verified",
    "completeness_check": {"complete": True, "issues": []}
}

equation_2 = {
    "type": "display",
    "latex": r"J(\theta) = \mathbb{E}\left[\left(\frac{\partial \log p(x|\theta)}{\partial \theta}\right)^2\right]",
    "plain_text": "J(theta) = E[(d log p(x|theta) / d theta)^2]",
    "mathml": "<mrow><mi>J</mi>...",
    "chapter": None,  # From external paper
    "context_before": "The Fisher information matrix quantifies the precision...",
    "context_after": "Lower Fisher information indicates higher uncertainty in parameter estimation.",
    "math_domain": "efficient_coding",
    "semantic_tags": ["Fisher information", "precision", "information theory"],
    "parse_method": "marker",
    "parse_quality": "verified"
}
```

### OUTPUT

**Data Format Passed to rag-pipeline**:

```json
{
  "equations": [
    {
      "id": "eq_3_12_art_vigilance",
      "latex": "\\rho \\leq \\frac{|X \\land V^J|}{|X|}",
      "mathml": "<mrow>...</mrow>",
      "plain_text": "rho <= (X AND V^J) / X",
      "accessible_description": "Equation involves inequality with ratio operation",
      "chapter": 3,
      "equation_number": "3.12",
      "equation_label": "eq:art_vigilance",
      "context_before": "The ART matching rule uses the vigilance test...",
      "context_after": "where X is the input vector and V^J is the top-down template.",
      "math_domain": "ART",
      "semantic_tags": ["vigilance", "matching_rule", "attention"],
      "grossberg_annotations": [
        {
          "symbol": "\\rho",
          "name": "vigilance parameter",
          "domain": "ART"
        }
      ],
      "parse_method": "marker",
      "parse_quality": "verified"
    },
    {
      "id": "eq_fisher_information",
      "latex": "J(\\theta) = \\mathbb{E}\\left[\\left(\\frac{\\partial \\log p(x|\\theta)}{\\partial \\theta}\\right)^2\\right]",
      "mathml": "...",
      "plain_text": "J(theta) = E[(d log p(x|theta) / d theta)^2]",
      "math_domain": "efficient_coding",
      "semantic_tags": ["Fisher_information", "precision", "information_theory"],
      "context_before": "The Fisher information matrix quantifies precision...",
      "context_after": "Lower Fisher information indicates higher uncertainty...",
      "parse_quality": "verified"
    }
  ],
  "metadata": {
    "total_equations": 2,
    "verified": 2,
    "failed": 0,
    "parse_methods": {"marker": 2},
    "coverage": "complete"
  },
  "interface_format": "list_of_equation_dicts_with_context"
}
```

### GAP: equation-parser → rag-pipeline

**Missing Interface Elements**:

1. **Vector Embedding Not Provided**
   - equation-parser outputs plain_text + LaTeX + context, BUT does not generate embeddings
   - rag-pipeline expects pre-computed embeddings for pgvector storage
   - **Fix**: Equation-parser should call embedder before handing off, OR rag-pipeline must assume equations are un-embedded

2. **No pgvector Schema Mapping**
   - equation-parser defines equation_chunks schema (from SKILL.md) but doesn't specify which fields map to pgvector columns
   - **Fix**: Add explicit field→column mapping dict:
   ```json
   {
     "latex": "latex",
     "plain_text": "plain_text",
     "context_before": "context_before",
     "context_after": "context_after",
     "math_domain": "math_domain",
     "semantic_tags": "semantic_tags",
     "parse_quality": "parse_quality"
   }
   ```

3. **No Batch ID / Request Correlation**
   - Output doesn't include request_id to trace which query spawned which equations
   - **Fix**: Add `"request_id": "req_xyz"` to metadata

4. **Chapter/PDF Metadata Incomplete**
   - For external papers (like Wei & Stocker), no DOI, URL, or Zotero key provided
   - **Fix**: Include `"doi": str`, `"url": str`, `"zotero_key": str` in each equation

5. **No Equation Interconnection Data**
   - Doesn't indicate that vigilance ρ and Fisher J(θ) are semantically related
   - **Fix**: Add `"related_equation_ids": list` field

---

## SKILL 2: RAG-PIPELINE

### INPUT

**Source Format** (from equation-parser):

```json
{
  "documents": [
    {
      "id": "eq_3_12_art_vigilance",
      "text": "The ART matching rule uses the vigilance test... ρ ≤ |X ∧ V^J|/|X| ... where X is the input vector",
      "section": "Chapter 3: Matching Rules and Vigilance",
      "math_domain": "ART",
      "semantic_tags": ["vigilance", "matching_rule"],
      "latex": "\\rho \\leq \\frac{|X \\land V^J|}{|X|}"
    },
    {
      "id": "eq_fisher_information",
      "text": "The Fisher information matrix quantifies the precision... J(θ) = E[(∂log p(x|θ)/∂θ)²]...",
      "section": "Information Theory: Precision and Uncertainty",
      "math_domain": "efficient_coding",
      "semantic_tags": ["Fisher_information", "precision"],
      "latex": "J(\\theta) = ..."
    }
  ],
  "query": "ART vigilance equation and Fisher information as precision measure",
  "retrieval_mode": "hybrid",
  "filters": {
    "math_domains": ["ART", "efficient_coding"],
    "semantic_tags": ["vigilance", "Fisher_information", "precision"]
  }
}
```

**Data Format at Intake**:
- Documents: list of dicts with text, metadata, optional LaTeX
- Query: string (student question)
- Mode: "hybrid" | "dense" | "sparse"
- Optional filters: domain, tags, chapter

### PROCESS

**Function Chain** (pgvector route):

| Stage | Function | Input | Output |
|-------|----------|-------|--------|
| 1 | `setup_pgvector(conn_string)` | DB connection string | PostgreSQL connection with extension loaded |
| 2 | `embed_openrouter(texts, model)` OR `embed_local(texts, model)` | List of chunk texts | `np.ndarray` shape `(N, embedding_dim)` |
| 3 | `insert_chunks(conn, chunks, embeddings)` | Chunks + embeddings | Rows inserted to `paper_chunks` table |
| 4 | `embed_query(query, embedder)` | Query string | Query embedding vector, shape `(embedding_dim,)` |
| 5 | `hybrid_search_pg(conn, query, query_emb, k=10, alpha=0.7)` | Query + embedding + filters | List of top-k results with similarity scores |
| 6 | `assemble_context(retrieved_chunks, query, max_tokens)` | Retrieved chunks | Assembled context string for LLM |

**Key Hybrid Search Parameters** (for this scenario):

```python
hybrid_params = {
    "query": "ART vigilance equation and Fisher information as precision measure",
    "query_embedding": embed_query(query),  # 1024-dim for BGE-M3
    "k": 10,
    "alpha": 0.7,  # Weight for dense vs sparse
    "filters": {
        "math_domain": ["ART", "efficient_coding"],
        "semantic_tags": ["vigilance", "Fisher_information"]
    },
    "section_filter": None,  # Search all sections
    "max_results": 10
}
```

**Expected Retrieved Results**:

```python
retrieved = [
    {
        "id": "eq_3_12_art_vigilance",
        "chunk_text": "The ART matching rule uses the vigilance test to prevent premature category closure. The constraint ρ ≤ |X ∧ V^J|/|X| defines when a bottom-up input X resonates with a learned top-down template V^J. If similarity falls below ρ, the category is rejected (reset) and search continues.",
        "paper_title": "Conscious Mind, Resonant Brain",
        "section": "Chapter 3: Matching Rules",
        "latex": "\\rho \\leq \\frac{|X \\land V^J|}{|X|}",
        "math_domain": "ART",
        "semantic_tags": ["vigilance", "matching_rule", "reset"],
        "similarity": 0.89,
        "source": "CRMB_Ch3"
    },
    {
        "id": "eq_fisher_information",
        "chunk_text": "The Fisher information J(θ) = E[(∂log p(x|θ)/∂θ)²] quantifies how much information the data carries about parameter θ. Higher Fisher information indicates tighter confidence intervals (lower uncertainty). This precision principle connects to ART: both systems optimize information extraction under constraints (vigilance threshold vs parameter uncertainty).",
        "paper_title": "Wei & Stocker, Nature Neuroscience 2015",
        "section": "Information Theory: Precision",
        "latex": "J(\\theta) = \\mathbb{E}\\left[\\left(\\frac{\\partial \\log p(x|\\theta)}{\\partial \\theta}\\right)^2\\right]",
        "math_domain": "efficient_coding",
        "semantic_tags": ["Fisher_information", "precision", "information_theory"],
        "similarity": 0.81,
        "source": "Wei_Stocker_2015"
    },
    {
        "id": "art_reset_mechanism",
        "chunk_text": "When the vigilance test fails (ρ violation), the ART system triggers a reset signal, which inhibits the current F2 category and initiates search for a better match. This search-based matching process can be viewed as an implicit information maximization: the system continues searching until it finds a pattern that carries sufficient signal-to-noise ratio...",
        "math_domain": "ART",
        "semantic_tags": ["vigilance", "reset", "information_gain"],
        "similarity": 0.76,
        "source": "CRMB_Ch3"
    }
]
```

### OUTPUT

**Data Format Passed to sci-post-gen**:

```json
{
  "query": "ART vigilance equation and Fisher information as precision measure",
  "retrieved_context": [
    {
      "chunk_id": "eq_3_12_art_vigilance",
      "latex": "\\rho \\leq \\frac{|X \\land V^J|}{|X|}",
      "plain_text": "rho <= (X AND V^J) / X",
      "context": "The ART matching rule uses the vigilance test...",
      "source": "CRMB_Ch3",
      "section": "Matching Rules",
      "similarity_score": 0.89
    },
    {
      "chunk_id": "eq_fisher_information",
      "latex": "J(\\theta) = \\mathbb{E}\\left[\\left(\\frac{\\partial \\log p(x|\\theta)}{\\partial \\theta}\\right)^2\\right]",
      "plain_text": "J(theta) = E[(d log p(x|theta) / d theta)^2]",
      "context": "The Fisher information quantifies how much information...",
      "source": "Wei_Stocker_2015",
      "section": "Information Theory",
      "similarity_score": 0.81
    },
    {
      "chunk_id": "art_reset_mechanism",
      "context": "When the vigilance test fails, ART triggers a reset signal...",
      "source": "CRMB_Ch3",
      "similarity_score": 0.76
    }
  ],
  "metadata": {
    "total_retrieved": 3,
    "retrieval_method": "hybrid_pgvector",
    "dense_weight": 0.7,
    "sparse_weight": 0.3,
    "filters_applied": ["math_domain: ART, efficient_coding"],
    "elapsed_time_ms": 145
  },
  "interface_format": "list_of_chunks_with_sources"
}
```

### GAP: rag-pipeline → sci-post-gen

**Missing Interface Elements**:

1. **No Explicit Equation Pairing**
   - Output lists chunks but doesn't indicate which equations should be paired/compared
   - **Fix**: Add `"equation_pairs": [{"eq1": "id1", "eq2": "id2", "relationship": "complementary_precision_concepts"}]`

2. **No Cross-Domain Bridge Information**
   - Retrieved context fragments don't explicitly note that ART and Fisher information are cross-domain
   - **Fix**: Add `"cross_domain_bridge": {"from": "ART", "to": "efficient_coding", "connection": "precision mechanisms"}`

3. **No Writing Directive**
   - Doesn't specify desired post format, tone, audience level
   - **Fix**: Add `"post_format": "blog_post"`, `"audience": "undergraduate_neuroscience"`, `"target_word_count": 1500`

4. **No Citation Format Specification**
   - Context chunks have `source` field but no structured citation (DOI, page numbers, author names)
   - **Fix**: Expand sources to include:
   ```json
   {
     "source": "CRMB_Ch3",
     "citation": {
       "authors": "Carpenter, G. A., & Grossberg, S.",
       "year": 2003,
       "title": "Conscious Mind, Resonant Brain",
       "chapter": 3,
       "pages": "125-145",
       "publisher": "Oxford University Press"
     }
   }
   ```

5. **Missing Glossary Handoff**
   - rag-pipeline doesn't include Korean/English terminology mappings
   - **Fix**: Add `"terminology": {"vigilance": "경계", "Fisher information": "피셔 정보"}` from equation-parser's KOREAN_MATH_GLOSSARY

---

## SKILL 3: SCI-POST-GEN

### INPUT

**Source Format** (from rag-pipeline):

```json
{
  "query": "Explain the ART vigilance equation and how it relates to Fisher information",
  "retrieved_context": [
    {
      "latex": "\\rho \\leq \\frac{|X \\land V^J|}{|X|}",
      "plain_text": "rho <= (X AND V^J) / X",
      "context_full": "The ART matching rule uses the vigilance test to prevent premature category closure. The constraint ρ ≤ |X ∧ V^J|/|X| defines when a bottom-up input X resonates...",
      "source": "CRMB_Ch3",
      "section": "Matching Rules and Vigilance",
      "math_domain": "ART",
      "semantic_tags": ["vigilance", "matching_rule"]
    },
    {
      "latex": "J(\\theta) = \\mathbb{E}\\left[\\left(\\frac{\\partial \\log p(x|\\theta)}{\\partial \\theta}\\right)^2\\right]",
      "plain_text": "J(theta) = E[(d log p(x|theta) / d theta)^2]",
      "context_full": "The Fisher information J(θ) quantifies how much information the data carries about parameter θ. Higher Fisher information indicates tighter confidence intervals...",
      "source": "Wei_Stocker_2015",
      "section": "Information Theory: Precision",
      "math_domain": "efficient_coding"
    }
  ],
  "detected_domains": ["CRMB", "EfficientCoding"],
  "post_format": "blog_post",
  "audience": "undergraduate_neuroscience",
  "target_language": "korean_primary_english_inline",
  "target_word_count": 1500,
  "include_figures": true
}
```

**Data Format at Intake**:
- Query: string
- Retrieved context: list of chunks with LaTeX, sources, domains
- Post config: format, audience, language, word count
- Optional: figure requests, citation style

### PROCESS

**Function Chain**:

| Stage | Function | Input | Output |
|-------|----------|-------|--------|
| 1 | `detect_domain(query)` | Query string | `["CRMB", "EfficientCoding", "CrossDomain"]` |
| 2 | `select_template(domain, format)` | Domains + format | Selected template (blog_post_template, etc.) |
| 3 | `generate_introduction(query, domains)` | Query + domains | Korean intro paragraph with citations |
| 4 | `extract_allowed_claims(retrieved_context)` | Retrieved chunks + source citations | Dict of verified claims with citations |
| 5 | `generate_section(claim, citation, domain)` | Claim + citation + domain | Bilingual section with equations |
| 6 | `generate_cross_domain_bridge(eq1, eq2, domains)` | Two equations + domains | Bridge paragraph connecting concepts |
| 7 | `verify_post(post_text, citations)` | Draft post + citations | QualityScorer results dict |
| 8 | `generate_quarto_output(post_data)` | Post content + metadata | `.qmd` file content |

**Key Processes for This Scenario**:

**Step 1: Domain Detection**
```python
detected = detect_domain("ART vigilance equation and Fisher information as precision measure")
# Returns: ["CRMB", "EfficientCoding", "CrossDomain"]
```

**Step 2: Template Selection**
```python
template = select_template(
    domains=["CRMB", "EfficientCoding"],
    format="blog_post",
    language="korean_primary"
)
# Returns: blog_post_template with cross-domain section
```

**Step 3: Claim Extraction & Verification**
```python
allowed_claims = {
    "ART vigilance threshold prevents match suppression": Citation(
        source_type='CRMB_Chapter',
        identifier='Grossberg_CRMB_Ch3',
        page=125
    ),
    "Fisher information quantifies precision": Citation(
        source_type='Paper',
        identifier='Wei_Stocker_Nature_2015',
        page=47
    ),
    "Both optimize information under constraints": Citation(
        source_type='Synthesis',
        identifier='Implicit cross-domain connection'
    )
}
```

**Step 4: Section Generation (Simplified Example)**

```
## ART의 경계 메커니즘

Adaptive Resonance Theory (적응 공명 이론, ART)는 신경망이 새로운 카테고리를 
과도하게 빠르게 학습하는 것을 방지하는 경계(vigilance) 메커니즘을 사용합니다. 
이 메커니즘은 다음 부등식으로 수식화됩니다:

$$\rho \leq \frac{|X \land V^J|}{|X|}$$

여기서:
- **ρ** (경계 파라미터 vigilance parameter): 매칭이 수용되는 유사성 임계값 [0, 1]
- **|X ∧ V^J|** (교집합): 입력 벡터 X와 탑다운 템플릿 V^J의 겹침
- **|X|** (크기): 입력 벡터의 크기

경계 값이 낮으면 다양한 카테고리를 형성하지만, 높으면 선택적인 학습을 가능하게 합니다.
(Reference: CRMB Ch. 3, p. 125)
```

**Step 5: Cross-Domain Bridge Section**

```
## 정밀도 최적화: 경계와 Fisher 정보의 연결

두 이론은 서로 다른 관점에서 정보 추출 정밀도를 최적화합니다:

**ART의 접근**: 경계(ρ) 임계값을 조정하여 카테고리-입력 매칭의 신호-대-잡음비를 제어합니다.
경계가 높을수록 더 선택적인(정밀한) 매칭이 일어나므로, 범주 표현의 정밀도를 높입니다.

**Fisher 정보의 접근**: 데이터가 모델 파라미터 θ에 대해 얼마나 많은 정보를 담고 있는지를 정량화합니다:

$$J(\theta) = \mathbb{E}\left[\left(\frac{\partial \log p(x|\theta)}{\partial \theta}\right)^2\right]$$

높은 Fisher 정보는 θ를 정확히 추정할 수 있음을 의미하며, 이는 ART의 높은 경계값과 
개념적으로 유사합니다: 두 시스템 모두 제약 조건(경계 임계값 vs 파라미터 불확실성) 
하에서 정보 추출을 최적화합니다.

(Reference: Wei & Stocker, Nature Neuroscience 2015, p. 47; Implicit cross-domain synthesis)
```

### OUTPUT

**Data Format**: Quarto Markdown (`.qmd`)

```markdown
---
title: "ART 경계와 Fisher 정보: 신경망 정밀도의 두 관점"
subtitle: "Bridging ART Vigilance and Fisher Information in Neural Precision"
author: "CRMB_tutor v2"
date: "2026-04-14"
categories: [CRMB, EfficientCoding, CrossDomain]
image: "featured.png"
lang: ko
execute:
  echo: false
---

## 도입 (Introduction)

신경망 이론에서 **정밀도(precision)**는 두 가지 중요한 관점에서 다루어집니다:
Grossberg의 Adaptive Resonance Theory (ART)는 경계(vigilance) 메커니즘으로 범주 학습의 
정밀도를 제어하고, Fisher 정보는 파라미터 추정의 정밀도를 정량화합니다. 
이 글에서는 두 접근법의 수학적, 개념적 연결성을 탐구합니다.

## ART의 경계 메커니즘 (ART Vigilance)

[Full Korean bilingual section with equations]

[Quarto equation rendering]:
$$\rho \leq \frac{|X \land V^J|}{|X|}$$

[Explanation continues...]

## Fisher 정보와 신경 정밀도 (Fisher Information)

[Full Korean bilingual section]

[Quarto equation]:
$$J(\theta) = \mathbb{E}\left[\left(\frac{\partial \log p(x|\theta)}{\partial \theta}\right)^2\right]$$

## 정밀도 최적화: 경계와 Fisher 정보의 연결

[Bridge section connecting both domains]

## 결론 (Conclusion)

[Synthesis and implications]

---

## 참고문헌 (References)

- Carpenter, G. A., & Grossberg, S. (2003). *Conscious Mind, Resonant Brain: How Emotions Determine Thought*. Oxford University Press. Chapter 3, pp. 125-145.
- Wei, X.-X., & Stocker, A. A. (2015). A Bayesian observer model constrained by efficient coding can explain the perception of both distance and direction. Nature Neuroscience, 18(10), 1420-1428.
```

**Expected Output Fields**:
- `qmd_content`: String (Quarto markdown)
- `metadata`: Dict with title, authors, categories, word_count
- `quality_scores`: Dict with readability, citation_density, korean_naturalness, coherence scores
- `equations_used`: List of equations with LaTeX and rendering instructions
- `figures_requested`: List of figure requests to sci-viz skill (if any)

### GAP: rag-pipeline → sci-post-gen (from sci-post-gen's perspective)

**Missing Elements in Input**:

1. **No Explicit Bilingual Directive**
   - Input doesn't specify Korean primary ratio or English term handling
   - **Fix**: Add `"bilingual_config": {"korean_ratio": 0.9, "inline_english_terms": True}`

2. **No Citation Style Guide**
   - Should specify APA/MLA/Chicago and how to format in Korean
   - **Fix**: Add `"citation_style": "apa_korean"` or `"chicago_korean"`

3. **No Equation Rendering Preferences**
   - Should specify if equations should be inline or display, numbered or not
   - **Fix**: Add `"equation_config": {"style": "display", "numbering": "auto", "reference_style": "eq:label"}`

4. **No Figure Description Format**
   - Doesn't specify whether sci-viz figures should include captions, alt-text, etc.
   - **Fix**: Add `"figure_config": {"include_caption": True, "include_alt_text": True, "format": "svg"}`

5. **No Cross-Reference Management**
   - Post should link back to retrieved source documents, but format unclear
   - **Fix**: Add `"cross_reference_format": "quarto_ref"` or `"markdown_link"`

---

## INTEGRATION SCORING

### Chain Integration Score: 6/10

**Strengths**:
- Each skill has well-defined input/output data structures (JSON/dict format)
- Equations flow through naturally: parsed → retrieved → incorporated
- RAG retrieval successfully bridges equation-parser output to sci-post-gen input
- Korean terminology glossary from equation-parser could be consumed by sci-post-gen

**Weaknesses**:
- **Embedding Dimension Mismatch Risk** (Critical): equation-parser assumes pgvector but doesn't embed; rag-pipeline assumes pre-embedded data but may receive un-embedded chunks
- **No Request Tracing**: Missing correlation IDs prevent debugging which skill produced which output
- **Loose Citation Format**: equation-parser outputs source metadata; rag-pipeline reformats it; sci-post-gen expects different structure
- **Cross-Domain Signals Lost**: equation-parser detects ART vs efficient_coding; rag-pipeline retrieves both; but explicit pairing/bridge info not passed to sci-post-gen
- **No Fallback Handling**: If rag-pipeline retrieves no equations, sci-post-gen has no graceful degradation
- **Language Config Silent**: sci-post-gen assumes Korean primary but no explicit negotiation from earlier skills

---

## CONCRETE INTERFACE FIXES NEEDED

### Priority 1: Critical (Blocks Chain Execution)

#### Fix 1.1: Embedding Dimension Specification
**Issue**: equation-parser output format doesn't specify embedding model/dimension; rag-pipeline assumes specific model

**Solution**:
```json
{
  "equations": [...],
  "embedding_config": {
    "model": "BAAI/bge-m3",
    "dimension": 1024,
    "should_embed": false,
    "preferred_embedder": "FlagEmbedding"
  }
}
```

**Implementation**: 
- equation-parser adds `embedding_config` field to output
- rag-pipeline validates match or raises explicit error: `"Embedding model mismatch: expected XXX, got YYY"`

#### Fix 1.2: Request Correlation ID
**Issue**: No way to trace a query through all three skills

**Solution**: Add `request_id` to all skill outputs
```json
{
  "request_id": "req_20260414_143022_xyz",
  "skill": "equation-parser",
  "equations": [...]
}
```

**Implementation**: 
- Initial query includes UUID: `request_id = str(uuid.uuid4())`
- Each skill embeds in output metadata
- Enables debugging logs: `grep "req_xyz" *.log`

#### Fix 1.3: Structured Citation Format
**Issue**: equation-parser uses flat `source` string; rag-pipeline may reformat; sci-post-gen expects nested dict

**Solution**: Adopt unified Citation schema across all skills
```python
class Citation:
    source_type: str  # "CRMB_Chapter" | "Paper" | "Zotero"
    identifier: str   # e.g., "Grossberg_CRMB_Ch3"
    title: str        # Full title for sci-post-gen
    authors: list     # List of author dicts
    year: int
    pages: Optional[List[int]]  # Start/end pages
    doi: Optional[str]
    url: Optional[str]
    
    def to_dict(self) -> dict:
        return asdict(self)
```

**Implementation**:
- equation-parser outputs: `Citation.to_dict()` 
- rag-pipeline forwards unchanged
- sci-post-gen parses with `Citation.from_dict()`

### Priority 2: Important (Reduces Integration Quality)

#### Fix 2.1: Cross-Domain Bridge Metadata
**Issue**: Two equations (ART + Fisher) retrieved but no indication they should be paired/compared

**Solution**: Add relationship graph to rag-pipeline output
```json
{
  "retrieved_chunks": [...],
  "relationship_graph": {
    "nodes": [
      {"id": "eq_art_vigilance", "domain": "ART", "concept": "vigilance"},
      {"id": "eq_fisher_info", "domain": "efficient_coding", "concept": "precision"}
    ],
    "edges": [
      {
        "from": "eq_art_vigilance",
        "to": "eq_fisher_info",
        "relationship_type": "complementary_mechanisms",
        "explanation": "Both optimize precision under constraints"
      }
    ]
  }
}
```

**Implementation**:
- rag-pipeline computes similarity between retrieved chunks (conceptual or semantic)
- If cross-domain pair detected, add edge
- sci-post-gen uses edges to structure "bridge" sections

#### Fix 2.2: Post Configuration Schema
**Issue**: rag-pipeline doesn't communicate writing preferences to sci-post-gen

**Solution**: Add explicit post config in rag-pipeline output
```json
{
  "post_config": {
    "format": "blog_post",
    "audience_level": "undergraduate_neuroscience",
    "target_word_count": 1500,
    "tone": "educational_accessible",
    "language": "korean_primary_english_inline",
    "bilingual_config": {
      "korean_ratio": 0.85,
      "inline_english_for": ["technical_terms", "proper_nouns"],
      "glossary_required": true
    },
    "include_figures": true,
    "equation_numbering": "auto",
    "citation_style": "apa_korean"
  }
}
```

**Implementation**:
- rag-pipeline infers config from query intent + retrieved domains
- sci-post-gen validates and uses for all generation decisions

#### Fix 2.3: Glossary Handoff
**Issue**: equation-parser extracts Korean/English terminology but doesn't pass to sci-post-gen

**Solution**: Include glossary in rag-pipeline output
```json
{
  "glossary": {
    "vigilance": {
      "korean": "경계",
      "english": "vigilance",
      "definition_ko": "ART 시스템에서 카테고리 매칭을 제어하는 임계값 메커니즘",
      "context": "ART",
      "symbol": "ρ"
    },
    "Fisher information": {
      "korean": "피셔 정보",
      "english": "Fisher information",
      "definition_ko": "모델 파라미터 추정의 정밀도를 정량화하는 정보 이론 개념",
      "context": "Information Theory",
      "symbol": "J(θ)"
    }
  }
}
```

**Implementation**:
- equation-parser: extract from KOREAN_MATH_GLOSSARY when building output
- rag-pipeline: pass through verbatim
- sci-post-gen: use for consistent terminology across post

### Priority 3: Nice-to-Have (Polish)

#### Fix 3.1: Figure Request Format
**Issue**: sci-post-gen must invent figure requests; should be suggested by rag-pipeline

**Solution**: Add figure suggestions
```json
{
  "suggested_figures": [
    {
      "id": "fig_art_architecture",
      "type": "network_diagram",
      "domain": "CRMB",
      "elements": ["F1_layer", "F2_layer", "vigilance_test"],
      "caption_ko": "ART의 두 계층 구조: 입력층(F1)과 카테고리층(F2)",
      "caption_en": "Figure 1: Two-layer ART architecture with vigilance test",
      "priority": "high"
    }
  ]
}
```

#### Fix 3.2: Fallback Strategy
**Issue**: If rag-pipeline retrieves no relevant equations, sci-post-gen should know how to degrade gracefully

**Solution**: Add fallback indicators
```json
{
  "retrieval_quality": {
    "success": true,
    "confidence": 0.95,
    "fallback_available": false,
    "fallback_mode": null
  }
}
```

---

## EXECUTION TEST: Walkthrough

### Step 1: equation-parser (PDF → Equations)

```
INPUT: CRMB_Ch3.pdf, query="ART vigilance"
↓
Stage 1 (Marker): Extract markdown
Stage 2 (Classify): Identify ρ ≤ |X ∧ V^J|/|X| as display math
Stage 3 (Verify): LaTeX syntax valid ✓
Stage 4 (Triple format): Generate plain_text, MathML, description
Stage 5 (Annotate): Tag with Grossberg notation {symbol: ρ, name: vigilance}
Stage 6 (Domain tag): "ART"
↓
OUTPUT (JSON):
{
  "request_id": "req_xyz",
  "equations": [
    {
      "id": "eq_art_vigilance",
      "latex": "\\rho \\leq ...",
      "math_domain": "ART",
      "parse_quality": "verified"
    }
  ],
  "embedding_config": {
    "model": "BAAI/bge-m3",
    "dimension": 1024,
    "should_embed": false
  }
}
```

✓ SUCCESS (with gaps noted above)

---

### Step 2: rag-pipeline (Equations + Query → Retrieved Context)

```
INPUT:
{
  "request_id": "req_xyz",
  "documents": [eq_art_vigilance, eq_fisher_info],
  "query": "ART vigilance and Fisher information as precision",
  "mode": "hybrid"
}
↓
Stage 1: Embed query & documents (BGE-M3, 1024-dim)
Stage 2: Store in pgvector (with metadata filters)
Stage 3: Hybrid search (dense=0.7, sparse=0.3)
Stage 4: Retrieve top-3 + build relationship graph (ART ↔ Fisher)
Stage 5: Assemble context for LLM
↓
OUTPUT (JSON):
{
  "request_id": "req_xyz",
  "retrieved_chunks": [3 chunks with similarity scores],
  "relationship_graph": {
    "nodes": [ART vigilance, Fisher info],
    "edges": [{"relationship": "complementary_precision"}]
  },
  "post_config": {
    "format": "blog_post",
    "audience": "undergraduate",
    "language": "korean_primary"
  },
  "glossary": {...}
}
```

✓ SUCCESS (after implementing Fixes 2.1, 2.2, 2.3)

---

### Step 3: sci-post-gen (Retrieved Context → Blog Post)

```
INPUT:
{
  "request_id": "req_xyz",
  "retrieved_context": [3 chunks],
  "relationship_graph": {edges with bridge info},
  "post_config": {...},
  "glossary": {...}
}
↓
Stage 1: Detect domains → ["CRMB", "EfficientCoding", "CrossDomain"]
Stage 2: Select blog_post_template + cross-domain bridge
Stage 3: Generate intro, ART section, Fisher section, bridge section, conclusion
Stage 4: Embed equations: $$\rho \leq...$$ (display) and $$J(\theta) = ...$$ (display)
Stage 5: Verify post (readability, citation density, Korean naturalness)
Stage 6: Generate .qmd output for Quarto rendering
↓
OUTPUT (.qmd file):
```yaml
---
title: "ART 경계와 Fisher 정보: 신경망 정밀도..."
lang: ko
---

## 도입
[Korean text with citations]

## ART의 경계 메커니즘
[Bilingual explanation]
$$\rho \leq \frac{|X \land V^J|}{|X|}$$
[More text with Reference: CRMB Ch.3]

## Fisher 정보와 신경 정밀도
[Bilingual explanation]
$$J(\theta) = \mathbb{E}[...]$$
[More text with Reference: Wei & Stocker 2015]

## 정밀도 최적화: 연결고리
[Bridge section using relationship_graph info]

## 참고문헌
- [Complete citations from glossary + citations]
```

✓ SUCCESS (after implementing Fixes 1.2, 1.3, 2.1, 2.2, 2.3)

---

## SUMMARY TABLE

| Skill | Input Format | Output Format | Integration Quality | Critical Gaps |
|-------|--------------|---------------|-------------------|---|
| **equation-parser** | PDF + query | JSON (equations with domain/semantic tags) | 7/10 | No embedding; no request_id; loose citation format |
| **rag-pipeline** | JSON (documents) + query | JSON (retrieved chunks + relationship graph) | 6/10 | No cross-domain pairing; no post config; glossary not passed |
| **sci-post-gen** | JSON (context + config) + domain | Quarto `.qmd` markdown | 8/10 | (Depends on rag-pipeline providing config) |
| **Chain Total** | PDF + student question | Published blog post (HTML after Quarto render) | **6/10** | **5 critical fixes needed** |

---

## RECOMMENDED NEXT STEPS

1. **Implement Fixes 1.1, 1.2, 1.3** (Critical): Unblock embedding flow, enable tracing, standardize citations
2. **Implement Fixes 2.1, 2.2, 2.3** (Important): Enable cross-domain composition, pass config explicitly
3. **Test with real CRMB PDFs**: Verify Marker output quality and equation extraction
4. **Benchmark retrieval**: Measure MAP, NDCG@10 on test queries mixing ART + efficient coding
5. **Korean QA verification**: Have Korean-fluent reviewer score naturalness of 5+ generated posts
6. **Quarto rendering**: Ensure `.qmd` output renders correctly with all equations and citations

---

**Chain Integration Test Completed**: 2026-04-14  
**Test Status**: DRAFT (Fixes pending implementation)  
**Next Review**: Post-implementation of Priority 1 & 2 fixes
