# Evaluation Prompt 3: Robustness Analysis
## CRMB Chapter 8 (Surface Perception) - Edge Case Handling

**Evaluator**: Claude Haiku 4.5  
**Date**: 2026-04-14  
**Focus**: Resilience to complex document structures with multiple failure points

---

## Scenario Context

Processing CRMB Chapter 8 (Surface Perception) with challenging characteristics:
- **10 full-page figures** with subfigures (a-d)
- **Tables** comparing model predictions vs human data
- **Footnotes** with equation corrections from errata
- **Appendix** with supplementary equations
- **Implementation**: Marker + chunker_v2.py pipeline

---

## Failure Mode Analysis

### (1) Subfigure Caption Extraction as Body Text

**Observed Behavior**: Marker processes the chapter but extracts subfigure captions (e.g., "(a) Condition 1", "(b) Condition 2") as body text rather than associating them with figures.

**Root Cause**:
The `extract_figures()` function in SKILL.md relies on caption detection via regex:
```python
caption_matches = re.finditer(
    r'(?:Figure|Fig\.?)\s+(\d+)[.:]\s*(.+?)(?=\n\n|\n(?:Figure|Fig|Table)|\Z)',
    page_data['text'], re.DOTALL | re.IGNORECASE
)
```
This pattern matches "Figure 8.1: [main caption]" but **does not handle subfigure patterns** like:
- "(a) Subfigure caption" (inline, without "Figure" prefix)
- "a. Sub-caption" (alternative numbering)
- Multi-line subfigure descriptions

**Impact**:
- Subfigure text (e.g., "(a) Stimulus presented at 45°") appears in `sections['results']['text']` as standalone sentences
- RAG chunking treats these as content rather than metadata
- Downstream tutor-content-gen may create quiz questions from subfigure descriptions
- Loss of hierarchical structure (main figure → subfigures)

**Evidence from SKILL.md**:
- Figure extraction does not distinguish main captions from subfigure labels
- No subfigure grouping logic in output schema (only `figure_num`, `caption`, `page`)

**Severity**: **MEDIUM** — Information is preserved but structural semantics are lost

---

### (2) Footnote Loss

**Observed Behavior**: Marker processes the chapter but drops all footnotes entirely.

**Root Cause**:
The skill has **no footnote detection or extraction** in its pipeline:
- `extract_from_pdf()` calls `page.get_text("text")` (plain text mode)
- `detect_sections()` and downstream processing only work with `section['text']`
- No regex pattern or PyMuPDF API call to identify footnote regions
- Marker's markdown output may preserve footnotes as `[^1]` references, but the skill does not process them

**Code Gap**:
```python
# MISSING: Footnote extraction logic
# No pattern for footnote indicators: [1], ^1, etc.
# No mapping of footnote text to inline citations
```

**Impact**:
- Equation corrections from errata (often in footnotes) are completely lost
- Qualifying statements ("...as noted in footnote 3") become orphaned
- Critical clarifications unreachable by RAG indexing
- Quality degradation for papers with dense supplementary notes

**Evidence from SKILL.md**:
- Input handling (PDF/arXiv/Zotero) does not mention footnotes
- Section detection regex does not target footnote markers
- Output schema has no `footnotes` or `corrections` field

**Severity**: **HIGH** — Critical information loss with no recovery path

---

### (3) Appendix Equations Included in Main Equation Count

**Observed Behavior**: The skill counts supplementary equations in Chapter 8 appendix as part of the main chapter equation total, inflating the count and obscuring the distinction between core and supplementary content.

**Root Cause**:
The `detect_equations()` function lacks **section awareness**:
```python
def detect_equations(page, text_blocks: list) -> list:
    equations = []
    for block in page.get_text("dict")['blocks']:
        # ... detection logic ...
        equations.append({...})  # No check: is this in appendix?
    return equations
```

The output schema includes an `equations` list but **no field for equation context** (`section`, `is_supplementary`, `appendix_ref`). Integration with section detection occurs after equation extraction, so appendix boundaries are not enforced.

**Code Gap**:
```python
# MISSING: Appendix detection before equation extraction
# MISSING: Equation classification (main vs supplementary)
# Current schema:
{
  "equation_id": "eq_2.3",  # No indicator of appendix origin
  "section": "methods",  # Could be misleading if from appendix
  ...
}
```

**Impact**:
- RAG chunking treats appendix equations with same weight as core derivations
- Tutor-content-gen may generate quiz questions from supplementary material
- Search/filtering by "main paper equations" is impossible
- CRMB context: Appendix equations are often alternative derivations; conflating them skews learning focus

**Evidence from SKILL.md**:
- Section detection includes `supplementary` label, but equations are extracted before/independently of section context
- Equation output lacks `is_supplementary: bool` field
- Batch processing quality checks do not validate equation-to-section mapping

**Severity**: **MEDIUM-HIGH** — Structural ambiguity; downstream systems must re-parse to filter

---

### (4) Table with Merged Cells Rendered as Garbled Text

**Observed Behavior**: A table comparing model predictions vs human data renders as corrupted/unreadable text due to merged cells.

**Root Cause**:
The skill **does not explicitly handle tables** at all. The SKILL.md file:
- Contains no `extract_tables()` function
- Does not document table detection or parsing
- Relies on Marker to convert tables to markdown, then passes through as-is

Marker's markdown conversion **fails on merged cells**:
- Markdown table syntax (pipes `|`) cannot represent merged cells
- Marker may output nonsensical cell boundaries or truncated content
- The garbled output is then captured as-is in section text

**Code Gap**:
```python
# MISSING: Table detection
# MISSING: Validation of table markdown (cell count consistency)
# MISSING: Fallback for complex tables (extract as image + caption)
# MISSING: Schema field for table metadata

# Expected but absent:
def extract_tables(doc, page_data: list) -> list:
    """Extract tables with metadata."""
    # — No implementation
```

**Impact**:
- RAG chunks contain corrupted data (e.g., "| Model | Human | ... ||| prediction | ", misaligned cells)
- Tutor-content-gen cannot parse the table into structured quiz questions
- Full-text search returns false positives (garbled text matches random queries)
- CRMB context: Quantitative comparisons (core to understanding) become inaccessible

**Evidence from SKILL.md**:
- Figure & Table Extraction section has code for figures only
- No `extract_tables()` implementation
- Output schema contains `figures` array but no `tables` array
- Quality verification checks do not include table validation

**Severity**: **HIGH** — Rendered data is corrupted; downstream systems cannot recover

---

## Robustness Scoring

### Dimension: Edge Case Handling

| Failure Mode | Coverage | Recovery | Root Cause | Score |
|---|---|---|---|---|
| Subfigure captions as body text | Partial (main figures only) | Manual re-parsing needed | Regex too narrow; no subfigure parser | 2/5 |
| Footnote loss | **None** | Impossible; data unrecoverable | No footnote detection logic | 1/5 |
| Appendix equations in main count | Partial (section detection exists but not wired) | Manual filtering possible | Missing equation-to-section mapping | 2/5 |
| Merged cells → garbled table | **None** (relies on Marker) | Impossible for complex tables | No table validation or fallback | 1/5 |

### Overall Robustness Score: **1.5 / 5**

**Interpretation**:
- **1-2/5**: Skill fails on standard document complexity; edge cases cause data loss or corruption
- Subfigure and table handling are stub implementations
- No graceful degradation (garbled table is worse than "table skipped" message)
- Footnote loss is silent (no warning logged)

---

## Specific Gaps & Improvements

### Gap 1: Subfigure Hierarchy

**Current**: Flat figure list with single caption per figure number

**Needed**:
```python
def extract_subfigures(page_text: str, figure_num: int) -> dict:
    """Parse subfigure hierarchy (a-d) with individual captions."""
    pattern = rf'(?:Figure|Fig\.?)\s+{figure_num}[:.]\s*(.+?)(?=\nFig|$)'
    main_caption = re.search(pattern, page_text, re.DOTALL)
    
    # Detect subfigure labels
    subfigs = re.findall(
        r'\(([a-z])\)\s+(.+?)(?=\n\([a-z]\)|\n(?:Figure|Fig)|$)',
        page_text, re.DOTALL | re.IGNORECASE
    )
    
    return {
        'figure_num': figure_num,
        'caption': main_caption.group(1) if main_caption else '',
        'subfigures': [
            {'label': sub[0], 'caption': sub[1].strip()}
            for sub in subfigs
        ]
    }
```

**Output Extension**:
```json
{
  "figures": [
    {
      "figure_num": 8.1,
      "caption": "Visual surface perception mechanisms",
      "subfigures": [
        {"label": "a", "caption": "Stimulus at 45°"},
        {"label": "b", "caption": "Neural response pattern"},
        {"label": "c", "caption": "Predicted model output"},
        {"label": "d", "caption": "Comparison with human judgment"}
      ]
    }
  ]
}
```

**Implementation Effort**: 2-3 hours  
**Value**: Enables structured quiz generation from subfigures; RAG precision improves

---

### Gap 2: Footnote Extraction & Mapping

**Current**: Footnotes are discarded; no mention in error logs

**Needed**:
```python
def extract_footnotes(doc) -> dict:
    """Extract footnotes and map to inline text."""
    footnotes = {}
    
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")['blocks']
        
        # Detect footnote regions (usually bottom of page, smaller font)
        for block in blocks:
            if block['type'] == 0:  # Text block
                # Check if block is footer region
                if block['bbox'][1] > page.rect.height * 0.85:
                    text = ''.join(
                        ''.join(span['text'] for span in line['spans'])
                        for line in block['lines']
                    )
                    # Parse footnote markers [1], ^1, etc.
                    for match in re.finditer(r'[\[\^](\d+)[\]\s]+(.+?)(?=[\[\^]|$)', text):
                        footnotes[f"fn_{match.group(1)}"] = {
                            'number': match.group(1),
                            'text': match.group(2).strip(),
                            'page': page_num + 1
                        }
    
    return footnotes

def map_footnotes_to_text(text: str, footnotes: dict) -> str:
    """Inject footnote content into sections referencing them."""
    for fn_id, fn_data in footnotes.items():
        marker = f"[^{fn_data['number']}]"
        if marker in text:
            # Store as structured reference, not inline replacement
            pass
    return text
```

**Output Extension**:
```json
{
  "sections": {
    "methods": "...[^1] equation derivation..."
  },
  "footnotes": {
    "fn_1": {
      "number": "1",
      "text": "Equation (2.3) corrected in errata: ...",
      "page": 12,
      "referenced_in": ["methods"]
    }
  }
}
```

**Implementation Effort**: 3-4 hours  
**Value**: Recovers critical errata; enables correction-aware RAG indexing

---

### Gap 3: Appendix Segmentation & Equation Classification

**Current**: Equations counted globally; no appendix flag

**Needed**:
```python
def classify_section_boundaries(doc, text: str) -> dict:
    """Detect appendix and supplementary regions."""
    boundaries = {
        'main_end': 0,
        'appendix_start': None,
        'supplementary_start': None
    }
    
    appendix_patterns = [
        r'(?:^|\n)\s*(?:APPENDIX|Appendix|SUPPLEMENT(?:ARY|AL))',
        r'(?:^|\n)\s*(?:A|S)(?:\.|:)\s+(?:Additional|Supplementary|Extended)',
    ]
    
    for pattern in appendix_patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            boundaries['appendix_start'] = match.start()
            break
    
    return boundaries

def extract_equations_with_context(doc, equation_text: str, boundaries: dict) -> dict:
    """Extract equation with appendix/main classification."""
    eq_pos = doc.text.find(equation_text)
    
    is_supplementary = (
        boundaries['appendix_start'] is not None and
        eq_pos > boundaries['appendix_start']
    )
    
    return {
        'equation_id': 'eq_X.Y',
        'latex': '...',
        'is_supplementary': is_supplementary,
        'section_scope': 'appendix' if is_supplementary else 'main',
        'page': page_num
    }
```

**Output Extension**:
```json
{
  "equations": [
    {
      "equation_id": "eq_8.2",
      "latex": "...",
      "section": "methods",
      "is_supplementary": false
    },
    {
      "equation_id": "eq_8.A1",
      "latex": "...",
      "section": "appendix",
      "is_supplementary": true,
      "label_hint": "A1"
    }
  ],
  "equation_summary": {
    "main_count": 12,
    "appendix_count": 8
  }
}
```

**Implementation Effort**: 2-3 hours  
**Value**: Filters/weights by supplementary status; tutor avoids overloading learner with alternative derivations

---

### Gap 4: Table Extraction & Fallback Handling

**Current**: Tables pass through Marker → markdown; no validation or fallback

**Needed**:
```python
def extract_tables_safe(doc, page_data: list) -> list:
    """Extract tables with validation and fallback."""
    tables = []
    
    for page_idx, page in enumerate(doc):
        blocks = page.get_text("dict")['blocks']
        
        for block in blocks:
            if block['type'] != 1:  # Skip non-table blocks
                continue
            
            # Attempt markdown table parsing
            table_text = ''.join(
                ''.join(span['text'] for span in line['spans'])
                for line in block.get('lines', [])
            )
            
            # Validate markdown table
            if is_valid_markdown_table(table_text):
                tables.append({
                    'type': 'markdown',
                    'content': table_text,
                    'page': page_idx + 1,
                    'validated': True
                })
            else:
                # Fallback: Extract as structured image + caption
                print(f"Warning: Table on page {page_idx+1} has invalid structure (merged cells?)")
                tables.append({
                    'type': 'image_fallback',
                    'caption': f'Table {len(tables)+1}: [structure not parsable]',
                    'page': page_idx + 1,
                    'validated': False,
                    'reason': 'merged_cells_or_complex_layout'
                })
    
    return tables

def is_valid_markdown_table(text: str) -> bool:
    """Check table row consistency."""
    lines = text.strip().split('\n')
    if len(lines) < 2:
        return False
    
    # Extract pipe count from first row
    expected_cols = text.count('|') // len(lines)
    
    # Verify all rows have same column count
    for line in lines:
        if line.count('|') != expected_cols:
            return False
    
    return True
```

**Output Extension**:
```json
{
  "tables": [
    {
      "table_id": "tbl_8.1",
      "caption": "Model predictions vs human data",
      "type": "markdown",
      "content": "| Condition | Model | Human | ... |",
      "page": 15,
      "validated": true,
      "validated_status": "pass"
    },
    {
      "table_id": "tbl_8.2",
      "caption": "Table 8.2: Comparison metrics",
      "type": "image_fallback",
      "page": 16,
      "validated": false,
      "note": "Merged cells detected; table extracted as image. Manual review required."
    }
  ]
}
```

**Implementation Effort**: 3-4 hours  
**Value**: Detects & reports table issues; RAG chunker knows to skip/defer corrupted tables

---

## Summary: Robustness Maturity Model

| Level | Definition | Current Skill State |
|---|---|---|
| **1. No Coverage** | Feature absent or completely broken | ✓ Footnotes, tables (no implementation) |
| **2. Partial Coverage** | Basic handling; fails on variants | ✓ Subfigures, appendix equations (limited regex) |
| **3. Robust** | Handles common cases; graceful degradation on edge cases | — |
| **4. Comprehensive** | Covers variants; detailed validation & logging | — |
| **5. Defensive** | Validates all steps; detailed error reporting; recovery options | — |

**Current Position**: **Level 2 / 5** (partial coverage with edge case brittleness)

---

## Recommendations (Priority Order)

1. **CRITICAL (Week 1)**:
   - Add footnote extraction + inline mapping (Gap 2)
   - Add table validation + image fallback (Gap 4)
   - Both are **silent failures** currently; detection + logging prevents downstream corruption

2. **HIGH (Week 2)**:
   - Add appendix/supplementary detection (Gap 3)
   - Extend equation output schema with `is_supplementary` flag
   - Implement subfigure hierarchy parsing (Gap 1)

3. **MEDIUM (Week 3)**:
   - Add per-section validation checks (section word count, equation count, figure count)
   - Implement quality report (`metadata.json` with pass/fail per chapter)
   - Log all skipped/degraded elements with locations (page, byte offset)

4. **LONG-TERM**:
   - Integrate OCR fallback for garbled table regions (Tesseract + confidence thresholding)
   - Build visual table understanding model (detect cell boundaries via computer vision)
   - Add heading hierarchy validation (h1 > h2 > h3 nesting rules)

---

## Test Cases for Validation

After implementing improvements, test against:

1. **Chapter 8 CRMB**: 10 figures with subfigures, dense footnotes, appendix equations, merged-cell table
2. **Chapter 13** (Learning): Heavy on equations; test appendix classification
3. **Synthetic edge case**: PDF with:
   - Subfigure labels across page boundaries
   - Footnote chain (footnote referencing another footnote)
   - Table with 3-way merged cells
   - Equation in figure caption (recursive structure)

**Success Criteria**:
- All 4 failure modes are either handled correctly or logged as "SKIP with reason"
- No silent data loss; all skipped elements appear in quality report
- Downstream RAG chunks are parseable (no garbled content)
- Tutor-content-gen can generate valid quiz questions from processed output

