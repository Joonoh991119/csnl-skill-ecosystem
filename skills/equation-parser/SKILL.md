---
name: equation-parser
description: >
  Scientific equation parsing pipeline for extracting, converting, and indexing mathematical
  equations from PDF papers and textbooks. Implements a 4-tool chain (Marker force_ocr,
  Nougat, LaTeX-OCR, pix2tex) with inline/display math detection, equation numbering
  preservation, cross-reference mapping, and LaTeX compilation verification. Outputs
  LaTeX + MathML + plain text. Includes Grossberg-specific notation (ART vigilance rho,
  BCS/FCS variables) and Korean math term glossary. Optimized for M4 Pro 64GB with MPS.
  MANDATORY TRIGGERS: equation parsing, math extraction, LaTeX OCR, formula detection,
  Nougat, pix2tex, LaTeX-OCR, equation indexing, math symbols, display math, inline math,
  cross-reference, equation numbering, MathML, Grossberg notation, scientific formulas.
---

# Equation Parser: Scientific Math Extraction Pipeline

You are a scientific equation extraction specialist. Your job is to parse mathematical
equations from PDF papers/textbooks and produce structured, verifiable, RAG-indexable output.

## 1. Tool Chain Architecture

```
PDF Input
  ↓
[Stage 1] Marker v1.10 (force_ocr=True)
  → markdown with LaTeX blocks (\$...\$, \$\$...\$\$)
  ↓ if equation quality < threshold
[Stage 2] Nougat (equation-specialized vision model)
  → high-fidelity LaTeX for complex equations
  ↓ if Nougat fails or unavailable
[Stage 3] LaTeX-OCR (lightweight, fast)
  → LaTeX from equation images
  ↓ if LaTeX-OCR fails
[Stage 4] pix2tex (final fallback)
  → best-effort LaTeX conversion
  ↓
[Verify] LaTeX compilation test
  ↓
[Output] LaTeX + MathML + plain text + metadata
```

### Stage 1: Marker v1.10 (Primary)

```python
import subprocess, json, os

def run_marker(pdf_path: str, output_dir: str, force_ocr: bool = True) -> dict:
    """Run Marker PDF→markdown with force_ocr for equation preservation."""
    cmd = [
        "marker_single", pdf_path, output_dir,
        "--force_ocr" if force_ocr else "",
        "--output_format", "markdown",
    ]
    result = subprocess.run([c for c in cmd if c], capture_output=True, text=True, timeout=600)
    
    md_path = os.path.join(output_dir, os.path.splitext(os.path.basename(pdf_path))[0] + ".md")
    with open(md_path) as f:
        content = f.read()
    
    # Extract equation blocks
    equations = extract_equations_from_markdown(content)
    return {"markdown": content, "equations": equations, "source": "marker"}


def extract_equations_from_markdown(md_content: str) -> list:
    """Extract inline ($...$) and display ($$...$$) math from Marker output."""
    import re
    equations = []
    
    # Display math: $$...$$ or \begin{equation}...\end{equation}
    for m in re.finditer(
        r'(\$\$(.+?)\$\$|\\begin\{(equation|align|gather|multline)\}(.+?)\\end\{\3\})',
        md_content, re.DOTALL
    ):
        latex = m.group(2) or m.group(4)
        equations.append({
            "type": "display",
            "latex": latex.strip(),
            "position": m.start(),
            "raw_match": m.group(0),
        })
    
    # Inline math: $...$  (not $$)
    for m in re.finditer(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', md_content):
        equations.append({
            "type": "inline",
            "latex": m.group(1).strip(),
            "position": m.start(),
            "raw_match": m.group(0),
        })
    
    return sorted(equations, key=lambda x: x["position"])
```

### Stage 2: Nougat (Equation-Specialized)

```python
import requests, base64
from pathlib import Path

NOUGAT_URL = "http://localhost:8503/predict"  # Local Nougat service

def run_nougat_on_page(pdf_path: str, page_num: int) -> dict:
    """Extract equations from a single PDF page using Nougat vision model."""
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=300)  # High DPI for equation clarity
    img_bytes = pix.tobytes("png")
    
    response = requests.post(NOUGAT_URL, files={"file": ("page.png", img_bytes, "image/png")})
    if response.status_code != 200:
        return {"error": f"Nougat failed: {response.status_code}", "source": "nougat"}
    
    nougat_md = response.json().get("text", "")
    equations = extract_equations_from_markdown(nougat_md)
    return {"markdown": nougat_md, "equations": equations, "source": "nougat"}


def nougat_batch_equations(pdf_path: str, equation_pages: list) -> list:
    """Process multiple equation-heavy pages through Nougat."""
    results = []
    for page_num in equation_pages:
        result = run_nougat_on_page(pdf_path, page_num)
        result["page"] = page_num
        results.append(result)
    return results
```

### Stage 3: LaTeX-OCR (Lightweight Fallback)

```python
def run_latex_ocr(image_path: str) -> str:
    """Use LaTeX-OCR for fast equation image → LaTeX conversion."""
    from pix2tex.cli import LatexOCR
    
    model = LatexOCR()
    from PIL import Image
    img = Image.open(image_path)
    latex = model(img)
    return latex


def run_latex_ocr_batch(image_paths: list) -> list:
    """Batch process equation images through LaTeX-OCR."""
    from pix2tex.cli import LatexOCR
    from PIL import Image
    
    model = LatexOCR()
    results = []
    for path in image_paths:
        try:
            img = Image.open(path)
            latex = model(img)
            results.append({"image": path, "latex": latex, "source": "latex-ocr"})
        except Exception as e:
            results.append({"image": path, "error": str(e), "source": "latex-ocr"})
    return results
```

### Stage 4: pix2tex (Final Fallback)

```python
def run_pix2tex(image_path: str) -> str:
    """pix2tex as final fallback for equation images."""
    try:
        from pix2tex.cli import LatexOCR
        model = LatexOCR()
        from PIL import Image
        return model(Image.open(image_path))
    except Exception:
        return "[PARSE_FAILED]"
```

### Cascading Pipeline

```python
def parse_equation(pdf_path: str, page_num: int, bbox: tuple = None,
                   equation_image_path: str = None) -> dict:
    """4-stage cascading equation parser. Returns best result."""
    
    # Stage 1: Try Marker (if full page)
    if not equation_image_path:
        marker_result = run_marker(pdf_path, "/tmp/marker_out")
        page_eqs = [e for e in marker_result["equations"] if e.get("page") == page_num]
        if page_eqs and all(verify_latex(e["latex"]) for e in page_eqs):
            return {"equations": page_eqs, "method": "marker", "quality": "verified"}
    
    # Stage 2: Try Nougat
    nougat_result = run_nougat_on_page(pdf_path, page_num)
    if nougat_result.get("equations") and not nougat_result.get("error"):
        verified = [e for e in nougat_result["equations"] if verify_latex(e["latex"])]
        if verified:
            return {"equations": verified, "method": "nougat", "quality": "verified"}
    
    # Stage 3: LaTeX-OCR
    if equation_image_path:
        latex = run_latex_ocr(equation_image_path)
        if verify_latex(latex):
            return {"equations": [{"latex": latex, "type": "display"}], 
                    "method": "latex-ocr", "quality": "verified"}
    
    # Stage 4: pix2tex fallback
    if equation_image_path:
        latex = run_pix2tex(equation_image_path)
        return {"equations": [{"latex": latex, "type": "display"}],
                "method": "pix2tex", "quality": "unverified"}
    
    return {"equations": [], "method": "none", "quality": "failed"}
```

## 2. Parsing Strategy: Inline vs Display Math

### Detection Heuristics

```python
import re

def classify_equation(latex: str, context_before: str = "", context_after: str = "") -> dict:
    """Classify equation as inline or display, detect numbering and cross-refs."""
    
    result = {
        "type": "unknown",
        "numbered": False,
        "equation_number": None,
        "label": None,
        "cross_refs": [],
    }
    
    # Display math indicators
    display_patterns = [
        r'\\begin\{(equation|align|gather|multline|eqnarray)',
        r'^\s*\$\$',              # Starts with $$
        r'\\frac\{',              # Complex fractions → likely display
        r'\\sum_\{',              # Summation → likely display
        r'\\int_\{',              # Integral → likely display
        r'\\prod_\{',             # Product → likely display
    ]
    
    if any(re.search(p, latex) for p in display_patterns):
        result["type"] = "display"
    else:
        result["type"] = "inline"
    
    # Equation numbering: (1), (2.3), (A.1)
    num_match = re.search(r'\((\d+(?:\.\d+)?(?:[a-z])?)\)\s*$', context_after)
    if num_match:
        result["numbered"] = True
        result["equation_number"] = num_match.group(1)
    
    # LaTeX label: \label{eq:art_vigilance}
    label_match = re.search(r'\\label\{(eq:[^}]+)\}', latex)
    if label_match:
        result["label"] = label_match.group(1)
    
    # Cross-references in surrounding text: Eq. (3), Equation 2.1, \eqref{...}
    ref_patterns = [
        r'(?:Eq|Equation|Eqn)\.?\s*\(?(\d+(?:\.\d+)?)\)?',
        r'\\eqref\{([^}]+)\}',
        r'\\ref\{(eq:[^}]+)\}',
    ]
    for pattern in ref_patterns:
        for m in re.finditer(pattern, context_before + " " + context_after):
            result["cross_refs"].append(m.group(1))
    
    return result


def build_cross_reference_map(equations: list) -> dict:
    """Map equation numbers/labels to their LaTeX content."""
    ref_map = {}
    for eq in equations:
        if eq.get("equation_number"):
            ref_map[eq["equation_number"]] = eq["latex"]
        if eq.get("label"):
            ref_map[eq["label"]] = eq["latex"]
    return ref_map
```

## 3. Quality Verification

### LaTeX Compilation Test

```python
import subprocess, tempfile, os

def verify_latex(latex: str) -> bool:
    """Verify LaTeX compiles without errors using pdflatex."""
    doc = r"""\documentclass{article}
\usepackage{amsmath,amssymb,amsfonts}
\begin{document}
$$ %s $$
\end{document}""" % latex.replace('\\', '\\\\') if '\\' not in latex[:5] else \
    r"""\documentclass{article}
\usepackage{amsmath,amssymb,amsfonts}
\begin{document}
%s
\end{document}""" % latex
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "test.tex")
        with open(tex_path, 'w') as f:
            f.write(doc)
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path],
            capture_output=True, text=True, cwd=tmpdir, timeout=15
        )
        return result.returncode == 0


def verify_latex_fast(latex: str) -> bool:
    """Fast LaTeX syntax check without full compilation (regex-based)."""
    # Check balanced braces
    depth = 0
    for ch in latex:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
        if depth < 0: return False
    if depth != 0: return False
    
    # Check balanced \begin/\end
    begins = re.findall(r'\\begin\{(\w+)\}', latex)
    ends = re.findall(r'\\end\{(\w+)\}', latex)
    if begins != ends: return False
    
    return True


def compare_rendered_vs_original(latex: str, original_image_path: str,
                                  similarity_threshold: float = 0.85) -> dict:
    """Render LaTeX and compare with original equation image."""
    import subprocess, tempfile
    from PIL import Image
    import numpy as np
    
    # Render LaTeX to image
    with tempfile.TemporaryDirectory() as tmpdir:
        tex = r"""\documentclass[preview]{standalone}
\usepackage{amsmath,amssymb}
\begin{document}
$\displaystyle %s $
\end{document}""" % latex
        tex_path = os.path.join(tmpdir, "eq.tex")
        with open(tex_path, 'w') as f:
            f.write(tex)
        
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_path],
                       capture_output=True, cwd=tmpdir, timeout=15)
        subprocess.run(["convert", "-density", "300", "eq.pdf", "eq.png"],
                       capture_output=True, cwd=tmpdir, timeout=15)
        
        rendered_path = os.path.join(tmpdir, "eq.png")
        if not os.path.exists(rendered_path):
            return {"match": False, "similarity": 0.0, "error": "render_failed"}
        
        # Compare images (structural similarity)
        from skimage.metrics import structural_similarity as ssim
        rendered = np.array(Image.open(rendered_path).convert('L').resize((256, 64)))
        original = np.array(Image.open(original_image_path).convert('L').resize((256, 64)))
        score = ssim(rendered, original)
        
        return {
            "match": score >= similarity_threshold,
            "similarity": round(score, 3),
            "threshold": similarity_threshold,
        }


def equation_completeness_check(latex: str) -> dict:
    """Check equation is complete (no truncation, all symbols resolved)."""
    issues = []
    
    # Truncation indicators
    if latex.rstrip().endswith(('...', '\\ldots', '\\cdots')):
        issues.append("possible_truncation")
    
    # Unresolved symbols
    if '[?]' in latex or 'UNKNOWN' in latex or '□' in latex:
        issues.append("unresolved_symbols")
    
    # Missing operands: operator at start/end without operand
    if re.match(r'^[+\-*/=]', latex.strip()):
        issues.append("missing_left_operand")
    if re.search(r'[+\-*/=]\s*$', latex.strip()):
        issues.append("missing_right_operand")
    
    # Grossberg-specific: check ART notation completeness
    if 'rho' in latex or '\\rho' in latex:
        if not re.search(r'\\rho\s*[<>=]', latex) and not re.search(r'\\rho\s*\(', latex):
            pass  # ρ alone is valid as a parameter reference
    
    return {"complete": len(issues) == 0, "issues": issues}
```

## 4. Output Format: Triple Representation

```python
def convert_to_triple_format(latex: str, context: str = "") -> dict:
    """Convert LaTeX to all three output formats: LaTeX + MathML + plain text."""
    
    output = {
        "latex": latex,
        "mathml": latex_to_mathml(latex),
        "plain_text": latex_to_plain_text(latex, context),
        "accessible_description": generate_accessible_description(latex),
    }
    return output


def latex_to_mathml(latex: str) -> str:
    """Convert LaTeX to MathML using latex2mathml."""
    try:
        import latex2mathml.converter
        return latex2mathml.converter.convert(latex)
    except Exception:
        return f"<!-- MathML conversion failed for: {latex[:50]} -->"


def latex_to_plain_text(latex: str, context: str = "") -> str:
    """Convert LaTeX to human-readable plain text for accessibility."""
    text = latex
    
    # Common replacements
    replacements = [
        (r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)'),
        (r'\\sqrt\{([^}]+)\}', r'sqrt(\1)'),
        (r'\\sum_\{([^}]+)\}\^\{([^}]+)\}', r'sum from \1 to \2 of'),
        (r'\\int_\{([^}]+)\}\^\{([^}]+)\}', r'integral from \1 to \2 of'),
        (r'\\partial', 'partial'),
        (r'\\infty', 'infinity'),
        (r'\\alpha', 'alpha'), (r'\\beta', 'beta'), (r'\\gamma', 'gamma'),
        (r'\\delta', 'delta'), (r'\\epsilon', 'epsilon'), (r'\\rho', 'rho'),
        (r'\\sigma', 'sigma'), (r'\\theta', 'theta'), (r'\\lambda', 'lambda'),
        (r'\\mu', 'mu'), (r'\\omega', 'omega'), (r'\\phi', 'phi'),
        (r'\\nabla', 'nabla'), (r'\\cdot', '*'), (r'\\times', 'x'),
        (r'\\leq', '<='), (r'\\geq', '>='), (r'\\neq', '!='),
        (r'\\approx', '≈'), (r'\\rightarrow', '->'), (r'\\leftarrow', '<-'),
        (r'\^(\{[^}]+\}|\w)', r'^(\1)'),  # superscripts
        (r'_(\{[^}]+\}|\w)', r'_(\1)'),    # subscripts
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    
    # Clean up remaining LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'[{}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def generate_accessible_description(latex: str) -> str:
    """Generate natural language description of equation for accessibility/RAG."""
    desc_parts = []
    
    if '\\frac' in latex:
        desc_parts.append("contains fraction")
    if '\\sum' in latex:
        desc_parts.append("contains summation")
    if '\\int' in latex:
        desc_parts.append("contains integral")
    if '\\partial' in latex:
        desc_parts.append("partial derivative")
    if 'matrix' in latex or 'bmatrix' in latex:
        desc_parts.append("matrix expression")
    if '\\rho' in latex:
        desc_parts.append("involves vigilance parameter (rho)")
    if re.search(r'\\(dot|ddot)\{', latex):
        desc_parts.append("time derivative")
    
    return "Equation " + ", ".join(desc_parts) if desc_parts else "Mathematical expression"
```

## 5. pgvector Storage Strategy

```python
from typing import List, Optional
import json

EQUATION_CHUNK_SCHEMA = """
CREATE TABLE IF NOT EXISTS equation_chunks (
    id SERIAL PRIMARY KEY,
    chapter INT NOT NULL,
    section_path TEXT,
    equation_number VARCHAR(20),
    equation_label VARCHAR(100),
    
    -- Triple representation
    latex TEXT NOT NULL,
    mathml TEXT,
    plain_text TEXT,
    accessible_description TEXT,
    
    -- Context window (surrounding text for RAG)
    context_before TEXT,          -- 2 sentences before equation
    context_after TEXT,           -- 2 sentences after equation
    variable_definitions JSONB,  -- extracted "where X = ..." definitions
    
    -- Classification
    equation_type VARCHAR(50),   -- differential, algebraic, integral, matrix, etc.
    math_domain VARCHAR(50),     -- ART, BCS, FCS, LAMINART, efficient_coding
    semantic_tags TEXT[],         -- ['vigilance', 'matching_rule', 'top_down']
    
    -- Cross-references
    cross_refs TEXT[],           -- equation numbers this eq references
    referenced_by TEXT[],        -- equations that reference this eq
    
    -- Embedding (BGE-M3 of context + plain_text description)
    vector vector(1024),
    
    -- Metadata
    page_number INT,
    parse_method VARCHAR(20),    -- marker, nougat, latex-ocr, pix2tex
    parse_quality VARCHAR(20),   -- verified, unverified, failed
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS eq_vector_idx 
    ON equation_chunks USING hnsw (vector vector_cosine_ops) 
    WITH (m=16, ef_construction=200);

-- GIN index for semantic tag filtering
CREATE INDEX IF NOT EXISTS eq_tags_idx ON equation_chunks USING gin (semantic_tags);

-- B-tree for chapter/section lookups
CREATE INDEX IF NOT EXISTS eq_chapter_idx ON equation_chunks (chapter, section_path);
"""


def store_equation_chunk(conn, equation: dict, embedder) -> int:
    """Store parsed equation in pgvector with context embedding."""
    
    # Embed: context + plain text description for semantic search
    embed_text = f"{equation.get('context_before', '')} {equation['plain_text']} {equation.get('context_after', '')}"
    vector = embedder.encode([embed_text], return_dense=True)['dense_vecs'][0].tolist()
    assert len(vector) == 1024, f"Expected 1024-dim, got {len(vector)}"
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO equation_chunks 
            (chapter, section_path, equation_number, equation_label,
             latex, mathml, plain_text, accessible_description,
             context_before, context_after, variable_definitions,
             equation_type, math_domain, semantic_tags,
             cross_refs, referenced_by, vector,
             page_number, parse_method, parse_quality)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            equation['chapter'], equation.get('section_path'),
            equation.get('equation_number'), equation.get('label'),
            equation['latex'], equation.get('mathml'), equation.get('plain_text'),
            equation.get('accessible_description'),
            equation.get('context_before'), equation.get('context_after'),
            json.dumps(equation.get('variable_definitions', {})),
            equation.get('equation_type'), equation.get('math_domain'),
            equation.get('semantic_tags', []),
            equation.get('cross_refs', []), equation.get('referenced_by', []),
            vector, equation.get('page_number'),
            equation.get('parse_method'), equation.get('parse_quality'),
        ))
        return cur.fetchone()[0]
    conn.commit()


def search_equations(conn, query_vector: list, filters: dict = None, top_k: int = 10) -> list:
    """Hybrid search: vector similarity + semantic tag filtering."""
    where_clauses = ["1=1"]
    params = [query_vector, top_k]
    
    if filters:
        if filters.get("chapter"):
            where_clauses.append("chapter = %s")
            params.insert(-1, filters["chapter"])
        if filters.get("math_domain"):
            where_clauses.append("math_domain = %s")
            params.insert(-1, filters["math_domain"])
        if filters.get("semantic_tags"):
            where_clauses.append("semantic_tags && %s")
            params.insert(-1, filters["semantic_tags"])
        if filters.get("equation_type"):
            where_clauses.append("equation_type = %s")
            params.insert(-1, filters["equation_type"])
    
    where = " AND ".join(where_clauses)
    
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, chapter, equation_number, latex, plain_text, 
                   context_before, context_after, semantic_tags,
                   1 - (vector <=> %s) AS similarity
            FROM equation_chunks
            WHERE {where}
            ORDER BY vector <=> %s
            LIMIT %s
        """, [query_vector] + params)
        return cur.fetchall()
```

## 6. Korean Math Term Glossary

```python
KOREAN_MATH_GLOSSARY = {
    # Basic operations
    "적분": "integral", "미분": "derivative", "편미분": "partial derivative",
    "급수": "series", "수열": "sequence", "극한": "limit",
    "합": "summation", "곱": "product",
    
    # Calculus & Analysis
    "미분방정식": "differential equation", "편미분방정식": "partial differential equation",
    "상미분방정식": "ordinary differential equation",
    "고유값": "eigenvalue", "고유벡터": "eigenvector",
    "야코비안": "Jacobian", "헤시안": "Hessian",
    "라플라시안": "Laplacian", "그래디언트": "gradient",
    "발산": "divergence", "회전": "curl",
    
    # Linear Algebra
    "행렬": "matrix", "벡터": "vector", "스칼라": "scalar",
    "전치": "transpose", "역행렬": "inverse matrix",
    "내적": "inner product", "외적": "outer product",
    "정규화": "normalization", "직교": "orthogonal",
    
    # Probability & Statistics
    "확률": "probability", "조건부 확률": "conditional probability",
    "사전 확률": "prior probability", "사후 확률": "posterior probability",
    "우도": "likelihood", "기대값": "expected value",
    "분산": "variance", "공분산": "covariance",
    "가우시안": "Gaussian", "정규분포": "normal distribution",
    
    # Neural/Computational
    "활성화 함수": "activation function", "가중치": "weight",
    "편향": "bias", "손실 함수": "loss function",
    "경사 하강법": "gradient descent", "역전파": "backpropagation",
    "수렴": "convergence", "안정점": "equilibrium point",
    "분기": "bifurcation", "리아푸노프 안정성": "Lyapunov stability",
    
    # Information Theory
    "엔트로피": "entropy", "상호정보량": "mutual information",
    "쿨백-라이블러 발산": "KL divergence",
    "채널 용량": "channel capacity", "부호화": "coding/encoding",
    
    # ART/Grossberg-specific
    "경계 감지": "vigilance", "범주 학습": "category learning",
    "하향식 기대": "top-down expectation", "상향식 입력": "bottom-up input",
    "공명": "resonance", "리셋": "reset",
    "보완적 부호화": "complementary coding",
}

# Reverse lookup: English → Korean
ENGLISH_TO_KOREAN = {v: k for k, v in KOREAN_MATH_GLOSSARY.items()}


def annotate_equation_korean(latex: str, plain_text: str) -> dict:
    """Add Korean annotations to equation terms."""
    korean_annotations = {}
    for en_term, ko_term in ENGLISH_TO_KOREAN.items():
        if en_term.lower() in plain_text.lower():
            korean_annotations[en_term] = ko_term
    return korean_annotations
```

## 7. Grossberg-Specific Notation Handling

```python
GROSSBERG_NOTATION = {
    # ART variables
    r'\rho': {
        "name": "vigilance parameter",
        "korean": "경계 매개변수",
        "domain": "ART",
        "description": "Controls category granularity in ART matching",
        "typical_range": "[0, 1]",
    },
    r'x_i': {
        "name": "F1 activity (input layer)",
        "korean": "F1층 활성도",
        "domain": "ART",
        "description": "Activity of i-th node in F1 (input representation) layer",
    },
    r'y_j': {
        "name": "F2 activity (category layer)",
        "korean": "F2층 활성도",
        "domain": "ART",
        "description": "Activity of j-th node in F2 (category) layer",
    },
    r'z_{ij}': {
        "name": "bottom-up weight (F1→F2)",
        "korean": "상향식 가중치",
        "domain": "ART",
        "description": "Adaptive weight from F1 node i to F2 node j",
    },
    r'z_{ji}': {
        "name": "top-down weight (F2→F1)",
        "korean": "하향식 가중치",
        "domain": "ART",
        "description": "Top-down template weight from F2 node j to F1 node i",
    },
    
    # BCS (Boundary Contour System) variables
    r'B_{ijk}': {
        "name": "BCS boundary signal",
        "korean": "BCS 경계 신호",
        "domain": "BCS",
        "description": "Boundary signal at position (i,j) for orientation k",
    },
    r'C_{ijk}': {
        "name": "BCS cooperative cell",
        "korean": "BCS 협동 세포",
        "domain": "BCS",
        "description": "Cooperative bipole cell completing boundary at (i,j,k)",
    },
    
    # FCS (Feature Contour System) variables
    r'F_{ij}': {
        "name": "FCS filling-in activity",
        "korean": "FCS 채움 활성도",
        "domain": "FCS",
        "description": "Surface brightness/color filling-in at position (i,j)",
    },
    r'D_{ij}': {
        "name": "FCS diffusion coefficient",
        "korean": "FCS 확산 계수",
        "domain": "FCS",
        "description": "Diffusion rate modulated by BCS boundary signals",
    },
    
    # LAMINART variables
    r'V_1': {
        "name": "V1 layer activity",
        "korean": "V1층 활성도",
        "domain": "LAMINART",
        "description": "Layer 2/3 excitatory activity in V1",
    },
    r'V_2': {
        "name": "V2 layer activity",
        "korean": "V2층 활성도",
        "domain": "LAMINART",
        "description": "V2 pale stripe activity for boundary grouping",
    },
    
    # Efficient Coding (cross-domain)
    r'I(X;Y)': {
        "name": "mutual information",
        "korean": "상호정보량",
        "domain": "efficient_coding",
        "description": "Mutual information between stimulus X and neural response Y",
    },
    r'\phi_i': {
        "name": "basis function",
        "korean": "기저 함수",
        "domain": "efficient_coding",
        "description": "i-th learned sparse basis function (Olshausen & Field)",
    },
}


def annotate_grossberg_notation(latex: str) -> list:
    """Identify Grossberg-specific notation in equation and return annotations."""
    annotations = []
    for pattern, info in GROSSBERG_NOTATION.items():
        # Escape for regex but handle LaTeX backslashes
        escaped = re.escape(pattern).replace(r'\\\\', r'\\')
        if re.search(escaped, latex) or pattern.replace('\\', '') in latex:
            annotations.append({
                "symbol": pattern,
                "name": info["name"],
                "korean": info["korean"],
                "domain": info["domain"],
                "description": info["description"],
            })
    return annotations


def tag_equation_domain(latex: str, context: str = "") -> str:
    """Determine which Grossberg domain an equation belongs to."""
    annotations = annotate_grossberg_notation(latex)
    if annotations:
        domains = [a["domain"] for a in annotations]
        # Return most frequent domain
        from collections import Counter
        return Counter(domains).most_common(1)[0][0]
    
    # Fallback: keyword detection in context
    domain_keywords = {
        "ART": ["vigilance", "category", "resonance", "reset", "matching rule", "F1", "F2"],
        "BCS": ["boundary", "contour", "bipole", "orientation", "edge"],
        "FCS": ["filling-in", "surface", "brightness", "diffusion"],
        "LAMINART": ["laminar", "V1", "V2", "layer 2/3", "layer 4"],
        "efficient_coding": ["sparse", "redundancy", "mutual information", "basis function"],
    }
    
    for domain, keywords in domain_keywords.items():
        if any(kw.lower() in context.lower() for kw in keywords):
            return domain
    
    return "general"
```

## 8. Full Pipeline: End-to-End

```python
def process_chapter_equations(pdf_path: str, chapter_num: int, 
                               conn, embedder, output_dir: str = "/tmp/eq_output") -> dict:
    """Full pipeline: PDF → parsed equations → pgvector storage."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    stats = {"total": 0, "verified": 0, "failed": 0, "methods": {}}
    
    # Step 1: Run Marker on full chapter
    marker_result = run_marker(pdf_path, output_dir)
    equations = marker_result["equations"]
    
    # Step 2: Classify each equation
    for eq in equations:
        classification = classify_equation(eq["latex"])
        eq.update(classification)
    
    # Step 3: Verify each equation, cascade to Nougat/LaTeX-OCR if needed
    for eq in equations:
        if not verify_latex_fast(eq["latex"]):
            # Try Nougat
            nougat = run_nougat_on_page(pdf_path, eq.get("page_number", 0))
            if nougat.get("equations"):
                eq["latex"] = nougat["equations"][0]["latex"]
                eq["parse_method"] = "nougat"
            else:
                eq["parse_method"] = "marker"
                eq["parse_quality"] = "unverified"
                stats["failed"] += 1
                continue
        
        eq["parse_method"] = eq.get("parse_method", "marker")
        eq["parse_quality"] = "verified"
        stats["verified"] += 1
    
    # Step 4: Generate triple format + annotations
    for eq in equations:
        triple = convert_to_triple_format(eq["latex"])
        eq.update(triple)
        
        eq["grossberg_annotations"] = annotate_grossberg_notation(eq["latex"])
        eq["math_domain"] = tag_equation_domain(eq["latex"], eq.get("context_before", ""))
        eq["semantic_tags"] = [a["name"] for a in eq["grossberg_annotations"]]
        eq["korean_annotations"] = annotate_equation_korean(eq["latex"], eq["plain_text"])
        eq["chapter"] = chapter_num
        
        # Completeness check
        completeness = equation_completeness_check(eq["latex"])
        eq["complete"] = completeness["complete"]
        eq["completeness_issues"] = completeness["issues"]
        
        stats["total"] += 1
        stats["methods"][eq["parse_method"]] = stats["methods"].get(eq["parse_method"], 0) + 1
    
    # Step 5: Store in pgvector
    stored_ids = []
    for eq in equations:
        if eq.get("parse_quality") != "failed":
            eq_id = store_equation_chunk(conn, eq, embedder)
            stored_ids.append(eq_id)
    
    stats["stored"] = len(stored_ids)
    
    # Step 6: Save JSON report
    import json
    report_path = os.path.join(output_dir, f"chapter_{chapter_num}_equations.json")
    with open(report_path, 'w') as f:
        json.dump({"stats": stats, "equations": equations}, f, indent=2, ensure_ascii=False)
    
    return stats


def process_all_chapters(pdf_dir: str, conn, embedder) -> dict:
    """Batch process all 20 CRMB chapters."""
    from pathlib import Path
    import glob
    
    pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    all_stats = {}
    
    for i, pdf_path in enumerate(pdfs):
        chapter_num = i + 1
        print(f"[{chapter_num}/20] Processing {Path(pdf_path).name}...")
        stats = process_chapter_equations(pdf_path, chapter_num, conn, embedder)
        all_stats[chapter_num] = stats
        print(f"  → {stats['total']} equations, {stats['verified']} verified, {stats['failed']} failed")
    
    return all_stats
```

## M4 Pro 64GB Optimization

```python
# MPS-optimized settings for Apple Silicon
MPS_CONFIG = {
    "device": "mps",
    "use_fp16": True,
    "batch_size": 32,         # Conservative for equation processing (images are large)
    "nougat_workers": 2,      # Parallel Nougat workers
    "marker_workers": 4,      # Parallel Marker workers
    "pdflatex_timeout": 15,   # Seconds per compilation
    "max_memory_gb": 48,      # Leave 16GB for system
}

# Nougat local service setup
NOUGAT_SETUP = """
# Install Nougat
pip install nougat-ocr

# Start local service (port 8503)
nougat_api --port 8503 --model 0.1.0-base &

# Or for better quality (slower):
nougat_api --port 8503 --model 0.1.0-small &
"""
```

## Dependencies

```bash
# Core
pip install marker-pdf nougat-ocr pix2tex[gui] latex2mathml
pip install pymupdf psycopg2-binary pgvector Pillow scikit-image
pip install FlagEmbedding torch tqdm

# LaTeX compilation (for verification)
brew install --cask mactex-no-gui  # or: brew install texlive

# Optional: ImageMagick for render comparison
brew install imagemagick
```

## Integration Points

- **db-pipeline**: Orchestrates this skill within full DB migration
- **paper-processor**: Provides initial PDF parsing; equation-parser handles math-specific extraction
- **rag-pipeline**: Consumes equation_chunks table for hybrid search
- **efficient-coding-domain**: Cross-domain equations (information theory, sparse coding)
- **eval-runner**: Tests equation retrieval quality

---

## 9. Cross-Domain: Efficient Coding Notation (Wei & Stocker, Barlow, Olshausen)

```python
EFFICIENT_CODING_NOTATION = {
    r'J(\theta)': {
        "name": "Fisher information matrix",
        "korean": "피셔 정보 행렬",
        "domain": "efficient_coding",
        "description": "Measures precision of neural encoding at stimulus θ",
    },
    r'p_{prior}(\theta)': {
        "name": "efficient prior",
        "korean": "효율적 사전 분포",
        "domain": "efficient_coding",
        "description": "Prior proportional to sqrt(Fisher info): p(θ) ∝ J(θ)^(1/2)",
    },
    r'I(X;Y)': {
        "name": "mutual information",
        "korean": "상호정보량",
        "domain": "efficient_coding",
        "description": "Information transmitted between stimulus X and neural response Y",
    },
    r'\phi_i': {
        "name": "sparse basis function",
        "korean": "희소 기저 함수",
        "domain": "efficient_coding",
        "description": "i-th learned basis function (Olshausen & Field 1996)",
    },
    r'g_{ij}': {
        "name": "Fisher-Rao metric tensor",
        "korean": "피셔-라오 계량 텐서",
        "domain": "efficient_coding",
        "description": "Riemannian metric on statistical manifold",
    },
    r'\nabla': {
        "name": "gradient/covariant derivative",
        "korean": "기울기/공변 미분",
        "domain": "efficient_coding",
        "description": "Gradient operator; in information geometry, covariant derivative",
    },
    r'D_{KL}': {
        "name": "KL divergence",
        "korean": "쿨백-라이블러 발산",
        "domain": "efficient_coding",
        "description": "Kullback-Leibler divergence between distributions",
    },
    r'E[\cdot]': {
        "name": "expectation operator",
        "korean": "기대값 연산자",
        "domain": "efficient_coding",
        "description": "Expected value over probability distribution",
    },
}

# Merge with Grossberg notation for unified lookup
ALL_NOTATION = {**GROSSBERG_NOTATION, **EFFICIENT_CODING_NOTATION}
```

## 10. Non-Standard Symbol Recovery

Handles Grossberg's non-standard notation that confuses standard OCR tools:

```python
NON_STANDARD_SYMBOL_MAP = {
    # Fuzzy AND (min operator) — Grossberg uses ∧ for fuzzy AND
    r'\land': r'\wedge',           # ∧ as fuzzy AND
    r'\vee': r'\vee',              # ∨ as fuzzy OR
    r'[x]^+': r'\max(x, 0)',      # Rectification [x]^+ = max(x, 0)
    r'[x]+': r'\max(x, 0)',       # Alternate OCR rendering
    r'\lceil x \rceil': r'\max(x, 0)',  # Sometimes OCR misreads rectification
    
    # Grossberg-specific shorthands
    r'STM': 'short-term memory',    # Sometimes in equations as variable name
    r'LTM': 'long-term memory',
    r'ON-cell': 'on-center cell',
    r'OFF-cell': 'off-center cell',
}

def recover_nonstandard_symbols(latex: str) -> tuple:
    """Attempt to recover non-standard symbols that OCR may have mangled.
    Returns (corrected_latex, corrections_made)."""
    corrections = []
    corrected = latex
    
    # [x]^+ rectification pattern (multiple OCR variants)
    rect_patterns = [
        (r'\[(\w+)\]\^?\+', r'\\max(\1, 0)'),       # [x]+ or [x]^+
        (r'\[([^]]+)\]\^?\{?\+\}?', r'\\max(\1, 0)'), # [expr]^{+}
    ]
    for pattern, replacement in rect_patterns:
        if re.search(pattern, corrected):
            corrected = re.sub(pattern, replacement, corrected)
            corrections.append(f"rectification: {pattern} → max(·, 0)")
    
    # Fuzzy AND: ∧ might be parsed as logical AND instead of min
    if r'\wedge' in corrected or r'\land' in corrected:
        # In Grossberg context, ∧ = min (fuzzy AND)
        corrections.append("fuzzy_AND: ∧ interpreted as min operator")
    
    # Missing subscript braces: B_ijk → B_{ijk}
    corrected = re.sub(r'([A-Z])_([a-z]{2,})', r'\1_{\2}', corrected)
    if corrected != latex:
        corrections.append("subscript_braces: added {} around multi-char subscripts")
    
    return corrected, corrections
```

## 11. Cross-Domain Equation Linking

```python
CROSS_DOMAIN_BRIDGES = {
    ("ART_vigilance", "Fisher_information"): {
        "relationship": "precision_analogy",
        "explanation": "ART vigilance ρ controls matching precision; Fisher info J(θ) quantifies encoding precision. Both serve as precision parameters in their respective frameworks.",
        "korean": "ART 경계 매개변수(ρ)와 피셔 정보(J(θ))는 각각의 프레임워크에서 정밀도 매개변수로 기능합니다.",
        "crmb_chapter": 3,
        "ec_paper": "Wei & Stocker 2015",
    },
    ("BCS_orientation", "sparse_basis"): {
        "relationship": "representation_analogy",
        "explanation": "BCS orientation columns detect oriented edges; sparse coding basis functions φ_i learn oriented Gabor-like filters. Both achieve orientation selectivity.",
        "korean": "BCS 방위 컬럼과 희소 부호화 기저 함수는 모두 방위 선택성을 구현합니다.",
        "crmb_chapter": 5,
        "ec_paper": "Olshausen & Field 1996",
    },
    ("FCS_diffusion", "efficient_representation"): {
        "relationship": "efficiency_analogy",
        "explanation": "FCS filling-in uses boundary-gated diffusion for efficient surface representation; efficient coding minimizes redundancy in neural representation.",
        "korean": "FCS 채움과 효율적 부호화는 모두 신경 표상의 효율성을 추구합니다.",
        "crmb_chapter": 5,
        "ec_paper": "Barlow 1961",
    },
}

def find_cross_domain_links(eq_a_domain: str, eq_b_domain: str, 
                             eq_a_tags: list, eq_b_tags: list) -> list:
    """Find cross-domain bridges between two equations from different domains."""
    links = []
    for (concept_a, concept_b), bridge in CROSS_DOMAIN_BRIDGES.items():
        a_match = any(concept_a.lower() in tag.lower() for tag in eq_a_tags)
        b_match = any(concept_b.lower() in tag.lower() for tag in eq_b_tags)
        if (a_match and b_match) or (b_match and a_match):
            links.append(bridge)
    return links
```


## Skill Interface: Output Schema

This skill produces standardized JSON output consumed by downstream skills (rag-pipeline, sci-post-gen).

```python
EQUATION_OUTPUT_SCHEMA = {
    "request_id": "uuid4",  # Correlation ID for tracing
    "embedding_config": {
        "model": "BAAI/bge-m3",
        "dimension": 1024,
        "device": "mps",
    },
    "equations": [{
        "latex": str,
        "mathml": str,
        "plain_text": str,
        "equation_number": str,
        "domain": str,  # ART, BCS, FCS, LAMINART, efficient_coding
        "semantic_tags": list,
        "cross_refs": list,
        "context_before": str,
        "context_after": str,
        "parse_method": str,
        "parse_quality": str,
        "korean_annotations": dict,
    }],
    "citation": {
        "source_type": str,  # "crmb_chapter" or "paper"
        "chapter": int,
        "authors": str,
        "year": int,
        "title": str,
        "page": int,
    }
}
```

**Output contract:** All equations include LaTeX, MathML, and plain-text representations. Citations are required for traceability. Request IDs enable cross-skill correlation logging.


## 12. Resilience: Checkpoint & Recovery

### Checkpoint System
Per-page progress tracking with resume capability:

```python
import json, os

class EquationCheckpoint:
    def __init__(self, checkpoint_path="./eq_checkpoint.json"):
        self.path = checkpoint_path
        self.state = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f: return json.load(f)
        return {"completed_pages": [], "failed_pages": [], "last_chapter": 0}
    
    def save(self): 
        with open(self.path, 'w') as f: json.dump(self.state, f)
    
    def should_process(self, chapter, page):
        return f"{chapter}_{page}" not in self.state["completed_pages"]
    
    def mark_done(self, chapter, page):
        self.state["completed_pages"].append(f"{chapter}_{page}")
        self.save()
    
    def mark_failed(self, chapter, page, error):
        self.state["failed_pages"].append({"id": f"{chapter}_{page}", "error": str(error)})
        self.save()
```

### Cross-Page Equation Stitching
Detect and merge split equations across page boundaries:

```python
def stitch_cross_page_equations(page_a_eqs, page_b_eqs):
    # Detect: last eq on page_a has unmatched { or missing \end
    # Merge with first eq on page_b if continuation pattern found
    # Verify merged equation compiles and renders correctly
    pass
```

### Nougat Crash Recovery
Retry with exponential backoff, fallback to LaTeX-OCR:

```python
import time

def nougat_with_retry(pdf_path, page, max_retries=3):
    for attempt in range(max_retries):
        try:
            return run_nougat_on_page(pdf_path, page)
        except Exception:
            time.sleep(2 ** attempt)
    return run_latex_ocr_from_page(pdf_path, page)
```

### Unicode Sanitization
Fix garbled Greek symbols and diacritics:

```python
UNICODE_FIXES = {
    'Î±': 'α', 'Î²': 'β', 'Î³': 'γ', 'Ï': 'ρ',
    'Î¸': 'θ', 'Ï†': 'φ', 'Î»': 'λ', 'Ï€': 'π'
}

def sanitize_unicode(text):
    for garbled, clean in UNICODE_FIXES.items():
        text = text.replace(garbled, clean)
    return text
```
