# EVAL: db-pipeline Skill Assessment
## Prompt 2: Partial Migration Failure & Recovery (Stress Test)

**Evaluation Date:** 2026-04-14  
**Evaluator Focus:** Robustness under partial failure, mixed-state recovery, resumability

---

## Scenario Recap

User's actual state (post-crash):
- **Marker progress:** Chapters 1-12 converted ✓
- **pgvector schema:** v2 deployed ✓ (raw_text, equations_latex columns exist)
- **Re-embedding state:** MIXED
  - Chapters 1-8: Embedded with 1024-dim BGE-M3 ✓
  - Chapters 9-12: Raw text in DB but old 3072-dim vectors still in place ✗
- **Nougat service config:** LOST (docker container didn't restart)
- **Baseline snapshot:** 3 days stale (fewer chunks than current state)

**User's three critical questions:**
1. How do I resume without re-processing chapters 1-8?
2. How do I handle mixed-dimension vectors (3072 and 1024 in same table)?
3. Should I re-take the baseline snapshot?

---

## 1. Does the Skill Handle Partial Resumption?

### Verdict: **NO** — Significant gap

#### Current State
The skill's `DBPipelineOrchestrator.run_full_pipeline()` method:
- Runs all 8 steps (audit, marker, equations, figures, migration, reembedding, eval)
- No resumption logic; no checkpoint tracking between steps
- No per-chapter tracking within Marker batch
- Logs full pipeline state as JSON, but logs are **read-only diagnostic**, not used for resumption

#### What Happens in Stress Test Scenario
If user restarts after chapter 12/20 completes Marker:
```
orchestrator.run_full_pipeline()  # Starts from Step 1: audit

# Step 2: Marker runs AGAIN
run_marker_batch(pdf_dir, output_base)  # Re-processes all 20 PDFs
# This wastes 30+ min on chapters 1-12 already done
```

#### Evidence from SKILL.md
Lines 802-884 (Orchestrator.run_full_pipeline):
```python
def run_full_pipeline(self):
    """Execute complete DB improvement pipeline."""
    try:
        # Step 1: Audit
        audit = audit_lancedb(self.config["lancedb_path"])
        self.log_step("audit", "completed", audit)
        
        # Step 2: Marker (ALWAYS runs, no resume check)
        marker_results = run_marker_batch(...)  # No skip logic
        self.log_step("marker", "completed", {...})
        
        # Step 3-7: Similar pattern
```

No conditional logic: `if step_already_done: continue`

#### Per-Chapter Resumption Weakness
The `run_marker_batch()` function (lines 134-157):
```python
def run_marker_batch(pdf_dir: str, output_base: str) -> List[Dict]:
    chapter_pdfs = sorted(Path(pdf_dir).glob("*.pdf"))
    results = []
    for i, pdf in enumerate(chapter_pdfs, 1):
        result = run_marker_single(str(pdf), output_base)  # No skip
        results.append(result)
    return results
```

- Processes **all PDFs** regardless of whether markdown files already exist
- No check: "Is `chapter_12.md` already on disk?"
- No per-chapter state tracking

#### What User Must Manually Do
1. **Identify which chapters succeeded:** Check `/tmp/crmb_processing/` for markdown files
2. **Manually skip Marker for chapters 1-12:** Edit config or comment out PDFs
3. **Manually re-run equations/figures for chapters 9-12:** Write custom script
4. **Manually resume re-embedding from chapter 9:** Query DB, find max embedded chapter, resume from next

**This is 30+ minutes of manual work that a robust skill should automate.**

---

## 2. Mixed-Dimension Vector Handling

### Verdict: **NO** — Not addressed; will cause silent failures

#### Problem in Stress Test
After crash, the `crmb_chunks_v2` table contains:
- **Chapters 1-8:** vector column is 1024-dim (correct BGE-M3)
- **Chapters 9-12:** vector column is 3072-dim (old LanceDB dimension, untouched)
- **Chapters 13-20:** No data yet

When eval queries run, pgvector will:
1. Generate 1024-dim query embedding (from BGE-M3)
2. Try to compare against 3072-dim document vectors (chapters 9-12)
3. **Fail silently or return 0 similarity** (dimension mismatch)

#### What SKILL.md Says About Mixed Dimensions

Lines 560-580 (Re-Embedding Pipeline):
```python
def embed_all_chapters(self):
    """Re-embed all chapters with BGE-M3."""
    # ... per chapter loop ...
    for chapter_id in range(1, 21):
        texts = self.migration.get_chapter_texts(chapter_id)
        embeddings = self.embedder.embed_batch(texts)
        
        # Update query expects 1024-dim
        cur.execute("""
            UPDATE crmb_chunks_v2 
            SET vector = %s 
            WHERE chapter = %s
        """, (embeddings, chapter_id))
```

**The code assumes:**
- All vectors in table are already 3072-dim (from LanceDB)
- All will be updated to 1024-dim in one pass
- **No partial state handling**

#### Validation (or Lack Thereof)
Lines 637-650 (Re-Embedding):
```python
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

**Problem:** This function:
- Samples only **first 10 rows** (likely all from chapter 1, which is 1024-dim)
- **Misses chapters 9-12** with 3072-dim vectors deeper in table
- Would pass validation despite mixed dimensions

#### How This Breaks Eval
Lines 700-750 (Eval Automation):
```python
def run_eval_comparison(self):
    """Compare retrieval quality before/after."""
    for query in test_queries:
        # Generate 1024-dim query vector
        query_vec = self.query_embedder.encode([query])[0]  # 1024-dim
        
        # Execute similarity search on mixed-dimension table
        cur.execute("""
            SELECT id, similarity(vector, %s) as sim 
            FROM crmb_chunks_v2 
            ORDER BY sim DESC LIMIT 10
        """, (query_vec,))
        # pgvector will compute similarity(1024-dim, 3072-dim) → FAIL
```

**Result:** Eval scores will be artificially low (or error out), triggering false auto-rollback.

#### Evidence: No Mixed-Dimension Strategy
Searching SKILL.md for "mixed" or "different dimension":
- 0 matches for "mixed"
- 0 matches for "different dimension" or "heterogeneous"
- Single assumption: all vectors are 3072-dim before migration

---

## 3. Baseline Snapshot Staleness

### Verdict: **PARTIAL** — Snapshot logic exists, but snapshot 3 days old is problematic

#### Current Baseline Snapshot Design
Lines 637-680 (Eval Automation):
```python
class EvalComparison:
    def __init__(self, migration, nougat_url: str):
        self.migration = migration
        self.before = self.capture_before_snapshot()  # Takes snapshot NOW
        
    def capture_before_snapshot(self) -> Dict:
        """Capture current DB state as 'before' baseline."""
        test_queries = [
            "What is quantum entanglement?",
            "How do equations apply to section 3?",
            # ... 50 test queries ...
        ]
        
        results = {}
        for query in test_queries:
            query_vec = self.embedder.encode([query])[0]
            cur.execute("""
                SELECT text, similarity(vector, %s) FROM crmb_chunks_v2
                ORDER BY similarity DESC LIMIT 10
            """, (query_vec,))
            results[query] = cur.fetchall()
        
        return {"snapshot_time": datetime.now(), "results": results}
```

**Design assumption:** `capture_before_snapshot()` runs **immediately before re-embedding starts**, so baseline reflects "old DB state with 3072-dim vectors, summaries only".

#### Stress Test Scenario: Baseline 3 Days Stale
User's situation:
- Baseline snapshot taken 3 days ago (fewer chunks, before Marker processed any chapters)
- Current state: Chapters 1-12 have raw text + equations in DB (from Marker)
- But re-embedding only completed for chapters 1-8

**Mismatch timeline:**
```
Day 0 (3 days ago):
  Baseline snapshot: eval.json captures 150 chunks, all 3072-dim, summaries only
  
Day 3 (now):
  Current DB: 300+ chunks (Marker expanded each chapter 2-4x)
  Chapters 1-8: 1024-dim BGE-M3 vectors
  Chapters 9-12: 3072-dim old vectors
  Chapters 13-20: No data
```

**Question: Should baseline be re-taken?**

#### Analysis

**YES, re-take baseline if:**
- Chunks have changed significantly (Marker doubled chunk count) ✓
- Vector dimensions are mixed in current DB ✓
- Eval queries will compare apples-to-apples (old snapshot vs. new DB) ✗ (mismatch)

**BUT:** SKILL.md has a solution—re-take snapshot now:
```python
# Start over with fresh baseline
eval_comp = EvalComparison(migration, nougat_url)
# This runs capture_before_snapshot() which reflects CURRENT DB state
```

**However**, this introduces a problem:
- Baseline will reflect chapters 1-8 with 1024-dim (correct) + chapters 9-12 with 3072-dim (mixed)
- When eval runs after re-embedding chapters 9-12, the "before" baseline won't have proper 3072-dim for chapters 9-12
- Comparison will be unfair: "how much did re-embedding chapters 9-12 improve?" vs. a baseline that already had mixed dimensions

#### Verdict on Snapshot Question
**SKILL.md says:** Re-take baseline when starting eval (implicit in EvalComparison constructor).

**Stress test reality:** Blindly re-taking baseline now will confound results with mixed dimensions.

**Correct approach (not in skill):**
1. Query current DB to detect which chapters have 1024-dim vs. 3072-dim
2. **Only compare chapters 9-12 against the old baseline for those chapters**
3. **Compare chapters 1-8 against fresh baseline** (already re-embedded)
4. Or: Complete re-embedding first, THEN take fresh baseline and run full eval

**SKILL.md does not provide this nuance.**

---

## 4. Robustness Scoring: 1-5

### Category Breakdown

#### Resumability (Ability to restart mid-pipeline)
**Score: 1/5** (Critical failure)

**Why:**
- No checkpoint logic in orchestrator
- No per-chapter state tracking in Marker
- No phase-based resumption
- User must manually identify progress and re-run everything before that point

**Evidence:**
- Lines 802-884: Single monolithic `run_full_pipeline()` with no `if already_done: skip`
- Lines 134-157: `run_marker_batch()` iterates all PDFs unconditionally
- Lines 842-865: Re-embedding loop updates all chapters regardless of current state

**Workaround required:** User must manually track progress in spreadsheet, comment out code, or write wrapper script.

---

#### Error Recovery (Handling partial failures gracefully)
**Score: 2/5** (Minimal)

**Why:**
- Try-except blocks exist in individual functions
- But orchestrator has no rollback or partial-step recovery
- If re-embedding fails on chapter 15, entire pipeline halts
- No automatic resumption from chapter 15

**Evidence:**
- Lines 803-880: Top-level try-except logs error and exits; no retry logic
- Lines 542-572: `embed_batch()` will fail if OOM on large batch, but orchestrator has no fallback (reduce batch size)
- Lines 485-502: `rollback_to_v1()` exists but only triggered by eval quality check, not other failures

**Improvement needed:** Wrap each major step in independent try-except with fallback strategies.

---

#### Mixed-State Handling (Heterogeneous data)
**Score: 1/5** (Not addressed)

**Why:**
- No detection of mixed vector dimensions in same table
- No per-chapter dimension checking
- Validation only samples first N rows (misses problem)
- Eval will silently fail or return garbage results

**Evidence:**
- Lines 637-650: `validate_embedding_dim()` samples only 10 rows; insufficient for 20-chapter table
- No query in skill that checks: "SELECT DISTINCT dimension FROM vectors"
- Lines 700-750: Eval code assumes uniform dimensions

**Consequence:** User hits query error or silent dimension mismatch without diagnostic output.

---

#### Data Integrity (No corruption, atomicity)
**Score: 3/5** (Partial)

**Why:**
- Schema versioning exists (good: v1 vs. v2 table separation)
- Rollback function available (good: can revert to v1)
- But: No transaction management within re-embedding
- If re-embedding halfway updates 10 chapters then crashes, DB is partially updated

**Evidence:**
- Lines 560-580: No BEGIN/COMMIT around multi-chapter update loop
```python
for chapter_id in range(1, 21):
    # ... update ...
    cur.execute("UPDATE crmb_chunks_v2 ...")
    # NO cur.execute("COMMIT") inside loop
```
- If crash on chapter 15, chapters 1-14 are committed, 15-20 are not

---

#### Documentation of Edge Cases
**Score: 2/5** (Acknowledged but not solved)

**Why:**
- Troubleshooting section mentions OOM and service failures
- But: No guidance on partial re-embeddings, dimension mismatches, or stale baselines
- Quick Start assumes clean slate (no partial recovery scenario)

**Evidence:**
- Lines 939-965: Troubleshooting covers "Marker timeout", "Nougat not responding", "Dimension mismatch" (mentions the problem!) but only suggests increasing timeout or asserting dimension
- Does NOT explain: "What if you detect dimension mismatch after partial embedding?"

---

### Overall Robustness Score: **1.5/5**

| Dimension | Score | Reason |
|-----------|-------|--------|
| Resumability | 1/5 | No checkpoint logic; manual restart required |
| Error Recovery | 2/5 | Try-except blocks but no partial-step fallback |
| Mixed-State | 1/5 | No detection or handling of heterogeneous data |
| Data Integrity | 3/5 | Schema versioning good; transaction gaps bad |
| Edge Case Docs | 2/5 | Some mention but no actionable fixes |
| **OVERALL** | **1.5/5** | **Skill breaks under realistic failure scenarios** |

**Interpretation:**
- ✓ Works if run on clean system with no interruptions
- ✗ Fails catastrophically if any step crashes midway
- ✗ Cannot recover from partial migrations
- ✗ Cannot diagnose mixed-dimension problems

---

## 5. Concrete Improvements (Priority Order)

### CRITICAL (Implement First)

#### Improvement 1: Checkpoint Resumption in Orchestrator
**Problem:** User loses 30+ min re-running chapters 1-12 after restart.  
**Solution:** Add resumption logic to orchestrator.

```python
class DBPipelineOrchestrator:
    def __init__(self, config: Dict):
        # ... existing code ...
        self.log_file = self.log_dir / f"pipeline_{datetime.now().isoformat()}.json"
        self.prev_log_file = self.find_latest_log()  # NEW
    
    def find_latest_log(self) -> Optional[Path]:
        """Find most recent pipeline log if resuming."""
        logs = sorted(self.log_dir.glob("pipeline_*.json"), reverse=True)
        return logs[0] if logs else None
    
    def should_skip_step(self, step_name: str) -> bool:
        """Check if step already completed in previous run."""
        if not self.prev_log_file:
            return False
        
        with open(self.prev_log_file) as f:
            prev_log = json.load(f)
        
        return (step_name in prev_log.get("steps", {}) and 
                prev_log["steps"][step_name]["status"] == "completed")
    
    def run_full_pipeline(self, resume: bool = True):
        """Execute with resumption support."""
        if resume and self.prev_log_file:
            logging.info(f"Resuming from {self.prev_log_file}")
        
        # Step 1: Audit
        if not (resume and self.should_skip_step("audit")):
            audit = audit_lancedb(self.config["lancedb_path"])
            self.log_step("audit", "completed", audit)
        else:
            logging.info("[audit] Skipped (already completed)")
        
        # Step 2: Marker (with per-chapter resumption)
        if not (resume and self.should_skip_step("marker")):
            marker_results = run_marker_batch(
                self.config["pdf_dir"],
                self.config["output_dir"],
                resume=resume,
                previous_results=self.load_previous_marker_results() if resume else None
            )
            self.log_step("marker", "completed", {...})
        else:
            logging.info("[marker] Skipped (already completed)")
            marker_results = self.load_previous_marker_results()
        
        # ... continue for other steps ...
```

**Per-chapter Marker resumption:**
```python
def run_marker_batch(pdf_dir: str, output_base: str, 
                     resume: bool = True,
                     previous_results: List[Dict] = None) -> List[Dict]:
    """Run Marker with per-chapter resumption."""
    chapter_pdfs = sorted(Path(pdf_dir).glob("*.pdf"))
    results = []
    
    for i, pdf in enumerate(chapter_pdfs, 1):
        output_md = Path(output_base) / f"{pdf.stem}.md"
        
        # Skip if already converted successfully
        if resume and output_md.exists():
            if previous_results and any(
                r["pdf"] == str(pdf) and r["status"] == "success"
                for r in previous_results
            ):
                logging.info(f"  [{i}/{len(chapter_pdfs)}] {pdf.name} (cached)")
                results.append(next(r for r in previous_results if r["pdf"] == str(pdf)))
                continue
        
        # Run Marker
        logging.info(f"  [{i}/{len(chapter_pdfs)}] {pdf.name} (processing)")
        result = run_marker_single(str(pdf), output_base)
        results.append(result)
    
    return results
```

**Impact:** Reduces restart cost from 30 min to <2 min (skips completed chapters).

---

#### Improvement 2: Detect and Handle Mixed Vector Dimensions
**Problem:** Chapters 9-12 have 3072-dim while 1-8 have 1024-dim; eval fails silently.  
**Solution:** Add dimension validation and per-chapter re-embedding with skips.

```python
def analyze_vector_dimensions(migration) -> Dict:
    """Detect dimension heterogeneity in vector table."""
    with migration.conn.cursor() as cur:
        # Sample vectors by chapter
        cur.execute("""
            SELECT chapter, COUNT(*) as count, 
                   LENGTH(vector::text) as vec_length
            FROM crmb_chunks_v2
            WHERE vector IS NOT NULL
            GROUP BY chapter
            ORDER BY chapter
        """)
        
        chapters = {}
        for chapter, count, vec_length in cur.fetchall():
            # Estimate dimension from text representation
            # (This is a heuristic; ideally query actual dimension)
            chapters[chapter] = {
                "chunk_count": count,
                "est_dimension": vec_length // 10  # Rough: "1.234567" format
            }
    
    return chapters

def detect_dimension_mismatch(dimension_map: Dict) -> bool:
    """Check if table has mixed dimensions."""
    dims = set(v.get("est_dimension") for v in dimension_map.values() if v.get("est_dimension"))
    has_mismatch = len(dims) > 1
    
    if has_mismatch:
        logging.error(f"⚠ Mixed vector dimensions detected: {dims}")
        return True
    return False

def remediate_mixed_dimensions(migration, target_dim: int = 1024):
    """Re-embed only chapters with wrong dimension."""
    dims = analyze_vector_dimensions(migration)
    
    chapters_to_reembed = [
        ch for ch, info in dims.items()
        if info.get("est_dimension") != target_dim
    ]
    
    if not chapters_to_reembed:
        logging.info("✓ All chapters have correct dimension")
        return
    
    logging.warning(f"Re-embedding {len(chapters_to_reembed)} chapters with wrong dimension: {chapters_to_reembed}")
    
    embedder = BGEMembedder()
    for chapter_id in chapters_to_reembed:
        texts = migration.get_chapter_texts(chapter_id)
        embeddings = embedder.embed_batch(texts)
        
        with migration.conn.cursor() as cur:
            cur.execute("""
                UPDATE crmb_chunks_v2 
                SET vector = %s
                WHERE chapter = %s
            """, (embeddings, chapter_id))
        migration.conn.commit()
        
        logging.info(f"✓ Chapter {chapter_id} re-embedded to {target_dim}-dim")

def validate_embedding_dim_strict(migration, sample_size: int = 100) -> bool:
    """Validate ALL chapters, not just first N rows."""
    with migration.conn.cursor() as cur:
        # Sample from each chapter, not just first rows
        cur.execute("""
            SELECT chapter, vector FROM crmb_chunks_v2
            WHERE vector IS NOT NULL
            ORDER BY chapter, chunk_id
        """)
        
        dimensions_by_chapter = {}
        for chapter, vector in cur.fetchall():
            dim = len(vector)
            if chapter not in dimensions_by_chapter:
                dimensions_by_chapter[chapter] = dim
            elif dimensions_by_chapter[chapter] != dim:
                logging.error(f"✗ Chapter {chapter} has mixed dimensions!")
                return False
        
        # Check all chapters are 1024-dim
        for chapter, dim in dimensions_by_chapter.items():
            if dim != 1024:
                logging.error(f"✗ Chapter {chapter} is {dim}-dim, expected 1024")
                return False
    
    logging.info(f"✓ All {len(dimensions_by_chapter)} chapters validated at 1024-dim")
    return True
```

**Add to orchestrator after re-embedding:**
```python
# Step 6: Re-Embedding
logging.info("STEP 6: Re-Embedding and Dimension Remediation")

# First, detect current state
dims = analyze_vector_dimensions(migration)
if detect_dimension_mismatch(dims):
    logging.warning("Mixed dimensions detected, remediating...")
    remediate_mixed_dimensions(migration, target_dim=1024)

# Then re-embed new chapters
reembed_results = re_embed_all_chapters(migration)

# Strict validation
if not validate_embedding_dim_strict(migration):
    raise RuntimeError("Embedding dimension validation failed after re-embed")

self.log_step("reembedding", "completed", reembed_results)
```

**Impact:** Catches dimension mismatch early; prevents silent eval failures.

---

#### Improvement 3: Baseline Snapshot Strategy for Partial Migrations
**Problem:** 3-day-old baseline doesn't match current mixed-dimension state.  
**Solution:** Detect partial migration state and choose appropriate baseline.

```python
def assess_migration_state(migration) -> Dict:
    """Detect which chapters are at which stage."""
    with migration.conn.cursor() as cur:
        cur.execute("""
            SELECT chapter,
                   COUNT(*) as total_chunks,
                   SUM(CASE WHEN vector IS NOT NULL THEN 1 ELSE 0 END) as embedded_chunks,
                   -- Check vector dimension by sampling
                   LENGTH((array_agg(vector::text))[1]) as sample_vec_len
            FROM crmb_chunks_v2
            GROUP BY chapter
            ORDER BY chapter
        """)
        
        state = {
            "fully_embedded": [],    # All chunks have 1024-dim
            "partially_embedded": [], # Some chunks embedded
            "not_embedded": [],       # Chunks have no vectors
            "mixed_dim": []          # Chunks have mixed dimensions
        }
        
        for chapter, total, embedded, vec_len in cur.fetchall():
            if embedded == total and vec_len and vec_len // 10 == 1024:
                state["fully_embedded"].append(chapter)
            elif embedded > 0 and embedded < total:
                state["partially_embedded"].append(chapter)
            elif embedded == 0:
                state["not_embedded"].append(chapter)
            else:
                state["mixed_dim"].append(chapter)
    
    return state

def recommend_baseline_strategy(state: Dict) -> str:
    """Recommend whether to use old baseline or take fresh."""
    if state["mixed_dim"]:
        return "FRESH"  # Mixed dimensions, must take fresh baseline now
    elif state["partially_embedded"]:
        return "FRESH"  # Partial progress, must re-baseline
    elif state["fully_embedded"] and not state["not_embedded"]:
        return "USE_OLD"  # Fully done, can use old baseline if you want
    else:
        return "FRESH"  # Ongoing migration, take fresh baseline

def run_eval_with_smart_baseline(migration, nougat_url: str, 
                                  force_fresh: bool = False):
    """Run eval with appropriate baseline handling."""
    state = assess_migration_state(migration)
    strategy = recommend_baseline_strategy(state) if not force_fresh else "FRESH"
    
    logging.info(f"Migration state: {state}")
    logging.info(f"Baseline strategy: {strategy}")
    
    if strategy == "FRESH":
        logging.info("Taking fresh baseline snapshot (current DB state)...")
        eval_comp = EvalComparison(migration, nougat_url)
    else:
        logging.info("Using previous baseline snapshot...")
        eval_comp = EvalComparison.load_from_file(...)
    
    report = eval_comp.generate_diff_report(threshold=0.10)
    
    if state["not_embedded"]:
        logging.warning(f"⚠ {len(state['not_embedded'])} chapters not embedded yet; "
                       f"eval results will be incomplete")
    
    return report
```

**Usage:**
```python
# In orchestrator, after re-embedding
state = assess_migration_state(migration)
eval_report = run_eval_with_smart_baseline(migration, nougat_url)

# Answer user's question directly
if state["mixed_dim"]:
    print("\n⚠ BASELINE QUESTION: YES, re-take baseline now.")
    print("  Reason: Chapters 9-12 still have 3072-dim.")
else:
    print("\n✓ BASELINE QUESTION: Baseline is appropriate.")
```

**Impact:** Provides clear guidance on baseline staleness; prevents invalid comparisons.

---

### HIGH PRIORITY (Add Next)

#### Improvement 4: Per-Chapter Re-Embedding with Batch Fallback
**Problem:** OOM on chapter 15 halts entire pipeline; no fallback.  
**Solution:** Batch-size auto-reduction on OOM.

```python
def embed_chapter_with_fallback(embedder, chapter_id: int, texts: List[str], 
                                 initial_batch_size: int = 32) -> np.ndarray:
    """Embed chapter with automatic batch-size reduction on OOM."""
    batch_size = initial_batch_size
    
    while batch_size >= 1:
        try:
            logging.info(f"  Embedding chapter {chapter_id} with batch_size={batch_size}...")
            embeddings = embedder.embed_batch(texts, batch_size=batch_size)
            return embeddings
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                batch_size = batch_size // 2
                logging.warning(f"  OOM detected; retrying with batch_size={batch_size}...")
                continue
            else:
                raise
    
    raise RuntimeError(f"Cannot embed chapter {chapter_id} (OOM at batch_size=1)")

def embed_all_chapters_with_recovery(migration, embedder):
    """Re-embed all chapters with per-chapter OOM fallback."""
    for chapter_id in range(1, 21):
        try:
            texts = migration.get_chapter_texts(chapter_id)
            
            # Check if already embedded (resumption)
            with migration.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM crmb_chunks_v2
                    WHERE chapter = %s AND vector IS NOT NULL
                """, (chapter_id,))
                if cur.fetchone()[0] == len(texts):
                    logging.info(f"✓ Chapter {chapter_id} already embedded")
                    continue
            
            embeddings = embed_chapter_with_fallback(
                embedder, chapter_id, texts, 
                initial_batch_size=32
            )
            
            # Update DB
            with migration.conn.cursor() as cur:
                cur.execute("""
                    UPDATE crmb_chunks_v2 
                    SET vector = %s
                    WHERE chapter = %s
                """, (embeddings, chapter_id))
            migration.conn.commit()
            
        except Exception as e:
            logging.error(f"✗ Chapter {chapter_id} failed: {e}")
            logging.info(f"Skipping chapter {chapter_id} and continuing...")
            continue
```

**Impact:** One failed chapter doesn't halt entire pipeline; user can manually retry later.

---

#### Improvement 5: Transaction Safety for Re-Embedding
**Problem:** Partial updates leave DB in inconsistent state.  
**Solution:** Use savepoints for atomic per-chapter updates.

```python
def embed_chapter_atomic(migration, embedder, chapter_id: int):
    """Embed and update chapter atomically."""
    texts = migration.get_chapter_texts(chapter_id)
    embeddings = embedder.embed_batch(texts)
    
    with migration.conn.cursor() as cur:
        # Create savepoint for this chapter
        cur.execute(f"SAVEPOINT chapter_{chapter_id}")
        
        try:
            cur.execute("""
                UPDATE crmb_chunks_v2 
                SET vector = %s
                WHERE chapter = %s
            """, (embeddings, chapter_id))
            
            # Verify update
            cur.execute("SELECT COUNT(*) FROM crmb_chunks_v2 WHERE chapter = %s AND vector IS NOT NULL", (chapter_id,))
            if cur.fetchone()[0] != len(texts):
                raise RuntimeError(f"Partial update for chapter {chapter_id}")
            
            # Commit savepoint
            cur.execute(f"RELEASE SAVEPOINT chapter_{chapter_id}")
            migration.conn.commit()
            
        except Exception as e:
            cur.execute(f"ROLLBACK TO SAVEPOINT chapter_{chapter_id}")
            migration.conn.commit()
            raise
```

**Impact:** If chapter 15 fails, chapters 1-14 remain committed; no rollback needed.

---

### MEDIUM PRIORITY (Polish)

#### Improvement 6: Dimension Assertion in Queries
**Add before eval queries run:**
```python
def validate_query_dim(query_vec):
    """Raise immediately if query is wrong dimension."""
    if len(query_vec) != 1024:
        raise RuntimeError(f"Query vector is {len(query_vec)}-dim, expected 1024")
```

#### Improvement 7: Pre-Eval Sanity Check
```python
def sanity_check_before_eval(migration):
    """Final checks before launching eval."""
    with migration.conn.cursor() as cur:
        # Any NULL vectors?
        cur.execute("SELECT COUNT(*) FROM crmb_chunks_v2 WHERE vector IS NULL")
        null_count = cur.fetchone()[0]
        if null_count > 0:
            logging.warning(f"⚠ {null_count} chunks have NULL vectors")
        
        # Check all chapters present
        cur.execute("SELECT COUNT(DISTINCT chapter) FROM crmb_chunks_v2")
        chapter_count = cur.fetchone()[0]
        if chapter_count < 20:
            logging.warning(f"⚠ Only {chapter_count}/20 chapters in DB")
```

---

## Summary: Answering User's Three Questions

Based on stress test evaluation, here's how SKILL.md currently answers user's questions:

| Question | SKILL.md Answer | Grade | Why |
|----------|-----------------|-------|-----|
| **1. Resume without re-processing 1-8?** | Not addressed; user must manually track and skip | F | No checkpoint logic; orchestrator always runs all steps |
| **2. Handle mixed 3072/1024 dims?** | Mentioned in troubleshooting but no code | F | `validate_embedding_dim()` only samples 10 rows; misses problem |
| **3. Re-take baseline snapshot?** | Implicitly yes (EvalComparison constructor takes snapshot now) | C+ | Correct answer, but doesn't explain why or account for partial state |

---

## Final Robustness Scorecard

| Criterion | Score | Interpretation |
|-----------|-------|-----------------|
| **Handles partial resumption** | 1/5 | ✗ Fails; user loses hours re-running completed chapters |
| **Handles mixed dimensions** | 1/5 | ✗ Fails; validation too shallow, eval runs with mismatched dims |
| **Handles stale baseline** | 2/5 | ~ Partial; correct answer but no strategy for mixed-dim scenario |
| **Error recovery** | 2/5 | ✗ Minimal; one failure halts entire pipeline |
| **Data integrity** | 3/5 | ~ Okay; schema versioning good but no transaction safety during updates |
| **Practical usability in failure** | 1/5 | ✗ User must debug, manually retry, write workarounds |
| **Overall Robustness** | 1.5/5 | ✗ **Skill assumes clean slate; fails catastrophically under realistic crash scenarios** |

---

## Recommendation

**Do not use this skill for production migrations where resilience matters.**

Use for:
- ✓ Learning the architecture (7-step pipeline is well-designed)
- ✓ Prototyping on clean systems (no interruptions expected)

Add before production use:
1. **Checkpoint resumption** (1-2 hours to implement)
2. **Mixed-dimension detection and remediation** (1 hour)
3. **Smart baseline strategy** (30 min)
4. **Per-chapter transaction safety** (1 hour)

Total hardening effort: ~4 hours.
