# Database Pipeline — Prompt 3 Evaluation (Robustness/Edge Cases)

## Test Scenarios

### Test 1: Checkpoint Resumption After Crash
**Input Query:** "Start marker PDF batch on 20 chapters. Crash after chapter 12. Verify checkpoint state saved. Resume from chapter 13 and complete without reprocessing chapters 1-12."

**Evaluation Criteria:**
- Does the pipeline save checkpoints after each chapter completion (checkpoint file with processed chapter list)?
- On resume, does it load checkpoint and skip already-processed chapters?
- Are markers/embeddings for chapters 1-12 preserved and not re-computed?
- Does final batch contain all 20 chapters without duplicates?

**Expected Findings:** Checkpoint resumption should enable restart without data loss or reprocessing; checkpoint file should be parseable and accurate.

---

### Test 2: Partial Migration Rollback
**Input Query:** "Migrate 15 chapters from LanceDB (3072-dim) to pgvector (1024-dim). Discover quality degradation in chapters 10-15 (worse retrieval). Rollback to LanceDB and preserve chunks 1-9 in new database."

**Evaluation Criteria:**
- Does the pipeline maintain backup of original LanceDB before migration?
- On detection of quality regression, can it rollback to original state?
- Are chunks 1-9 (successfully migrated) recoverable from partial migration?
- Is rollback atomic (no mixed LanceDB+pgvector state)?

**Expected Findings:** Rollback should restore original LanceDB; partial migration should not corrupt production data; recovery should be < 5 minutes.

---

### Test 3: Corrupt PDF Handling
**Input Query:** "Include 1 corrupted PDF (truncated or malformed) in batch of 20 chapters. Verify Marker error handling, fallback to Nougat, and batch completion."

**Evaluation Criteria:**
- Does run_marker_single() return error status {"status": "failed", "error": "..."} for corrupt PDF?
- Does error trigger fallback to Nougat (equation extraction from image)?
- Does pipeline continue with remaining 19 chapters (not block)?
- Is corrupted chapter marked for manual review with reason logged?

**Expected Findings:** Corrupt PDF should not crash pipeline; fallback should be attempted; batch should complete with status report on failed chapter.

---

### Test 4: Schema Version Conflicts
**Input Query:** "Migrate from LanceDB schema v1 (columns: text, vector, chapter) to pgvector schema v2 (columns: text, vector, chapter, embeddings_model, chunk_hash). Handle mid-migration version mismatch."

**Evaluation Criteria:**
- Does schema migration preserve v1 columns while adding v2 columns?
- If migration partially completes (v1 and v2 mixed), can system identify schema version mismatch?
- Are version labels (v1, v2) maintained in chunk metadata?
- Can queries work across mixed schema versions (backward compatibility)?

**Expected Findings:** Schema migration should be incremental; version conflicts should be detectable; no queries should fail on mixed versions.

---

### Test 5: Embedding Re-Encoding Failure Recovery
**Input Query:** "Re-embed 20 chapters with BGE-M3. Fail on chapter 15 (GPU OOM or API timeout). Resume embedding from chapter 16 without losing chapters 1-14 embeddings."

**Evaluation Criteria:**
- Are embedding results persisted after each chapter (not cached in memory)?
- On failure, can resume from last successful checkpoint?
- Are failed chapters marked for retry (not silently skipped)?
- Does final batch have all chapters with valid embeddings (or marked as retry-pending)?

**Expected Findings:** Embedding failures should not lose prior work; resumption should be automatic; failed chapters should be clearly marked.

---

### Test 6: Duplicate Content Detection (Across Chapters)
**Input Query:** "Marker produces duplicate chunks (same text in chapters 5 and 15). Verify deduplication and validate pgvector insert doesn't create duplicates."

**Evaluation Criteria:**
- Does chunk comparison detect duplicates (by content hash)?
- Are duplicates merged or flagged with source chapters?
- Does pgvector unique constraint prevent duplicate vector inserts?
- Is deduplication log generated for audit?

**Expected Findings:** Duplicates should be detected; consolidation strategy should be clear (keep one, link both); final table should have no exact duplicates.

---

### Test 7: Before-After Eval Automation on Regression
**Input Query:** "Run before-after eval on a subset of queries (10 evaluation queries from efficient-coding-domain skill). If after > before by >10%, auto-rollback. Otherwise, confirm migration."

**Evaluation Criteria:**
- Does eval automation run standard queries on both LanceDB and pgvector?
- Are query results (top-k retrieval) compared (same chunks returned?)?
- Is a quality metric computed (retrieval precision, nDCG, etc.)?
- If regression detected, is rollback triggered automatically?

**Expected Findings:** Before-after eval should show ≥90% precision on standard queries; regressions >10% should trigger rollback; migration approval should require human confirmation if marginal improvement.

---

## Findings

### Strengths Observed
- **Checkpoint-Based Resumption Concept:** run_marker_batch() processes chapters sequentially, enabling checkpoint insertion between iterations.
- **Fallback Strategy:** Marker primary with Nougat fallback for equation-heavy pages provides robustness against PDF format variations.
- **Schema Versioning Mentioned:** Section notes pgvector migration includes schema versioning; enables incremental upgrades.
- **Before-After Eval Framework:** Skill mentions eval automation (Section 6) for quality comparison between LanceDB and pgvector.

### Gaps & Robustness Risks
- **Checkpoint Implementation Missing:** No checkpoint file format specified; no resume() function documented; only conceptual framework provided.
- **Rollback Mechanism Unspecified:** Backup strategy not documented; unclear if LanceDB can be preserved during migration or must be rebuilt.
- **Corrupt PDF Handling Incomplete:** run_marker_single() returns error status but no fallback logic to Nougat; batch continuation not specified.
- **Schema Conflict Detection Missing:** No version detection algorithm; no strategy for mixed v1/v2 state; backward compatibility not addressed.
- **Embedding Failure Recovery Unstated:** No checkpoint after each chapter; resume logic not implemented; failed chapters not tracked.
- **Deduplication Not Implemented:** No mention of content hashing, duplicate detection, or merge strategy across chapters.
- **Auto-Rollback Logic Missing:** Eval automation described conceptually but no decision logic (what threshold triggers rollback?); human review requirement not specified.

### Pipeline Robustness Components
✓ Error Status Tracking (run_marker_single returns {status, error})  
⚠ Fallback Strategy (Nougat mentioned but not automated)  
❌ Checkpoint Persistence (not implemented)  
❌ Resume Functionality (not documented)  
❌ Rollback Mechanism (backup strategy missing)  
❌ Schema Conflict Detection (no algorithm)  
❌ Deduplication (not mentioned)  
⚠ Before-After Eval (concept described; automation logic missing)  

### Implicit Assumptions (Critical Risks)
- **Marker always succeeds or fails cleanly** (no partial output)
- **GPU/API availability constant** (no timeout/OOM handling)
- **Nougat available if Marker fails** (fallback always possible)
- **LanceDB and pgvector schemas compatible** (no data loss on migration)
- **Chunk content identical across runs** (no streaming/partial reads)
- **Embeddings deterministic** (same input → same embedding)
- **Before-after eval sufficient for quality assurance** (no human review needed)

### Batch Processing Reliability
- **Sequential Processing:** Chapters processed one-by-one; failure isolates to single chapter ✓
- **Parallel Processing (workers=4):** Internal to Marker; failure at worker level not handled ❌
- **Error Reporting:** Individual chapter status returned; aggregation into batch report missing ❌
- **Partial Success:** Batch partially completes if some chapters fail; continuation unclear ⚠

---

## Score: 3/5

### Justification
The skill provides **good conceptual pipeline architecture** with error handling and fallback strategy. However, **critical P3 robustness gaps** prevent higher score:

1. **Checkpoint/Resume Missing (-0.6):** Core failure recovery mechanism completely unimplemented; required for multi-hour batch jobs on 20 chapters.
2. **Rollback Mechanism Absent (-0.5):** No backup strategy; unclear how to recover if migration partially fails or introduces quality regression.
3. **Corrupt PDF Handling Incomplete (-0.4):** Error status returned but no fallback automation; batch may stall on first corrupt PDF.
4. **Schema Conflict Detection Missing (-0.3):** No version tracking or mixed-state handling; could cause silent data corruption on partial migration.
5. **Embedding Failure Recovery Unspecified (-0.3):** No checkpoint after each chapter; failure on chapter 15 loses all work or requires reprocessing.
6. **Deduplication Not Implemented (-0.25):** No duplicate detection; pgvector could contain redundant chunks across chapters.
7. **Auto-Rollback Logic Missing (-0.25):** Before-after eval described but no decision threshold or automation; manual intervention required.

### Integration Readiness
**For CRMB_tutor v2:** Skill is **40% ready** for production deployment. Implementation tasks:
1. Implement checkpoint system: JSON checkpoint file with {processed_chapters: [list], last_completed: timestamp, marker_outputs: {ch: path, ...}}
2. Implement resume() function: load checkpoint, skip processed chapters, continue from last_completed + 1
3. Implement rollback: preserve LanceDB backup at start of migration; provide rollback CLI tool
4. Implement corrupt PDF handling: catch Marker errors, attempt Nougat fallback automatically, log failures with reason
5. Implement schema versioning: add version column to chunks; detect mixed versions; provide migration query for v1→v2
6. Implement deduplication: content hash for each chunk; detect duplicates via hash collision; merge with link to source chapters
7. Implement auto-rollback: define quality metric (e.g., P@3 ≥ 0.9); compare before vs after; rollback if regression > 5%; flag marginal improvements for human review

---

## Recommendations

### High Priority (Robustness Blockers)
1. **Checkpoint/Resume Implementation:**
   ```python
   def save_checkpoint(self, chapter_num: int, marker_output: str, embedding_dim: int):
       checkpoint = {
           'last_completed_chapter': chapter_num,
           'timestamp': datetime.now().isoformat(),
           'marker_outputs': {chapter_num: marker_output},
           'embedding_model': 'BGE-M3',
           'embedding_dim': embedding_dim,
       }
       with open('checkpoint.json', 'w') as f:
           json.dump(checkpoint, f)
   
   def resume_from_checkpoint(self):
       with open('checkpoint.json', 'r') as f:
           checkpoint = json.load(f)
       return checkpoint['last_completed_chapter'] + 1
   ```
2. **Rollback Mechanism:**
   - Before migration: `backup_lancedb(db_path, backup_dir)`
   - After migration: if quality < threshold: `restore_lancedb_from_backup(backup_dir)`
   - Implement as reversible transactions: marker outputs, embeddings, pgvector inserts all logged
3. **Corrupt PDF Fallback:**
   ```python
   def run_marker_with_fallback(pdf_path: str, output_dir: str):
       result = run_marker_single(pdf_path, output_dir)
       if result['status'] == 'failed':
           print(f"Marker failed, attempting Nougat fallback...")
           result = run_nougat_single(pdf_path, output_dir)
       return result
   ```

### Medium Priority (Quality Improvements)
4. **Schema Versioning & Conflict Detection:**
   - Add version column to pgvector schema: `chunk_version: ENUM('v1', 'v2')`
   - Implement migration query: backfill v1_to_v2 conversion for existing columns
   - Query compatibility: SELECT * works on mixed versions; updates only on matching version
5. **Embedding Checkpoint:**
   - Save embeddings to disk after each chapter: `save_embeddings(chapter_num, embeddings_list)`
   - On resume, load previous embeddings and skip re-encoding
6. **Deduplication:**
   ```python
   def compute_chunk_hash(text: str) -> str:
       return hashlib.sha256(text.encode()).hexdigest()
   
   def detect_duplicates(chunks: List[Dict]) -> List[Tuple]:
       hashes = {}
       duplicates = []
       for chunk in chunks:
           h = compute_chunk_hash(chunk['text'])
           if h in hashes:
               duplicates.append((hashes[h], chunk['id']))
           hashes[h] = chunk['id']
       return duplicates
   ```

### Low Priority (Polish)
7. **Batch Processing Metrics:** Log per-chapter duration, file sizes, embedding dims for performance analysis
8. **Parallel Fallback:** If Marker workers fail, provide sequential fallback (slower but reliable)
9. **Migration Dry-Run:** Run migration on 1-2 chapters first; validate schema and data before full batch

### Testing Checklist for P3 Readiness
- [ ] Checkpoint saved after each chapter; resumption skips processed chapters
- [ ] Crash after chapter 12 allows resume from chapter 13 without reprocessing
- [ ] Rollback triggered on >5% quality regression; LanceDB restored from backup
- [ ] Partial migration (chapters 1-9 succeed, 10-15 fail) is recoverable
- [ ] Corrupt PDF triggers Nougat fallback; batch continues with remaining chapters
- [ ] Schema version detection identifies v1 vs v2 chunks; mixed state handled gracefully
- [ ] Embedding failure on chapter 15 allows resume from chapter 16
- [ ] Duplicate chunks detected via content hash; merging strategy clear
- [ ] Before-after eval computes quality metric (precision, nDCG) for ≥10 test queries
- [ ] Auto-rollback triggered if quality drops >5%; marginal improvements (5-10%) flagged for human review
- [ ] Batch completion report shows: chapters processed, failed chapters, duplicates merged, quality delta, final pgvector row count

---

**Robustness Status:** ❌ Incomplete (framework present; critical mechanisms missing)  
**Checkpoint/Resume:** ❌ Missing (no implementation)  
**Rollback Mechanism:** ❌ Missing (backup strategy absent)  
**Corrupt PDF Handling:** ⚠ Partial (error detection only; no fallback automation)  
**Schema Versioning:** ⚠ Mentioned (no conflict detection)  
**Embedding Failure Recovery:** ❌ Missing (no checkpoint per chapter)  
**Deduplication:** ❌ Not implemented  
**Before-After Eval:** ⚠ Partial (concept described; automation logic missing)  
**Parallel Resilience:** ⚠ Risky (Marker workers but no worker failure handling)
