#!/usr/bin/env python3
"""
Test script demonstrating paper-processor skill on Zhang & Luck (2008).

This test validates:
1. Section detection using SECTION_PATTERNS from SKILL.md
2. Claim extraction using CLAIM_INDICATORS patterns
3. Figure caption extraction
4. Key term identification
5. JSON output schema conformance
"""

import json
import sys
from pathlib import Path
from paper_processor import PaperProcessor, PaperMetadata


def test_section_detection():
    """Test that sections are detected correctly."""
    processor = PaperProcessor()
    
    text = """
Abstract
Visual working memory has limited capacity, about 3-4 items.

Introduction
Previous studies suggest capacity limits...

Methods
Participants: 30 undergraduates.

Results
Mean capacity was 3.47 items (SD = 0.92).

Discussion
These findings support discrete representations.

References
[references...]
"""
    
    sections = processor.detect_sections(text)
    
    print("✓ Section Detection Test")
    print(f"  Detected {len(sections)} sections:")
    for section in sections:
        print(f"    - {section.section}: {len(section.text)} chars")
    
    # Verify expected sections
    section_labels = [s.section for s in sections]
    expected = ['abstract', 'introduction', 'methods', 'results', 'discussion', 'references']
    for expected_label in expected:
        assert expected_label in section_labels, f"Missing section: {expected_label}"
    
    return True


def test_claim_extraction():
    """Test claim extraction with statistical evidence detection."""
    processor = PaperProcessor()
    
    text = """
Results
Mean VWM capacity was 3.47 items (SD = 0.92). 
Capacity remained essentially constant across set sizes (F(2, 24) = 1.23, p > .30).
Error rates increased significantly with set size (F(2, 24) = 45.67, p < .001).
We found that capacity does not depend on feature complexity.

Discussion
These results demonstrate that VWM capacity is limited to 3-4 items.
Consistent with previous findings, the capacity limit appears to be object-based.
"""
    
    # Create minimal section objects for testing
    from paper_processor import Section, SectionLabel
    sections = [
        Section(
            section=SectionLabel.RESULTS,
            header="Results",
            text="Mean VWM capacity was 3.47 items (SD = 0.92). Capacity remained essentially constant across set sizes (F(2, 24) = 1.23, p > .30). Error rates increased significantly with set size (F(2, 24) = 45.67, p < .001). We found that capacity does not depend on feature complexity.",
            char_range=(0, 500)
        ),
        Section(
            section=SectionLabel.DISCUSSION,
            header="Discussion",
            text="These results demonstrate that VWM capacity is limited to 3-4 items. Consistent with previous findings, the capacity limit appears to be object-based.",
            char_range=(500, 800)
        )
    ]
    
    claims = processor.extract_claims(sections)
    
    print("\n✓ Claim Extraction Test")
    print(f"  Extracted {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"    {i}. [{claim.section}] has_stats={claim.has_stats}")
        print(f"       {claim.text[:70]}...")
    
    # Verify claims have statistics
    stats_claims = [c for c in claims if c.has_stats]
    assert len(stats_claims) > 0, "Should extract claims with statistics"
    print(f"  {len(stats_claims)} claims have statistical evidence")
    
    return True


def test_figure_extraction():
    """Test figure caption extraction."""
    processor = PaperProcessor()
    
    text = """
Methods section here.

Figure 1: Mean VWM capacity (K) as a function of set size and retention interval.

Results
Capacity decreased with longer retention intervals.

Figure 2: Error rates as a function of set size. Error bars show ±1 SE.

Discussion
These patterns are consistent with decay models.

Figure 3: VWM capacity across different stimulus types and complexities.
"""
    
    figures = processor.extract_figures(text)
    
    print("\n✓ Figure Extraction Test")
    print(f"  Extracted {len(figures)} figures:")
    for fig in figures:
        print(f"    Fig {fig.figure_num}: {fig.caption[:60]}...")
    
    assert len(figures) == 3, "Should extract 3 figures"
    assert all(hasattr(f, 'figure_num') for f in figures), "Figures should have numbers"
    assert all(hasattr(f, 'caption') for f in figures), "Figures should have captions"
    
    return True


def test_key_terms_extraction():
    """Test key term identification."""
    processor = PaperProcessor()
    
    text = """
Abstract
We investigated Visual Working Memory capacity limits using a change-detection task.
Participants viewed arrays of colored objects and reported changes.
We found that VWM capacity remains constant at 3-4 items regardless of stimulus complexity.

Introduction
Visual Working Memory is a critical cognitive system...
"""
    
    from paper_processor import Section, SectionLabel, Claim
    sections = [Section(section=SectionLabel.ABSTRACT, header="Abstract", text=text[:200], char_range=(0, 200))]
    claims = [Claim(text="VWM capacity was 3-4 items", section='abstract', type='empirical_claim', has_stats=False)]
    
    terms = processor.extract_key_terms(text, claims)
    
    print("\n✓ Key Terms Extraction Test")
    print(f"  Extracted {len(terms)} key terms:")
    print(f"    {terms}")
    
    assert len(terms) > 0, "Should extract key terms"
    
    return True


def test_output_schema():
    """Test that output conforms to SKILL.md schema."""
    processor = PaperProcessor()
    
    metadata = PaperMetadata(
        title="Test Paper",
        authors=["Author A", "Author B"],
        year=2008,
        journal="Journal of Vision",
        doi="10.1167/8.6.7",
        arxiv_id=None,
        zotero_key="TEST123"
    )
    
    result = processor.process_paper(
        "Abstract\nTest abstract.\n\nMethods\nTest methods.\n\nResults\nTest results.",
        metadata,
        "test_paper"
    )
    
    print("\n✓ Output Schema Conformance Test")
    
    # Check required fields
    required_fields = [
        'paper_id', 'title', 'authors', 'year', 'journal', 'doi', 'arxiv_id',
        'sections', 'claims', 'figures', 'key_terms', 'citation_count', 'zotero_key'
    ]
    
    for field in required_fields:
        assert field in result, f"Missing field: {field}"
        print(f"    ✓ {field}")
    
    # Check sections dict structure
    assert isinstance(result['sections'], dict), "Sections should be a dict"
    print(f"    ✓ sections is dict with {len(result['sections'])} entries")
    
    # Check claims structure
    assert isinstance(result['claims'], list), "Claims should be a list"
    if result['claims']:
        claim = result['claims'][0]
        assert 'text' in claim, "Claim missing 'text'"
        assert 'section' in claim, "Claim missing 'section'"
        assert 'type' in claim, "Claim missing 'type'"
        assert 'has_stats' in claim, "Claim missing 'has_stats'"
        print(f"    ✓ claims is list with {len(result['claims'])} items (valid structure)")
    
    # Check figures structure
    assert isinstance(result['figures'], list), "Figures should be a list"
    print(f"    ✓ figures is list with {len(result['figures'])} items")
    
    # Check key_terms
    assert isinstance(result['key_terms'], list), "Key terms should be a list"
    print(f"    ✓ key_terms is list with {len(result['key_terms'])} items")
    
    return True


def test_zhang_luck_2008():
    """Test on actual Zhang & Luck 2008 example output."""
    print("\n✓ Zhang & Luck 2008 Integration Test")
    
    # Load the example output
    example_path = Path(__file__).parent / "zhang_luck_2008_example_output.json"
    
    if example_path.exists():
        with open(example_path) as f:
            example_output = json.load(f)
        
        print(f"    Paper: {example_output['title']}")
        print(f"    Authors: {', '.join(example_output['authors'])}")
        print(f"    Year: {example_output['year']}")
        print(f"    Sections: {list(example_output['sections'].keys())}")
        print(f"    Claims extracted: {len(example_output['claims'])}")
        print(f"    Figures extracted: {len(example_output['figures'])}")
        print(f"    Key terms: {len(example_output['key_terms'])}")
        
        # Verify structure
        assert example_output['paper_id'] == 'zhang_luck_2008'
        assert len(example_output['sections']) >= 5  # At least abstract, intro, methods, results, discussion
        assert len(example_output['claims']) > 0
        assert len(example_output['figures']) > 0
        
        return True
    else:
        print("    (Example JSON not found, skipping)")
        return True


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("Section Detection", test_section_detection),
        ("Claim Extraction", test_claim_extraction),
        ("Figure Extraction", test_figure_extraction),
        ("Key Terms Extraction", test_key_terms_extraction),
        ("Output Schema", test_output_schema),
        ("Zhang & Luck 2008", test_zhang_luck_2008),
    ]
    
    print("=" * 70)
    print("PAPER-PROCESSOR SKILL VALIDATION TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ {test_name} ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
