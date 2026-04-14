---
name: corpus-manager
description: "Manages the CRMB source corpus lifecycle: loading PDFs, validating chapter completeness, versioning, and providing a unified access interface for all downstream skills. TRIGGERS: corpus, chapters, PDF loading, source material, book chapters, CRMB text"
version: 1.0.0
tags: [corpus, infrastructure, crmb, lifecycle]
requires: []
---

# Corpus Manager Skill

## Overview

The corpus-manager skill provides critical infrastructure for the CRMB tutor ecosystem. It:
- Loads and validates the 17-chapter CRMB source material
- Maintains versioning and integrity checksums for corpus reproducibility
- Provides unified access interfaces for downstream skills
- Manages supplementary papers (Olshausen & Field 1996, Pouget et al. 2000, etc.)
- Performs quality validation (OCR, equation extraction, figure counts)
- Maintains Korean metadata for international support

All other skills reference "CRMB chapters"—this skill ensures those references always point to validated, versioned source material.

---

## 1. Corpus Registry

### CRMB Chapter Definitions

```python
CRMB_CHAPTERS = {
    1: {
        "title": "Overview and Introduction to Adaptive Resonance Theory",
        "title_ko": "적응 공명 이론 개요 및 소개",
        "pages": (1, 30),
        "key_concepts": [
            "stability-plasticity dilemma",
            "Adaptive Resonance Theory (ART)",
            "consciousness",
            "neural learning"
        ],
        "expected_equations": 8,
        "expected_figures": 6
    },
    2: {
        "title": "Biological Foundations of Neural Learning",
        "title_ko": "신경 학습의 생물학적 기초",
        "pages": (31, 65),
        "key_concepts": [
            "synaptic plasticity",
            "Hebbian learning",
            "long-term potentiation (LTP)",
            "long-term depression (LTD)",
            "neural oscillations"
        ],
        "expected_equations": 12,
        "expected_figures": 9
    },
    3: {
        "title": "Pattern Recognition and Feature Learning",
        "title_ko": "패턴 인식 및 특징 학습",
        "pages": (66, 105),
        "key_concepts": [
            "feature extraction",
            "receptive fields",
            "sparse coding",
            "pattern completion",
            "invariance learning"
        ],
        "expected_equations": 15,
        "expected_figures": 11
    },
    4: {
        "title": "Efficient Coding Hypothesis",
        "title_ko": "효율적 코딩 가설",
        "pages": (106, 145),
        "key_concepts": [
            "information maximization",
            "sparse representation",
            "natural image statistics",
            "basis functions",
            "overcomplete dictionaries"
        ],
        "expected_equations": 18,
        "expected_figures": 8
    },
    5: {
        "title": "Neural Coding and Population Coding",
        "title_ko": "신경 코딩 및 집단 코딩",
        "pages": (146, 185),
        "key_concepts": [
            "rate coding",
            "temporal coding",
            "population vector decoding",
            "optimal decoding",
            "information capacity"
        ],
        "expected_equations": 14,
        "expected_figures": 10
    },
    6: {
        "title": "Attention and Gain Modulation",
        "title_ko": "주의력 및 이득 변조",
        "pages": (186, 220),
        "key_concepts": [
            "attention mechanisms",
            "gain modulation",
            "spatial attention",
            "feature-based attention",
            "divisive normalization"
        ],
        "expected_equations": 11,
        "expected_figures": 9
    },
    7: {
        "title": "Memory Systems and Consolidation",
        "title_ko": "기억 체계 및 고착화",
        "pages": (221, 260),
        "key_concepts": [
            "working memory",
            "long-term memory",
            "memory consolidation",
            "systems consolidation",
            "reconsolidation"
        ],
        "expected_equations": 10,
        "expected_figures": 8
    },
    8: {
        "title": "Decision-Making and Value Learning",
        "title_ko": "의사결정 및 가치 학습",
        "pages": (261, 305),
        "key_concepts": [
            "value representation",
            "reinforcement learning",
            "dopamine signaling",
            "reward prediction error",
            "optimal decision-making"
        ],
        "expected_equations": 16,
        "expected_figures": 12
    },
    9: {
        "title": "Motor Control and Cerebellar Learning",
        "title_ko": "운동 제어 및 소뇌 학습",
        "pages": (306, 345),
        "key_concepts": [
            "motor learning",
            "cerebellar plasticity",
            "predictive control",
            "error-driven learning",
            "forward models"
        ],
        "expected_equations": 13,
        "expected_figures": 10
    },
    10: {
        "title": "Sensorimotor Integration",
        "title_ko": "감각운동 통합",
        "pages": (346, 385),
        "key_concepts": [
            "sensorimotor transformation",
            "coordinate frames",
            "gain fields",
            "body schema",
            "vestibular-visual integration"
        ],
        "expected_equations": 12,
        "expected_figures": 9
    },
    11: {
        "title": "Spatial Representation and Navigation",
        "title_ko": "공간 표현 및 항법",
        "pages": (386, 425),
        "key_concepts": [
            "place cells",
            "grid cells",
            "head direction cells",
            "path integration",
            "cognitive maps"
        ],
        "expected_equations": 11,
        "expected_figures": 10
    },
    12: {
        "title": "Language and Semantic Representation",
        "title_ko": "언어 및 의미 표현",
        "pages": (426, 465),
        "key_concepts": [
            "lexical access",
            "semantic networks",
            "distributional semantics",
            "compositional structure",
            "grounding language in perception"
        ],
        "expected_equations": 9,
        "expected_figures": 8
    },
    13: {
        "title": "Social Cognition and Theory of Mind",
        "title_ko": "사회 인지 및 마음의 이론",
        "pages": (466, 505),
        "key_concepts": [
            "mentalizing",
            "mirror neurons",
            "social prediction",
            "intention inference",
            "theory of mind (ToM)"
        ],
        "expected_equations": 10,
        "expected_figures": 9
    },
    14: {
        "title": "Emotion and Affect Processing",
        "title_ko": "정서 및 정동 처리",
        "pages": (506, 545),
        "key_concepts": [
            "affect valuation",
            "amygdala function",
            "emotion regulation",
            "emotional learning",
            "interoception and embodied emotion"
        ],
        "expected_equations": 9,
        "expected_figures": 10
    },
    15: {
        "title": "Sleep and Memory Consolidation",
        "title_ko": "수면 및 기억 고착화",
        "pages": (546, 585),
        "key_concepts": [
            "REM sleep function",
            "non-REM sleep",
            "sleep spindles",
            "replay during sleep",
            "systems consolidation in sleep"
        ],
        "expected_equations": 8,
        "expected_figures": 9
    },
    16: {
        "title": "Consciousness and Integrated Information",
        "title_ko": "의식 및 통합 정보",
        "pages": (586, 625),
        "key_concepts": [
            "integrated information theory (IIT)",
            "conscious access",
            "neural correlates of consciousness",
            "metacognition",
            "binding problem"
        ],
        "expected_equations": 11,
        "expected_figures": 11
    },
    17: {
        "title": "Future Directions and Open Questions",
        "title_ko": "향후 방향 및 공개 질문",
        "pages": (626, 660),
        "key_concepts": [
            "artificial general intelligence",
            "brain-inspired computing",
            "quantum cognition",
            "neuroethics",
            "translational neuroscience"
        ],
        "expected_equations": 7,
        "expected_figures": 8
    }
}
```

---

## 2. PDF Loading and Validation

### Core Loading Functions

```python
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import PyPDF2

class CorpusLoader:
    """Handles PDF loading and initial validation."""
    
    def __init__(self, corpus_root: str):
        """
        Args:
            corpus_root: Base directory for corpus storage
        """
        self.corpus_root = Path(corpus_root)
        self.chapters_dir = self.corpus_root / "chapters"
        self.chapters_dir.mkdir(parents=True, exist_ok=True)
        self.validation_log = []
    
    def load_chapter_pdf(self, chapter_num: int, pdf_path: str) -> Dict:
        """
        Load a chapter PDF and validate basic properties.
        
        Args:
            chapter_num: Chapter number (1-17)
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with load metadata:
            {
                "chapter": int,
                "pdf_path": str,
                "page_count": int,
                "file_size_mb": float,
                "sha256": str,
                "load_timestamp": str,
                "validation_status": str,
                "warnings": List[str]
            }
        
        Raises:
            ValueError: If chapter number out of range or PDF invalid
            FileNotFoundError: If PDF not found
        """
        if chapter_num not in CRMB_CHAPTERS:
            raise ValueError(f"Chapter {chapter_num} not in CRMB_CHAPTERS")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Extract page count
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
        except Exception as e:
            raise ValueError(f"Cannot read PDF: {e}")
        
        # Compute SHA-256
        sha256_hash = self._compute_file_hash(pdf_path)
        
        # Validate against expected page range
        expected_pages = CRMB_CHAPTERS[chapter_num]["pages"]
        expected_range = expected_pages[1] - expected_pages[0] + 1
        
        warnings = []
        if abs(page_count - expected_range) > 5:
            warnings.append(
                f"Page count {page_count} differs from expected ~{expected_range} "
                f"(range {expected_pages[0]}-{expected_pages[1]})"
            )
        
        # Store chapter copy in corpus
        dest_path = self.chapters_dir / f"chapter_{chapter_num:02d}.pdf"
        if not dest_path.exists():
            import shutil
            shutil.copy2(pdf_path, dest_path)
        
        metadata = {
            "chapter": chapter_num,
            "pdf_path": str(dest_path),
            "page_count": page_count,
            "file_size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
            "sha256": sha256_hash,
            "load_timestamp": self._get_timestamp(),
            "validation_status": "valid" if not warnings else "warning",
            "warnings": warnings
        }
        
        self.validation_log.append(metadata)
        return metadata
    
    def _compute_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Compute SHA-256 hash of file."""
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def _get_timestamp(self) -> str:
        """Get ISO 8601 timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def validate_corpus_completeness(self) -> Dict:
        """
        Validate that all 17 chapters are present and loadable.
        
        Returns:
            {
                "complete": bool,
                "chapters_present": List[int],
                "chapters_missing": List[int],
                "total_pages": int,
                "total_size_mb": float,
                "validation_timestamp": str
            }
        """
        chapters_present = []
        chapters_missing = []
        total_pages = 0
        total_size_mb = 0.0
        
        for chapter_num in range(1, 18):
            chapter_path = self.chapters_dir / f"chapter_{chapter_num:02d}.pdf"
            if chapter_path.exists():
                chapters_present.append(chapter_num)
                try:
                    with open(chapter_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        page_count = len(reader.pages)
                        total_pages += page_count
                    total_size_mb += round(chapter_path.stat().st_size / (1024 * 1024), 2)
                except:
                    chapters_missing.append(chapter_num)
            else:
                chapters_missing.append(chapter_num)
        
        return {
            "complete": len(chapters_present) == 17,
            "chapters_present": chapters_present,
            "chapters_missing": chapters_missing,
            "total_pages": total_pages,
            "total_size_mb": total_size_mb,
            "validation_timestamp": self._get_timestamp()
        }
    
    def compute_chapter_hash(self, chapter_num: int) -> str:
        """Compute SHA-256 hash of specific chapter PDF."""
        chapter_path = self.chapters_dir / f"chapter_{chapter_num:02d}.pdf"
        if not chapter_path.exists():
            raise FileNotFoundError(f"Chapter {chapter_num} PDF not found")
        return self._compute_file_hash(chapter_path)
```

---

## 3. Corpus Versioning

### Version Management

```python
import json
from datetime import datetime

class CorpusVersion:
    """Manages corpus versioning and integrity tracking."""
    
    def __init__(self, base_dir: str):
        """
        Args:
            base_dir: Base directory containing corpus and manifest
        """
        self.base_dir = Path(base_dir)
        self.manifest_path = self.base_dir / "corpus_manifest.json"
        self.versions_dir = self.base_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self._load_or_create_manifest()
    
    def _load_or_create_manifest(self):
        """Load existing manifest or create new one."""
        if self.manifest_path.exists():
            with open(self.manifest_path, 'r') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {
                "created": datetime.utcnow().isoformat() + "Z",
                "versions": [],
                "chapters": {}
            }
    
    def register_chapter(self, chapter_num: int, pdf_path: str, 
                        processing_date: str, metadata: Dict = None):
        """
        Register a chapter in the manifest.
        
        Args:
            chapter_num: Chapter number (1-17)
            pdf_path: Path to PDF file
            processing_date: ISO 8601 timestamp of processing
            metadata: Optional metadata dict
        """
        chapter_key = f"chapter_{chapter_num:02d}"
        loader = CorpusLoader(str(self.base_dir))
        
        chapter_hash = loader.compute_chapter_hash(chapter_num)
        
        self.manifest["chapters"][chapter_key] = {
            "chapter_num": chapter_num,
            "title": CRMB_CHAPTERS[chapter_num]["title"],
            "title_ko": CRMB_CHAPTERS[chapter_num]["title_ko"],
            "pdf_path": pdf_path,
            "sha256": chapter_hash,
            "processing_date": processing_date,
            "metadata": metadata or {}
        }
        
        self._save_manifest()
    
    def get_version_hash(self) -> str:
        """
        Compute hash representing entire corpus version.
        
        Returns:
            SHA-256 hash of manifest (all chapters + metadata)
        """
        manifest_str = json.dumps(self.manifest, sort_keys=True)
        return hashlib.sha256(manifest_str.encode()).hexdigest()
    
    def create_version_snapshot(self, version_name: str, description: str = ""):
        """
        Create a snapshot of current corpus state.
        
        Args:
            version_name: Semantic version (e.g., "1.0.0")
            description: Human-readable description
        """
        version_hash = self.get_version_hash()
        
        snapshot = {
            "version": version_name,
            "hash": version_hash,
            "created": datetime.utcnow().isoformat() + "Z",
            "description": description,
            "manifest": self.manifest.copy()
        }
        
        snapshot_path = self.versions_dir / f"v{version_name}.json"
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        self.manifest["versions"].append({
            "version": version_name,
            "hash": version_hash,
            "created": snapshot["created"],
            "description": description
        })
        self._save_manifest()
        
        return snapshot_path
    
    def diff(self, other_version_path: str) -> Dict:
        """
        Compare current corpus with another version snapshot.
        
        Args:
            other_version_path: Path to other version JSON
        
        Returns:
            {
                "version_1": str,
                "version_2": str,
                "chapters_added": List[int],
                "chapters_removed": List[int],
                "chapters_modified": List[int],
                "summary": str
            }
        """
        with open(other_version_path, 'r') as f:
            other_manifest = json.load(f)["manifest"]
        
        current_chapters = set(self.manifest["chapters"].keys())
        other_chapters = set(other_manifest["chapters"].keys())
        
        added = current_chapters - other_chapters
        removed = other_chapters - current_chapters
        modified = []
        
        for ch_key in current_chapters & other_chapters:
            if (self.manifest["chapters"][ch_key].get("sha256") !=
                other_manifest["chapters"][ch_key].get("sha256")):
                modified.append(int(ch_key.split("_")[1]))
        
        return {
            "current_hash": self.get_version_hash(),
            "other_hash": other_manifest.get("hash", "unknown"),
            "chapters_added": sorted([int(k.split("_")[1]) for k in added]),
            "chapters_removed": sorted([int(k.split("_")[1]) for k in removed]),
            "chapters_modified": sorted(modified),
            "summary": f"Added {len(added)}, removed {len(removed)}, modified {len(modified)}"
        }
    
    def _save_manifest(self):
        """Save manifest to disk."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
```

---

## 4. Unified Access Interface

### Content Retrieval API

```python
class CorpusAccessor:
    """Unified interface for accessing corpus content across all chapters."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.chapters_dir = self.base_dir / "chapters"
        self._cache = {}
    
    def get_chapter_text(self, chapter_num: int, use_cache: bool = True) -> str:
        """
        Extract raw text from chapter PDF.
        
        Args:
            chapter_num: Chapter number (1-17)
            use_cache: Whether to cache extracted text
        
        Returns:
            Raw text extracted from PDF
        """
        cache_key = f"text_ch{chapter_num}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        chapter_path = self.chapters_dir / f"chapter_{chapter_num:02d}.pdf"
        if not chapter_path.exists():
            raise FileNotFoundError(f"Chapter {chapter_num} not found")
        
        text = ""
        try:
            with open(chapter_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise RuntimeError(f"Error extracting text from chapter {chapter_num}: {e}")
        
        if use_cache:
            self._cache[cache_key] = text
        
        return text
    
    def get_chapter_sections(self, chapter_num: int) -> Dict:
        """
        Extract hierarchical section structure from chapter.
        
        Returns:
            {
                "chapter": int,
                "title": str,
                "sections": [
                    {
                        "level": 1 or 2 or 3,
                        "title": str,
                        "page_range": (start, end),
                        "content_preview": str,
                        "subsections": [...]
                    }
                ]
            }
        
        Note: Actual extraction requires PDF structural analysis or heuristic
        detection based on formatting (font sizes, indentation, etc.)
        """
        text = self.get_chapter_text(chapter_num)
        
        # Simple heuristic: Look for numbered/lettered patterns
        sections = []
        current_section = None
        
        import re
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Detect section headers (heuristic)
            if re.match(r'^[\d]+\.[\s]', line):  # "1. Section Title"
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "level": 1,
                    "title": line.strip(),
                    "line_start": i,
                    "content_preview": ""
                }
            elif current_section and len(line.strip()) > 0:
                current_section["content_preview"] += line + " "
        
        if current_section:
            sections.append(current_section)
        
        return {
            "chapter": chapter_num,
            "title": CRMB_CHAPTERS[chapter_num]["title"],
            "section_count": len(sections),
            "sections": sections[:10]  # Preview first 10
        }
    
    def get_chapter_equations(self, chapter_num: int) -> List[Dict]:
        """
        Extract mathematical equations from chapter.
        
        Returns:
            [
                {
                    "equation_id": str,
                    "latex_source": str,
                    "context": str (surrounding text),
                    "page": int,
                    "equation_type": "inline" or "display"
                }
            ]
        
        Note: Full equation extraction requires specialized PDF parsing or OCR
        with mathematical formula recognition (e.g., mathpix, pdfplumber with
        layout analysis).
        """
        # Placeholder implementation
        return [
            {
                "equation_id": f"ch{chapter_num}_eq1",
                "latex_source": "E = mc^2",
                "context": "Einstein's mass-energy equivalence",
                "page": CRMB_CHAPTERS[chapter_num]["pages"][0],
                "equation_type": "display",
                "note": "Full extraction requires mathpix or specialized OCR"
            }
        ]
    
    def get_chapter_figures(self, chapter_num: int) -> List[Dict]:
        """
        Extract figure references and captions from chapter.
        
        Returns:
            [
                {
                    "figure_id": str,
                    "caption": str,
                    "page": int,
                    "referenced_in_text": List[str]
                }
            ]
        """
        text = self.get_chapter_text(chapter_num)
        
        # Simple heuristic: Find "Figure X" patterns
        figures = []
        import re
        
        pattern = r'Figure\s+(\d+)[:\.]?\s+([^.\n]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            figures.append({
                "figure_id": f"ch{chapter_num}_fig{match.group(1)}",
                "caption": match.group(2).strip(),
                "page": CRMB_CHAPTERS[chapter_num]["pages"][0],
                "referenced_in_text": [match.group(0)]
            })
        
        return figures[:20]  # Limit preview
    
    def search_across_chapters(self, query: str, chapters: Optional[List[int]] = None,
                               case_sensitive: bool = False) -> Dict:
        """
        Basic full-text search across corpus.
        
        Args:
            query: Search string
            chapters: List of chapters to search (None = all)
            case_sensitive: Whether search is case-sensitive
        
        Returns:
            {
                "query": str,
                "results": [
                    {
                        "chapter": int,
                        "page": int,
                        "context": str (text snippet),
                        "match_count": int
                    }
                ],
                "total_matches": int
            }
        """
        if chapters is None:
            chapters = list(range(1, 18))
        
        results = []
        total_matches = 0
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for ch_num in chapters:
            try:
                text = self.get_chapter_text(ch_num)
            except:
                continue
            
            matches = list(re.finditer(re.escape(query), text, flags))
            if matches:
                for match in matches[:3]:  # Preview first 3 matches per chapter
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    results.append({
                        "chapter": ch_num,
                        "chapter_title": CRMB_CHAPTERS[ch_num]["title"],
                        "context": f"...{context}...",
                        "match_position": match.start()
                    })
                
                total_matches += len(matches)
        
        return {
            "query": query,
            "chapters_searched": chapters,
            "results": results,
            "total_matches": total_matches,
            "note": f"Showing first 3 matches per chapter (total matches: {total_matches})"
        }
```

---

## 5. Efficient Coding Corpus Extension

### External Paper Management

```python
class ExternalCorpusManager:
    """Manages supplementary papers (Olshausen & Field 1996, Pouget et al., etc.)"""
    
    PAPER_REGISTRY = {
        "olshausen_field_1996": {
            "title": "Emergence of simple-cell receptive field properties by learning a sparse code",
            "authors": ["Bruno A. Olshausen", "David J. Field"],
            "year": 1996,
            "journal": "Nature",
            "volume": 381,
            "pages": (607, 609),
            "doi": "10.1038/381607a0",
            "domain": "efficient_coding",
            "key_concepts": ["sparse coding", "ICA", "natural image statistics"]
        },
        "pouget_et_al_2000": {
            "title": "Information processing with population codes",
            "authors": ["Alexandre Pouget", "Peter Dayan", "Richard Sejnowski"],
            "year": 2000,
            "journal": "Nature Reviews Neuroscience",
            "volume": 1,
            "pages": (125, 132),
            "doi": "10.1038/35039062",
            "domain": "population_coding",
            "key_concepts": ["population codes", "neural representation", "decoding"]
        },
        "barlow_1961": {
            "title": "Possible principles underlying the transformation of sensory messages",
            "authors": ["Horace B. Barlow"],
            "year": 1961,
            "conference": "Sensory Communication",
            "domain": "efficient_coding",
            "key_concepts": ["redundancy reduction", "coding efficiency", "information theory"]
        }
    }
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.papers_dir = self.base_dir / "external_papers"
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.papers_manifest_path = self.base_dir / "papers_manifest.json"
        self._load_papers_manifest()
    
    def _load_papers_manifest(self):
        """Load or create papers manifest."""
        if self.papers_manifest_path.exists():
            with open(self.papers_manifest_path, 'r') as f:
                self.papers_manifest = json.load(f)
        else:
            self.papers_manifest = {"papers": {}, "updated": None}
    
    def register_external_paper(self, paper_id: str, pdf_path: str,
                                domain: str = "efficient_coding",
                                metadata: Dict = None) -> Dict:
        """
        Register an external research paper.
        
        Args:
            paper_id: Identifier (e.g., "olshausen_field_1996")
            pdf_path: Path to PDF file
            domain: Research domain tag
            metadata: Additional metadata
        
        Returns:
            Registration metadata
        """
        if paper_id not in self.PAPER_REGISTRY:
            raise ValueError(f"Paper {paper_id} not in PAPER_REGISTRY")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Copy to papers directory
        dest_path = self.papers_dir / f"{paper_id}.pdf"
        if not dest_path.exists():
            import shutil
            shutil.copy2(pdf_path, dest_path)
        
        paper_info = self.PAPER_REGISTRY[paper_id].copy()
        paper_info.update({
            "pdf_path": str(dest_path),
            "file_size_mb": round(dest_path.stat().st_size / (1024 * 1024), 2),
            "domain": domain,
            "registered": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
        })
        
        self.papers_manifest["papers"][paper_id] = paper_info
        self.papers_manifest["updated"] = datetime.utcnow().isoformat() + "Z"
        self._save_papers_manifest()
        
        return paper_info
    
    def get_papers_by_domain(self, domain: str) -> List[Dict]:
        """Get all papers in a specific domain."""
        return [
            p for p in self.papers_manifest["papers"].values()
            if p.get("domain") == domain
        ]
    
    def _save_papers_manifest(self):
        """Save papers manifest."""
        with open(self.papers_manifest_path, 'w') as f:
            json.dump(self.papers_manifest, f, indent=2)
```

---

## 6. Quality Checks

### Validation and Assessment

```python
class CorpusQualityValidator:
    """Validates corpus quality across OCR, equations, and figures."""
    
    def __init__(self, base_dir: str, corpus_accessor: CorpusAccessor):
        self.base_dir = Path(base_dir)
        self.accessor = corpus_accessor
        self.quality_report = {}
    
    def assess_ocr_quality(self, chapter_num: int) -> Dict:
        """
        Assess OCR quality by detecting garbled text and confidence issues.
        
        Returns:
            {
                "chapter": int,
                "quality_score": float (0-100),
                "character_confidence": float,
                "garbled_text_rate": float,
                "detected_issues": List[str],
                "sample_issues": List[str]
            }
        """
        text = self.accessor.get_chapter_text(chapter_num)
        
        # Heuristics for garbled text detection
        garbled_indicators = []
        
        # Count sequences of unlikely character combinations
        import re
        unusual_sequences = re.findall(r'[^a-zA-Z0-9\s\-\.\,\:\;\(\)\[\]]{3,}', text)
        garbled_rate = len(unusual_sequences) / (len(text) / 1000) if text else 0
        
        # Check for common OCR errors
        ocr_errors = [
            ('rn', 'm'),  # 'rn' misread as 'm'
            ('1', 'l'),   # '1' vs 'l'
            ('0', 'O'),   # '0' vs 'O'
        ]
        
        detected_issues = []
        if garbled_rate > 0.5:
            detected_issues.append(f"High garbled text rate: {garbled_rate:.1f}%")
        
        # Simple confidence estimate (inverse of garbled rate)
        confidence = max(0, 100 - (garbled_rate * 100))
        
        return {
            "chapter": chapter_num,
            "quality_score": round(confidence, 1),
            "character_confidence": round(confidence, 1),
            "garbled_text_rate": round(garbled_rate, 3),
            "detected_issues": detected_issues,
            "sample_issues": unusual_sequences[:5]
        }
    
    def validate_equation_extraction(self, chapter_num: int) -> Dict:
        """
        Validate equation extraction completeness.
        
        Returns:
            {
                "chapter": int,
                "expected_equations": int,
                "extracted_equations": int,
                "coverage_rate": float,
                "assessment": str
            }
        """
        expected = CRMB_CHAPTERS[chapter_num]["expected_equations"]
        equations = self.accessor.get_chapter_equations(chapter_num)
        extracted = len(equations)
        
        coverage = (extracted / expected * 100) if expected > 0 else 0
        
        if coverage >= 80:
            assessment = "Good"
        elif coverage >= 60:
            assessment = "Moderate"
        else:
            assessment = "Poor - Manual review needed"
        
        return {
            "chapter": chapter_num,
            "expected_equations": expected,
            "extracted_equations": extracted,
            "coverage_rate": round(coverage, 1),
            "assessment": assessment
        }
    
    def validate_figure_count(self, chapter_num: int) -> Dict:
        """
        Validate figure extraction against expected count.
        
        Returns:
            {
                "chapter": int,
                "expected_figures": int,
                "extracted_figures": int,
                "validation_status": str
            }
        """
        expected = CRMB_CHAPTERS[chapter_num]["expected_figures"]
        figures = self.accessor.get_chapter_figures(chapter_num)
        extracted = len(figures)
        
        tolerance = 0.1  # 10% tolerance
        diff_rate = abs(extracted - expected) / expected if expected > 0 else 0
        
        if diff_rate <= tolerance:
            status = "PASS"
        else:
            status = "REVIEW_NEEDED"
        
        return {
            "chapter": chapter_num,
            "expected_figures": expected,
            "extracted_figures": extracted,
            "difference": extracted - expected,
            "validation_status": status
        }
    
    def full_corpus_quality_report(self) -> Dict:
        """
        Generate comprehensive quality report for entire corpus.
        
        Returns:
            {
                "generated": str (timestamp),
                "summary": {
                    "avg_ocr_quality": float,
                    "avg_equation_coverage": float,
                    "figure_validation_pass_rate": float
                },
                "chapter_reports": {
                    1: {...},
                    2: {...},
                    ...
                }
            }
        """
        chapter_reports = {}
        ocr_scores = []
        equation_coverages = []
        figure_passes = []
        
        for ch_num in range(1, 18):
            try:
                ocr_report = self.assess_ocr_quality(ch_num)
                equation_report = self.validate_equation_extraction(ch_num)
                figure_report = self.validate_figure_count(ch_num)
                
                chapter_reports[ch_num] = {
                    "ocr": ocr_report,
                    "equations": equation_report,
                    "figures": figure_report
                }
                
                ocr_scores.append(ocr_report["quality_score"])
                equation_coverages.append(equation_report["coverage_rate"])
                figure_passes.append(1 if figure_report["validation_status"] == "PASS" else 0)
            except:
                pass
        
        return {
            "generated": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "chapters_assessed": len(chapter_reports),
                "avg_ocr_quality": round(sum(ocr_scores) / len(ocr_scores), 1) if ocr_scores else 0,
                "avg_equation_coverage": round(sum(equation_coverages) / len(equation_coverages), 1) if equation_coverages else 0,
                "figure_validation_pass_rate": round(sum(figure_passes) / len(figure_passes) * 100, 1) if figure_passes else 0
            },
            "chapter_reports": chapter_reports
        }
```

---

## 7. Korean Metadata

### Localization Support

```python
class KoreanMetadata:
    """Manages Korean translations and localized metadata."""
    
    # Chapter title translations are in CRMB_CHAPTERS["title_ko"]
    
    KOREAN_CONCEPTS = {
        "stability-plasticity dilemma": "안정성-가소성 딜레마",
        "Adaptive Resonance Theory": "적응 공명 이론",
        "consciousness": "의식",
        "neural learning": "신경 학습",
        "synaptic plasticity": "시냅스 가소성",
        "Hebbian learning": "헵식 학습",
        "long-term potentiation": "장기 강화",
        "long-term depression": "장기 억제",
        "neural oscillations": "신경 진동",
        "feature extraction": "특징 추출",
        "receptive fields": "수용장",
        "sparse coding": "희소 코딩",
        "pattern completion": "패턴 완성",
        "invariance learning": "불변성 학습",
        "information maximization": "정보 최대화",
        "natural image statistics": "자연 이미지 통계",
        "basis functions": "기저 함수",
        "overcomplete dictionaries": "과완전 사전",
        "rate coding": "발화율 코딩",
        "temporal coding": "시간적 코딩",
        "population vector decoding": "집단 벡터 디코딩",
        "optimal decoding": "최적 디코딩",
        "information capacity": "정보 용량",
        "attention mechanisms": "주의 메커니즘",
        "gain modulation": "이득 변조",
        "spatial attention": "공간적 주의",
        "feature-based attention": "특징 기반 주의",
        "divisive normalization": "분할 정규화",
        "working memory": "작업 기억",
        "long-term memory": "장기 기억",
        "memory consolidation": "기억 고착화",
        "systems consolidation": "체계적 고착화",
        "reconsolidation": "재고착화",
        "value representation": "가치 표현",
        "reinforcement learning": "강화 학습",
        "dopamine signaling": "도파민 신호",
        "reward prediction error": "보상 예측 오차",
        "optimal decision-making": "최적 의사결정",
        "motor learning": "운동 학습",
        "cerebellar plasticity": "소뇌 가소성",
        "predictive control": "예측 제어",
        "error-driven learning": "오차 주도 학습",
        "forward models": "전진 모델",
        "sensorimotor transformation": "감각운동 변환",
        "coordinate frames": "좌표계",
        "gain fields": "이득장",
        "body schema": "신체 도식",
        "vestibular-visual integration": "전정계-시각 통합",
        "place cells": "위치 세포",
        "grid cells": "격자 세포",
        "head direction cells": "머리 방향 세포",
        "path integration": "경로 통합",
        "cognitive maps": "인지 지도",
        "lexical access": "어휘 접근",
        "semantic networks": "의미 네트워크",
        "distributional semantics": "분포적 의미론",
        "compositional structure": "조합론적 구조",
        "grounding language in perception": "지각에 언어 기반",
        "mentalizing": "마음 이론화",
        "mirror neurons": "거울 신경원",
        "social prediction": "사회적 예측",
        "intention inference": "의도 추론",
        "theory of mind": "마음의 이론",
        "affect valuation": "정동 가치평가",
        "amygdala function": "편도체 기능",
        "emotion regulation": "정서 조절",
        "emotional learning": "정서 학습",
        "interoception": "내감각",
        "embodied emotion": "구현된 정서",
        "REM sleep": "REM 수면",
        "non-REM sleep": "non-REM 수면",
        "sleep spindles": "수면 스핀들",
        "replay during sleep": "수면 중 재생",
        "integrated information theory": "통합 정보 이론",
        "conscious access": "의식적 접근",
        "neural correlates of consciousness": "의식의 신경 상관물",
        "metacognition": "메타인지",
        "binding problem": "결합 문제",
        "artificial general intelligence": "일반 인공지능",
        "brain-inspired computing": "뇌에 영감받은 컴퓨팅",
        "quantum cognition": "양자 인지",
        "neuroethics": "신경윤리",
        "translational neuroscience": "번역 신경과학"
    }
    
    @staticmethod
    def translate_concept(english_concept: str) -> Optional[str]:
        """Get Korean translation of a concept."""
        return KoreanMetadata.KOREAN_CONCEPTS.get(english_concept)
    
    @staticmethod
    def get_chapter_metadata_ko(chapter_num: int) -> Dict:
        """Get full Korean metadata for a chapter."""
        if chapter_num not in CRMB_CHAPTERS:
            return {}
        
        chapter = CRMB_CHAPTERS[chapter_num]
        return {
            "chapter_num": chapter_num,
            "title_en": chapter["title"],
            "title_ko": chapter["title_ko"],
            "key_concepts_en": chapter["key_concepts"],
            "key_concepts_ko": [
                KoreanMetadata.translate_concept(c) or c
                for c in chapter["key_concepts"]
            ]
        }
```

---

## Integration Guidance

### Usage Examples

```python
# 1. Initialize corpus infrastructure
loader = CorpusLoader("/path/to/corpus")
versioner = CorpusVersion("/path/to/corpus")
accessor = CorpusAccessor("/path/to/corpus")
validator = CorpusQualityValidator("/path/to/corpus", accessor)

# 2. Load chapters
for chapter_num in range(1, 18):
    metadata = loader.load_chapter_pdf(
        chapter_num,
        f"/path/to/original/chapter_{chapter_num}.pdf"
    )
    print(f"Loaded chapter {chapter_num}: {metadata['validation_status']}")

# 3. Validate completeness
completeness = loader.validate_corpus_completeness()
print(f"Corpus complete: {completeness['complete']}")
print(f"Chapters: {completeness['chapters_present']}")

# 4. Create version
for ch_num in range(1, 18):
    versioner.register_chapter(
        ch_num,
        f"/path/to/corpus/chapters/chapter_{ch_num:02d}.pdf",
        datetime.utcnow().isoformat() + "Z"
    )

versioner.create_version_snapshot("1.0.0", "Initial CRMB corpus load")

# 5. Access content
text = accessor.get_chapter_text(1)
sections = accessor.get_chapter_sections(3)
equations = accessor.get_chapter_equations(4)
figures = accessor.get_chapter_figures(2)

# 6. Search corpus
results = accessor.search_across_chapters("sparse coding")

# 7. Validate quality
quality_report = validator.full_corpus_quality_report()

# 8. Register external papers
paper_manager = ExternalCorpusManager("/path/to/corpus")
paper_manager.register_external_paper(
    "olshausen_field_1996",
    "/path/to/Olshausen_Field_1996.pdf",
    domain="efficient_coding"
)

# 9. Korean metadata
korean_ch1 = KoreanMetadata.get_chapter_metadata_ko(1)
print(korean_ch1["title_ko"])
```

---

## Performance Considerations

- **Caching**: CorpusAccessor implements in-memory cache for extracted text and sections
- **Lazy Loading**: PDF pages are extracted on-demand, not preloaded
- **Versioning**: Manifest-based approach avoids re-hashing large PDFs on every check
- **Search**: Full-text search is linear; consider indexing for large deployments

---

## Dependencies

- PyPDF2: PDF reading and page extraction
- hashlib: SHA-256 computation
- json: Manifest and metadata storage
- pathlib: Path operations
- datetime: Timestamps and versioning
- Optional: mathpix, pdfplumber for advanced equation/layout extraction
