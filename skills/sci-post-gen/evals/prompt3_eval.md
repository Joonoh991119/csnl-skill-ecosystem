# sci-post-gen — Prompt 3 Evaluation (Robustness/Edge Cases)

**Evaluation Date:** 2026-04-14  
**Skill File:** `/private/tmp/csnl-skill-ecosystem/skills/sci-post-gen/SKILL.md` (464 lines)  
**Focus:** Content generation edge cases — two-domain posts, equation rendering, Korean audience adaptation, citation accuracy, Quarto rendering failures, CuriosityModulator hook diversity

---

## Test Scenarios

### 1. Two-Domain Blog Post: ART + Sparse Coding
**Scenario:** User requests: "Write a blog post bridging Adaptive Resonance Theory and sparse coding principles."

**Expected Behavior:**
- Domain detection (lines 85–110) identifies both CRMB (ART) and EfficientCoding (sparse coding)
- Classification: CrossDomain post
- Post structure: Intro → ART section → Sparse coding section → Unified bridge → Conclusion
- Citations grounded in both CRMB chapters and EC papers
- Korean primary text with inline English terms

**Actual Result:** ⚠️ **PARTIAL FAIL**
- `detect_domain()` (lines 85–110) correctly identifies both domains and returns `['CRMB', 'EfficientCoding', 'CrossDomain']`
- Template selection (lines 89–104) would choose blog_post_template
- **BUT:** Worked example (lines 352–408) provides outline but no actual implementation of generation logic
- No specification of how tutor integrates RAG chunks from both domains
- Post structure outline is aspirational; no code generates actual bilingual content
- Bridge section (section 4, lines 113–117) is conceptual; actual bridge writing strategy is missing

**Impact:** High — Cross-domain posts are central to skill value; implementation is incomplete.

---

### 2. Equation Rendering in Blog Posts: Quarto Math Failures
**Scenario:** Blog post includes complex equation: "$V = \sum_{i} w_i \phi_i(x)$ for sparse coding basis decomposition"

**Expected Behavior:**
- Inline math wrapped in `$...$` for Quarto
- Display math in `$$...$$` block
- LaTeX compiles without error in Quarto render
- Fallback to MathJax if LaTeX unavailable

**Actual Result:** ⚠️ **PARTIAL FAIL**
- Section 5 (lines 217–221) describes inline and display math with correct Quarto syntax
- `generate_quarto_post()` (lines 296–316) includes YAML frontmatter with format specification
- **BUT:** No equation validation before embedding in Quarto
- If user's equation has unmatched braces or undefined macros, Quarto rendering silently fails
- No error handling in QualityScorer (lines 226–267); equation syntax is not validated
- Example worked post (lines 384–408) shows embedded equations but no explanation of verification

**Impact:** High — Silent Quarto rendering failures frustrate users; no debugging guidance provided.

---

### 3. Korean Audience Adaptation: Cultural Context
**Scenario:** Post on sparse coding targeted at Korean neuroscience undergraduate audience.

**Expected Behavior:**
- Adapt examples to Korean visual culture (e.g., Korean writing systems for character recognition tasks)
- Use Korean-language references when available (e.g., Korean papers on sparse coding)
- Explain concepts with Korean-specific analogies

**Actual Result:** ❌ **FAILS**
- Post templates (lines 23–79) specify Korean primary with English parentheticals
- TERM_GLOSSARY (lines 158–175) provides English ↔ Korean translations
- **BUT:** No cultural adaptation layer; posts would use Western examples (Olshausen natural images, English papers)
- No repository of Korean-language references or analogies
- QualityScorer (lines 226–267) has `korean_naturalness()` metric (lines 238–243) but no audience-specific adaptation scoring
- Worked example (lines 352–408) is bilingual but culturally generic

**Impact:** Medium — Korean readers would find content linguistically accessible but culturally distant.

---

### 4. Citation Accuracy: Hallucinated References
**Scenario:** Cross-domain post claims: "Barlow's efficient coding hypothesis (1961) directly predicts ART's vigilance mechanism."

**Expected Behavior:**
- Verification checklist (lines 145–154) validates citations against ALLOWED_CLAIMS
- If claim is not in ALLOWED_CLAIMS, post is blocked or flagged
- User receives: "Citation needed: Barlow and ART vigilance link not found in knowledge base"

**Actual Result:** ❌ **FAILS**
- ALLOWED_CLAIMS (lines 137–141) is defined but remains empty/stub in actual implementation
- `verify_post()` (lines 146–154) checks for citations and grammar but does not validate claim-to-citation mapping
- No mechanism enforces that claims in generated text match citations in ALLOWED_CLAIMS
- If LLM generates "Barlow's hypothesis predicts ART vigilance," no validation would catch hallucination
- Cross-domain posts are high-risk for unsupported claims; no safeguard exists

**Impact:** Critical — Hallucinated citations undermine tutor credibility; users would propagate false claims.

---

### 5. Quarto Rendering Failure: Missing Dependencies
**Scenario:** Generated post includes Quarto code block with Python visualization:

```
```{python}
import matplotlib.pyplot as plt
# Plot sparse coding basis functions
```
```

But user's environment lacks matplotlib.

**Expected Behavior:**
- Skill detects missing dependencies and suggests installation
- Generates post with dependency list (requirements.txt)
- Provides CLI command for setup

**Actual Result:** ❌ **FAILS**
- `generate_quarto_post()` (lines 296–316) outputs .qmd file but does not validate environment
- No dependency tracking or requirements file generation
- Post renders locally; if matplotlib is missing, Quarto fails silently with cryptic error
- No post-generation validation (e.g., quarto render --dry-run)
- User receives broken .qmd with no guidance on fixing

**Impact:** Medium-High — Users expect self-contained, runnable posts; broken rendering is frustrating.

---

### 6. CuriosityModulator Hook Diversity
**Scenario:** Generate 5 blog posts on related ART topics (vigilance, category learning, binding problem).

**Expected Behavior:**
- Each post uses different hook types to maintain reader curiosity
- Skill tracks hook usage across posts and rotates them
- Verification: Each post uses ≥2 unique hook types (PARADOX, CONNECTION, HISTORY, IMPLICATION, MISCONCEPTION, FRONTIER)

**Actual Result:** ❌ **FAILS**
- CuriosityModulator is not defined in SKILL.md (mentioned in user request but absent from implementation)
- No hook selection logic in `generate_bilingual_sentence()` or `generate_quarto_post()`
- Post generation does not integrate curiosity hooks (unlike conversation-sim skill)
- Multiple posts on same topic would be repetitive without hook rotation
- No mechanism to measure "hook diversity" across a post series

**Impact:** Medium-High — Posts would lack pedagogical variety; reader engagement would suffer.

---

### 7. Korean Rendering Failures: Font and Encoding
**Scenario:** Post contains Korean text with special characters (ㄱ, ㄴ, ㅁ diacritics) and mathematical terms mixing Hangul + Latin.

**Expected Behavior:**
- Quarto/markdown correctly encodes UTF-8 Korean text
- Display in HTML/PDF without mojibake
- LaTeX (if usetex=True) supports Korean font packages

**Actual Result:** ⚠️ **PARTIAL FAIL**
- Post templates use Markdown (UTF-8 native)
- Quarto HTML output should render correctly
- **BUT:** PDF output (via LaTeX) requires xeCJK or kotex package
- SKILL.md provides no guidance on Korean font setup for PDF
- If user exports to PDF, Korean text may not render unless LaTeX is configured
- No font package inclusion in Quarto YAML metadata

**Impact:** Medium — Users generating PDFs for Korean audiences would encounter rendering issues.

---

### 8. Multi-Domain Post: Domain Mismatch in Citations
**Scenario:** Cross-domain post (CRMB + EC) contains sections citing both Grossberg CRMB chapters and Olshausen papers.

**Expected Behavior:**
- References section clearly separates CRMB and EC citations
- In-text citations disambiguate source domain (e.g., "[CRMB Ch.3]" vs. "[Olshausen 1996]")

**Actual Result:** ⚠️ **PARTIAL FAIL**
- Section 7 (lines 311–321) shows references list generation
- Citations are appended to markdown footer (lines 313–314)
- **BUT:** No domain-aware citation formatting
- Worked example (lines 384–408) shows unified references; no domain separation
- If CRMB and EC papers have similar year/author (e.g., two 1996 papers), in-text citation formatting is ambiguous
- Quarto would render citations correctly but tutor output lacks semantic clarity

**Impact:** Low-Medium — Citations render but domain context is lost; potential reader confusion.

---

## Findings Summary

### What Works
1. ✓ Domain detection (CRMB, EC, CrossDomain) correctly classifies queries
2. ✓ Template system provides structure for blog, social, newsletter, academic formats
3. ✓ Bilingual generation (Korean primary, English inline) is well-specified
4. ✓ Term glossary for consistent terminology
5. ✓ Quality scoring framework (readability, citations, coherence, Korean naturalness)
6. ✓ Quarto integration with .qmd file generation

### What Breaks
1. ❌ **Cross-domain generation incomplete:** Worked example is outline; no actual implementation
2. ❌ **Equation rendering unvalidated:** No LaTeX syntax checking; silent Quarto failures
3. ❌ **Korean audience adaptation absent:** No cultural context or Korean references
4. ❌ **Citation hallucination undetected:** No claim-to-citation validation; ALLOWED_CLAIMS is stub
5. ❌ **Quarto dependencies undeclared:** Missing matplotlib or other packages causes silent failures
6. ❌ **CuriosityModulator absent:** No hook integration; posts lack pedagogical variety
7. ❌ **Korean font support incomplete:** PDF rendering requires external LaTeX config
8. ❌ **Cross-domain citations unambiguous:** No domain-aware formatting; reader confusion

### Root Causes
- **Incomplete implementation:** Worked example is architectural; core generation logic is missing
- **No validation layer:** Equations, citations, dependencies are not verified before post generation
- **Korean support is partial:** Glossary provided but cultural/audience adaptation absent
- **No curiosity hooks:** Unlike conversation-sim, pedagogical engagement is not tracked
- **Silent failures:** Quarto rendering, LaTeX compilation, dependency issues cause cryptic errors
- **Citation grounding weak:** ALLOWED_CLAIMS is empty; no hallucination safeguards

---

## Score: 2/5

**Rationale:**
- **Relevance: 3/5** — Addresses bilingual post generation for two domains; templates are sound
- **Completeness: 2/5** — Cross-domain generation is mostly outline; core logic is missing
- **Cross-Domain Robustness: 2/5** — Domain detection works; bridge post generation fails
- **Citation Integrity: 1/5** — No validation against ALLOWED_CLAIMS; hallucination risk is high
- **Korean Support: 2/5** — Glossary and bilingual templates provided; cultural adaptation absent
- **Error Handling: 1/5** — Silent failures in Quarto, LaTeX, equation rendering; no debugging support
- **Pedagogical Design: 1/5** — No CuriosityModulator; posts lack engagement hooks

**Composite:** (3 + 2 + 2 + 1 + 2 + 1 + 1) / 7 = **1.71/5** → **2/5**

---

## Recommendations

### Critical Patches (Priority 1)

1. **Implement cross-domain post generation:**
   ```python
   def generate_cross_domain_post(query: str, template: str) -> str:
       """Generate unified post bridging CRMB and EC domains."""
       domains = detect_domain(query)
       
       if 'CrossDomain' not in domains:
           raise ValueError(f"Query not cross-domain: {domains}")
       
       # Retrieve chunks from both RAG systems
       crmb_chunks = rag_crmb.retrieve(query, top_k=5)
       ec_chunks = rag_ec.retrieve(query, top_k=5)
       
       # Structure: Intro, CRMB section, EC section, bridge, conclusion
       content = f"""
   ## 도입 (Introduction)
   {generate_intro(query, crmb_chunks, ec_chunks)}
   
   ## ART와 적응 공명 이론 (Adaptive Resonance Theory)
   {generate_domain_section('CRMB', crmb_chunks, query)}
   
   ## 희소 부호화 (Sparse Coding)
   {generate_domain_section('EC', ec_chunks, query)}
   
   ## 연결고리 (Unified Bridge)
   {generate_bridge_section(crmb_chunks, ec_chunks, query)}
   
   ## 결론 (Conclusion)
   {generate_conclusion(query)}
       """
       return content
   ```

2. **Add equation validation:**
   ```python
   def validate_latex_equations(text: str) -> List[str]:
       """Check LaTeX syntax in math blocks."""
       import re
       
       math_blocks = re.findall(r'\$\$(.+?)\$\$|(?<![\\])\$([^\$]+)\$', text, re.DOTALL)
       errors = []
       
       for eq in math_blocks:
           eq_text = eq[0] or eq[1]
           try:
               # Check balanced braces
               if eq_text.count('{') != eq_text.count('}'):
                   errors.append(f"Unmatched braces in: {eq_text[:50]}")
               # Check for undefined macros
               undefined = check_undefined_macros(eq_text)
               errors.extend(undefined)
           except Exception as e:
               errors.append(str(e))
       
       return errors
   ```

3. **Populate and enforce ALLOWED_CLAIMS:**
   ```python
   ALLOWED_CLAIMS = {
       "ART uses vigilance thresholds": {
           "source": "CRMB_Chapter_3",
           "page": 125,
           "confidence": "high"
       },
       "Sparse coding matches V1 receptive fields": {
           "source": "Olshausen_Field_1996",
           "doi": "10.1038/381607a0",
           "confidence": "high"
       },
       "Barlow predicts ART vigilance": {
           "source": None,  # Not validated
           "confidence": "low",  # REJECT
       }
   }
   
   def validate_claim(claim: str) -> Dict:
       """Check if claim is in ALLOWED_CLAIMS."""
       if claim not in ALLOWED_CLAIMS:
           return {"valid": False, "reason": "Claim not in knowledge base"}
       
       info = ALLOWED_CLAIMS[claim]
       if info.get("confidence") == "low":
           return {"valid": False, "reason": "Claim confidence too low"}
       
       return {"valid": True, "source": info["source"], "page": info.get("page")}
   ```

### High-Priority Patches (Priority 2)

4. **Integrate CuriosityModulator for hook diversity:**
   ```python
   class CuriosityModulator:
       def __init__(self):
           self.hooks = [
               'PARADOX',      # Surprising fact
               'CONNECTION',   # Link to known concept
               'HISTORY',      # Historical context
               'IMPLICATION',  # Practical consequence
               'MISCONCEPTION',# Common error
               'FRONTIER',     # Open problem
           ]
           self.hook_usage = {h: 0 for h in self.hooks}
       
       def select_hook(self, topic: str, previous_hooks: List[str]) -> str:
           """Select least-used hook for diversity."""
           available = [h for h in self.hooks if h not in previous_hooks]
           if not available:
               available = self.hooks
           
           # Choose hook with lowest usage count
           selected = min(available, key=lambda h: self.hook_usage[h])
           self.hook_usage[selected] += 1
           return selected
   
   # Use in post generation:
   modulator = CuriosityModulator()
   for section in post_sections:
       hook = modulator.select_hook(section["topic"], previous_hooks)
       section["content"] = add_hook(section["content"], hook)
   ```

5. **Add Korean audience adaptation:**
   ```python
   KOREAN_AUDIENCE_CONTEXT = {
       "undergrad": {
           "examples": ["Hangul character recognition", "Korean visual culture"],
           "references": ["Korean neuroscience papers on sparse coding"],
           "analogy_style": "everyday Korean experience",
       },
       "researcher": {
           "examples": ["Naturalistic Korean images (COCO-Korean dataset)"],
           "references": ["Korean and international papers"],
           "analogy_style": "technical Korean terminology",
       },
   }
   
   def adapt_for_korean_audience(post: str, audience: str) -> str:
       """Adapt examples and references for Korean context."""
       context = KOREAN_AUDIENCE_CONTEXT[audience]
       post = post.replace("[example]", context["examples"][0])
       # ... integrate Korean references
       return post
   ```

6. **Add Quarto environment validation:**
   ```python
   def check_quarto_environment(post: PostData) -> Dict[str, List[str]]:
       """Check dependencies and Quarto configuration."""
       issues = []
       dependencies = []
       
       # Scan for Python imports in code blocks
       import re
       imports = re.findall(r'import (\w+)', post.content)
       dependencies.extend(imports)
       
       # Check if packages are available
       missing = []
       for pkg in set(dependencies):
           try:
               __import__(pkg)
           except ImportError:
               missing.append(pkg)
       
       if missing:
           issues.append(f"Missing packages: {missing}")
       
       # Check Korean LaTeX support
       if 'Korean' in post.content or any(ord(c) > 0xAC00 for c in post.content):
           # Text contains Korean
           if 'xeCJK' not in post.yaml_metadata:
               issues.append("Korean text detected; recommend xeCJK in Quarto YAML")
       
       return {"issues": issues, "dependencies": list(set(dependencies))}
   ```

### Medium-Priority Patches (Priority 3)

7. **Domain-aware citation formatting:**
   ```python
   def format_citations_by_domain(citations: List[Citation], domains: List[str]) -> str:
       """Group and format citations by domain."""
       md = "## 참고문헌 (References)\n\n"
       
       for domain in domains:
           domain_citations = [c for c in citations if c.domain == domain]
           if domain_citations:
               md += f"### {domain}\n"
               for c in domain_citations:
                   md += f"- {c.to_string()}\n"
       
       return md
   ```

8. **Quarto rendering validation:**
   - Add post-generation step: `quarto render --dry-run post.qmd`
   - Catch and report LaTeX errors, missing packages
   - Suggest fixes before returning to user

9. **Extend ALLOWED_CLAIMS from knowledge base:**
   - Auto-populate from RAG corpus
   - Mark confidence levels based on citation frequency
   - Block low-confidence cross-domain claims

---

## Testing Checklist for Next Eval

- [ ] Generate cross-domain post (ART + sparse coding) → verify structure includes bridge section
- [ ] Include complex LaTeX equation → verify validation catches syntax errors; Quarto renders
- [ ] Generate post for Korean undergraduate audience → verify examples are Korean-culturally relevant
- [ ] Attempt hallucinated claim "Barlow predicts ART vigilance" → verify rejection with reason
- [ ] Generate post with matplotlib code block → verify dependency check warns user
- [ ] Generate 3 posts on related ART topics → verify hook types are diverse across posts
- [ ] Export post to PDF with Korean text → verify font rendering or LaTeX config recommendation
- [ ] Generate cross-domain post → verify citations are domain-separated in references

---

**Summary:** sci-post-gen provides well-designed templates and bilingual structure but lacks core implementation for cross-domain generation, equation validation, and pedagogical engagement. Citation hallucination is a critical risk; CuriosityModulator is absent. Investment in cross-domain orchestration, equation/citation validation, and hook integration would elevate from 2/5 → 4/5.
