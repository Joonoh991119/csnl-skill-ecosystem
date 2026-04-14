# EVAL: db-pipeline Skill Assessment
## Prompt 1: Complete CRMB_tutor Migration (Audit → Marker → Nougat → pgvector → BGE-M3 → Eval)

**Evaluation Date:** 2026-04-14  
**Evaluator Focus:** Real-world end-to-end complex vector DB migration with 7-step pipeline

---

## 1. Sufficiency of Guidance

### Sections That Help (✓ Strengths)

#### 1.1 Section 1: Current State Assessment
- **Directly addresses** "audit the current DB state" requirement
- Provides `audit_lancedb()` function that checks:
  - Chunk count, vector dimensions (detects the 3072-dim bug)
  - Column schema
  - Content types (summaries-only detection)
- **Concrete output:** Shows expected audit results (150 chunks, 3072-dim, no raw_text/equations)
- **Immediately actionable:** Copy-paste ready code

#### 1.2 Section 2: Marker Pipeline
- **Fully addresses** "run Marker on all 20 CRMB chapter PDFs"
- Two functions provided:
  - `run_marker_single()` - CLI wrapper with timeout handling
  - `run_marker_batch()` - Orchestrates all 20 chapters with progress display
- **Integration guidance:** Shows how to replace PDF parsing in `chunker_v2.py` with Marker output
- **Practical detail:** Includes section hierarchy preservation (headings → chunks)
- **Clear expected outcome:** "✓ Marker batch: X/20 successful"

#### 1.3 Section 3: Nougat Fallback
- **Addresses** "use Nougat for equation-heavy pages"
- Provides equation detection heuristics (`detect_equation_pages()`)
- Shows Docker launch for Nougat service
- Demonstrates merge strategy: inject Nougat LaTeX back into Marker markdown
- **Well-scoped:** Only handles pages with >10 equation indicators

#### 1.4 Section 4: Figure Extraction
- **Completely covers** "extract figures with PyMuPDF"
- `extract_figures()` provides:
  - Image extraction with `.get_images()`
  - Caption detection (heuristic: text below image bbox)
  - Metadata JSON export
  - `batch_extract_figures()` for all 20 chapters
- **Output structure:** `figures_dir/fig_PAGE_INDEX.png` + `metadata.json`

#### 1.5 Section 5: pgvector Schema Migration
- **Directly supports** "migrate to pgvector with correct 1024-dim BGE-M3 embeddings"
- Addresses **schema versioning** (migration tracking table)
- Provides v1→v2 schema definition with new columns:
  - `raw_text` (full Marker text)
  - `equations_latex` (Nougat/Marker equations)
  - `figure_refs` (array of figure paths)
  - `section_path` (hierarchy info)
- **Rollback support:** `rollback_to_v1()` for quality issues
- **Critical dimension fix noted:** "BGE-M3 correct dimension is 1024, not 3072"
- Creates HNSW index for efficient similarity search

#### 1.6 Section 6: Re-Embedding Pipeline
- **Core task:** "re-embed everything with correct 1024-dim BGE-M3"
- `BGEMembedder` class with:
  - Apple Silicon MPS device optimization (relevant for MacBook dev)
  - Batch embedding with progress tracking
  - **Multi-modal:** dense + sparse + ColBERT embeddings
  - Assertion: `assert dense.shape[1] == 1024` (dimension validation)
- Per-chapter update loop with batch commit
- **Verification:** Confirms 1024-dim after embedding

#### 1.7 Section 7: Eval Automation
- **Addresses** "verify quality improved with before/after eval"
- `EvalComparison` class:
  - Pre-migration snapshot capture
  - Post-migration bootstrap query evaluation (50 test queries)
  - Metrics: NDCG@10, MRR@5, Recall@20
  - **Auto-rollback:** If NDCG drops >10%, automatically rolls back to v1
- Query examples provided (summaries, equations, figures, sections)
- Clear pass/fail threshold logic

#### 1.8 Section 8: Orchestrator
- **Ties all pieces together** in `DBPipelineOrchestrator`
- Runs all 7 steps in sequence
- Comprehensive logging (JSON pipeline log with timestamps)
- Error handling and automatic state recovery
- Can run end-to-end from single config dict

#### 1.9 Quick Start
- Shell command sequence for dependency installation
- Docker launch for Nougat service
- Python invocation example with config

---

## 2. Scoring: Relevance, Completeness, Actionability

### Relevance: 5/5
The skill maps **exactly** to the eval prompt's 7 tasks:
1. ✓ Audit current DB state → Section 1
2. ✓ Run Marker on 20 PDFs → Section 2
3. ✓ Nougat for equations → Section 3
4. ✓ Extract figures with PyMuPDF → Section 4
5. ✓ Migrate to pgvector (1024-dim) → Section 5
6. ✓ Re-embed with BGE-M3 → Section 6
7. ✓ Verify quality (before/after) → Section 7

Zero scope creep; laser-focused on CRMB_tutor transformation.

### Completeness: 4.5/5

**Comprehensive coverage of:**
- All 7 pipeline stages with working code
- Schema versioning and rollback strategy
- Multi-modal embeddings (dense, sparse, ColBERT)
- Error handling (timeouts, service failures, dimension validation)
- Logging and reproducibility
- Configuration management

**Minor gaps (0.5 point deduction):**
- No explicit handling of "chapter PDFs naming convention" — assumes `chapter_*.pdf` or alphabetical sort, but doesn't validate files exist first
- Eval metrics (NDCG, MRR, Recall) use simplified "keyword in text" relevance instead of reference dataset ground truth; suitable for bootstrap eval but not production-grade
- Figure caption extraction uses simple heuristic (text within 50px below image); won't work for figure numbers far from images
- No explicit handling of multi-column layouts or horizontal text in PDFs (Marker assumption)

### Actionability: 4.5/5

**High actionability:**
- Every function is production-ready with type hints
- Copy-paste code blocks have clear entry points
- Config dict clearly specifies all paths needed
- Docker command provided for Nougat
- Quick Start section gets user to working state in ~5 steps

**Minor friction points (0.5 point deduction):**
- Assumes PostgreSQL/pgvector already installed and accessible (no connection validation)
- Assumes Marker CLI already installed (`marker_single` command); user must `pip install markers`
- Assumes LanceDB DB already exists at specified path; audit function will fail if missing
- Figure extraction assumes PyMuPDF (`fitz`) is available but not explicitly listed in pip install
- Nougat endpoint (`http://localhost:8503`) hardcoded in function; requires Docker service running or code modification
- Re-embedding requires 20+ GB VRAM for BGE-M3 model; no guidance on OOM fallback strategies beyond batch size reduction

---

## 3. Gaps and Concrete Improvement Recommendations

### Gap 1: Pre-flight Validation (HIGH PRIORITY)

**Current state:** Orchestrator assumes all resources exist and are accessible.  
**Risk:** User runs pipeline for 2 hours, fails at step 5 due to missing PostgreSQL.

**Recommendation:**
```python
def validate_prerequisites(config: Dict) -> Dict:
    """Check all dependencies before pipeline starts."""
    issues = []
    
    # Check Marker installation
    try:
        subprocess.run(["marker_single", "--help"], capture_output=True, timeout=5)
    except FileNotFoundError:
        issues.append("✗ marker_single CLI not found. Install: pip install markers")
    
    # Check Nougat service
    try:
        requests.get(f"{config['nougat_url']}/health", timeout=3)
    except Exception as e:
        issues.append(f"✗ Nougat service not responding at {config['nougat_url']}: {e}")
    
    # Check PostgreSQL connectivity
    try:
        psycopg2.connect(config["pgvector_url"])
    except Exception as e:
        issues.append(f"✗ PostgreSQL connection failed: {e}")
    
    # Check LanceDB exists
    try:
        lancedb.connect(config["lancedb_path"]).open_table("crmb_chunks")
    except Exception as e:
        issues.append(f"✗ LanceDB source not accessible: {e}")
    
    # Check PDF directory
    pdf_count = len(list(Path(config["pdf_dir"]).glob("*.pdf")))
    if pdf_count == 0:
        issues.append(f"✗ No PDFs found in {config['pdf_dir']}")
    
    if issues:
        print("\n⚠ PRE-FLIGHT CHECKS FAILED:\n" + "\n".join(issues))
        return {"passed": False, "issues": issues}
    
    return {"passed": True, "pdf_count": pdf_count}
```

**Add to orchestrator.run_full_pipeline() beginning:**
```python
check = validate_prerequisites(self.config)
if not check["passed"]:
    raise RuntimeError("Pre-flight checks failed. See above.")
```

**Impact:** Saves hours of debugging by failing fast with actionable error messages.

---

### Gap 2: Graceful Handling of Partial Failures (HIGH PRIORITY)

**Current state:** If Marker fails on chapter 15/20, entire batch aborts. User must manually resume.

**Recommendation:**
Add checkpoint resumption to orchestrator:

```python
def should_skip_step(self, step_name: str) -> bool:
    """Check if step already completed in log."""
    return (step_name in self.pipeline_log["steps"] and 
            self.pipeline_log["steps"][step_name]["status"] == "completed")

def run_full_pipeline(self, resume: bool = True):
    """Execute pipeline with resumption support."""
    steps = ["audit", "marker", "equations", "figures", "migration", 
             "reembedding", "eval"]
    
    for step_name in steps:
        if resume and self.should_skip_step(step_name):
            logging.info(f"[{step_name}] Already completed (resuming)...")
            continue
        
        # Run step...
```

**For Marker specifically**, track per-chapter success:
```python
def run_marker_batch(pdf_dir: str, output_base: str, 
                     resume: bool = True, 
                     previous_results: List[Dict] = None) -> List[Dict]:
    """Run Marker with per-chapter resumption."""
    # ... existing code ...
    
    for i, pdf in enumerate(chapter_pdfs, 1):
        # Skip if already successful
        if resume and previous_results and any(
            r["pdf"] == str(pdf) and r["status"] == "success" 
            for r in previous_results
        ):
            print(f"  [{i}/{len(chapter_pdfs)}] {pdf.name} (cached)")
            results.append(next(r for r in previous_results if r["pdf"] == str(pdf)))
            continue
        
        # Run Marker...
```

**Impact:** Pipelines become robust to transient failures (network, OOM, service restarts).

---

### Gap 3: Explicit Data Validation at Each Stage (MEDIUM PRIORITY)

**Current state:** No validation that Marker output is actually markdown, Nougat returned LaTeX, etc.

**Recommendation:**

Add validation functions after each major step:

```python
def validate_marker_output(marker_results: List[Dict]) -> bool:
    """Check Marker produced valid markdown."""
    for result in marker_results:
        if result["status"] != "success":
            continue
        
        md_path = result.get("markdown")
        if not md_path or not Path(md_path).exists():
            logging.error(f"✗ Marker markdown missing: {md_path}")
            return False
        
        with open(md_path) as f:
            content = f.read()
            if len(content) < 100:
                logging.warning(f"⚠ Suspiciously short: {md_path}")
            if not any(c in content for c in ["#", "##", "###"]):
                logging.warning(f"⚠ No headings in: {md_path}")
    
    return True

def validate_pgvector_schema(migration) -> bool:
    """Check v2 schema columns exist."""
    with migration.conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'crmb_chunks_v2'
        """)
        cols = {row[0] for row in cur.fetchall()}
        
        required = {"raw_text", "equations_latex", "figure_refs", "section_path", "vector"}
        if not required.issubset(cols):
            missing = required - cols
            logging.error(f"✗ Missing columns: {missing}")
            return False
    
    return True

def validate_embedding_dim(migration, sample_size: int = 10) -> bool:
    """Verify all vectors are 1024-dim."""
    with migration.conn.cursor() as cur:
        cur.execute(f"SELECT vector FROM crmb_chunks_v2 LIMIT {sample_size}")
        
        for row in cur.fetchall():
            if len(row[0]) != 1024:
                logging.error(f"✗ Wrong dim: {len(row[0])}, expected 1024")
                return False
    
    return True
```

Then add to orchestrator:
```python
# After Marker step
if not validate_marker_output(marker_results):
    raise RuntimeError("Marker output validation failed")

# After migration step
if not validate_pgvector_schema(migration):
    raise RuntimeError("Schema validation failed")

# After re-embedding
if not validate_embedding_dim(migration):
    raise RuntimeError("Embedding dimension mismatch")
```

**Impact:** Catches silent data corruption early; provides clear error messages for debugging.

---

### Gap 4: Clearer Handling of PDF-Specific Challenges (MEDIUM PRIORITY)

**Current state:** Code assumes PDFs behave uniformly (they don't).

**Recommendation:**

Add per-PDF configuration:

```python
CHAPTER_OVERRIDES = {
    "chapter_07.pdf": {
        "marker_timeout": 1200,  # Scanned PDF, longer processing
        "use_nougat": True,  # Heavy equations
        "skip_figure_extraction": False,
    },
    "chapter_12.pdf": {
        "skip_marker": False,
        "orientation": "portrait",  # vs. landscape
    },
}

def run_marker_batch(pdf_dir: str, output_base: str) -> List[Dict]:
    """Run Marker with per-PDF config overrides."""
    # ... existing code ...
    
    for i, pdf in enumerate(chapter_pdfs, 1):
        override = CHAPTER_OVERRIDES.get(pdf.name, {})
        timeout = override.get("marker_timeout", 600)
        
        result = run_marker_single(str(pdf), output_base, timeout=timeout)
        results.append(result)
```

Also add guidance in docstring:
```
If Marker times out on chapter X:
  1. Check PDF size: ls -lh chapter_X.pdf
  2. Add to CHAPTER_OVERRIDES with timeout=1200
  3. If still fails: check if scanned PDF (run `pdftotext chapter_X.pdf`)
  4. For scanned PDFs, consider OCR preprocessing
```

**Impact:** Handles real-world PDF heterogeneity gracefully.

---

### Gap 5: Rollback and Comparison Context (MEDIUM PRIORITY)

**Current state:** Auto-rollback is binary (roll back if NDCG < -10%); no detailed comparison.

**Recommendation:**

Enhance eval report to show per-chapter, per-query changes:

```python
def generate_detailed_diff_report(self, threshold: float = 0.10) -> Dict:
    """Detailed before/after breakdown by chapter and query."""
    
    report = self.generate_diff_report(threshold)
    
    # Add per-chapter metrics
    report["by_chapter"] = {}
    with self.migration.conn.cursor() as cur:
        for chapter in range(1, 21):
            cur.execute("""
                SELECT COUNT(*), AVG(similarity) FROM crmb_chunks_v2
                WHERE chapter = %s AND vector IS NOT NULL
            """, (chapter,))
            count, avg_sim = cur.fetchone()
            report["by_chapter"][f"chapter_{chapter:02d}"] = {
                "chunk_count": count,
                "avg_similarity": avg_sim
            }
    
    # Add per-query detail
    report["per_query"] = {}
    for detail in self.after.get("query_details", []):
        report["per_query"][detail["query"]] = {
            "ndcg": detail["ndcg"],
            "before": self.before["query_details"].get(detail["query"], {}).get("ndcg"),
            "improvement": detail["ndcg"] - self.before["query_details"].get(detail["query"], {}).get("ndcg", 0)
        }
    
    return report
```

**Impact:** Operator can see which chapters/queries improved vs. degraded, enabling manual override of auto-rollback.

---

### Gap 6: Explicit Memory/Resource Requirements (LOW PRIORITY)

**Current state:** Re-embedding section mentions "may cause OOM" but no quantification.

**Recommendation:**

Add resource guide to beginning:

```
## Prerequisites & Resource Requirements

### Minimum Hardware
- **RAM:** 32 GB (BGE-M3 model ~4GB, batch processing ~8GB, PG instance ~4GB)
- **Disk:** 100 GB free (/tmp/crmb_processing for Marker outputs, figures, logs)
- **GPU/Accelerator:** Optional but recommended
  - NVIDIA GPU: 12GB VRAM minimum
  - Apple Silicon (MPS): Supported via `device='mps'` in BGEMembedder
- **CPU:** 8+ cores (Marker uses parallel page processing with --workers=4)

### Installation Checklist
```bash
# Dependencies
pip install marker sentence-transformers pymupdf lancedb psycopg2-binary

# PostgreSQL
brew install postgresql  # macOS
sudo apt install postgresql postgresql-contrib  # Ubuntu
createdb crmb

# pgvector extension
psql crmb -c "CREATE EXTENSION IF NOT EXISTS vector"

# Nougat (optional, only if equation-heavy)
docker pull quay.io/nougat/nougat:latest
# Will run as: docker run --gpus all -p 8503:8000 ...
```

### Time Estimates
- Marker (20 chapters): 30-60 min (depends on PDF complexity)
- Nougat (equation pages): 10-20 min
- Figure extraction: 2-5 min
- pgvector migration: 5 min
- BGE-M3 re-embedding (batch=32): 15-30 min
- Eval (50 queries): 5-10 min
- **Total:** 1.5-2.5 hours

If timing is critical, parallelize Marker + figure extraction in separate processes.
```

**Impact:** Users know upfront whether their hardware is suitable; no surprises at step 5.

---

### Gap 7: Migration Rollback Nuance (LOW PRIORITY)

**Current state:** `rollback_to_v1()` drops v2 table; no way to keep v2 for debugging.

**Recommendation:**

```python
def rollback_to_v1(self, keep_v2: bool = True):
    """Rollback with optional archival of v2 for post-mortem."""
    with self.conn.cursor() as cur:
        if keep_v2:
            # Rename instead of drop for forensics
            cur.execute("ALTER TABLE crmb_chunks_v2 RENAME TO crmb_chunks_v2_failed")
            logging.warning("⚠ Kept failed v2 as crmb_chunks_v2_failed for analysis")
        else:
            cur.execute("DROP TABLE IF EXISTS crmb_chunks_v2")
        
        cur.execute("UPDATE schema_versions SET status = 'rolled_back' WHERE version LIKE '%v1_to_v2%'")
        self.conn.commit()
        logging.info("✓ Rolled back to v1")
```

**Impact:** Enables root cause analysis of quality degradation without losing data.

---

## Summary Table

| Dimension | Score | Evidence |
|-----------|-------|----------|
| **Relevance** | 5/5 | Maps 1:1 to all 7 eval tasks; zero extraneous content |
| **Completeness** | 4.5/5 | All core stages present; minor gaps in edge cases (PDF naming, figure captions) |
| **Actionability** | 4.5/5 | Copy-paste ready; missing pre-flight checks and resumption logic |
| **Code Quality** | 4.5/5 | Type hints, docstrings, error handling; no explicit validation |
| **Production Readiness** | 4/5 | Good for 1-off migrations; needs hardening for repeated runs |

---

## Verdict

**This skill adequately guides a user through the complete CRMB_tutor migration.**

### What Works
- Architecture is sound: 7-step linear pipeline with schema versioning
- Code is concrete and testable (not pseudocode)
- Addresses the exact pain points (3072→1024 dim, summaries→raw text, Marker integration)
- Auto-rollback on quality degradation is a strong pattern
- Logging and reproducibility built in

### What Needs Improvement
1. **Pre-flight validation** (HIGH) — Fail fast on missing dependencies
2. **Resumption logic** (HIGH) — Handle partial failures gracefully
3. **Data validation** (MEDIUM) — Verify outputs at each stage
4. **PDF heterogeneity** (MEDIUM) — Per-chapter configuration overrides
5. **Resource requirements** (LOW) — Upfront hardware/time transparency
6. **Rollback nuance** (LOW) — Archive v2 for debugging

### Recommended Use
**✓ DO use this skill when:**
- You have 20 CRMB chapter PDFs in LanceDB
- You want to migrate to pgvector + BGE-M3
- You have infrastructure (PostgreSQL, 32GB RAM)
- You're comfortable debugging Python code

**⚠ DO NOT use this skill when:**
- You need a production SLA (add 2-week hardening per Gap 1-3)
- You're migrating >100 chapters (will need parallel orchestration)
- You're unfamiliar with pgvector/LanceDB (study schema first)

---

## Improvement Priority Roadmap

**If improving this skill in order:**
1. Add `validate_prerequisites()` — protects against hour-long fails
2. Add checkpoint resumption — enables robust operation
3. Add per-stage data validation — catches silent corruption
4. Add resource requirement guide — sets expectations upfront
5. Add PDF override configuration — handles real-world PDF diversity

All can be completed in ~200 lines of code across existing functions.

