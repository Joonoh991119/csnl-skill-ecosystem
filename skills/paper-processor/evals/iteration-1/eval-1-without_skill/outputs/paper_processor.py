#!/usr/bin/env python3
"""
Academic Paper PDF Processor
Extracts structured sections, key claims with statistical evidence, and figure captions
from academic PDF papers into a standardized JSON format.
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import PyPDF2
    from PyPDF2 import PdfReader
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)

try:
    import fitz  # pymupdf
except ImportError:
    print("Note: PyMuPDF not installed. PDF text extraction will be less accurate.")
    print("For better results, run: pip install PyMuPDF")
    fitz = None


@dataclass
class Figure:
    """Represents a figure or table in the paper."""
    number: str
    caption: str
    type: str  # 'figure', 'table', 'image'
    page: int
    description: Optional[str] = None


@dataclass
class Claim:
    """Represents a key claim with supporting evidence."""
    text: str
    evidence_type: str  # 'statistical', 'experimental', 'theoretical'
    statistics: Optional[Dict[str, Any]] = None
    supporting_text: Optional[str] = None
    page: Optional[int] = None


@dataclass
class Section:
    """Represents a major section of the paper."""
    title: str
    level: int  # 1=main, 2=subsection, etc.
    content: str
    start_page: int
    end_page: Optional[int] = None
    subsections: List['Section'] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []


class PaperProcessor:
    """Main processor for extracting structured information from academic PDFs."""

    def __init__(self, pdf_path: str):
        """Initialize with a PDF file path."""
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.text = ""
        self.pages = []
        self.metadata = {}
        self._extract_text()

    def _extract_text(self):
        """Extract text from PDF using available libraries."""
        if fitz:
            self._extract_with_pymupdf()
        else:
            self._extract_with_pypdf2()

    def _extract_with_pymupdf(self):
        """Extract text using PyMuPDF for better accuracy."""
        try:
            doc = fitz.open(str(self.pdf_path))
            self.metadata = doc.metadata

            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                self.pages.append({
                    'number': page_num,
                    'text': page_text,
                    'height': page.rect.height,
                    'width': page.rect.width
                })
                self.text += f"\n--- Page {page_num} ---\n{page_text}"

            doc.close()
        except Exception as e:
            print(f"Warning: PyMuPDF extraction failed: {e}. Falling back to PyPDF2.")
            self._extract_with_pypdf2()

    def _extract_with_pypdf2(self):
        """Fallback text extraction using PyPDF2."""
        try:
            reader = PdfReader(str(self.pdf_path))
            self.metadata = reader.metadata

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                self.pages.append({
                    'number': page_num,
                    'text': page_text
                })
                self.text += f"\n--- Page {page_num} ---\n{page_text}"
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

    def extract_sections(self) -> List[Section]:
        """Extract paper sections (Introduction, Methods, Results, Discussion, etc.)."""
        sections = []

        # Common academic section patterns
        section_patterns = [
            r'^(ABSTRACT|INTRODUCTION|METHODS?|PROCEDURE|MATERIALS?.*METHODS?|RESULTS?|DISCUSSION|CONCLUSION|REFERENCES?|ACKNOWLEDGMENTS?)',
            r'^(\d+\.?\s+[A-Z][A-Za-z\s]+?)$',  # Numbered sections
        ]

        lines = self.text.split('\n')
        current_section = None
        current_content = []
        current_page = 1

        for i, line in enumerate(lines):
            # Track page numbers
            if line.startswith('--- Page'):
                match = re.search(r'Page (\d+)', line)
                if match:
                    current_page = int(match.group(1))

            # Check for section headers
            is_section = False
            for pattern in section_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    # Save previous section
                    if current_section:
                        current_section.content = '\n'.join(current_content).strip()
                        current_section.end_page = current_page
                        sections.append(current_section)

                    # Start new section
                    current_section = Section(
                        title=line.strip(),
                        level=1,
                        content="",
                        start_page=current_page
                    )
                    current_content = []
                    is_section = True
                    break

            if not is_section and current_section:
                current_content.append(line)

        # Add final section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            current_section.end_page = current_page
            sections.append(current_section)

        return sections

    def extract_claims_with_evidence(self) -> List[Claim]:
        """Extract key claims with statistical and experimental evidence."""
        claims = []

        # Patterns for identifying claims with statistical evidence
        stat_patterns = [
            r'([A-Z][^.!?]*?)(?:was|were|is|are)\s+([a-z]+(?:\s+[a-z]+)?)\s*(?:\(|,)?\s*([Ff]|[Tt]|[Mm]|χ²|r|p)\s*(?:=|<|>)\s*([\d.]+)',
            r'([A-Z][^.!?]*?)\s*:\s*([mM]ean|[Mm]edian|[Ss]td)\s*(?:=|:)?\s*([\d.]+)\s*(?:\(|,)?\s*([^),]*)',
            r'([A-Z][^.!?]*?)\s+(\d+)\s*%',
            r'([A-Z][^.!?]*?)\s+(?:significantly|reliably|substantially)\s+',
        ]

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', self.text)

        for sent_idx, sentence in enumerate(sentences):
            if len(sentence.strip()) < 20:
                continue

            # Check for statistical evidence
            for pattern in stat_patterns:
                matches = re.finditer(pattern, sentence)
                for match in matches:
                    claim_text = match.group(1).strip()
                    if claim_text:
                        # Extract statistical data
                        stats = {}
                        if len(match.groups()) >= 4:
                            try:
                                stats['value'] = float(match.group(len(match.groups())))
                                if len(match.groups()) >= 3:
                                    stats['statistic'] = match.group(3)
                            except (ValueError, IndexError):
                                pass

                        page = self._find_page_for_sentence(sentence)
                        claims.append(Claim(
                            text=claim_text,
                            evidence_type='statistical',
                            statistics=stats if stats else None,
                            supporting_text=sentence[:200],
                            page=page
                        ))

        return claims

    def extract_figures_and_tables(self) -> List[Figure]:
        """Extract figure and table captions."""
        figures = []

        # Patterns for figure/table captions
        caption_patterns = [
            r'(?:^|\n)\s*(Figure|Fig\.?)\s+(\d+[A-Za-z]?)\s*[\.:]\s*(.+?)(?=(?:Figure|Fig\.|Table|$))',
            r'(?:^|\n)\s*(Table)\s+(\d+[A-Za-z]?)\s*[\.:]\s*(.+?)(?=(?:Figure|Fig\.|Table|$))',
        ]

        for pattern in caption_patterns:
            matches = re.finditer(pattern, self.text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                fig_type = match.group(1).lower()
                if 'table' in fig_type:
                    fig_type = 'table'
                else:
                    fig_type = 'figure'

                caption_text = match.group(3).strip()
                # Clean up caption text
                caption_text = re.sub(r'\s+', ' ', caption_text)
                caption_text = caption_text[:500]  # Limit length

                page = self._find_page_for_text(match.group(0))
                figures.append(Figure(
                    number=match.group(2),
                    caption=caption_text,
                    type=fig_type,
                    page=page,
                    description=None
                ))

        return figures

    def _find_page_for_sentence(self, sentence: str) -> int:
        """Find which page a sentence appears on."""
        for page_info in self.pages:
            if sentence in page_info.get('text', ''):
                return page_info['number']
        return 1

    def _find_page_for_text(self, text: str) -> int:
        """Find which page text appears on."""
        for page_info in self.pages:
            if text in page_info.get('text', ''):
                return page_info['number']
        return 1

    def extract_metadata(self) -> Dict[str, Any]:
        """Extract paper metadata."""
        metadata = {
            'title': None,
            'authors': None,
            'year': None,
            'doi': None,
            'abstract': None,
        }

        # Try to extract from PDF metadata
        if hasattr(self, 'metadata') and self.metadata:
            pdf_meta = self.metadata
            metadata['title'] = pdf_meta.get('/Title')
            metadata['authors'] = pdf_meta.get('/Author')

        # Try to find title, authors, year from text
        lines = self.text.split('\n')[:50]  # Check first 50 lines
        text_section = '\n'.join(lines)

        # Extract year from common patterns
        year_match = re.search(r'\b(19|20)\d{2}\b', text_section)
        if year_match:
            metadata['year'] = int(year_match.group(0))

        # Extract abstract if present
        abstract_match = re.search(
            r'(?:^|\n)\s*(?:ABSTRACT|Abstract)\s*[\n:]\s*(.+?)(?=(?:INTRODUCTION|Introduction|KEYWORDS|$))',
            self.text[:2000],
            re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            metadata['abstract'] = re.sub(r'\s+', ' ', abstract_text)[:500]

        return metadata

    def process(self) -> Dict[str, Any]:
        """Process the entire PDF and return structured data."""
        print(f"Processing: {self.pdf_path.name}")

        result = {
            'file': str(self.pdf_path),
            'metadata': self.extract_metadata(),
            'sections': [asdict(s) for s in self.extract_sections()],
            'claims': [asdict(c) for c in self.extract_claims_with_evidence()],
            'figures': [asdict(f) for f in self.extract_figures_and_tables()],
            'page_count': len(self.pages),
        }

        return result


def process_pdf_to_json(pdf_path: str, output_path: Optional[str] = None) -> str:
    """
    Process a PDF and save to JSON.

    Args:
        pdf_path: Path to the PDF file
        output_path: Optional path for output JSON (default: same as PDF with .json)

    Returns:
        Path to the output JSON file
    """
    processor = PaperProcessor(pdf_path)
    result = processor.process()

    if output_path is None:
        output_path = str(Path(pdf_path).with_suffix('.json'))

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python paper_processor.py <pdf_path> [output_json_path]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result_path = process_pdf_to_json(pdf_path, output_path)
        print(f"\nSuccess! Output: {result_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
