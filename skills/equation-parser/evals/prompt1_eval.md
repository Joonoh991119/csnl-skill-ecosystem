# Equation Parser Skill Evaluation: Prompt 1 (Core Use Case)

## Evaluation Context

**Test Prompt (Core Use Case):**
> "I have CRMB Chapter 5 (BCS/FCS) as a PDF with 40+ equations including Grossberg's boundary completion differential equations, FCS diffusion equations, and ART vigilance conditions. Many equations use ρ (vigilance), B_ijk (BCS boundary signals), F_ij (FCS filling-in). Some equations span two lines, some are numbered (5.1)-(5.47), and there are cross-references like 'substituting Eq. (5.3) into (5.12)'. I need to: extract all equations preserving numbering, convert to LaTeX+MathML+plain text, annotate Grossberg-specific notation, store in pgvector with semantic tags, and verify nothing was lost. Show me the pipeline."

**Evaluation Date:** 2026-04-14  
**Skill File Size:** 942 lines  
**Skill Complexity:** Comprehensive 8-section architecture

---

## 1. Sufficiency Assessment

### Which Sections Help?

| Section | Relevance to Test Prompt | Help Level | Specific Value |
|---------|-------------------------|------------|-----------------|
| **1. Tool Chain Architecture** | Critical | ⭐⭐⭐⭐⭐ | Provides cascading 4-stage parser (Marker → Nougat → LaTeX-OCR → pix2tex) directly applicable to "40+ equations" extraction with quality fallback |
| **2. Parsing Strategy** | Critical | ⭐⭐⭐⭐⭐ | Inline vs display math classification, equation numbering detection (matches "(5.1)-(5.47)" requirement), cross-reference mapping ("Eq. (5.3) into (5.12)") |
| **3. Quality Verification** | Critical | ⭐⭐⭐⭐⭐ | LaTeX compilation testing, fast syntax validation, completeness checking ("verify nothing was lost") |
| **4. Triple Format Output** | Critical | ⭐⭐⭐⭐⭐ | Converts to LaTeX + MathML + plain text as explicitly requested; includes accessible descriptions |
| **5. pgvector Storage** | Critical | ⭐⭐⭐⭐⭐ | Full SQL schema with semantic tags, cross-ref tracking, HNSW indexing for storage/retrieval |
| **6. Korean Math Glossary** | Helpful | ⭐⭐⭐ | Provides Korean annotations; not strictly required for CRMB Chapter 5 but adds value |
| **7. Grossberg-Specific Notation** | **Excellent** | ⭐⭐⭐⭐⭐ | **Core requirement met:** Comprehensive notation handling for ρ (vigilance), B_ijk, F_ij, domain tagging (ART, BCS, FCS, LAMINART) |
| **8. End-to-End Pipeline** | Critical | ⭐⭐⭐⭐⭐ | Full workflow from PDF to pgvector storage with stats tracking and JSON reporting |
| **M4 Pro Optimization** | Helpful | ⭐⭐⭐ | MPS device support, batch sizing, memory configuration for Apple Silicon (execution context) |
| **Dependencies** | Helpful | ⭐⭐⭐⭐ | Complete package list including Nougat, pix2tex, LaTeX2MathML, pgvector, embeddings |

### Key Strengths by Requirement

**Extraction + Numbering (5.1)-(5.47):**
- Section 2 (`classify_equation()`) explicitly handles equation numbering with regex: `r'\((\d+(?:\.\d+)?(?:[a-z])?)\)'`
- Cross-reference mapping (`build_cross_reference_map()`) connects numbered equations

**LaTeX + MathML + Plain Text:**
- Section 4 (`convert_to_triple_format()`) provides all three conversions in one function
- `latex_to_mathml()` uses latex2mathml library
- `latex_to_plain_text()` includes Grossberg symbol replacements (e.g., `\\rho` → "rho")

**Grossberg-Specific Notation (ρ, B_ijk, F_ij):**
- Section 7 has explicit entries for all three symbols
- `annotate_grossberg_notation()` identifies and tags with metadata (name, domain, description)
- Domain tagging (ART, BCS, FCS) matches "boundary completion differential equations, FCS diffusion equations, ART vigilance"

**Cross-References & Two-Line Equations:**
- Section 2 detects cross-refs: `r'(?:Eq|Equation|Eqn)\.?\s*\(?(\d+(?:\.\d+)?)\)?'`
- Section 1 Stage 2 (Nougat) handles complex multi-line equations via high-DPI rendering (300 dpi)

**pgvector Storage with Semantic Tags:**
- Section 5 defines schema with `semantic_tags TEXT[]` and GIN index
- Section 7 populates tags from Grossberg annotations: `eq["semantic_tags"] = [a["name"] for a in eq["grossberg_annotations"]]`

**Verification & Loss Prevention:**
- Section 3 includes four verification layers:
  1. `verify_latex()` - full pdflatex compilation
  2. `verify_latex_fast()` - regex-based syntax check
  3. `compare_rendered_vs_original()` - structural similarity (SSIM) against original image
  4. `equation_completeness_check()` - detects truncation, unresolved symbols, missing operands

---

## 2. Scoring: Relevance, Completeness, Actionability

### Relevance (1-5): **5/5**

**Justification:**
- Every requirement from the test prompt is directly addressed by the skill
- Grossberg notation (Section 7) is not generic—it includes domain-specific parameters with descriptions
- Equations spanning two lines are handled by Nougat (300 DPI page rendering) and OCR fallbacks
- Cross-reference detection in Section 2 is built specifically for scholarly equation styles

**Evidence:**
```python
# From Section 7: ρ (vigilance) is explicitly modeled
r'\rho': {
    "name": "vigilance parameter",
    "korean": "경계 매개변수",
    "domain": "ART",
    "description": "Controls category granularity in ART matching",
    "typical_range": "[0, 1]",
}

# From Section 2: Equation numbering detection
num_match = re.search(r'\((\d+(?:\.\d+)?(?:[a-z])?)\)\s*$', context_after)
if num_match:
    result["numbered"] = True
    result["equation_number"] = num_match.group(1)
```

### Completeness (1-5): **4.5/5**

**What is Complete:**
- ✅ 4-stage extraction pipeline with fallbacks (Marker → Nougat → LaTeX-OCR → pix2tex)
- ✅ Triple format output (LaTeX, MathML, plain text)
- ✅ Equation numbering and cross-reference mapping
- ✅ Grossberg domain tagging (ART, BCS, FCS, LAMINART)
- ✅ Verification layer (compilation test, syntax check, completeness)
- ✅ pgvector storage with HNSW indexing and semantic tags
- ✅ End-to-end pipeline from PDF to database storage
- ✅ JSON reporting with stats

**Minor Gaps:**
- **Variable definition extraction:** Section 8 mentions `variable_definitions JSONB` in schema but no code to extract "where X = ..." definitions from context
  - *Impact:* Medium—annotations like "where ρ ∈ [0,1]" won't be automatically captured
  - *Workaround:* Could be added as post-processing regex in `store_equation_chunk()`

- **Multi-language label handling:** Section 6 has Korean glossary, but no mechanism to detect/preserve Korean equation labels in PDFs
  - *Impact:* Low—assumes CRMB Chapter 5 is English; handles Korean terms in context only

- **Equation image extraction:** Implicit in Nougat/LaTeX-OCR stages but no explicit `extract_equation_bboxes()` function
  - *Impact:* Low—Marker/Nougat implicitly extract bboxes, but not exposed as standalone output

- **Ambiguous symbol handling:** Regex for cross-refs may miss some scholarly formats (e.g., "Eqs. (5.3) and (5.12)" with "and")
  - *Impact:* Low—would catch most cases but edge cases exist

### Actionability (1-5): **4.5/5**

**What Works Out of the Box:**
- ✅ All code is ready to execute (functions are self-contained, imports specified)
- ✅ SQL schema is complete and ready for `CREATE TABLE`
- ✅ End-to-end example (`process_chapter_equations()`) shows exact workflow
- ✅ MPS configuration provided for M4 Pro execution
- ✅ Dependencies list is explicit and installable via pip

**Friction Points:**
1. **Nougat Service Setup:** Skill mentions "NOUGAT_SETUP" but assumes local service on port 8503
   - Must be running: `nougat_api --port 8503 --model 0.1.0-base &`
   - No fallback if service is unavailable (would error in `run_nougat_on_page()`)
   - *Mitigation:* Add try-except wrapper with clear error message

2. **LaTeX Compilation:** Requires pdflatex and ImageMagick installed
   - Listed in dependencies but no guidance on troubleshooting if missing
   - `verify_latex()` will fail silently if pdflatex not in PATH
   - *Mitigation:* Add pre-flight check in `process_chapter_equations()`

3. **Database Connection:** Code assumes `conn` (psycopg2) is already open
   - No connection initialization code provided
   - `store_equation_chunk()` expects prepared embedder model
   - *Mitigation:* Add boilerplate for connection and embedder initialization

4. **Embedder Model:** Code assumes `embedder.encode()` returns `{'dense_vecs': [...]}`
   - Matches FlagEmbedding BGE-M3 API, but not explicitly stated
   - 1024-dim assumption is hard-coded (`assert len(vector) == 1024`)
   - *Mitigation:* Add setup code for FlagEmbedding initialization

---

## 3. Gaps and Concrete Improvement Recommendations

### Gap 1: Variable Definition Extraction (Medium Priority)

**Current State:** Schema includes `variable_definitions JSONB` but no extraction code.

**Needed Code:**
```python
def extract_variable_definitions(context_after: str) -> dict:
    """Extract definitions like 'where ρ ∈ [0,1]' or 'B_ijk: BCS boundary signal'"""
    definitions = {}
    
    # Pattern 1: "where X = ..." or "where X ∈ ..."
    where_patterns = [
        r'where\s+(\w+|\\\w+)\s*[:=∈]\s*([^,.\n]+)',
        r'(\w+|\\\w+)\s*:\s*([^,.\n]+(?:in [^,.\n]+)?)',
    ]
    
    for pattern in where_patterns:
        for m in re.finditer(pattern, context_after, re.IGNORECASE):
            var_name = m.group(1)
            definition = m.group(2).strip()
            if var_name not in definitions:
                definitions[var_name] = definition
    
    return definitions

# Usage in store_equation_chunk():
equation['variable_definitions'] = extract_variable_definitions(
    equation.get('context_after', '')
)
```

**Impact:** Enables RAG queries like "show equations where ρ is in [0, 1]" and automatic parameter range validation.

---

### Gap 2: Nougat Service Robustness (High Priority)

**Current State:** `run_nougat_on_page()` assumes service is running; no fallback or error messaging.

**Needed Code:**
```python
def run_nougat_on_page_safe(pdf_path: str, page_num: int, fallback_to_latex_ocr=True) -> dict:
    """Run Nougat with error handling and graceful fallback."""
    import requests
    from requests.exceptions import ConnectionError, Timeout
    
    try:
        response = requests.post(
            NOUGAT_URL,
            files={"file": ("page.png", img_bytes, "image/png")},
            timeout=30
        )
        if response.status_code == 200:
            return {"markdown": response.json().get("text", ""), "source": "nougat"}
    except (ConnectionError, Timeout) as e:
        if fallback_to_latex_ocr:
            print(f"⚠️  Nougat unavailable ({e}). Falling back to LaTeX-OCR.")
            # Fall through to LaTeX-OCR stage
        else:
            raise RuntimeError(f"Nougat service unavailable at {NOUGAT_URL}: {e}")
    
    return {"error": "nougat_failed", "source": "nougat"}

# Update cascading pipeline:
def parse_equation(...):
    # ...
    nougat_result = run_nougat_on_page_safe(pdf_path, page_num, fallback_to_latex_ocr=True)
    # ...
```

**Impact:** Makes skill production-ready; prevents silent failures and provides clear diagnostics.

---

### Gap 3: Database & Embedder Initialization (High Priority)

**Current State:** `process_chapter_equations()` expects `conn` and `embedder` parameters; no initialization code.

**Needed Code:**
```python
def initialize_database(db_host: str, db_name: str, db_user: str, db_pass: str):
    """Initialize PostgreSQL connection and create schema."""
    import psycopg2
    from psycopg2.extensions import connection
    
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pass,
    )
    
    # Create pgvector extension
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(EQUATION_CHUNK_SCHEMA)
    conn.commit()
    
    return conn

def initialize_embedder(model_name: str = "BAAI/bge-m3"):
    """Initialize embedding model (BGE-M3 for 1024-dim dense vectors)."""
    from FlagEmbedding import BGEM3FlagModel
    
    embedder = BGEM3FlagModel(model_name, use_fp16=True)
    return embedder

# Usage:
if __name__ == "__main__":
    conn = initialize_database("localhost", "equations_db", "postgres", "password")
    embedder = initialize_embedder()
    
    stats = process_chapter_equations(
        "/path/to/CRMB_Chapter_5.pdf",
        chapter_num=5,
        conn=conn,
        embedder=embedder
    )
```

**Impact:** Enables users to run the skill end-to-end without external setup code.

---

### Gap 4: Cross-Reference Ambiguity Handling (Low-Medium Priority)

**Current State:** `classify_equation()` cross-ref detection may miss plural forms and conjunctions.

**Current Regex:**
```python
r'(?:Eq|Equation|Eqn)\.?\s*\(?(\d+(?:\.\d+)?)\)?'
```

**Issue:** Misses "Eqs. (5.3) and (5.12)" → only captures first equation number.

**Improved Code:**
```python
def extract_equation_references(context: str) -> list:
    """Extract all equation references including plurals and conjunctions."""
    refs = []
    
    # Pattern 1: Single ref "Eq. (5.3)"
    pattern1 = r'(?:Eqs?|Equations?|Eqns?)\.?\s*\(?(\d+(?:\.\d+)?)\)?'
    
    # Pattern 2: Multiple refs "Eqs. (5.3) and (5.12)" or "(5.3)-(5.12)"
    pattern2 = r'(?:Eqs?|Equations?)\.?\s*\((\d+(?:\.\d+)?)\)(?:\s*(?:and|,|;|-)\s*\(?(\d+(?:\.\d+)?)\)?)+'
    
    # Collect all matches from pattern1
    for m in re.finditer(pattern1, context):
        refs.append(m.group(1))
    
    # Handle pattern2 (multiple refs in one phrase)
    for m in re.finditer(pattern2, context):
        for group in m.groups():
            if group:
                refs.append(group)
    
    return list(set(refs))  # Deduplicate
```

**Impact:** Improves cross-reference completeness for scholarly text; prevents missing related equations.

---

### Gap 5: Missing Integration Glue Code (Medium Priority)

**Current State:** Section 8 mentions "Integration Points" (db-pipeline, paper-processor, rag-pipeline) but no actual integration code.

**Needed Additions:**

1. **Input from paper-processor:** No code to consume output from upstream PDF parsing
2. **Output to rag-pipeline:** `search_equations()` expects query_vector but no example RAG query flow
3. **Error reporting to eval-runner:** No structured logging for evaluation metrics

**Suggested Code Structure:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class EquationExtractionReport:
    """Report for eval-runner integration."""
    chapter: int
    total_equations: int
    verified: int
    failed: int
    methods_used: dict
    storage_succeeded: int
    storage_failed: int
    avg_parse_quality: float
    completeness_issues: dict  # counts of issue types
    grossberg_notation_found: int
    
    def to_metrics(self) -> dict:
        """Convert to metrics for eval-runner."""
        return {
            "extraction_rate": self.verified / self.total_equations if self.total_equations > 0 else 0,
            "storage_rate": self.storage_succeeded / self.total_equations if self.total_equations > 0 else 0,
            "quality_score": self.avg_parse_quality,
            "grossberg_coverage": self.grossberg_notation_found / self.total_equations,
        }
```

---

### Gap 6: Two-Line Equation Handling Documentation (Low Priority)

**Current State:** Skill handles multi-line equations implicitly (Nougat uses high-DPI rendering) but no explicit documentation.

**Suggested Addition:**

```markdown
### Multi-Line Equation Handling

Multi-line equations (those spanning 2+ lines in PDF) are handled at Stage 2 (Nougat) via:
- High DPI rendering: `pix = page.get_pixmap(dpi=300)`
- Full page context: Nougat processes entire pages, not cropped regions
- LaTeX environment preservation: Equations in \begin{align}...\end{align} are preserved

**Example:** CRMB Chapter 5 BCS boundary completion equations typically span 2-3 lines:
\```
dB_ij/dt = -A*B_ij + (B+1)*∑_k C_ijk - B*∑_n B_in*∑_m [C_ijm - 1]
\```

Marker stage extracts as single \$\$...\$\$ block; Nougat verifies continuity.
```

---

## Summary Table: Gaps & Severity

| Gap | Severity | Effort | Impact | Status |
|-----|----------|--------|--------|--------|
| Variable definition extraction | Medium | 15 min | Enables semantic RAG queries | New code needed |
| Nougat service robustness | High | 20 min | Prevents silent failures in production | New code needed |
| Database & embedder init | High | 30 min | Makes skill executable end-to-end | New code needed |
| Cross-ref plural handling | Medium | 10 min | Catches all equation relationships | Enhance existing regex |
| Integration glue (eval-runner) | Medium | 20 min | Enables automated evaluation | New dataclass + method |
| Multi-line equation docs | Low | 5 min | Clarifies non-obvious behavior | Documentation only |

---

## Final Scoring Summary

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| **Relevance to CRMB Chapter 5 Use Case** | **5/5** | All requirements (numbering, triple format, Grossberg notation, pgvector) are directly addressed |
| **Completeness** | **4.5/5** | Core pipeline is complete; 3 gaps (variable extraction, service robustness, initialization) are fixable |
| **Actionability** | **4.5/5** | Code is mostly ready but requires external setup (DB, embedder, Nougat service) |
| **Code Quality** | **4/5** | Well-structured, comprehensive; lacks error handling in a few critical paths |
| **Documentation** | **4/5** | Clear architecture and examples; missing some integration and edge-case docs |
| **Overall Evaluation** | **4.5/5** | **Production-ready with minor enhancements; suitable for 40+ equation extraction pipeline** |

---

## Recommended Next Steps

1. **For Immediate Use:** Add error handling wrapper around Nougat service (Gap 2) and database initialization (Gap 3)
2. **For Robustness:** Implement variable definition extraction (Gap 1) and improved cross-ref detection (Gap 4)
3. **For Integration:** Add eval-runner compatible reporting (Gap 5) and integration examples
4. **For Documentation:** Clarify two-line equation handling and add troubleshooting guide for missing pdflatex/ImageMagick

**Recommended Skill Status:** ✅ **Deploy with caveats** (add 3 critical error handlers; document external dependencies clearly)
