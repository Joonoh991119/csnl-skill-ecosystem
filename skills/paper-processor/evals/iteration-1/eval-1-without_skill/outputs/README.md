# Paper Processor

A Python tool for extracting structured information from academic PDF papers into standardized JSON format.

## Overview

This tool processes academic papers (PDFs) and automatically extracts:

- **Metadata**: Title, authors, publication year, abstract
- **Sections**: Hierarchical structure (Introduction, Methods, Results, Discussion, etc.)
- **Key Claims**: Statements with supporting statistical or experimental evidence
- **Figures & Tables**: Captions and references with page numbers

Output follows a strict JSON schema suitable for downstream processing, analysis, or integration into research databases.

## Features

- Multi-library support (PyMuPDF for accuracy, PyPDF2 fallback)
- Robust section detection using academic paper conventions
- Statistical evidence extraction (F-tests, t-tests, p-values, effect sizes)
- Figure and table caption extraction
- Page tracking for all extracted elements
- Clean, queryable JSON output

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone or download this directory

2. Install required dependencies:

```bash
# Install both PDF libraries for best results
pip install PyMuPDF PyPDF2

# Or install just PyPDF2 (less accurate but lighter weight)
pip install PyPDF2
```

**Note**: PyMuPDF provides better text extraction accuracy. PyPDF2 is a lightweight fallback.

## Usage

### Command Line

```bash
# Basic usage: process PDF and save to output.json
python paper_processor.py input_paper.pdf

# Specify custom output path
python paper_processor.py input_paper.pdf output.json

# Example with Zhang & Luck (2008)
python paper_processor.py ~/Zotero/storage/ABCD1234/zhang_luck_2008.pdf output.json
```

### Python API

```python
from paper_processor import PaperProcessor, process_pdf_to_json
import json

# Method 1: Using the convenience function
result_path = process_pdf_to_json(
    pdf_path='paper.pdf',
    output_path='paper.json'
)

# Method 2: Using the processor class
processor = PaperProcessor('paper.pdf')
result = processor.process()

# Access specific extracted data
print(f"Title: {result['metadata']['title']}")
print(f"Pages: {result['page_count']}")
print(f"Sections: {len(result['sections'])}")
print(f"Figures: {len(result['figures'])}")
print(f"Claims with evidence: {len(result['claims'])}")

# Save manually
with open('output.json', 'w') as f:
    json.dump(result, f, indent=2)
```

## Output Format

The output JSON follows the schema defined in `schema.json`. Example structure:

```json
{
  "file": "/path/to/paper.pdf",
  "page_count": 24,
  "metadata": {
    "title": "Discrete fixed-resolution representations in visual working memory",
    "authors": "Zhang & Luck",
    "year": 2008,
    "doi": null,
    "abstract": "Visual working memory can hold only a limited number..."
  },
  "sections": [
    {
      "title": "INTRODUCTION",
      "level": 1,
      "content": "Text content of introduction...",
      "start_page": 1,
      "end_page": 3,
      "subsections": []
    }
  ],
  "claims": [
    {
      "text": "Visual working memory stores 3-4 items",
      "evidence_type": "statistical",
      "statistics": {
        "value": 3.8,
        "statistic": "mean"
      },
      "supporting_text": "...participants were able to maintain...",
      "page": 5
    }
  ],
  "figures": [
    {
      "number": "1",
      "caption": "Example stimuli and experimental design...",
      "type": "figure",
      "page": 2,
      "description": null
    }
  ]
}
```

## JSON Schema

See `schema.json` for the complete schema definition. Key properties:

- **Metadata**: Paper identification information
- **Sections**: Nested hierarchical document structure
- **Claims**: Evidence-based statements with statistical support
- **Figures**: Visual elements with captions and page numbers

## Processing Pipeline

1. **Text Extraction**: PDF → raw text (PyMuPDF or PyPDF2)
2. **Metadata Parsing**: Title, authors, year from PDF metadata and text patterns
3. **Section Detection**: Regex patterns match common academic section headers
4. **Claim Extraction**: Statistical patterns identify evidence-supported statements
5. **Figure Extraction**: Caption patterns extract tables and figures
6. **Page Tracking**: All elements mapped to source pages
7. **JSON Serialization**: Structured data to standardized JSON

## Known Limitations

1. **OCR**: Does not perform OCR on scanned PDFs. Text extraction requires searchable PDFs.

2. **Layout**: Heavy reliance on text order; complex multi-column layouts may extract incorrectly.

3. **Statistical Patterns**: Extraction focuses on common statistical reporting formats. Novel formats may be missed.

4. **Figures**: Extracts captions only; does not extract images or analyze figure content beyond caption text.

5. **Metadata**: PDF metadata varies widely; fallback text extraction may not find all information.

## Customization

### Adding New Section Patterns

Edit the `section_patterns` list in `extract_sections()`:

```python
section_patterns = [
    r'^(YOUR_SECTION_NAME|ANOTHER_SECTION)',
    r'^(\d+\.?\s+[A-Z][A-Za-z\s]+?)$',
]
```

### Extending Statistical Pattern Matching

Add patterns to `extract_claims_with_evidence()`:

```python
stat_patterns = [
    r'your_pattern_here',
]
```

### Custom Post-Processing

```python
processor = PaperProcessor('paper.pdf')
result = processor.process()

# Apply custom transformations
for claim in result['claims']:
    # Custom processing here
    pass
```

## Troubleshooting

**Issue**: "No module named 'PyPDF2'"
- Solution: Run `pip install PyPDF2`

**Issue**: "PDF text extraction failed"
- Solution: Ensure PDF is not encrypted or scanned. Try installing PyMuPDF: `pip install PyMuPDF`

**Issue**: Sections not detected correctly
- Solution: Check PDF has readable text layer. Adjust section_patterns for your specific paper format.

**Issue**: Statistics not extracted
- Solution: Verify statistical reporting format matches patterns. Consider adding custom patterns.

## Example: Processing Zhang & Luck (2008)

```bash
python paper_processor.py ~/Zotero/storage/ABCD1234/zhang_luck_2008.pdf zhang_luck_output.json
```

This will extract:
- Key finding: Working memory capacity constraints
- Experimental methods: Change detection paradigm
- Statistical evidence: Accuracy/capacity tradeoffs
- Figures: Stimulus examples, performance curves, capacity estimates

## Integration

### With Zotero

Store PDFs in standard Zotero locations:
```bash
python paper_processor.py ~/Zotero/storage/[KEY]/document.pdf
```

### Batch Processing

```python
from pathlib import Path
from paper_processor import process_pdf_to_json

pdf_dir = Path('./papers')
for pdf_file in pdf_dir.glob('*.pdf'):
    try:
        process_pdf_to_json(str(pdf_file))
        print(f"✓ {pdf_file.name}")
    except Exception as e:
        print(f"✗ {pdf_file.name}: {e}")
```

### With Database Integration

```python
import json
import sqlite3
from paper_processor import process_pdf_to_json

# Process and insert into database
result = process_pdf_to_json('paper.pdf')
data = json.load(open('paper.json'))

conn = sqlite3.connect('papers.db')
cursor = conn.cursor()
cursor.execute('''
    INSERT INTO papers (filepath, metadata, sections, claims, figures)
    VALUES (?, ?, ?, ?, ?)
''', (
    data['file'],
    json.dumps(data['metadata']),
    json.dumps(data['sections']),
    json.dumps(data['claims']),
    json.dumps(data['figures'])
))
conn.commit()
```

## Performance Notes

- Small papers (< 10 pages): ~1-2 seconds
- Medium papers (10-30 pages): ~3-5 seconds
- Large papers (> 30 pages): ~5-15 seconds

Performance depends on:
- PDF size and complexity
- Text extraction library (PyMuPDF faster than PyPDF2)
- System I/O speed

## License

This tool is provided as-is for academic research purposes.

## Contributing

For improvements or bug reports, please document:
1. The PDF (or similar test case)
2. Expected vs. actual output
3. Relevant error messages or logs

## References

This processor is designed to work with academic papers following standard formatting conventions (e.g., ACM, APA, IEEE formats).

Example papers that work well:
- Zhang & Luck (2008): Discrete fixed-resolution representations in visual working memory
- Papers published by major venues (Nature, Science, PNAS, cognition journals, etc.)
