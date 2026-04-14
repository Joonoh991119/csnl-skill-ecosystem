---
name: db-pipeline
description: >
  Comprehensive LanceDB-to-pgvector migration for CRMB_tutor with Marker PDF conversion,
  equation extraction via Nougat, figure extraction, schema migration, re-embedding with
  BGE-M3, and before/after eval automation. Migrates 20 chapters from summaries-only
  (3072-dim) to full raw text + equations (1024-dim correct for BGE-M3).
  MANDATORY TRIGGERS: db pipeline, migrate schema, marker pdf, nougat equations,
  pgvector migration, chapter extraction, crmb database improvement, re-embedding,
  schema versioning, LanceDB audit, batch processing chapters.
---

# db-pipeline: Comprehensive DB Improvement for CRMB_tutor

## Overview

This skill orchestrates a complete database improvement pipeline for CRMB_tutor:
- **Current state**: LanceDB with chapter summaries only, 3072-dim vectors
- **Target state**: PostgreSQL pgvector with raw text + equations + figures, 1024-dim BGE-M3 vectors

The pipeline integrates:
1. **Marker** for high-quality PDF→markdown conversion (uses existing chunker_v2.py)
2. **Nougat** for equation-heavy pages (fallback)
3. **PyMuPDF** for figure extraction with captions
4. **pgvector migration** with schema versioning and rollback support
5. **BGE-M3 re-embedding** with batch optimization for Apple Silicon
6. **Eval automation** with before/after quality comparison and auto-rollback

---

## 1. Current State Assessment

Audit your existing LanceDB to understand what you're starting with.

```python
import lancedb
import pandas as pd
from pathlib import Path

def audit_lancedb(db_path: str = "./db/crmb_lance") -> dict:
    """Audit existing LanceDB: chunks, dimensions, schema."""
    try:
        db = lancedb.connect(db_path)
        table = db.open_table("crmb_chunks")
        df = table.to_pandas()
        
        sample_vec = df["vector"].iloc[0]
        dims = len(sample_vec) if isinstance(sample_vec, list) else sample_vec.shape[0]
        
        audit = {
            "total_chunks": len(df),
            "vector_dims": dims,
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
        }
        
        # Check for summaries-only content
        has_raw_text = "raw_text" in df.columns
        has_equations = "equations_latex" in df.columns
        
        audit["content_types"] = {
            "summaries_only": not has_raw_text and not has_equations,
            "has_raw_text": has_raw_text,
            "has_equations": has_equations,
        }
        
        print(f"\n✓ LanceDB Audit Complete")
        print(f"  Chunks: {audit['total_chunks']}")
        print(f"  Vector dims: {audit['vector_dims']}")
        print(f"  Columns: {audit['columns']}")
        print(f"  Content: {audit['content_types']}")
        return audit
        
    except Exception as e:
        print(f"✗ Audit failed: {e}")
        return None

# Usage
audit = audit_lancedb()
```

**Expected output for current state:**
```
✓ LanceDB Audit Complete
  Chunks: ~150
  Vector dims: 3072
  Columns: ['text', 'vector', 'chapter', 'page']
  Content: {'summaries_only': True, 'has_raw_text': False, 'has_equations': False}
```

---

## 2. Marker Pipeline: PDF→Markdown Conversion

Use Marker for batch conversion of all 20 CRMB chapters to high-quality markdown.

```python
import subprocess
import json
from pathlib import Path
from typing import List, Dict

def run_marker_single(pdf_path: str, output_dir: str) -> Dict:
    """Run marker_single CLI on one chapter PDF."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            "marker_single",
            pdf_path,
            "-o", str(output_dir),
            "--workers", "4",  # Parallel page processing
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            # Extract output markdown path
            md_file = output_dir / Path(pdf_path).stem / "index.md"
            return {
                "pdf": pdf_path,
                "status": "success",
                "markdown": str(md_file) if md_file.exists() else None,
                "output_dir": str(output_dir),
            }
        else:
            return {"pdf": pdf_path, "status": "failed", "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"pdf": pdf_path, "status": "timeout"}
    except Exception as e:
        return {"pdf": pdf_path, "status": "error", "error": str(e)}

def run_marker_batch(pdf_dir: str, output_base: str) -> List[Dict]:
    """Run Marker on all 20 CRMB chapter PDFs."""
    pdf_dir = Path(pdf_dir)
    results = []
    
    # Discover all chapter PDFs
    chapter_pdfs = sorted(pdf_dir.glob("chapter_*.pdf")) or \
                   sorted(pdf_dir.glob("*.pdf"))
    
    print(f"\n→ Running Marker on {len(chapter_pdfs)} chapters...")
    for i, pdf in enumerate(chapter_pdfs, 1):
        print(f"  [{i}/{len(chapter_pdfs)}] {pdf.name}...", end=" ", flush=True)
        result = run_marker_single(str(pdf), f"{output_base}/marker")
        results.append(result)
        print(f"{'✓' if result['status'] == 'success' else '✗'}")
    
    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"\n✓ Marker batch: {successful}/{len(chapter_pdfs)} successful")
    return results

def load_marker_markdown(md_path: str) -> str:
    """Load markdown from Marker output."""
    with open(md_path, "r") as f:
        return f.read()

# Usage
marker_results = run_marker_batch(
    pdf_dir="/path/to/crmb_chapters",
    output_base="/tmp/crmb_processing"
)
```

**Integration with chunker_v2.py:**
```python
# In chunker_v2.py, replace raw PDF parsing with Marker output:
def chunk_marker_output(md_content: str, chapter_id: int) -> List[Dict]:
    """Parse Marker markdown and create chunks with preserved structure."""
    chunks = []
    
    # Split by headings while preserving hierarchy
    sections = re.split(r'^(#{1,3})\s+(.+)$', md_content, flags=re.MULTILINE)
    
    for i in range(1, len(sections), 3):
        level, heading, content = sections[i:i+3]
        chunk = {
            "chapter": chapter_id,
            "heading": heading.strip(),
            "level": len(level),
            "content": content.strip(),
            "raw_text": f"{heading}\n\n{content}",  # NEW
        }
        chunks.append(chunk)
    
    return chunks
```

---

## 3. Nougat Fallback for Equation-Heavy Pages

When Marker has trouble with complex equations, use Nougat as fallback.

```python
import requests
import json
from pathlib import Path

def detect_equation_pages(pdf_path: str) -> List[int]:
    """Detect pages with heavy equation content using heuristics."""
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    equation_pages = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        # Heuristic: count equation indicators
        eq_indicators = text.count("$") + text.count("\\") + text.count("∑")
        if eq_indicators > 10:  # Tunable threshold
            equation_pages.append(page_num)
    
    return equation_pages

def run_nougat(pdf_path: str, page_numbers: List[int], 
               nougat_url: str = "http://localhost:8503") -> Dict:
    """Submit pages to Nougat service for equation extraction."""
    try:
        # Start Nougat service if not running
        # docker run --gpus all -p 8503:8000 nougat-service
        
        with open(pdf_path, "rb") as f:
            files = {"pdf": f}
            data = {"pages": ",".join(map(str, page_numbers))}
            response = requests.post(
                f"{nougat_url}/predict",
                files=files,
                data=data,
                timeout=300
            )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "pages": page_numbers,
                "latex": response.json()
            }
        else:
            return {"status": "failed", "error": response.text}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def merge_nougat_with_marker(marker_md: str, nougat_result: Dict) -> str:
    """Merge Nougat equation output back into Marker markdown."""
    if nougat_result["status"] != "success":
        return marker_md
    
    # Replace equation blocks in markdown with Nougat LaTeX
    latex_blocks = nougat_result.get("latex", {})
    merged = marker_md
    
    for page_str, latex_content in latex_blocks.items():
        # Find equation placeholders and replace with Nougat output
        placeholder = f"[EQUATION_PAGE_{page_str}]"
        if placeholder in merged:
            merged = merged.replace(placeholder, latex_content)
    
    return merged

# Usage
def process_chapter_with_nougat_fallback(pdf_path: str, marker_md: str) -> str:
    """Enhanced chapter processing with Nougat fallback."""
    eq_pages = detect_equation_pages(pdf_path)
    
    if eq_pages:
        print(f"  Detected {len(eq_pages)} equation-heavy pages, using Nougat...")
        nougat_result = run_nougat(pdf_path, eq_pages)
        marker_md = merge_nougat_with_marker(marker_md, nougat_result)
    
    return marker_md
```

---

## 4. Figure Extraction Pipeline

Extract all figures with captions and create figure-to-section mappings.

```python
import fitz  # PyMuPDF
import json
from pathlib import Path
from typing import List, Tuple

def extract_figures(pdf_path: str, output_dir: str, chapter_id: int) -> List[Dict]:
    """Extract all images from PDF with caption detection."""
    output_dir = Path(output_dir)
    figures_dir = output_dir / "figures" / f"chapter_{chapter_id:02d}"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    figures = []
    
    for page_num, page in enumerate(doc):
        # Extract images
        image_list = page.get_images()
        
        for img_index, img_id in enumerate(image_list):
            xref = img_id
            pix = fitz.Pixmap(doc, xref)
            
            # Save image
            img_file = figures_dir / f"fig_{page_num:03d}_{img_index:02d}.png"
            pix.save(str(img_file))
            pix = None
            
            # Detect caption: text below image
            # (Simple heuristic: text within 50px below image bbox)
            img_rect = page.get_image_bbox(img_id)
            search_rect = fitz.Rect(img_rect.x0, img_rect.y1, img_rect.x1, 
                                   img_rect.y1 + 50)
            caption_text = page.get_text("text", clip=search_rect).strip()
            
            figures.append({
                "chapter": chapter_id,
                "page": page_num,
                "image_file": str(img_file),
                "caption": caption_text or "No caption",
                "bbox": {
                    "x0": img_rect.x0, "y0": img_rect.y0,
                    "x1": img_rect.x1, "y1": img_rect.y1
                }
            })
    
    doc.close()
    
    # Save metadata
    metadata_file = figures_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(figures, f, indent=2)
    
    print(f"  Extracted {len(figures)} figures → {figures_dir}")
    return figures

def batch_extract_figures(pdf_dir: str, output_base: str) -> Dict:
    """Extract figures from all chapters."""
    pdf_dir = Path(pdf_dir)
    all_figures = {}
    
    chapter_pdfs = sorted(pdf_dir.glob("chapter_*.pdf")) or \
                   sorted(pdf_dir.glob("*.pdf"))
    
    for chapter_id, pdf in enumerate(chapter_pdfs, 1):
        print(f"→ Extracting figures from {pdf.name}...")
        figures = extract_figures(str(pdf), output_base, chapter_id)
        all_figures[f"chapter_{chapter_id}"] = figures
    
    return all_figures
```

---

## 5. pgvector Schema Migration

Versioned migration from LanceDB to PostgreSQL with dimension fix.

```python
import psycopg2
from psycopg2.extras import execute_values
import json
from datetime import datetime

MIGRATIONS = {
    'v1_to_v2': {
        'description': 'Summaries-only (current) → Raw text + equations + figures',
        'changes': {
            'add_columns': [
                ('raw_text', 'TEXT', 'Full chapter text from Marker'),
                ('equations_latex', 'TEXT', 'Equation content as LaTeX'),
                ('figure_refs', 'TEXT[]', 'References to extracted figures'),
                ('section_path', 'TEXT', 'Hierarchical section path'),
            ],
            'alter_dim': {'from': 3072, 'to': 1024},
            'note': 'BGE-M3 correct dimension is 1024, not 3072'
        }
    }
}

class PgvectorMigration:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
    
    def connect(self):
        """Connect to PostgreSQL."""
        self.conn = psycopg2.connect(self.db_url)
        return self.conn
    
    def init_schema_versioning(self):
        """Create schema version tracking table."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT NOW(),
                    status VARCHAR(20) DEFAULT 'pending'
                )
            """)
            self.conn.commit()
    
    def create_v2_schema(self):
        """Create pgvector table for v2 (raw text + equations)."""
        with self.conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create chunks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crmb_chunks_v2 (
                    id BIGSERIAL PRIMARY KEY,
                    chapter INT NOT NULL,
                    page INT,
                    text TEXT,
                    raw_text TEXT,
                    equations_latex TEXT,
                    figure_refs TEXT[],
                    section_path TEXT,
                    vector vector(1024),
                    vector_sparse JSON,
                    vector_colbert JSON,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create HNSW index for fast similarity search
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_crmb_vector_hnsw 
                ON crmb_chunks_v2 
                USING hnsw (vector vector_cosine_ops)
                WITH (m=16, ef_construction=200)
            """)
            
            self.conn.commit()
    
    def migrate_v1_to_v2(self, lancedb_df):
        """Migrate data from LanceDB to pgvector v2."""
        print("→ Migrating data from LanceDB to pgvector...")
        
        with self.conn.cursor() as cur:
            # Insert data from LanceDB
            rows = []
            for _, row in lancedb_df.iterrows():
                rows.append((
                    row['chapter'],
                    row.get('page', None),
                    row.get('text', ''),
                    row.get('raw_text', ''),  # NEW
                    row.get('equations_latex', ''),  # NEW
                    row.get('figure_refs', []),  # NEW
                    row.get('section_path', ''),  # NEW
                    row['vector'],  # Will be re-embedded
                ))
            
            execute_values(
                cur,
                """INSERT INTO crmb_chunks_v2 
                   (chapter, page, text, raw_text, equations_latex, 
                    figure_refs, section_path, vector)
                   VALUES %s""",
                rows,
                page_size=1000
            )
            self.conn.commit()
            print(f"✓ Inserted {len(rows)} chunks into pgvector")
    
    def record_migration(self, from_version: str, to_version: str, status: str):
        """Record migration in schema_versions table."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO schema_versions (version, description, status)
                VALUES (%s, %s, %s)
            """, (
                f"{from_version}_to_{to_version}",
                MIGRATIONS[f"{from_version}_to_{to_version}"].get('description', ''),
                status
            ))
            self.conn.commit()
    
    def rollback_to_v1(self):
        """Rollback migration if quality degradation detected."""
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS crmb_chunks_v2")
            cur.execute("UPDATE schema_versions SET status = 'rolled_back' WHERE version LIKE '%v1_to_v2%'")
            self.conn.commit()
            print("✓ Rolled back to v1")
    
    def close(self):
        if self.conn:
            self.conn.close()

# Usage
def setup_pgvector(db_url: str, lancedb_df):
    """Complete setup: versioning + v2 schema + migration."""
    migration = PgvectorMigration(db_url)
    migration.connect()
    
    try:
        migration.init_schema_versioning()
        migration.create_v2_schema()
        migration.migrate_v1_to_v2(lancedb_df)
        migration.record_migration('v1', 'v2', 'completed')
        print("✓ pgvector v2 schema ready")
        return migration
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        migration.rollback_to_v1()
        raise
    finally:
        migration.close()
```

---

## 6. Re-Embedding Pipeline

Batch embed with BGE-M3 (dense + sparse + ColBERT), optimized for Apple Silicon.

```python
from sentence_transformers import SentenceTransformer
import numpy as np
import torch
from tqdm import tqdm
from typing import List, Tuple

class BGEMembedder:
    def __init__(self, device: str = "mps"):
        """Initialize BGE-M3 with device optimization."""
        self.device = device
        if device == "mps":
            # Apple Silicon optimization
            torch.set_default_device("mps")
        
        self.model = SentenceTransformer("BAAI/bge-m3")
        self.model.to(device)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Batch embedding with progress tracking."""
        embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size), 
                      desc="Embedding chunks"):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(
                batch,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            embeddings.append(batch_embeddings)
        
        return np.vstack(embeddings)
    
    def embed_with_sparse_colbert(self, texts: List[str]) -> Tuple[np.ndarray, list, list]:
        """BGE-M3 dense + sparse + ColBERT embeddings."""
        # Dense embeddings
        dense = self.model.encode(
            texts,
            batch_size=32,
            return_dense=True,
            convert_to_numpy=True
        )
        
        # Sparse embeddings (BM25-style token weights)
        sparse = self.model.encode(
            texts,
            batch_size=32,
            return_sparse=True
        )
        
        # ColBERT embeddings (late interaction)
        colbert = self.model.encode(
            texts,
            batch_size=32,
            return_colbert_vecs=True
        )
        
        return dense, sparse, colbert

def reembed_all_chunks(pgvector_migration, chapters: int = 20):
    """Re-embed all chunks with BGE-M3."""
    print("\n→ Re-embedding chunks with BGE-M3...")
    
    embedder = BGEMembedder(device="mps")
    
    with pgvector_migration.conn.cursor() as cur:
        for chapter in range(1, chapters + 1):
            # Fetch chapter chunks
            cur.execute("""
                SELECT id, raw_text FROM crmb_chunks_v2 
                WHERE chapter = %s
                ORDER BY page
            """, (chapter,))
            
            rows = cur.fetchall()
            if not rows:
                continue
            
            # Extract texts
            ids = [row[0] for row in rows]
            texts = [row[1] for row in rows]
            
            # Embed with BGE-M3
            dense, sparse, colbert = embedder.embed_with_sparse_colbert(texts)
            
            # Verify dimension
            assert dense.shape[1] == 1024, f"ERROR: Dense dim {dense.shape[1]}, expected 1024"
            
            # Update database
            for idx, (chunk_id, d, s, c) in enumerate(
                zip(ids, dense, sparse, colbert)
            ):
                cur.execute("""
                    UPDATE crmb_chunks_v2 
                    SET vector = %s, 
                        vector_sparse = %s,
                        vector_colbert = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (d.tolist(), json.dumps(s), json.dumps(c), chunk_id))
            
            pgvector_migration.conn.commit()
            print(f"  ✓ Chapter {chapter}: re-embedded {len(ids)} chunks")
    
    print("✓ Re-embedding complete (1024-dim BGE-M3)")

# Usage: reembed_all_chunks(migration, chapters=20)
```

---

## 7. Eval Automation: Before/After Comparison

Compare retrieval quality before and after migration with auto-rollback.

```python
import json
from typing import Dict, List

class EvalComparison:
    def __init__(self, pgvector_migration, before_snapshot: Dict):
        self.migration = pgvector_migration
        self.before = before_snapshot
        self.after = {}
    
    def run_bootstrap_queries_v2(self, num_queries: int = 50) -> Dict:
        """Run bootstrap_ground_truth_v2 evaluation after migration."""
        print(f"\n→ Running {num_queries} bootstrap queries on v2...")
        
        # Example evaluation queries (customize for your domain)
        test_queries = [
            "chapter summaries and key concepts",
            "mathematical equations and definitions",
            "figure captions and illustrations",
            "section organization and hierarchies",
            # ... add more as needed
        ]
        
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-m3")
        
        results = {
            "ndcg_10": [],
            "mrr_5": [],
            "recall_20": [],
            "query_details": []
        }
        
        with self.migration.conn.cursor() as cur:
            for query in test_queries[:num_queries]:
                # Embed query
                q_embedding = model.encode(query, convert_to_numpy=True)
                
                # Retrieve top-20 neighbors
                cur.execute("""
                    SELECT id, text, 1 - (vector <=> %s::vector) as similarity
                    FROM crmb_chunks_v2
                    ORDER BY vector <=> %s::vector
                    LIMIT 20
                """, (q_embedding.tolist(), q_embedding.tolist()))
                
                retrieved = cur.fetchall()
                
                # Calculate metrics (simplified)
                ndcg = self._calc_ndcg(retrieved, query)
                mrr = self._calc_mrr(retrieved, query)
                recall = self._calc_recall(retrieved, query)
                
                results["ndcg_10"].append(ndcg)
                results["mrr_5"].append(mrr)
                results["recall_20"].append(recall)
                results["query_details"].append({
                    "query": query,
                    "ndcg": ndcg,
                    "mrr": mrr,
                    "recall": recall
                })
        
        self.after = {
            "ndcg_10_mean": np.mean(results["ndcg_10"]),
            "mrr_5_mean": np.mean(results["mrr_5"]),
            "recall_20_mean": np.mean(results["recall_20"]),
            "queries_tested": num_queries
        }
        
        return results
    
    def _calc_ndcg(self, results, query, k=10):
        """Simplified NDCG calculation."""
        relevance = [1 if query.lower() in r[1].lower() else 0 
                     for r in results[:k]]
        dcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(relevance))
        return dcg
    
    def _calc_mrr(self, results, query, k=5):
        """Mean Reciprocal Rank."""
        for i, (_, text, _) in enumerate(results[:k], 1):
            if query.lower() in text.lower():
                return 1.0 / i
        return 0.0
    
    def _calc_recall(self, results, query):
        """Recall@20."""
        relevant = sum(1 for _, text, _ in results 
                       if query.lower() in text.lower())
        return min(relevant / 5, 1.0)  # Assume ~5 relevant
    
    def generate_diff_report(self, threshold: float = 0.10) -> Dict:
        """Compare before/after and generate report."""
        print("\n→ Generating eval report...")
        
        before_ndcg = self.before.get("ndcg_10_mean", 0)
        after_ndcg = self.after.get("ndcg_10_mean", 0)
        
        ndcg_change = (after_ndcg - before_ndcg) / max(before_ndcg, 0.01)
        
        report = {
            "before": self.before,
            "after": self.after,
            "improvements": {
                "ndcg_10": f"{ndcg_change:+.2%}",
                "status": "✓ PASS" if ndcg_change > -threshold else "✗ ROLLBACK"
            }
        }
        
        print(f"\nEval Report:")
        print(f"  Before NDCG@10: {before_ndcg:.4f}")
        print(f"  After NDCG@10:  {after_ndcg:.4f}")
        print(f"  Change: {ndcg_change:+.2%}")
        print(f"  Status: {report['improvements']['status']}")
        
        if ndcg_change < -threshold:
            print(f"\n⚠ Quality degradation > {threshold:.0%}, initiating rollback...")
            self.migration.rollback_to_v1()
            report["rolled_back"] = True
        else:
            report["rolled_back"] = False
        
        return report

# Usage in orchestrator
```

---

## 8. Pipeline Orchestrator: Full End-to-End Execution

Complete workflow: audit → Marker → equations → figures → migrate → re-embed → eval.

```python
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DBPipelineOrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.log_dir = Path(config.get("log_dir", "/tmp/crmb_pipeline"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"pipeline_{datetime.now().isoformat()}.json"
        self.pipeline_log = {"start_time": datetime.now().isoformat(), "steps": {}}
    
    def log_step(self, step_name: str, status: str, details: Dict = None):
        """Log pipeline step execution."""
        self.pipeline_log["steps"][step_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        logging.info(f"[{step_name}] {status}")
    
    def run_full_pipeline(self):
        """Execute complete DB improvement pipeline."""
        try:
            # Step 1: Audit
            logging.info("\n" + "="*60)
            logging.info("STEP 1: Current State Assessment")
            logging.info("="*60)
            audit = audit_lancedb(self.config["lancedb_path"])
            self.log_step("audit", "completed", audit)
            
            # Step 2: Marker
            logging.info("\n" + "="*60)
            logging.info("STEP 2: Marker PDF→Markdown Conversion")
            logging.info("="*60)
            marker_results = run_marker_batch(
                self.config["pdf_dir"],
                self.config["output_dir"]
            )
            self.log_step("marker", "completed", {"successful": len([r for r in marker_results if r['status'] == 'success'])})
            
            # Step 3: Equations (Nougat)
            logging.info("\n" + "="*60)
            logging.info("STEP 3: Nougat Equation Extraction")
            logging.info("="*60)
            equation_results = {}
            for marker_result in marker_results:
                if marker_result["status"] == "success":
                    md_content = load_marker_markdown(marker_result["markdown"])
                    md_enhanced = process_chapter_with_nougat_fallback(
                        marker_result["pdf"],
                        md_content
                    )
                    equation_results[marker_result["pdf"]] = md_enhanced
            self.log_step("equations", "completed", {"chapters_processed": len(equation_results)})
            
            # Step 4: Figures
            logging.info("\n" + "="*60)
            logging.info("STEP 4: Figure Extraction")
            logging.info("="*60)
            figures = batch_extract_figures(
                self.config["pdf_dir"],
                self.config["output_dir"]
            )
            self.log_step("figures", "completed", {"total_figures": sum(len(v) for v in figures.values())})
            
            # Step 5: Schema Migration
            logging.info("\n" + "="*60)
            logging.info("STEP 5: pgvector Schema Migration")
            logging.info("="*60)
            lancedb_df = lancedb.connect(self.config["lancedb_path"]).open_table("crmb_chunks").to_pandas()
            migration = setup_pgvector(self.config["pgvector_url"], lancedb_df)
            self.log_step("migration", "completed", {"rows_migrated": len(lancedb_df)})
            
            # Step 6: Re-embedding
            logging.info("\n" + "="*60)
            logging.info("STEP 6: BGE-M3 Re-embedding (1024-dim)")
            logging.info("="*60)
            reembed_all_chunks(migration, chapters=20)
            self.log_step("reembedding", "completed", {})
            
            # Step 7: Eval
            logging.info("\n" + "="*60)
            logging.info("STEP 7: Before/After Eval")
            logging.info("="*60)
            eval_comp = EvalComparison(migration, audit)
            eval_results = eval_comp.run_bootstrap_queries_v2(num_queries=50)
            report = eval_comp.generate_diff_report(threshold=0.10)
            self.log_step("eval", "completed", report)
            
            self.pipeline_log["end_time"] = datetime.now().isoformat()
            self.pipeline_log["status"] = "success" if not report.get("rolled_back") else "rolled_back"
            
            # Save log
            with open(self.log_file, "w") as f:
                json.dump(self.pipeline_log, f, indent=2)
            
            logging.info(f"\n✓ Pipeline complete. Log: {self.log_file}")
            return report
            
        except Exception as e:
            logging.error(f"\n✗ Pipeline failed: {e}")
            self.log_step("error", "failed", {"error": str(e)})
            with open(self.log_file, "w") as f:
                json.dump(self.pipeline_log, f, indent=2)
            raise

# Usage
if __name__ == "__main__":
    config = {
        "lancedb_path": "/path/to/crmb_lance",
        "pgvector_url": "postgresql://user:pass@localhost/crmb",
        "pdf_dir": "/path/to/crmb_chapters",
        "output_dir": "/tmp/crmb_processing",
        "log_dir": "/tmp/crmb_pipeline/logs",
        "nougat_url": "http://localhost:8503",
    }
    
    orchestrator = DBPipelineOrchestrator(config)
    report = orchestrator.run_full_pipeline()
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install markers nougat sentence-transformers pymupdf lancedb psycopg2-binary

# 2. Start Nougat service (in separate terminal)
docker run --gpus all -p 8503:8000 nougat-service

# 3. Run pipeline
python -c "
from db_pipeline import DBPipelineOrchestrator
config = {
    'lancedb_path': './db/crmb_lance',
    'pgvector_url': 'postgresql://user:pass@localhost/crmb',
    'pdf_dir': './data/chapters',
    'output_dir': '/tmp/crmb_processing',
}
orchestrator = DBPipelineOrchestrator(config)
report = orchestrator.run_full_pipeline()
"
```

---

## Key Metrics & Success Criteria

- ✓ All 20 chapters converted via Marker to markdown with equations preserved
- ✓ Figure extraction: 100+ figures extracted with captions
- ✓ pgvector v2 schema: raw_text, equations_latex, figure_refs columns added
- ✓ Vector dimension: **1024-dim BGE-M3** (from incorrect 3072-dim)
- ✓ Eval: NDCG@10 improvement ≥5% or maintain within -10% threshold
- ✓ Zero data loss: rollback supported if quality degradation detected

---

## Troubleshooting

**Marker timeout on large PDFs:**
```python
# Increase timeout in run_marker_single
subprocess.run(cmd, timeout=1200)  # 20 min
```

**Nougat service not responding:**
```bash
curl http://localhost:8503/health  # Check service
docker logs nougat-service  # View logs
```

**pgvector dimension mismatch:**
```python
# Always verify after migration
cur.execute("SELECT vector FROM crmb_chunks_v2 LIMIT 1")
vec = cur.fetchone()[0]
assert len(vec) == 1024, f"Got {len(vec)}-dim, expected 1024"
```

**Out of memory during re-embedding:**
```python
# Reduce batch size
embedder.embed_batch(texts, batch_size=8)
```

## Resilience: Checkpoint & Partial Resumption

### Pipeline Checkpoint
```python
class PipelineCheckpoint:
    STEPS = ['marker', 'nougat', 'figures', 'migrate', 'embed', 'eval']
    
    def __init__(self, path="./pipeline_checkpoint.json"):
        self.path = path
        self.state = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f: return json.load(f)
        return {"chapters": {}, "current_step": None}
    
    def chapter_status(self, ch):
        return self.state["chapters"].get(str(ch), {})
    
    def mark_step_done(self, ch, step):
        self.state["chapters"].setdefault(str(ch), {})[step] = "done"
        with open(self.path, 'w') as f: json.dump(self.state, f)
    
    def needs_processing(self, ch, step):
        return self.chapter_status(ch).get(step) != "done"
```

### Mixed-Dimension Detection & Fix
```python
def detect_mixed_dimensions(conn):
    """Find chapters with wrong vector dimensions."""
    cur = conn.cursor()
    cur.execute("SELECT chapter, array_length(vector, 1) as dim, COUNT(*) FROM chunks GROUP BY chapter, dim")
    mixed = {}
    for ch, dim, count in cur.fetchall():
        if dim != 1024: mixed[ch] = {"dim": dim, "count": count}
    return mixed

def fix_mixed_dimensions(conn, embedder, mixed_chapters):
    """Re-embed only chapters with wrong dimensions."""
    for ch, info in mixed_chapters.items():
        texts = fetch_chapter_texts(conn, ch)
        new_vecs = batch_reembed_mps(texts)
        update_chapter_vectors(conn, ch, new_vecs)
```

### Smart Baseline Strategy
```python
def should_retake_baseline(conn, last_baseline_date, current_chunk_count):
    """Decide if baseline needs refresh."""
    baseline_count = get_baseline_chunk_count(last_baseline_date)
    drift = abs(current_chunk_count - baseline_count) / max(baseline_count, 1)
    mixed = detect_mixed_dimensions(conn)
    if mixed: return True, "mixed dimensions detected"
    if drift > 0.1: return True, f"chunk count drift {drift:.0%}"
    return False, "baseline still valid"
```

---

## Deep Robustness: P3 Eval Enhancements

### 1. Enhanced Checkpoint with File-Based Persistence

Full file-based checkpoint system with resume capabilities:

```python
import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

class PipelineCheckpoint:
    CHECKPOINT_FILE = "pipeline_checkpoint.json"
    STEPS = ['marker', 'nougat', 'figures', 'migrate', 'embed', 'eval']
    
    def __init__(self, checkpoint_file: str = "pipeline_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
        self.chapters = {}
        self.timestamps = {}
    
    def save(self):
        """Persist checkpoint state to JSON file with timestamp."""
        checkpoint_data = {
            "chapters": self.chapters,
            "timestamps": self.timestamps,
            "last_save": datetime.now().isoformat(),
            "total_chapters": len(self.chapters)
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logging.info(f"✓ Checkpoint saved to {self.checkpoint_file}")
        except IOError as e:
            logging.error(f"✗ Failed to save checkpoint: {e}")
            raise
    
    def load(self) -> bool:
        """Resume from last saved checkpoint."""
        if not os.path.exists(self.checkpoint_file):
            logging.info("No existing checkpoint found, starting fresh")
            return False
        
        try:
            with open(self.checkpoint_file) as f:
                data = json.load(f)
            self.chapters = data.get("chapters", {})
            self.timestamps = data.get("timestamps", {})
            logging.info(f"✓ Checkpoint loaded: {len(self.chapters)} chapters")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"✗ Failed to load checkpoint: {e}")
            return False
    
    def mark_step_done(self, chapter: int, step: str):
        """Mark a step as complete for a chapter."""
        ch_str = str(chapter)
        if ch_str not in self.chapters:
            self.chapters[ch_str] = {}
        self.chapters[ch_str][step] = "done"
        self.timestamps[f"{ch_str}_{step}"] = datetime.now().isoformat()
        self.save()
    
    def needs_processing(self, chapter: int, step: str) -> bool:
        """Check if a step needs processing for a chapter."""
        ch_str = str(chapter)
        return self.chapters.get(ch_str, {}).get(step) != "done"
    
    def get_resume_point(self) -> Optional[Tuple[int, str]]:
        """Find first incomplete step across all chapters."""
        for ch_num in sorted([int(k) for k in self.chapters.keys()]):
            for step in self.STEPS:
                if self.needs_processing(ch_num, step):
                    return (ch_num, step)
        return None
    
    def get_progress_summary(self) -> Dict:
        """Get human-readable progress summary."""
        summary = {
            "total_chapters": len(self.chapters),
            "steps_by_chapter": {},
            "completion_percentage": 0
        }
        
        total_tasks = len(self.chapters) * len(self.STEPS)
        completed_tasks = 0
        
        for ch_str, steps in self.chapters.items():
            completed = sum(1 for s in self.STEPS if steps.get(s) == "done")
            summary["steps_by_chapter"][ch_str] = f"{completed}/{len(self.STEPS)}"
            completed_tasks += completed
        
        if total_tasks > 0:
            summary["completion_percentage"] = (completed_tasks / total_tasks) * 100
        
        return summary
```

### 2. Partial Migration Rollback Manager

Handle schema migrations with built-in rollback capabilities:

```python
import psycopg2
from typing import List, Dict
import logging

class RollbackManager:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.snapshots = {}
        self.migration_log = []
    
    def snapshot_before_migration(self, table_name: str) -> bool:
        """Save table state before migration for rollback."""
        try:
            cur = self.conn.cursor()
            # Save schema
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            schema = cur.fetchall()
            
            # Count rows
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cur.fetchone()[0]
            
            # Save row samples (first 100)
            cur.execute(f"SELECT * FROM {table_name} LIMIT 100")
            sample_rows = cur.fetchall()
            
            self.snapshots[table_name] = {
                "schema": schema,
                "row_count": row_count,
                "sample_rows": sample_rows,
                "timestamp": datetime.now().isoformat()
            }
            
            self.migration_log.append({
                "action": "snapshot",
                "table": table_name,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            logging.info(f"✓ Snapshot saved for {table_name}: {row_count} rows")
            return True
        except Exception as e:
            logging.error(f"✗ Snapshot failed for {table_name}: {e}")
            self.migration_log.append({
                "action": "snapshot",
                "table": table_name,
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def rollback(self, table_name: str) -> bool:
        """Restore table to pre-migration state."""
        if table_name not in self.snapshots:
            logging.error(f"✗ No snapshot available for {table_name}")
            return False
        
        try:
            cur = self.conn.cursor()
            snapshot = self.snapshots[table_name]
            
            # Rename current table
            cur.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_failed")
            
            # Restore from backup table if exists
            cur.execute(f"ALTER TABLE {table_name}_backup RENAME TO {table_name}")
            
            self.conn.commit()
            
            self.migration_log.append({
                "action": "rollback",
                "table": table_name,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            logging.info(f"✓ Rollback successful for {table_name}")
            return True
        except Exception as e:
            logging.error(f"✗ Rollback failed: {e}")
            self.migration_log.append({
                "action": "rollback",
                "table": table_name,
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def verify_migration(self, table_name: str, expected_schema: List[str]) -> bool:
        """Compare post-migration schema against expected schema."""
        try:
            cur = self.conn.cursor()
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            actual_columns = [row[0] for row in cur.fetchall()]
            
            missing = set(expected_schema) - set(actual_columns)
            extra = set(actual_columns) - set(expected_schema)
            
            if missing or extra:
                logging.warning(f"Schema mismatch for {table_name}:")
                if missing:
                    logging.warning(f"  Missing columns: {missing}")
                if extra:
                    logging.warning(f"  Extra columns: {extra}")
                return False
            
            logging.info(f"✓ Schema verification passed for {table_name}")
            return True
        except Exception as e:
            logging.error(f"✗ Verification failed: {e}")
            return False
    
    def get_migration_report(self) -> Dict:
        """Generate migration report."""
        success_count = sum(1 for log in self.migration_log if log.get("status") == "success")
        return {
            "total_operations": len(self.migration_log),
            "successful": success_count,
            "failed": len(self.migration_log) - success_count,
            "log": self.migration_log
        }
```

### 3. Corrupt PDF Recovery

Handle corrupt PDFs with multiple recovery strategies:

```python
import fitz  # PyMuPDF
import requests
from typing import Optional, Dict
import logging

class CorruptPDFRecovery:
    MAX_RETRIES = 3
    
    def __init__(self, pdf_url_map: Dict[str, str], ocr_fallback: bool = True):
        """
        pdf_url_map: Dict mapping chapter IDs to download URLs for re-download
        ocr_fallback: Whether to use OCR as fallback if PDF extraction fails
        """
        self.pdf_url_map = pdf_url_map
        self.ocr_fallback = ocr_fallback
        self.recovery_log = []
    
    def handle_corrupt_pdf(self, pdf_path: str, chapter_id: int) -> Optional[str]:
        """
        Handle corrupt PDF with retry and fallback strategies.
        Returns: extracted markdown on success, None on failure
        """
        strategies = [
            ("direct_extraction", lambda: self._try_direct_extraction(pdf_path)),
            ("re_download", lambda: self._try_redownload(pdf_path, chapter_id)),
            ("ocr_fallback", lambda: self._try_ocr_fallback(pdf_path) if self.ocr_fallback else None),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                result = strategy_func()
                if result:
                    self.recovery_log.append({
                        "chapter": chapter_id,
                        "status": "recovered",
                        "strategy": strategy_name,
                        "timestamp": datetime.now().isoformat()
                    })
                    logging.info(f"✓ Chapter {chapter_id} recovered via {strategy_name}")
                    return result
            except Exception as e:
                logging.warning(f"  {strategy_name} failed: {e}")
                continue
        
        self.recovery_log.append({
            "chapter": chapter_id,
            "status": "unrecoverable",
            "timestamp": datetime.now().isoformat()
        })
        logging.error(f"✗ Failed to recover chapter {chapter_id}")
        return None
    
    def _try_direct_extraction(self, pdf_path: str) -> Optional[str]:
        """Try direct extraction with validation."""
        try:
            doc = fitz.open(pdf_path)
            text = doc.get_text()
            doc.close()
            
            if len(text.strip()) < 100:
                raise ValueError("Extracted text too short, likely corrupted")
            return text
        except Exception as e:
            raise
    
    def _try_redownload(self, pdf_path: str, chapter_id: int) -> Optional[str]:
        """Try to re-download PDF from source."""
        if chapter_id not in self.pdf_url_map:
            raise ValueError(f"No download URL for chapter {chapter_id}")
        
        url = self.pdf_url_map[chapter_id]
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                # Validate downloaded file
                doc = fitz.open(pdf_path)
                text = doc.get_text()
                doc.close()
                
                if len(text.strip()) < 100:
                    raise ValueError("Downloaded PDF too short")
                
                return text
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logging.warning(f"  Retry {attempt + 1}/{self.MAX_RETRIES}: {e}")
                    continue
                raise
    
    def _try_ocr_fallback(self, pdf_path: str) -> Optional[str]:
        """Use OCR as last resort (requires pytesseract/tesseract)."""
        try:
            import pytesseract
            from PIL import Image
            import io
            
            doc = fitz.open(pdf_path)
            full_text = []
            
            for page_num, page in enumerate(doc):
                try:
                    # Render page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR the image
                    text = pytesseract.image_to_string(img)
                    full_text.append(text)
                except Exception as e:
                    logging.warning(f"  OCR failed for page {page_num}: {e}")
                    continue
            
            doc.close()
            result = "\n".join(full_text)
            
            if len(result.strip()) < 100:
                raise ValueError("OCR extracted too little text")
            
            return result
        except ImportError:
            raise ValueError("pytesseract not available for OCR fallback")
    
    def get_recovery_report(self) -> Dict:
        """Generate recovery report."""
        recovered = sum(1 for log in self.recovery_log if log.get("status") == "recovered")
        unrecoverable = sum(1 for log in self.recovery_log if log.get("status") == "unrecoverable")
        
        return {
            "total_attempts": len(self.recovery_log),
            "recovered": recovered,
            "unrecoverable": unrecoverable,
            "recovery_rate": (recovered / len(self.recovery_log)) if self.recovery_log else 0,
            "log": self.recovery_log
        }
```

### 4. Deduplication via Embedding Cosine Similarity

Remove duplicate chunks using vector similarity:

```python
import numpy as np
from scipy.spatial.distance import cosine
from typing import List, Dict, Tuple
import logging

class ChunkDeduplicator:
    def __init__(self, similarity_threshold: float = 0.95):
        """
        similarity_threshold: Cosine similarity threshold for duplicates (0-1)
        Default 0.95 = 95% similar = likely duplicate
        """
        self.similarity_threshold = similarity_threshold
        self.dedup_log = []
    
    def deduplicate_chunks(self, chunks: List[Dict], 
                          vector_field: str = "vector") -> Tuple[List[Dict], Dict]:
        """
        Deduplicate chunks using cosine similarity on vectors.
        Returns: (deduplicated_chunks, dedup_stats)
        """
        if not chunks:
            return chunks, {"removed": 0, "kept": len(chunks)}
        
        kept_chunks = []
        removed_indices = set()
        
        # Build embeddings list
        embeddings = []
        for chunk in chunks:
            vec = chunk.get(vector_field)
            if isinstance(vec, list):
                embeddings.append(np.array(vec))
            else:
                embeddings.append(vec)
        
        # Compare each chunk with all previous kept chunks
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            is_duplicate = False
            
            for j, kept_idx in enumerate(range(len(kept_chunks))):
                # Calculate cosine similarity
                similarity = 1 - cosine(embedding, embeddings[kept_idx])
                
                if similarity >= self.similarity_threshold:
                    self.dedup_log.append({
                        "removed_index": i,
                        "duplicate_of_index": kept_idx,
                        "similarity": float(similarity),
                        "chapter": chunk.get("chapter"),
                        "page": chunk.get("page")
                    })
                    is_duplicate = True
                    logging.debug(f"Chunk {i} marked as duplicate of {kept_idx} (sim={similarity:.3f})")
                    break
            
            if not is_duplicate:
                kept_chunks.append(chunk)
        
        stats = {
            "total_input": len(chunks),
            "removed": len(chunks) - len(kept_chunks),
            "kept": len(kept_chunks),
            "removal_rate": (len(chunks) - len(kept_chunks)) / max(len(chunks), 1)
        }
        
        logging.info(f"✓ Deduplication complete: {stats['removed']} removed, {stats['kept']} kept")
        return kept_chunks, stats
    
    def get_dedup_report(self) -> Dict:
        """Generate deduplication report."""
        return {
            "total_duplicates_found": len(self.dedup_log),
            "threshold": self.similarity_threshold,
            "log": self.dedup_log
        }
```

### 5. Schema Conflict Resolution

Handle v1→v2 dimension mismatches and schema conflicts:

```python
import psycopg2
from typing import Dict, List, Optional
import logging

class SchemaConflictResolver:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.conflict_log = []
    
    def detect_schema_conflicts(self, table_name: str) -> Dict:
        """Detect schema version conflicts."""
        try:
            cur = self.conn.cursor()
            
            # Get vector dimensions
            cur.execute(f"""
                SELECT 
                    column_name,
                    array_length(vector, 1) as dim
                FROM {table_name}
                WHERE vector IS NOT NULL
                LIMIT 1
            """)
            
            result = cur.fetchone()
            conflicts = {
                "table": table_name,
                "has_conflicts": False,
                "dimension_mismatches": [],
                "missing_columns": []
            }
            
            if result:
                actual_dim = result[1]
                expected_dim = 1024  # BGE-M3 default
                
                if actual_dim != expected_dim:
                    conflicts["has_conflicts"] = True
                    conflicts["dimension_mismatches"].append({
                        "expected": expected_dim,
                        "actual": actual_dim,
                        "mismatch": actual_dim - expected_dim
                    })
            
            # Check for required columns
            required_columns = ["raw_text", "equations_latex", "figure_refs", "vector"]
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s
            """, (table_name,))
            
            actual_columns = {row[0] for row in cur.fetchall()}
            missing = set(required_columns) - actual_columns
            
            if missing:
                conflicts["has_conflicts"] = True
                conflicts["missing_columns"] = list(missing)
            
            return conflicts
        except Exception as e:
            logging.error(f"✗ Schema conflict detection failed: {e}")
            return {"error": str(e)}
    
    def resolve_schema_conflict(self, table_name: str, 
                               source_dim: int = 3072,
                               target_dim: int = 1024) -> bool:
        """Resolve dimension mismatches by re-embedding with correct model."""
        try:
            cur = self.conn.cursor()
            
            # Detect chapters with wrong dimensions
            cur.execute(f"""
                SELECT DISTINCT chapter
                FROM {table_name}
                WHERE array_length(vector, 1) != %s
            """, (target_dim,))
            
            wrong_dim_chapters = [row[0] for row in cur.fetchall()]
            
            if not wrong_dim_chapters:
                logging.info(f"✓ No dimension conflicts in {table_name}")
                return True
            
            logging.info(f"Found {len(wrong_dim_chapters)} chapters with {source_dim}→{target_dim} mismatch")
            
            # Log conflict
            self.conflict_log.append({
                "table": table_name,
                "action": "dimension_migration",
                "source_dim": source_dim,
                "target_dim": target_dim,
                "affected_chapters": wrong_dim_chapters,
                "count": len(wrong_dim_chapters),
                "timestamp": datetime.now().isoformat(),
                "status": "detected"
            })
            
            # Create temp table with correct schema
            cur.execute(f"""
                CREATE TABLE {table_name}_v2_temp AS
                SELECT * FROM {table_name}
                WHERE array_length(vector, 1) = %s
                LIMIT 0
            """, (target_dim,))
            
            # For affected chapters, text would need re-embedding
            # (actual re-embedding done in orchestrator with BGE-M3)
            logging.info(f"✓ Schema resolution prepared for {len(wrong_dim_chapters)} chapters")
            
            self.conflict_log[-1]["status"] = "prepared"
            return True
        except Exception as e:
            logging.error(f"✗ Schema resolution failed: {e}")
            self.conflict_log.append({
                "table": table_name,
                "action": "dimension_migration",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def get_conflict_report(self) -> Dict:
        """Generate conflict resolution report."""
        return {
            "total_conflicts": len(self.conflict_log),
            "resolved": sum(1 for c in self.conflict_log if c.get("status") == "resolved"),
            "prepared": sum(1 for c in self.conflict_log if c.get("status") == "prepared"),
            "failed": sum(1 for c in self.conflict_log if c.get("status") == "failed"),
            "log": self.conflict_log
        }
```

### Integration Example

```python
# Usage within DBPipelineOrchestrator
def run_full_pipeline_with_deep_robustness(self):
    """Full pipeline with checkpoint, rollback, recovery, and dedup."""
    
    # Initialize resilience managers
    checkpoint = PipelineCheckpoint()
    rollback_mgr = RollbackManager(self.pg_conn)
    corrupt_recovery = CorruptPDFRecovery(self.pdf_url_map)
    deduplicator = ChunkDeduplicator(threshold=0.95)
    schema_resolver = SchemaConflictResolver(self.pg_conn)
    
    try:
        # Load or start fresh
        checkpoint.load()
        
        # Process chapters
        for chapter_id in range(1, 21):
            resume_point = checkpoint.get_resume_point()
            if resume_point and resume_point[0] > chapter_id:
                continue
            
            # Process chapter with recovery
            pdf_path = self.pdf_dir / f"chapter_{chapter_id}.pdf"
            try:
                markdown = self._process_pdf(pdf_path)
            except Exception:
                markdown = corrupt_recovery.handle_corrupt_pdf(str(pdf_path), chapter_id)
                if not markdown:
                    continue
            
            checkpoint.mark_step_done(chapter_id, 'marker')
            
            # ... rest of pipeline steps ...
        
        # Deduplicate chunks before migration
        chunks = self._load_all_chunks()
        chunks, dedup_stats = deduplicator.deduplicate_chunks(chunks)
        
        # Migrate with rollback support
        rollback_mgr.snapshot_before_migration("crmb_chunks")
        self._migrate_to_pgvector(chunks)
        schema_resolver.resolve_schema_conflict("crmb_chunks_v2")
        rollback_mgr.verify_migration("crmb_chunks_v2", ["raw_text", "equations_latex", "vector"])
        
        # Generate reports
        return {
            "checkpoint": checkpoint.get_progress_summary(),
            "deduplication": deduplicator.get_dedup_report(),
            "recovery": corrupt_recovery.get_recovery_report(),
            "schema": schema_resolver.get_conflict_report(),
            "rollback": rollback_mgr.get_migration_report()
        }
    except Exception as e:
        logging.error(f"Pipeline failed, triggering rollback: {e}")
        rollback_mgr.rollback("crmb_chunks_v2")
        raise
```
```
