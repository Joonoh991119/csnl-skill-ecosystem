# SKILL Evaluation: paper-processor

**Evaluation Date:** 2026-04-14  
**Evaluator:** Claude Code Agent  
**Test Prompt:** EVAL PROMPT 2 (Edge Cases)

---

## Query Summary

The user needs to extract equations and their surrounding context from Grossberg's CRMB Chapter 5 (BCS/FCS) with the following characteristics:
- Complex multi-line equations with Greek symbols, subscripts, and equation numbering
- Some equations span page breaks
- Goal: Preserve equation semantics for downstream RAG indexing

---

## Skill Assessment

### 1. Sufficiency of Guidance

**Overall: INSUFFICIENT for the specific use case**

The skill provides a solid general-purpose pipeline for academic paper processing (section detection, claim extraction, figure extraction, batch processing). However, it **has significant gaps in equation handling**:

#### What the skill covers:
- General PDF text extraction using PyMuPDF (fitz)
- Section detection (abstract, methods, results, etc.)
- Figure and image extraction with captions
- Citation metadata handling
- Claim extraction focused on natural language claims with statistical tests

#### What the skill DOES NOT cover:
1. **Equation extraction and parsing** — No code or guidance for identifying, extracting, or preserving mathematical equations
2. **Multi-line equation handling** — No discussion of equations spanning multiple lines or across page breaks
3. **Equation semantics preservation** — No mention of LaTeX source format, MathML conversion, or equation-to-semantics mapping
4. **Greek symbols and special characters** — Text extraction may lose mathematical notation; no character encoding/handling strategy described
5. **Equation numbering and references** — No method to link equations to their labels and cross-references in text
6. **Page break equation handling** — No strategies for reconstructing equations split across pages
7. **RAG-specific equation indexing** — No guidance on how to structure equation data for semantic search or RAG retrieval

---

### 2. Specific Sections/Code: Helps vs Gaps

#### Sections That Help:

**PDF Input Handling (Partial Help)**
```python
def extract_from_pdf(pdf_path: str) -> dict:
    # ... fitz library extraction
    'blocks': page.get_text("dict")['blocks']  # Structured blocks
```
- **Why it helps:** The structured "blocks" extraction from PyMuPDF does preserve some formatting information about text positions. This COULD be used to detect equations if further processing is added.
- **Limitation:** fitz.get_text("dict") returns generic text blocks, not equation-specific parsing. Greek letters may appear as Unicode or be garbled depending on PDF encoding.

**arXiv Extraction (Partial Help)**
```python
def extract_from_arxiv(arxiv_id: str) -> dict:
    """Fetch paper from arXiv. Prefer LaTeX source for equation preservation."""
    # Try LaTeX source first (better equation/figure extraction)
```
- **Why it helps:** The docstring explicitly mentions "Prefer LaTeX source for equation preservation" — shows awareness that LaTeX is better for equations.
- **Limitation:** The actual implementation is missing (stub only). No code shows how to extract, parse, or preserve LaTeX equations.

**Output Schema (Partial Help)**
```json
{
  "sections": { "abstract": "...", ... },
  "figures": [ { "figure_num": 1, ... } ]
}
```
- **Why it helps:** The schema is extensible — could add an "equations" field.
- **Limitation:** No "equations" field is currently defined in the schema. Unclear how equation data should be structured.

#### Critical Gaps:

**Gap 1: No Equation Detection Logic**
- No regex patterns or heuristics to identify equation boundaries
- No code to distinguish between inline equations ($...$) and display equations ($$...$$)
- No LaTeX equation environment detection (\begin{equation}, \align, etc.)

**Gap 2: No Multi-line or Page-break Handling**
- The figure extraction logic iterates page-by-page independently
- No mechanism to stitch together content split across page boundaries
- No "context window" around equations to preserve surrounding narrative

**Gap 3: No Character Encoding/Symbol Handling**
- PDF text extraction can corrupt Greek letters (α → α, β → b, etc.)
- No mention of Unicode normalization or special character preservation
- No guidance on handling MathML, AMS-TeX, or other math markup variants

**Gap 4: No RAG-Specific Indexing Strategy**
- Output schema has "claims" (natural language), but no "equations" field
- No guidance on equation → semantic embedding pipeline
- No mention of equation numbering linkage (Eq. 5.2 reference → actual equation)
- No chunking strategy for equations (e.g., "equation + surrounding context" chunks)

**Gap 5: No LaTeX Parsing Implementation**
- Docstring says "Try LaTeX source first," but the function is a stub
- No LaTeX extraction, cleaning, or compilation discussed
- No handling of equation compilation to MathML or other interchange formats

---

### 3. Scoring (1-5 scale)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Relevance** | 2 | The skill is broadly relevant to paper processing but orthogonal to the specific problem of equation extraction. General claims extraction is not sufficient for mathematical content. |
| **Completeness** | 1 | Critical components missing: equation detection, parsing, semantics preservation, multi-line handling, page-break reconstruction, RAG-specific indexing. Only ~5% of the needed functionality is present. |
| **Actionability** | 2 | A user following this skill could extract PDF text, detect sections, and get figures—but would be unable to extract/index equations without substantial custom development. The LaTeX extraction is mentioned but not implemented. |

**Overall Score:** 1.5 / 5 — Not suitable for equation-focused RAG pipelines without major extensions.

---

## Improvement Recommendations

### High Priority

#### 1. Add Equation Detection & Extraction Module
```python
def extract_equations(doc, pages_data: list, output_dir: str = "/tmp/equations") -> list:
    """Extract equations (inline, display, numbered) and their surrounding context."""
    equations = []
    
    for page_idx, page_data in enumerate(pages_data):
        text = page_data['text']
        
        # Pattern 1: LaTeX inline equations ($...$)
        for match in re.finditer(r'\$([^\$]+)\$', text):
            equations.append({
                'type': 'inline',
                'latex': match.group(1),
                'page': page_idx + 1,
                'context': extract_context(text, match.start(), match.end()),
                'char_range': [match.start(), match.end()]
            })
        
        # Pattern 2: LaTeX display equations ($$...$$, \[...\], equation environment)
        for match in re.finditer(
            r'(?:\$\$|\\\[)(.*?)(?:\$\$|\\\])', 
            text, re.DOTALL
        ):
            equations.append({
                'type': 'display',
                'latex': match.group(1).strip(),
                'page': page_idx + 1,
                'context': extract_context(text, match.start(), match.end()),
                'char_range': [match.start(), match.end()]
            })
        
        # Pattern 3: Numbered equations (Equation 5.2, Eq. (3), etc.)
        for match in re.finditer(
            r'(?:Equation|Eq\.?)\s+\(?(\d+(?:\.\d+)?)\)?',
            text
        ):
            equations.append({
                'type': 'reference',
                'label': match.group(1),
                'page': page_idx + 1,
                'context': extract_context(text, match.start(), match.end())
            })
    
    return equations

def extract_context(text: str, start: int, end: int, window_chars: int = 200) -> str:
    """Extract surrounding narrative context (e.g., 200 chars before/after)."""
    context_start = max(0, start - window_chars)
    context_end = min(len(text), end + window_chars)
    return text[context_start:context_end]
```

#### 2. Handle arXiv LaTeX Source Extraction
```python
def extract_from_arxiv_latex(arxiv_id: str) -> dict:
    """Download and extract LaTeX source from arXiv for equation preservation."""
    import tarfile
    import requests
    import tempfile
    import os
    
    # arXiv LaTeX source endpoint
    latex_url = f"https://arxiv.org/e-print/{arxiv_id}"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = f"{tmpdir}/source.tar.gz"
        
        # Download source archive
        response = requests.get(latex_url, headers={'User-Agent': 'paper-processor/1.0'})
        with open(tar_path, 'wb') as f:
            f.write(response.content)
        
        # Extract archive
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(tmpdir)
        
        # Find main .tex file
        tex_files = [f for f in os.listdir(tmpdir) if f.endswith('.tex')]
        if not tex_files:
            return None  # Fall back to PDF
        
        main_tex = os.path.join(tmpdir, tex_files[0])
        with open(main_tex, 'r', encoding='utf-8', errors='ignore') as f:
            latex_source = f.read()
        
        return {
            'format': 'latex',
            'source': latex_source,
            'equations': parse_latex_equations(latex_source)
        }

def parse_latex_equations(latex_source: str) -> list:
    """Extract all equations from LaTeX source with their definitions and numbering."""
    equations = []
    
    # Match various LaTeX equation environments
    equation_patterns = [
        (r'\$\$([^\$]+)\$\$', 'display'),
        (r'\\\[(.*?)\\\]', 'display'),
        (r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', 'numbered_display'),
        (r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}', 'multi_line'),
        (r'\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}', 'multi_line'),
        (r'\$([^\$]+)\$', 'inline'),
    ]
    
    for pattern, env_type in equation_patterns:
        for match in re.finditer(pattern, latex_source, re.DOTALL):
            latex_content = match.group(1).strip()
            
            # Extract equation label if present
            label_match = re.search(r'\\label\{([^}]+)\}', latex_content)
            label = label_match.group(1) if label_match else None
            
            equations.append({
                'type': env_type,
                'latex': latex_content,
                'label': label,
                'is_numbered': label is not None or 'numbered' in env_type,
                'char_pos': match.start()
            })
    
    return equations
```

#### 3. Extend Output Schema for Equations
```json
{
  "paper_id": "arxiv:2301.12345",
  "sections": { ... },
  "equations": [
    {
      "eq_id": "eq_5_2",
      "label": "5.2",
      "latex": "V(x,t) = \\int_0^T I(s,t) ds",
      "type": "display",
      "page": 12,
      "section": "methods",
      "context_before": "The membrane potential evolves according to:",
      "context_after": "where I(s,t) is the input current at position s and time t.",
      "is_numbered": true,
      "referenced_in": ["page_13_par_2", "discussion_section"]
    }
  ],
  "figures": [ ... ],
  "claims": [ ... ]
}
```

#### 4. Add Page-Break Reconstruction Logic
```python
def reconstruct_multipage_content(pages_data: list, item_type: str = 'equation') -> list:
    """Reconstruct items (equations, sentences) split across page breaks."""
    reconstructed = []
    buffer = ""
    buffer_start_page = 0
    
    for page_idx, page_data in enumerate(pages_data):
        text = page_data['text']
        
        # Heuristic: items incomplete (missing closing delimiter/balance)
        open_delimiters = text.count('$') % 2  # Odd = unmatched
        open_envs = (text.count(r'\begin{') - text.count(r'\end{'))
        
        if buffer and (open_delimiters == 0 and open_envs == 0):
            # Previous buffer is now complete
            reconstructed.append({
                'content': (buffer + text).strip(),
                'pages': f"{buffer_start_page}-{page_idx + 1}",
                'is_reconstructed': True
            })
            buffer = ""
        elif open_delimiters > 0 or open_envs > 0:
            # Content continues to next page
            if not buffer:
                buffer_start_page = page_idx + 1
            buffer += text + "\n"
    
    # Handle any remaining buffer
    if buffer:
        reconstructed.append({
            'content': buffer.strip(),
            'pages': f"{buffer_start_page}-end",
            'is_reconstructed': True,
            'warning': 'Incomplete (missing closing delimiter)'
        })
    
    return reconstructed
```

### Medium Priority

#### 5. Add RAG Chunking Strategy
```python
def create_equation_chunks_for_rag(equations: list, context_window: int = 500) -> list:
    """Create semantically coherent chunks for RAG indexing."""
    chunks = []
    for eq in equations:
        # Chunk = equation + surrounding context
        chunk_text = f"{eq['context_before']}\n\n[EQUATION {eq.get('label', '?')}]\n{eq['latex']}\n\n{eq['context_after']}"
        
        chunks.append({
            'id': eq['eq_id'],
            'type': 'equation_with_context',
            'content': chunk_text,
            'metadata': {
                'equation_latex': eq['latex'],
                'page': eq['page'],
                'label': eq.get('label'),
                'section': eq['section']
            },
            'embedding_priority': 'high'  # Equations often critical
        })
    
    return chunks
```

#### 6. Add LaTeX → MathML Conversion
```python
def latex_to_mathml(latex_eq: str) -> str:
    """Convert LaTeX equation to MathML for semantic representation."""
    # Option A: Use pylatexenc + amsmath support
    # Option B: Call external LaTeX ML server
    # Option C: Use sympy.latex to parse and convert
    try:
        from sympy.parsing.latex import parse_latex
        expr = parse_latex(latex_eq)
        # Can then convert to MathML via sympy.printing.mathml
        return str(expr)  # Simplified; proper MathML conversion needed
    except:
        return None  # Fallback: store only LaTeX
```

#### 7. Add Greek Symbol & Encoding Handling
```python
def normalize_equation_text(text: str) -> str:
    """Normalize special characters, Greek letters, and Unicode variants."""
    # Common PDF encoding issues with math symbols
    replacements = {
        'α': 'alpha',
        'β': 'beta',
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'θ': 'theta',
        'μ': 'mu',
        'σ': 'sigma',
        '∫': 'int',
        '∑': 'sum',
        '∏': 'prod',
        '√': 'sqrt',
        '≈': 'approx',
        '→': '->',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text
```

### Low Priority (Nice-to-Have)

- Add equation classification (e.g., differential equation, algebraic, matrix form)
- Implement equation similarity matching for duplicate detection
- Build equation knowledge graph (what variables appear in which equations)
- Generate quiz questions from equations and their context

---

## Summary

The current `paper-processor` skill is **insufficient for the stated task**. It provides a solid foundation for general paper processing (sections, claims, figures) but completely lacks the equation extraction, semantics preservation, and multi-line/page-break handling needed for RAG-friendly equation indexing.

**Key Deficits:**
1. No equation detection or extraction logic
2. No LaTeX source processing (despite mentioning it as a goal)
3. No multi-line or page-break equation reconstruction
4. No RAG-specific equation chunking strategy
5. No semantic preservation (LaTeX → MathML) capability
6. No handling of equation numbering and cross-references

**Minimum Required Changes:** Implement recommendations 1-4 (equation extraction, LaTeX parsing, schema extension, page-break handling) before the skill can handle Grossberg-style technical papers with heavy equation content.

