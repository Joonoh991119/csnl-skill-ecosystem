---
name: paper-processor
description: >
  Scientific paper processing and structured information extraction pipeline.
  Extracts structured sections (abstract, methods, results, discussion), key claims,
  figures with captions, equations, and citation metadata from academic papers.
  Supports PDF, LaTeX source (arXiv), and Zotero library items. Outputs structured
  JSON, Notion pages, or markdown for downstream use by RAG pipelines and tutoring systems.
  MANDATORY TRIGGERS: Any request involving paper analysis, literature review,
  paper summarization, extracting methods or results, citation extraction, figure
  extraction, reading scientific PDFs, parsing LaTeX, creating structured summaries,
  processing papers for a knowledge base, or bulk paper ingestion. Trigger when user
  says "summarize this paper", "extract the methods", "what are the key findings",
  "process these papers", "add this paper to the knowledge base", or "break down
  this paper". Also trigger for arXiv IDs (e.g., "2301.12345") or DOIs.
---

# Scientific Paper Processor

You extract structured, machine-readable information from academic papers to feed into
RAG knowledge bases and tutoring content generators.

## Why This Matters

The quality of a RAG tutor depends directly on how well its source documents are processed.
A paper that's just raw text loses structure — the distinction between a method description
and a result claim disappears. This skill preserves that structure so downstream systems
(tutor-content-gen, rag-pipeline) can use it intelligently.

## Processing Pipeline

```
Input (PDF/arXiv/Zotero) → Text Extraction → Section Detection → Claim Extraction
                                                                        ↓
Output (Structured JSON) ← Citation Linking ← Figure/Table Extraction ←┘
```

## Input Handling

### From PDF
```python
import fitz  # PyMuPDF

def extract_from_pdf(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    raw = {
        'metadata': {
            'title': doc.metadata.get('title', ''),
            'authors': doc.metadata.get('author', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'page_count': len(doc)
        },
        'pages': []
    }
    for page in doc:
        raw['pages'].append({
            'text': page.get_text("text"),
            'blocks': page.get_text("dict")['blocks'],  # Structured blocks
            'images': page.get_images(full=True)
        })
    return raw
```

### From arXiv (via arXiv LaTeX MCP if available, else PDF)
```python
def extract_from_arxiv(arxiv_id: str) -> dict:
    """Fetch paper from arXiv. Prefer LaTeX source for equation preservation."""
    # Try LaTeX source first (better equation/figure extraction)
    # Fall back to PDF if LaTeX unavailable
    import requests
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    # ... download and process
```

### From Zotero (via connected Zotero MCP)
```
Use: zotero.get_content(item_key) → extract PDF attachment
Then: zotero.get_item_details(item_key) → metadata
Then: zotero.get_annotations(item_key) → user highlights/notes
```

## Section Detection

Academic papers follow predictable structures. Detect and label each section:

```python
import re

SECTION_PATTERNS = [
    (r'abstract', 'abstract'),
    (r'introduction', 'introduction'),
    (r'(?:materials?\s+and\s+)?methods?', 'methods'),
    (r'results?(?:\s+and\s+discussion)?', 'results'),
    (r'discussion', 'discussion'),
    (r'conclusion', 'conclusion'),
    (r'references?|bibliography', 'references'),
    (r'supplementary|supporting\s+information', 'supplementary'),
    (r'acknowledgment', 'acknowledgments'),
    (r'(?:data|code)\s+availability', 'data_availability'),
]

def detect_sections(full_text: str) -> list:
    """Split paper into labeled sections."""
    sections = []
    positions = []

    for pattern, label in SECTION_PATTERNS:
        for match in re.finditer(
            rf'\n\s*(?:\d+\.?\s*)?({pattern})\s*\n',
            full_text, re.IGNORECASE
        ):
            positions.append((match.start(), label, match.group()))

    positions.sort(key=lambda x: x[0])

    for i, (pos, label, header) in enumerate(positions):
        end = positions[i+1][0] if i+1 < len(positions) else len(full_text)
        sections.append({
            'section': label,
            'header': header.strip(),
            'text': full_text[pos:end].strip(),
            'char_range': [pos, end]
        })

    return sections
```

## Key Claim Extraction

Extract testable/quotable claims from Results and Discussion sections:

```python
CLAIM_INDICATORS = [
    r'we found that',
    r'our results (?:show|demonstrate|indicate|suggest|reveal)',
    r'there was a (?:significant|reliable|robust)',
    r'consistent with',
    r'these (?:results|findings|data) (?:suggest|indicate|demonstrate)',
    r'p\s*[<>=]\s*[\d.]+',  # Statistical test results
    r'F\s*\(\s*\d+\s*,\s*\d+\s*\)\s*=',  # F-statistics
    r't\s*\(\s*\d+\s*\)\s*=',  # t-statistics
    r'r\s*=\s*[\d.]+',  # Correlations
    r'β\s*=\s*[\d.]+',  # Regression coefficients
]

def extract_claims(sections: list) -> list:
    """Extract key empirical claims with their statistical evidence."""
    claims = []
    for section in sections:
        if section['section'] not in ('results', 'discussion'):
            continue
        sentences = re.split(r'(?<=[.!?])\s+', section['text'])
        for sent in sentences:
            for pattern in CLAIM_INDICATORS:
                if re.search(pattern, sent, re.IGNORECASE):
                    claims.append({
                        'text': sent.strip(),
                        'section': section['section'],
                        'type': 'empirical_claim',
                        'has_stats': bool(re.search(r'p\s*[<>=]|F\s*\(|t\s*\(|r\s*=', sent))
                    })
                    break
    return claims
```

## Figure & Table Extraction

```python
def extract_figures(doc, pages_data: list, output_dir: str = "/tmp/figures") -> list:
    """Extract figure images and their captions."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    figures = []
    for page_idx, page_data in enumerate(pages_data):
        # Find figure captions in text
        caption_matches = re.finditer(
            r'(?:Figure|Fig\.?)\s+(\d+)[.:]\s*(.+?)(?=\n\n|\n(?:Figure|Fig|Table)|\Z)',
            page_data['text'], re.DOTALL | re.IGNORECASE
        )
        for match in caption_matches:
            figures.append({
                'figure_num': int(match.group(1)),
                'caption': match.group(2).strip(),
                'page': page_idx + 1,
            })

        # Extract actual images from page and save as PNG
        page = doc[page_idx]
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:  # CMYK → RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_path = f"{output_dir}/fig_p{page_idx+1}_{img_idx}.png"
                pix.save(img_path)
                # Link image to nearest figure caption by page proximity
                for fig in figures:
                    if fig['page'] == page_idx + 1 and 'image_path' not in fig:
                        fig['image_path'] = img_path
                        break
            except Exception as e:
                print(f"Warning: Could not extract image {xref} on page {page_idx+1}: {e}")

    return figures
```

## Output Schema

The final structured output for each paper:

```json
{
  "paper_id": "arxiv:2301.12345",
  "title": "Visual Working Memory Capacity Limits in Neural Networks",
  "authors": ["Author A", "Author B"],
  "year": 2023,
  "journal": "Nature Neuroscience",
  "doi": "10.1038/s41593-023-xxxxx",
  "sections": {
    "abstract": "...",
    "introduction": "...",
    "methods": "...",
    "results": "...",
    "discussion": "..."
  },
  "claims": [
    {
      "text": "VWM capacity was significantly reduced under high cognitive load (t(29) = 3.45, p < .01)",
      "section": "results",
      "type": "empirical_claim",
      "has_stats": true
    }
  ],
  "figures": [
    {
      "figure_num": 1,
      "caption": "Mean VWM capacity (K) as a function of set size and cognitive load condition.",
      "page": 4
    }
  ],
  "key_terms": ["visual working memory", "capacity", "cognitive load", "set size"],
  "citation_count": null,
  "zotero_key": "ABC123XY"
}
```

## Batch Processing

For processing multiple papers (e.g., entire Zotero collection):

```python
def batch_process(paper_sources: list, output_dir: str) -> dict:
    """Process multiple papers and save structured outputs."""
    results = {'processed': 0, 'failed': 0, 'papers': []}
    for source in paper_sources:
        try:
            paper = process_single_paper(source)
            save_json(paper, f"{output_dir}/{paper['paper_id']}.json")
            results['processed'] += 1
            results['papers'].append(paper)
        except Exception as e:
            results['failed'] += 1
            print(f"Failed: {source} — {e}")
    return results
```

## Integration Points

- **rag-pipeline**: Structured output feeds directly into chunking stage (section-aware chunks)
- **tutor-content-gen**: Claims + figures → quiz questions, concept explanations
- **sci-viz**: Re-creates/adapts figures from extracted data descriptions
- **Zotero MCP**: Source documents, annotations, tags
- **Notion MCP**: Write structured summaries as Notion pages


## Equation Extraction & LaTeX Representation

Mathematical equations are critical for scientific papers (especially textbooks like Grossberg's CRMB)
but are often lost in plain-text extraction. This section preserves equation structure for RAG indexing.

### Equation Detection

Use PyMuPDF font and layout analysis to identify equation regions:

```python
import fitz
from collections import Counter

def detect_equations(page, text_blocks: list) -> list:
    """Identify equation regions by font changes, centering, and numbering patterns."""
    equations = []
    
    for block in page.get_text("dict")['blocks']:
        if block['type'] != 0:  # Skip non-text blocks
            continue
        
        block_text = ''.join(
            ''.join(line['spans'][0]['text'] for line in block['lines'])
            for block in [block]
        )
        
        # Heuristic 1: Numbered equations (Eq. 1, Equation 2.3, etc.)
        if any(re.search(r'(?:Eq|Equation|Formula|Eqn)\.?\s*\(?(\d+(?:\.\d+)?)\)?', 
                        block_text)):
            equations.append({
                'type': 'numbered_equation',
                'raw_text': block_text.strip(),
                'bbox': block['bbox']
            })
        
        # Heuristic 2: Centered text with special characters (math symbols)
        if (block['bbox'][0] > page.rect.width * 0.2 and  # Centered region
            block['bbox'][2] < page.rect.width * 0.8 and
            any(c in block_text for c in 'αβγδεμσΣ∫∑∏±×÷≈≠≤≥')):
            equations.append({
                'type': 'centered_math',
                'raw_text': block_text.strip(),
                'bbox': block['bbox']
            })
    
    return equations
```

### Multi-line & Page-break Handling

Reconstruct equations that span multiple lines or pages:

```python
def reconstruct_multiline_equation(doc, start_page: int, start_block_idx: int) -> str:
    """Reassemble equation fragments across lines and page boundaries."""
    reconstructed = ""
    
    for page_num in range(start_page, min(start_page + 2, len(doc))):
        page = doc[page_num]
        blocks = page.get_text("dict")['blocks']
        
        for block in blocks[start_block_idx if page_num == start_page else 0:]:
            if block['type'] != 0:
                continue
            
            block_text = ''.join(
                ''.join(span['text'] for span in line['spans'])
                for line in block.get('lines', [])
            )
            
            # Check if line ends with continuation character or incomplete expression
            if block_text.rstrip().endswith(('\\', '+', '-', '=')):
                reconstructed += block_text.strip() + " "
            else:
                reconstructed += block_text.strip()
                break  # Equation complete
    
    return reconstructed.strip()
```

### LaTeX Representation

Convert extracted equations to LaTeX format for RAG indexing:

```python
import subprocess

def convert_to_latex(raw_equation: str, method: str = 'nougat') -> str:
    """
    Convert equation image/text to LaTeX string.
    Methods: 'nougat' (vision-based), 'pix2tex' (image), or regex fallback.
    """
    if method == 'nougat':
        # For image-based equations, use nougat model
        try:
            import requests
            response = requests.post(
                'http://localhost:8503/predict',  # Nougat service
                json={'image': raw_equation}  # Base64 encoded image
            )
            return response.json().get('latex', raw_equation)
        except Exception:
            pass
    
    elif method == 'pix2tex':
        # Alternative: pix2tex for better OCR
        try:
            from pix2tex.cli import LatexOCR
            ocr = LatexOCR()
            return ocr(raw_equation)  # Image path
        except Exception:
            pass
    
    # Fallback: regex-based heuristic for common patterns
    latex = raw_equation
    replacements = {
        r'(\w+)\^(\w+|\{[^}]+\})': r'\\1^{\\2}',  # Superscripts
        r'(\w+)_(\w+|\{[^}]+\})': r'\\1_{\\2}',   # Subscripts
        r'sqrt\(([^)]+)\)': r'\\sqrt{\\1}',        # Square roots
        r'∑': r'\\sum',                             # Greek letters
        r'∫': r'\\int',
        r'αβγδεμσ': r'\\alpha\\beta\\gamma...',
    }
    
    for pattern, replacement in replacements.items():
        latex = re.sub(pattern, replacement, latex)
    
    return latex
```

### Equation Context Preservation

Include surrounding context in metadata for RAG indexing:

```python
def extract_equation_with_context(doc, eq_page: int, eq_bbox, 
                                  context_lines: int = 3) -> dict:
    """Extract equation with surrounding text context."""
    page = doc[eq_page]
    blocks = page.get_text("dict")['blocks']
    
    # Find equation block and nearby text
    before_text = ""
    after_text = ""
    
    for block in blocks:
        block_rect = fitz.Rect(block['bbox'])
        if block['bbox'][1] < eq_bbox[1]:  # Before equation
            before_text += ''.join(
                ''.join(span['text'] for span in line['spans'])
                for line in block.get('lines', [])
            )
        elif block['bbox'][1] > eq_bbox[3]:  # After equation
            after_text += ''.join(
                ''.join(span['text'] for span in line['spans'])
                for line in block.get('lines', [])
            )
    
    return {
        'context_before': before_text[-200:].strip(),
        'context_after': after_text[:200].strip(),
        'variable_definitions': extract_variable_defs(before_text),
        'chapter_ref': extract_chapter_reference(doc, eq_page)
    }

def extract_variable_defs(text: str) -> dict:
    """Parse variable definitions (Where X = ..., where Y represents ...)."""
    var_defs = {}
    for match in re.finditer(r'(?:where|let|define)\s+(\w+)\s*(?:=|is|represents)\s*([^.,]+)', 
                             text, re.IGNORECASE):
        var_defs[match.group(1)] = match.group(2).strip()
    return var_defs
```

### Output Schema Extension

Add "equations" field to paper processing output:

```python
# Extended output schema (add to existing structure):
{
  "paper_id": "arxiv:2301.12345",
  "equations": [
    {
      "equation_id": "eq_2.3",
      "latex": "\\frac{dV}{dt} = -V + I_{ext}",
      "raw_text": "dV/dt = -V + I_ext",
      "page": 12,
      "section": "methods",
      "context_before": "...voltage dynamics described by...",
      "context_after": "...where V is membrane potential...",
      "variable_definitions": {
        "V": "membrane potential (mV)",
        "I_ext": "external input current"
      },
      "equation_type": "differential_equation",
      "referenced_in_text": ["Fig 3a", "Table 1", "Discussion para 2"]
    }
  ]
}
```
