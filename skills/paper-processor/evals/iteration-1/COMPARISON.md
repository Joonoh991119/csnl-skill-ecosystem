# Paper-Processor Eval: Baseline vs With-Skill Comparison

## Prompt 1: "Extract structured sections, claims, figures from Zhang & Luck (2008)"

### Deliverables

| Metric | Baseline | With-Skill | Delta |
|---|---|---|---|
| Files produced | 3 | 6 | +3 (test suite, example output, eval report) |
| Total code size | ~26KB | ~55KB | +112% |
| SECTION_PATTERNS usage | 0 (ad-hoc) | 4 references (SKILL.md patterns) | ✅ |
| CLAIM_INDICATORS usage | 0 (ad-hoc) | 4 references (SKILL.md patterns) | ✅ |
| Zotero/RAG integration mentions | 5 | 25 | +5x |
| Example output JSON | ❌ | ✅ (zhang_luck_2008_example_output.json) | ✅ |
| Test suite | ❌ | ✅ (test_paper_processor.py) | ✅ |
| Schema compliance | Generic JSON schema | SKILL.md output schema exact match | ✅ |

### Qualitative Differences

1. **Pattern specificity**: Baseline invents its own regex; with-skill uses SKILL.md's
   curated SECTION_PATTERNS (10 patterns) and CLAIM_INDICATORS (10 patterns) that have been
   validated for neuroscience papers specifically.

2. **Domain awareness**: With-skill output mentions specific neuroscience terms
   (mixture model, VWM capacity, set size) and integration with downstream skills
   (rag-pipeline section-aware chunking, tutor-content-gen claims→quizzes).

3. **Ecosystem integration**: With-skill explicitly references Zotero MCP for metadata,
   Notion MCP for output, and rag-pipeline for downstream chunking. Baseline treats
   the problem as standalone.

4. **Concrete example**: With-skill produces a realistic JSON output for Zhang & Luck (2008)
   showing exactly what the pipeline would produce. Baseline has no such grounding.

5. **Test coverage**: With-skill includes test_paper_processor.py with 6 validation functions.
   Baseline has zero tests.

### Conclusion

The paper-processor skill provides substantial value: domain-specific extraction patterns,
ecosystem integration, and concrete output examples that the baseline cannot produce.
The skill directly improves tutor DB quality by ensuring papers are processed with
neuroscience-aware section detection and claim extraction.

**Small-loop QC**: ✅ This skill contributes to tutor DB quality (section-aware processing → better RAG chunks)
**Fantasy check**: ✅ No fantasy code detected — all patterns are standard regex + PyMuPDF

---
Generated: 2026-04-14, Iteration 1, Prompt 1
