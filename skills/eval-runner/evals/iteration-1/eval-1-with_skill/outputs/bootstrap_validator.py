#!/usr/bin/env python3
"""
Bootstrap Ground Truth Dataset Validator

Validates the structure and content of the CRMB textbook ground truth dataset.
Ensures all queries follow required schema and contain essential fields.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


class BootstrapValidator:
    """Validator for ground truth query datasets."""
    
    # Required fields for each query
    REQUIRED_QUERY_FIELDS = {
        'id': str,
        'query_en': str,
        'query_ko': str,
        'relevant_papers': list,
        'relevant_sections': list,
        'difficulty': str,
        'domain': str
    }
    
    # Valid difficulty levels
    VALID_DIFFICULTIES = {'undergrad', 'master', 'phd'}
    
    # Valid domains
    VALID_DOMAINS = {
        'sensory_neuroscience',
        'systems_neuroscience',
        'cellular_neuroscience',
        'developmental_neuroscience',
        'computational_neuroscience',
        'neuroimaging'
    }
    
    def __init__(self, json_path: str):
        """Initialize validator with path to JSON file."""
        self.json_path = Path(json_path)
        self.data = None
        self.errors = []
        self.warnings = []
        
    def load_json(self) -> bool:
        """Load and parse JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except FileNotFoundError:
            self.errors.append(f"File not found: {self.json_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON parse error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading file: {e}")
            return False
    
    def validate_metadata(self) -> bool:
        """Validate dataset metadata."""
        if 'metadata' not in self.data:
            self.errors.append("Missing 'metadata' section")
            return False
        
        metadata = self.data['metadata']
        required_meta = ['dataset_name', 'num_chapters', 'num_queries', 'institution']
        
        for field in required_meta:
            if field not in metadata:
                self.errors.append(f"Missing metadata field: {field}")
                return False
        
        # Check that num_chapters matches actual chapters
        actual_chapters = len(self.data.get('chapters', {}))
        declared_chapters = metadata.get('num_chapters', 0)
        if actual_chapters != declared_chapters:
            self.warnings.append(
                f"Chapter count mismatch: declared {declared_chapters}, "
                f"found {actual_chapters}"
            )
        
        return len(self.errors) == 0
    
    def validate_chapters(self) -> bool:
        """Validate chapter structure."""
        if 'chapters' not in self.data:
            self.errors.append("Missing 'chapters' section")
            return False
        
        chapters = self.data['chapters']
        if not chapters:
            self.errors.append("No chapters found in dataset")
            return False
        
        total_queries = 0
        
        for chapter_id, chapter_data in chapters.items():
            # Validate chapter has required fields
            if 'name' not in chapter_data:
                self.errors.append(f"Chapter {chapter_id} missing 'name'")
                continue
            
            if 'queries' not in chapter_data:
                self.errors.append(f"Chapter {chapter_id} ({chapter_data['name']}) missing 'queries'")
                continue
            
            queries = chapter_data['queries']
            if not isinstance(queries, list):
                self.errors.append(
                    f"Chapter {chapter_id} queries must be a list, "
                    f"got {type(queries).__name__}"
                )
                continue
            
            total_queries += len(queries)
            
            # Validate each query
            for query_idx, query in enumerate(queries):
                self._validate_query(query, chapter_id, query_idx)
        
        # Check total queries
        declared_queries = self.data.get('metadata', {}).get('num_queries', 0)
        if total_queries != declared_queries:
            self.warnings.append(
                f"Query count mismatch: declared {declared_queries}, "
                f"found {total_queries}"
            )
        
        return len(self.errors) == 0
    
    def _validate_query(self, query: Dict[str, Any], chapter_id: str, 
                       query_idx: int) -> None:
        """Validate individual query structure."""
        context = f"Chapter {chapter_id}, Query {query_idx}"
        
        # Check all required fields are present
        for field, expected_type in self.REQUIRED_QUERY_FIELDS.items():
            if field not in query:
                self.errors.append(f"{context}: Missing field '{field}'")
                continue
            
            # Type checking
            value = query[field]
            if not isinstance(value, expected_type):
                self.errors.append(
                    f"{context} field '{field}': expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
        
        # Validate specific field values
        if 'difficulty' in query:
            if query['difficulty'] not in self.VALID_DIFFICULTIES:
                self.errors.append(
                    f"{context}: Invalid difficulty '{query['difficulty']}'. "
                    f"Must be one of {self.VALID_DIFFICULTIES}"
                )
        
        if 'domain' in query:
            if query['domain'] not in self.VALID_DOMAINS:
                self.errors.append(
                    f"{context}: Invalid domain '{query['domain']}'. "
                    f"Must be one of {self.VALID_DOMAINS}"
                )
        
        # Validate list fields are non-empty
        if 'relevant_papers' in query:
            if not query['relevant_papers']:
                self.warnings.append(
                    f"{context}: Empty relevant_papers list"
                )
        
        if 'relevant_sections' in query:
            if not query['relevant_sections']:
                self.warnings.append(
                    f"{context}: Empty relevant_sections list"
                )
        
        # Validate text fields are non-empty
        if 'query_en' in query and not query['query_en'].strip():
            self.errors.append(f"{context}: Empty query_en")
        
        if 'query_ko' in query and not query['query_ko'].strip():
            self.errors.append(f"{context}: Empty query_ko")
    
    def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations."""
        if not self.load_json():
            return False, self._generate_report()
        
        self.validate_metadata()
        self.validate_chapters()
        
        return len(self.errors) == 0, self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            'valid': len(self.errors) == 0,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """Print formatted validation report."""
        print("\n" + "="*70)
        print("BOOTSTRAP GROUND TRUTH VALIDATION REPORT")
        print("="*70)
        
        status = "✓ PASSED" if report['valid'] else "✗ FAILED"
        print(f"\nStatus: {status}")
        print(f"Errors: {report['total_errors']}")
        print(f"Warnings: {report['total_warnings']}")
        
        if report['errors']:
            print("\n" + "-"*70)
            print("ERRORS:")
            print("-"*70)
            for error in report['errors']:
                print(f"  • {error}")
        
        if report['warnings']:
            print("\n" + "-"*70)
            print("WARNINGS:")
            print("-"*70)
            for warning in report['warnings']:
                print(f"  • {warning}")
        
        if not report['errors'] and not report['warnings']:
            print("\n✓ All validations passed!")
        
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python bootstrap_validator.py <path_to_json>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    validator = BootstrapValidator(json_path)
    valid, report = validator.validate_all()
    validator.print_report(report)
    
    sys.exit(0 if valid else 1)


if __name__ == '__main__':
    main()
