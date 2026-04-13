# Paper Processor WITH-SKILL Evaluation
**Evaluation Type:** WITH-SKILL  
**Paper:** Zhang & Luck (2008) "Discrete fixed-resolution representations in visual working memory"  
**Date:** 2026-04-14

## Overview

This evaluation demonstrates the **paper-processor** skill using the patterns, regex templates, and output schema defined in `/tmp/csnl-skill-ecosystem/skills/paper-processor/SKILL.md`.

The skill extracts structured information from scientific PDFs to feed into downstream systems (RAG pipelines, tutoring content generators, knowledge bases).

## Files in This Evaluation

### 1. `paper_processor.py`
Complete Python implementation of the paper-processor skill pipeline:

**Key Components:**
- **`PaperProcessor` class:** Main processing engine
- **`Section` dataclass:** Represents detected paper sections (abstract, methods, results, etc.)
- **`Claim` dataclass:** Represents extracted empirical claims with statistical evidence
- **`Figure` dataclass:** Figure metadata and captions
- **`PaperMetadata` dataclass:** Bibliographic metadata (authors, year, DOI, etc.)

**Methods:**
- `detect_sections(text)`: Split paper into labeled sections using SECTION_PATTERNS regex
- `extract_claims(sections)`: Extract key empirical claims using CLAIM_INDICATORS patterns
- `extract_figures(text)`: Extract figure captions using regex pattern matching
- `extract_key_terms(text, claims)`: Identify key terminology from abstract and claims
- `process_paper(text, metadata)`: Main pipeline combining all extraction steps

**Pattern References:**
- Uses `SECTION_PATTERNS` regex from SKILL.md (abstract, introduction, methods, results, discussion, etc.)
- Uses `CLAIM_INDICATORS` regex (p-values, t-statistics, F-statistics, correlations, etc.)
- Applies figure caption detection: `(?:Figure|Fig\.?)\s+(\d+)[.:]`

### 2. `zhang_luck_2008_example_output.json`
Example structured JSON output for the Zhang & Luck (2008) paper following the exact schema from SKILL.md.

**Output Schema:**
```json
{
  "paper_id": "zhang_luck_2008",
  "title": "Discrete fixed-resolution representations in visual working memory",
  "authors": ["Zhang, W.", "Luck, S. J."],
  "year": 2008,
  "journal": "Journal of Vision",
  "doi": "10.1167/8.6.7",
  "arxiv_id": null,
  "sections": {
    "abstract": "...",
    "introduction": "...",
    "methods": "...",
    "results": "...",
    "discussion": "..."
  },
  "claims": [
    {
      "text": "Mean VWM capacity was 3.47 items (SD = 0.92)",
      "section": "results",
      "type": "empirical_claim",
      "has_stats": true
    }
  ],
  "figures": [
    {
      "figure_num": 1,
      "caption": "Mean VWM capacity (K) as a function of set size.",
      "page": null
    }
  ],
  "key_terms": ["visual working memory", "capacity limits", ...],
  "citation_count": null,
  "zotero_key": "ABCD1234"
}
```

## Integration Points

### With RAG Pipeline
The structured JSON output feeds directly into the **rag-pipeline** skill:
- **Section-aware chunking:** The pipeline can treat each section boundary as a natural chunk division
- **Claims as fact units:** Individual claims with `has_stats=true` can be prioritized for embeddings
- **Figure context:** Figure captions provide visual context for retrieval-augmented generation

**Integration workflow:**
```
paper_processor.py (extract structure)
         ↓
       JSON output
         ↓
rag-pipeline (section-aware chunking + embedding)
         ↓
Vector database (for semantic search)
```

### With Zotero MCP
The processor is designed to work with the **Zotero MCP** for:
- **Source documents:** `zotero.get_content(item_key)` → extract PDF text
- **Metadata:** `zotero.get_item_details(item_key)` → populate author, year, DOI fields
- **Annotations:** `zotero.get_annotations(item_key)` → integrate user highlights as additional context
- **Collection management:** Store processed papers with tags and collections

**Integration code pattern:**
```python
from zotero import ZoteroAPI

zotero = ZoteroAPI()
item = zotero.get_item_details("ABCD1234")
text = zotero.get_content("ABCD1234")
annotations = zotero.get_annotations("ABCD1234")

processor = PaperProcessor()
result = processor.process_paper(
    text=text,
    metadata=PaperMetadata(
        title=item['title'],
        authors=item['creators'],
        year=item['year'],
        journal=item['publicationTitle'],
        doi=item['DOI'],
        zotero_key="ABCD1234"
    )
)
```

### With Tutoring Systems (tutor-content-gen)
Processed claims and figures feed into the **tutor-content-gen** skill:
- **Quiz generation:** Claims with statistics → multiple-choice questions
- **Concept explanations:** Claims from discussion section → instructional content
- **Figure adaptation:** Figure captions → visual exercises

## Usage Example

```python
from paper_processor import PaperProcessor, PaperMetadata

processor = PaperProcessor()

# Process a paper
metadata = PaperMetadata(
    title="Discrete fixed-resolution representations in visual working memory",
    authors=["Zhang, W.", "Luck, S. J."],
    year=2008,
    journal="Journal of Vision",
    doi="10.1167/8.6.7",
    arxiv_id=None,
    zotero_key="ABCD1234"
)

# Assumes text extracted from ~/Zotero/storage/ABCD1234/zhang_luck_2008.pdf
with open("paper_text.txt", "r") as f:
    text = f.read()

result = processor.process_paper(text, metadata, paper_id="zhang_luck_2008")

# Output as JSON
import json
print(json.dumps(result, indent=2))
```

## Key Design Decisions

1. **Regex-based section detection:** Fast, reliable on standard academic paper layouts
2. **Explicit claim indicators:** Statistical patterns (p-values, t-stats) make claims machine-actionable
3. **Figure caption extraction:** Enables downstream figure-based indexing and search
4. **Zotero integration:** Leverages existing user libraries rather than creating new data silos
5. **Section-aware output:** Preserves document structure for better RAG retrieval

## Limitations & Future Improvements

- **PDF extraction:** Currently placeholder; needs PyMuPDF (fitz) or pdfplumber integration
- **Table extraction:** Figure extraction implemented; table extraction not yet included
- **Citation linking:** Citation count is null; could integrate with Semantic Scholar API
- **Layout handling:** Regex patterns may fail on non-standard paper formats
- **Equation extraction:** LaTeX source preferred for equations; PDF equations need OCR
- **Language support:** Currently English-only; could extend with multilingual patterns

## Dependencies

**For full PDF processing:**
```
fitz (PyMuPDF)  # PDF text/image extraction
pdfplumber       # Alternative for table extraction
requests         # For arXiv API calls
zotero-api       # For Zotero MCP integration (optional)
```

**Core script dependencies:**
- Python 3.8+
- Built-in: `re`, `json`, `pathlib`, `dataclasses`, `enum`

## Schema Conformance

This implementation strictly follows the **output schema** from SKILL.md:
- ✅ `paper_id`: String identifier (arxiv:ID or custom)
- ✅ `title`, `authors`, `year`, `journal`, `doi`: Bibliographic fields
- ✅ `sections`: Dict mapping section labels to text
- ✅ `claims`: List of empirical claims with section, type, has_stats
- ✅ `figures`: List of figures with number, caption, page
- ✅ `key_terms`: Extracted terminology
- ✅ `citation_count`: Placeholder for Semantic Scholar integration
- ✅ `zotero_key`: Optional Zotero item key for source tracking

## References

- SKILL.md: `/tmp/csnl-skill-ecosystem/skills/paper-processor/SKILL.md`
- RAG Pipeline: `/tmp/csnl-skill-ecosystem/skills/rag-pipeline/SKILL.md`
- Zotero MCP: Integration via Zotero Python API
- Zhang & Luck (2008): doi:10.1167/8.6.7
