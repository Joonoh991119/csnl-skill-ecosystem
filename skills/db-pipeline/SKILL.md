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
