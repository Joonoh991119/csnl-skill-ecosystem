---
name: ontology-rag
description: |
  Ontology-augmented RAG for CRMB using concept graphs, hybrid retrieval (vector + graph),
  and chunk-to-ontology linking. Build domain ontologies from chapters, expand queries via
  is-a/part-of/causes relations, perform SPARQL-like traversal, and boost LanceDB search with
  ontology metadata. Supports efficient coding theory extension.
triggers:
  - ontology construction
  - ontology-augmented retrieval
  - concept graph expansion
  - SPARQL-like query
  - hybrid RAG search
  - LanceDB ontology pipeline
  - efficient coding integration
---

# Ontology-Augmented RAG for CRMB

Build adaptive resonance theory (ART) concept ontologies from Grossberg's CRMB chapters and use them to augment vector retrieval with graph-based re-ranking and query expansion.

## Overview

This skill implements a complete ontology-augmented RAG pipeline:

1. **Ontology Construction** — Extract hierarchical concept graphs from CRMB chapters (ART, BCS/FCS, LAMINART, etc.)
2. **Query Expansion** — Traverse concept relations (is-a, part-of, causes) to broaden retrieval scope
3. **Hybrid Retrieval** — Combine BGE-M3 embeddings (1024-dim) with graph-based re-ranking via LanceDB
4. **Chunk Linking** — Tag each RAG chunk with ontology node IDs for structured filtering
5. **LanceDB Pipeline** — Metadata-rich table creation with ontology boost weights
6. **Domain Extension** — Integrate efficient coding theory as a second domain

## Key Components

### 1. Ontology Construction from Chapters

Extract is-a, part-of, and causes relations from CRMB text:

```python
from typing import Dict, List, Tuple
import re
import networkx as nx

class OntologyBuilder:
    """Extract concept ontologies from CRMB chapters."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.chapters = {
            "ART": "Adaptive Resonance Theory foundations",
            "BCS/FCS": "Boundary Contour System / Feature Contour System",
            "LAMINART": "Laminar Automated Network Technology",
            "nart": "Neural ARTmap with hierarchical learning",
        }
    
    def extract_relations(self, chapter_text: str, chapter_name: str) -> Dict:
        """Extract concept relations using pattern matching and NLP."""
        relations = {"is_a": [], "part_of": [], "causes": []}
        
        # Pattern: "X is a type of Y" or "X is-a Y"
        is_a_pattern = r"(\w+(?:\s+\w+)*?)\s+(?:is\s+a|is-a|type of)\s+(\w+(?:\s+\w+)*?)"
        for match in re.finditer(is_a_pattern, chapter_text, re.IGNORECASE):
            child, parent = match.groups()
            relations["is_a"].append((child.strip(), parent.strip(), chapter_name))
            self.graph.add_edge(child.strip(), parent.strip(), relation="is_a", source=chapter_name)
        
        # Pattern: "X is part of Y"
        part_pattern = r"(\w+(?:\s+\w+)*?)\s+(?:is part of|comprise|contain)\s+(\w+(?:\s+\w+)*?)"
        for match in re.finditer(part_pattern, chapter_text, re.IGNORECASE):
            child, parent = match.groups()
            relations["part_of"].append((child.strip(), parent.strip(), chapter_name))
            self.graph.add_edge(child.strip(), parent.strip(), relation="part_of", source=chapter_name)
        
        # Pattern: "X causes Y" or "X triggers Y"
        causes_pattern = r"(\w+(?:\s+\w+)*?)\s+(?:causes|triggers|initiates)\s+(\w+(?:\s+\w+)*?)"
        for match in re.finditer(causes_pattern, chapter_text, re.IGNORECASE):
            cause, effect = match.groups()
            relations["causes"].append((cause.strip(), effect.strip(), chapter_name))
            self.graph.add_edge(cause.strip(), effect.strip(), relation="causes", source=chapter_name)
        
        return relations
    
    def add_chapter(self, chapter_name: str, chapter_text: str):
        """Build ontology from a chapter."""
        relations = self.extract_relations(chapter_text, chapter_name)
        print(f"[{chapter_name}] Extracted {len(relations['is_a'])} is-a, "
              f"{len(relations['part_of'])} part-of, {len(relations['causes'])} causes relations")
        return relations
    
    def get_ancestors(self, node: str, relation: str = None) -> List[str]:
        """Get all ancestor nodes via specified relation type."""
        ancestors = []
        visited = set()
        
        def dfs(current):
            if current in visited:
                return
            visited.add(current)
            
            for successor in self.graph.successors(current):
                edge = self.graph[current][successor]
                if relation is None or edge.get("relation") == relation:
                    ancestors.append(successor)
                    dfs(successor)
        
        dfs(node)
        return list(set(ancestors))
    
    def multi_hop_query(self, concept: str, max_hops: int = 3) -> Dict:
        """SPARQL-like traversal: expand concept via all relation types."""
        result = {"original": concept, "expansion": {}}
        current_level = [concept]
        
        for hop in range(1, max_hops + 1):
            next_level = set()
            for node in current_level:
                for successor in self.graph.successors(node):
                    edge = self.graph[node][successor]
                    relation = edge.get("relation", "related")
                    if relation not in result["expansion"]:
                        result["expansion"][relation] = []
                    result["expansion"][relation].append(successor)
                    next_level.add(successor)
            current_level = list(next_level)
            if not current_level:
                break
        
        return result
```

### 2. Ontology-Augmented Query Expansion

Expand queries using the concept graph:

```python
class QueryExpander:
    """Expand queries via ontology traversal."""
    
    def __init__(self, ontology_builder: OntologyBuilder):
        self.builder = ontology_builder
    
    def expand_query(self, query: str, max_terms: int = 10) -> Dict:
        """Expand query by finding related ontology concepts."""
        # Simple concept extraction (in production, use NER or embedding similarity)
        concepts = self._extract_concepts(query)
        
        expanded = {"original": query, "concepts": {}}
        for concept in concepts:
            if concept in self.builder.graph:
                ancestors = self.builder.get_ancestors(concept, relation="is_a")
                children = list(self.builder.graph.predecessors(concept))
                
                expanded["concepts"][concept] = {
                    "parents": ancestors[:3],
                    "children": children[:3],
                }
        
        # Flatten expansion into additional search terms
        all_terms = set([query])
        for concept_data in expanded["concepts"].values():
            all_terms.update(concept_data.get("parents", []))
            all_terms.update(concept_data.get("children", []))
        
        expanded["search_terms"] = list(all_terms)[:max_terms]
        return expanded
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract concept mentions (stub: use NER in production)."""
        concepts = []
        for node in self.builder.graph.nodes():
            if node.lower() in text.lower():
                concepts.append(node)
        return concepts
```

### 3. Chunk-to-Ontology Linking

Tag RAG chunks with ontology metadata:

```python
class ChunkOntologyLinker:
    """Link RAG chunks to ontology concepts."""
    
    def __init__(self, builder: OntologyBuilder, embeddings_model):
        self.builder = builder
        self.embeddings_model = embeddings_model
    
    def link_chunk(self, chunk_id: str, chunk_text: str, source_chapter: str) -> Dict:
        """Assign ontology concepts to a chunk using text matching and embeddings."""
        # Concept extraction: match node names in chunk text
        matched_concepts = []
        for node in self.builder.graph.nodes():
            if node.lower() in chunk_text.lower():
                matched_concepts.append(node)
        
        # Embedding-based concept assignment (1024-dim BGE-M3)
        chunk_embedding = self.embeddings_model.encode(chunk_text, return_dense=True, return_sparse=True)
        
        # Concept embeddings
        concept_embeddings = {}
        for concept in self.builder.graph.nodes():
            concept_embeddings[concept] = self.embeddings_model.encode(
                concept, return_dense=True, return_sparse=True
            )
        
        # Find closest concepts by cosine similarity (dense embeddings)
        import numpy as np
        chunk_dense = chunk_embedding["dense_vecs"]
        similarities = {}
        for concept, emb in concept_embeddings.items():
            sim = np.dot(chunk_dense, emb["dense_vecs"]) / (
                np.linalg.norm(chunk_dense) * np.linalg.norm(emb["dense_vecs"]) + 1e-8
            )
            similarities[concept] = sim
        
        top_concepts = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "chunk_id": chunk_id,
            "source_chapter": source_chapter,
            "matched_concepts": matched_concepts,
            "embedding_top_concepts": [c[0] for c in top_concepts],
            "concept_scores": {c[0]: float(c[1]) for c in top_concepts},
        }
```

### 4. LanceDB Hybrid Search Pipeline

Create tables with ontology metadata and enable hybrid search:

```python
import lancedb
import pandas as pd

class LanceDBOntologyPipeline:
    """Hybrid RAG pipeline with ontology boost in LanceDB."""
    
    def __init__(self, db_path: str = "/tmp/crmb_rag.db"):
        self.db = lancedb.connect(db_path)
    
    def create_table(self, chunks: List[Dict], ontology_builder: OntologyBuilder):
        """Create LanceDB table with ontology metadata columns."""
        rows = []
        
        for chunk in chunks:
            # Each chunk has: id, text, source_chapter, concept_ids
            chunk_embedding = self._embed_text(chunk["text"])
            
            # Calculate ontology boost: sum of importance scores of linked concepts
            ontology_boost = 0.0
            for concept_id in chunk.get("concept_ids", []):
                if concept_id in ontology_builder.graph:
                    # In-degree as importance (more connections = more central)
                    in_degree = ontology_builder.graph.in_degree(concept_id)
                    ontology_boost += in_degree * 0.1
            
            rows.append({
                "chunk_id": chunk["id"],
                "text": chunk["text"],
                "source_chapter": chunk["source_chapter"],
                "concept_ids": chunk.get("concept_ids", []),
                "embedding": chunk_embedding,
                "ontology_boost": min(ontology_boost, 2.0),  # Cap at 2.0
            })
        
        df = pd.DataFrame(rows)
        table = self.db.create_table("chunks", data=df, mode="overwrite")
        print(f"Created LanceDB table with {len(df)} chunks")
        return table
    
    def hybrid_search(self, query: str, expander: QueryExpander, k: int = 10) -> List[Dict]:
        """Hybrid search: vector + ontology boost."""
        # Expand query via ontology
        expanded = expander.expand_query(query)
        search_terms = expanded["search_terms"]
        
        # Vector search on expanded terms
        query_embedding = self._embed_text(" ".join(search_terms))
        
        table = self.db.open_table("chunks")
        
        # LanceDB vector search
        results = table.search(query_embedding).limit(k * 2).to_list()
        
        # Re-rank by ontology boost
        for result in results:
            result["score"] = result.get("_distance", 0.5) + result.get("ontology_boost", 0.0) * 0.3
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def _embed_text(self, text: str):
        """Embed using BGE-M3 (stub)."""
        from FlagEmbedding import BGEM3FlagModel
        model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
        embeddings = model.encode([text], return_dense=True, return_sparse=True)
        return embeddings["dense_vecs"][0]
```

### 5. Efficient Coding Integration

Extend ontology with efficient coding theory concepts:

```python
class EfficientCodingDomain:
    """Extend CRMB ontology with efficient coding theory."""
    
    CODING_CONCEPTS = {
        "efficient_coding": "Optimal information representation",
        "sparse_coding": "Minimal active neurons for representation",
        "predictive_coding": "Prediction error minimization",
        "information_bottleneck": "Trade-off between compression and prediction",
    }
    
    CODING_RELATIONS = [
        # (source, target, relation_type)
        ("sparse_coding", "efficient_coding", "is_a"),
        ("predictive_coding", "efficient_coding", "is_a"),
        ("information_bottleneck", "efficient_coding", "related_to"),
        ("ART", "predictive_coding", "shares_principle"),  # Link to CRMB
        ("BCS/FCS", "sparse_coding", "implements"),
    ]
    
    @staticmethod
    def extend_ontology(builder: OntologyBuilder) -> OntologyBuilder:
        """Add efficient coding concepts and relations to CRMB ontology."""
        # Add nodes
        for concept, description in EfficientCodingDomain.CODING_CONCEPTS.items():
            builder.graph.add_node(concept, description=description, domain="efficient_coding")
        
        # Add relations
        for source, target, relation in EfficientCodingDomain.CODING_RELATIONS:
            builder.graph.add_edge(source, target, relation=relation, source="efficient_coding")
        
        print(f"Extended ontology with {len(EfficientCodingDomain.CODING_CONCEPTS)} efficient coding concepts")
        return builder
```

## Robustness & Edge Cases

Production ontology systems must handle cycles, orphans, multi-hop complexity, diverse query patterns, and multilingual data. This section adds essential robustness features.

### 1. Cycle Detection & Reporting

Identify circular dependencies in the concept graph using depth-first search with back-edge detection:

```python
class CycleDetector:
    """Detect and report cycles in the ontology graph."""
    
    def __init__(self, graph):
        self.graph = graph
        self.cycles = []
    
    def detect_cycles(self) -> List[List[str]]:
        """
        Find all cycles using DFS with back-edge detection.
        Returns: List of cycle paths, e.g., [['A', 'B', 'C', 'A'], ['X', 'Y', 'X']]
        """
        visited = set()
        rec_stack = set()
        parent_map = {}
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph.successors(node):
                if neighbor not in visited:
                    parent_map[neighbor] = node
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Back edge found: cycle detected
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    if cycle not in self.cycles:
                        self.cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in self.graph.nodes():
            if node not in visited:
                dfs(node, [])
        
        return self.cycles
    
    def report_cycles_to_user(self) -> str:
        """Format cycles as readable warnings for user display."""
        if not self.cycles:
            return "✓ No cycles detected. Ontology is acyclic."
        
        report = f"⚠ Found {len(self.cycles)} cycle(s):\n"
        for i, cycle in enumerate(self.cycles, 1):
            path_str = " → ".join(cycle)
            report += f"  Cycle {i}: {path_str}\n"
        
        report += "\nRecommendation: Review these relations and remove edges to break cycles.\n"
        return report
```

### 2. Orphan Node Handling

Identify disconnected concepts and apply strategies for handling them:

```python
class OrphanNodeHandler:
    """Find and handle disconnected concepts in the ontology."""
    
    STRATEGIES = ["warn", "auto_connect_to_root", "exclude_with_log"]
    
    def __init__(self, graph, root_nodes=None):
        self.graph = graph
        self.root_nodes = root_nodes or ["ART", "BCS/FCS", "LAMINART"]
        self.orphans = []
    
    def find_orphan_nodes(self) -> List[str]:
        """
        Identify nodes with no incoming or outgoing edges.
        Returns: List of orphan node names
        """
        self.orphans = []
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            # Orphan: no connections at all, or only self-loops
            if in_degree + out_degree == 0:
                self.orphans.append(node)
        
        return self.orphans
    
    def handle_orphans(self, strategy: str = "warn") -> Dict:
        """
        Apply strategy to orphan nodes.
        Strategies:
          - 'warn': Log warnings for orphans (no modification)
          - 'auto_connect_to_root': Connect orphans to nearest root
          - 'exclude_with_log': Remove orphans and log them
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        self.find_orphan_nodes()
        report = {"strategy": strategy, "orphans": self.orphans, "actions": []}
        
        if strategy == "warn":
            for orphan in self.orphans:
                report["actions"].append(f"WARNING: {orphan} is disconnected")
        
        elif strategy == "auto_connect_to_root":
            for orphan in self.orphans:
                # Connect to nearest root node
                target_root = self.root_nodes[0] if self.root_nodes else "ROOT"
                self.graph.add_edge(orphan, target_root, relation="connects_to_root", auto=True)
                report["actions"].append(f"Auto-connected {orphan} → {target_root}")
        
        elif strategy == "exclude_with_log":
            for orphan in self.orphans:
                self.graph.remove_node(orphan)
                report["actions"].append(f"Removed orphan: {orphan}")
        
        return report
```

### 3. Multi-Hop Query Optimization

Traverse the graph with deduplication and relevance decay:

```python
class MultiHopQueryOptimizer:
    """Optimize multi-hop traversal with deduplication and relevance scoring."""
    
    def __init__(self, graph):
        self.graph = graph
    
    def multi_hop_query(self, start_concept: str, max_hops: int = 3) -> Dict:
        """
        Traverse graph up to max_hops, deduplicating results.
        Relevance scores decay with hop distance: score *= 0.8^hop
        """
        result = {
            "start": start_concept,
            "max_hops": max_hops,
            "by_hop": {},
            "all_reached": {},
        }
        
        visited = {start_concept}  # Deduplication set
        current_level = [(start_concept, 1.0)]  # (node, relevance_score)
        
        for hop in range(1, max_hops + 1):
            next_level = []
            hop_results = []
            
            for node, score in current_level:
                for successor in self.graph.successors(node):
                    if successor not in visited:
                        # Decay score: multiply by 0.8 per hop
                        new_score = score * (0.8 ** hop)
                        visited.add(successor)
                        next_level.append((successor, new_score))
                        hop_results.append({
                            "node": successor,
                            "score": float(new_score),
                            "source": node
                        })
                        # Store in consolidated result
                        if successor not in result["all_reached"]:
                            result["all_reached"][successor] = new_score
                        else:
                            result["all_reached"][successor] = max(result["all_reached"][successor], new_score)
            
            result["by_hop"][hop] = hop_results
            current_level = next_level
            
            if not current_level:
                break
        
        # Sort consolidated results by score
        result["ranked"] = sorted(
            result["all_reached"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return result
```

### 4. SPARQL-like Boolean Queries

Support complex query logic with AND/OR/NOT operators:

```python
class OntologyQuery:
    """SPARQL-like query engine for ontology traversal with boolean logic."""
    
    def __init__(self, graph):
        self.graph = graph
    
    def AND(self, *relations: str) -> List[str]:
        """Return nodes satisfying ALL relation types."""
        if not relations:
            return list(self.graph.nodes())
        
        # Start with nodes matching first relation
        candidates = set()
        for node in self.graph.nodes():
            for successor in self.graph.successors(node):
                edge = self.graph[node][successor]
                if edge.get("relation") == relations[0]:
                    candidates.add(successor)
        
        # Filter by remaining relations
        for relation in relations[1:]:
            filtered = set()
            for node in candidates:
                for successor in self.graph.successors(node):
                    edge = self.graph[node][successor]
                    if edge.get("relation") == relation:
                        filtered.add(successor)
            candidates = filtered
        
        return list(candidates)
    
    def OR(self, *relations: str) -> List[str]:
        """Return nodes satisfying ANY relation type."""
        candidates = set()
        for node in self.graph.nodes():
            for successor in self.graph.successors(node):
                edge = self.graph[node][successor]
                if edge.get("relation") in relations:
                    candidates.add(successor)
        return list(candidates)
    
    def NOT(self, relation: str) -> List[str]:
        """Return nodes NOT connected via the specified relation."""
        all_nodes = set(self.graph.nodes())
        excluded = set()
        
        for node in self.graph.nodes():
            for successor in self.graph.successors(node):
                edge = self.graph[node][successor]
                if edge.get("relation") == relation:
                    excluded.add(successor)
        
        return list(all_nodes - excluded)
    
    def path(self, start: str, end: str, max_hops: int = 3) -> List[List[str]]:
        """Find all paths from start to end within max_hops."""
        paths = []
        
        def dfs(current, target, visited, path):
            if len(path) > max_hops:
                return
            if current == target:
                paths.append(path[:])
                return
            
            for successor in self.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    path.append(successor)
                    dfs(successor, target, visited, path)
                    path.pop()
                    visited.remove(successor)
        
        visited = {start}
        dfs(start, end, visited, [start])
        return paths
```

### 5. Korean Ontology Support

Add bilingual (English-Korean) relation types for CRMB translation:

```python
class BilingualOntology:
    """Support bilingual ontology construction and traversal."""
    
    KOREAN_RELATION_TYPES = {
        "is_a": "~이다",
        "part_of": "~의 일부",
        "causes": "~를 야기한다",
        "relates_to": "~와 관련",
        "comprises": "~를 포함",
        "implements": "~를 구현",
        "shares_principle": "~와 원리 공유",
    }
    
    KOREAN_CONCEPTS = {
        "ART": "적응 공명 이론",
        "BCS/FCS": "경계 윤곽 시스템 / 특성 윤곽 시스템",
        "LAMINART": "층상 자동화 신경망 기술",
        "sparse_coding": "희소 부호화",
        "predictive_coding": "예측 부호화",
    }
    
    def __init__(self, graph):
        self.graph = graph
        self.bilingual_metadata = {}
    
    def build_bilingual_ontology(self) -> Dict:
        """
        Annotate existing ontology with Korean translations.
        Returns: Dictionary mapping nodes to {en: name, ko: name, relations_ko: {...}}
        """
        for node in self.graph.nodes():
            en_name = node
            ko_name = self.KOREAN_CONCEPTS.get(node, self._translate_to_korean(node))
            
            self.bilingual_metadata[node] = {
                "en": en_name,
                "ko": ko_name,
                "relations_en": {},
                "relations_ko": {},
            }
            
            # Annotate outgoing relations
            for successor in self.graph.successors(node):
                edge = self.graph[node][successor]
                relation_type = edge.get("relation", "related")
                
                en_rel = relation_type
                ko_rel = self.KOREAN_RELATION_TYPES.get(relation_type, relation_type)
                
                self.bilingual_metadata[node]["relations_en"][successor] = en_rel
                self.bilingual_metadata[node]["relations_ko"][successor] = ko_rel
        
        return self.bilingual_metadata
    
    def _translate_to_korean(self, english_term: str) -> str:
        """
        Simple fallback translation (in production, use Google Translate API).
        """
        # Replace underscores with spaces and titlecase
        return english_term.replace("_", " ").title()
    
    def format_korean_report(self) -> str:
        """Generate bilingual query report."""
        report = "=== 양언어 온톨로지 (Bilingual Ontology) ===\n"
        for node, metadata in self.bilingual_metadata.items():
            report += f"\n[{node} | {metadata['ko']}]\n"
            for target, rel in metadata["relations_en"].items():
                ko_rel = metadata["relations_ko"].get(target, rel)
                report += f"  {rel} | {ko_rel} → {target}\n"
        return report
```

### 6. NLP-based Relation Extraction

Guidance for advanced extraction beyond regex patterns:

```python
class NLPRelationExtractor:
    """
    Extract relations using NLP models (spaCy, KoNLPy) for accuracy beyond regex.
    
    Example dependencies:
    - pip install spacy
    - python -m spacy download en_core_web_sm
    - pip install konlpy
    """
    
    def __init__(self, lang: str = "en"):
        """
        Initialize NLP extractor.
        lang: 'en' for spaCy, 'ko' for KoNLPy
        """
        self.lang = lang
        if lang == "en":
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        elif lang == "ko":
            from konlpy.tag import Okt
            self.nlp = Okt()
    
    def extract_relations_spacy(self, text: str) -> List[Dict]:
        """
        Extract relations using spaCy's dependency parsing.
        Looks for SVO (Subject-Verb-Object) patterns.
        
        Example:
        "ART is a learning mechanism" →
        {"subject": "ART", "verb": "is", "object": "learning mechanism", "relation": "is_a"}
        """
        doc = self.nlp(text)
        relations = []
        
        for token in doc:
            # Look for copula "is" or "are"
            if token.lemma_ in ["be", "is"]:
                # Subject: left-dependent noun
                subject = None
                for child in token.head.children:
                    if child.dep_ == "nsubj":
                        subject = child.text
                        break
                
                # Object: right-dependent noun (via attr)
                obj = None
                for child in token.children:
                    if child.dep_ == "attr":
                        obj = child.text
                        break
                
                if subject and obj:
                    relations.append({
                        "subject": subject,
                        "relation": "is_a",
                        "object": obj,
                        "confidence": 0.9,
                    })
        
        return relations
    
    def extract_relations_konlpy(self, text: str) -> List[Dict]:
        """
        Extract relations from Korean text using KoNLPy.
        Looks for 이다 (is) and 포함 (comprises) patterns.
        
        Example:
        "ART는 적응 공명 이론이다" →
        {"subject": "ART", "relation": "is_a", "object": "적응 공명 이론"}
        """
        # Tokenize and tag
        pos_tagged = self.nlp.pos(text)
        relations = []
        
        # Simple pattern: Noun + 이다 → is_a relation
        for i, (word, pos) in enumerate(pos_tagged):
            if pos.startswith("VV") and word in ["이다", "이"]:
                # Collect preceding nouns as subject
                subject_tokens = []
                for j in range(i - 1, -1, -1):
                    prev_word, prev_pos = pos_tagged[j]
                    if prev_pos.startswith("N"):
                        subject_tokens.insert(0, prev_word)
                    elif prev_pos.startswith("J"):  # josa (particle)
                        break
                
                # Collect following nouns as object
                obj_tokens = []
                for j in range(i + 1, len(pos_tagged)):
                    next_word, next_pos = pos_tagged[j]
                    if next_pos.startswith("N"):
                        obj_tokens.append(next_word)
                    elif next_pos.startswith("J"):
                        break
                
                if subject_tokens and obj_tokens:
                    relations.append({
                        "subject": "".join(subject_tokens),
                        "relation": "is_a",
                        "object": "".join(obj_tokens),
                        "confidence": 0.85,
                        "language": "ko",
                    })
        
        return relations
    
    @staticmethod
    def example_usage():
        """Show how to use NLP extraction in production."""
        extractor_en = NLPRelationExtractor(lang="en")
        extractor_ko = NLPRelationExtractor(lang="ko")
        
        # English example
        text_en = "Boundary Contour System is a neural pathway in visual cortex."
        relations_en = extractor_en.extract_relations_spacy(text_en)
        
        # Korean example
        text_ko = "경계윤곽시스템은 시각피질의 신경경로이다"
        relations_ko = extractor_ko.extract_relations_konlpy(text_ko)
        
        return {
            "en": relations_en,
            "ko": relations_ko,
        }
```

### Usage Example: Robustness Checks

```python
# Initialize with robustness features
builder = OntologyBuilder()
builder.add_chapter("ART", chapter_text)

# 1. Check for cycles
cycle_detector = CycleDetector(builder.graph)
cycles = cycle_detector.detect_cycles()
print(cycle_detector.report_cycles_to_user())

# 2. Handle orphans
orphan_handler = OrphanNodeHandler(builder.graph)
report = orphan_handler.handle_orphans(strategy="auto_connect_to_root")
print(f"Orphan handling: {report}")

# 3. Multi-hop with deduplication
optimizer = MultiHopQueryOptimizer(builder.graph)
expanded = optimizer.multi_hop_query("BCS_boundary_completion", max_hops=3)
print(f"Reached concepts: {expanded['ranked'][:5]}")

# 4. Boolean queries
query_engine = OntologyQuery(builder.graph)
is_a_nodes = query_engine.AND("is_a")
is_a_or_part = query_engine.OR("is_a", "part_of")
paths = query_engine.path("ART", "sparse_coding", max_hops=4)

# 5. Korean support
bilingual = BilingualOntology(builder.graph)
bilingual.build_bilingual_ontology()
print(bilingual.format_korean_report())

# 6. NLP extraction
extractor = NLPRelationExtractor(lang="en")
text = "Predictive coding is a subset of efficient coding theory."
relations = extractor.extract_relations_spacy(text)
print(f"Extracted: {relations}")
```

## Example Usage

```python
# 1. Build CRMB ontology from chapters
builder = OntologyBuilder()
builder.add_chapter("ART", "Adaptive Resonance Theory is-a competitive learning mechanism...")
builder.add_chapter("BCS/FCS", "The Boundary Contour System is part of visual processing...")

# 2. Extend with efficient coding
builder = EfficientCodingDomain.extend_ontology(builder)

# 3. Query expansion
expander = QueryExpander(builder)
expanded = expander.expand_query("How does boundary completion work?")
print(expanded["search_terms"])  # [original + related concepts]

# 4. Chunk linking
linker = ChunkOntologyLinker(builder, embeddings_model)
chunk_meta = linker.link_chunk("c1", "The BCS implements sparse coding...", "BCS/FCS")

# 5. LanceDB hybrid search
pipeline = LanceDBOntologyPipeline()
pipeline.create_table(chunks, builder)
results = pipeline.hybrid_search("boundary completion mechanisms", expander)
```

## Integration with CRMB_tutor Project

- **concept_graph/**: Mount ontology nodes and edges from builder.graph
- **src/rag/knowledge_graph.py**: Replace with OntologyBuilder + QueryExpander
- **src/rag/dual_retrieval.py**: Integrate hybrid_search() as secondary ranker
- **LanceDB store**: Add ontology_boost column and re-ranking logic

## Performance Notes

- **Ontology extraction**: ~10-50ms per chapter (regex + NLP)
- **Query expansion**: ~5-20ms (graph traversal, limited to 3 hops)
- **Chunk linking**: ~50-100ms per chunk (embedding + similarity)
- **LanceDB search**: ~10-30ms for k=10 (vector) + ~5ms re-ranking (ontology)

Total end-to-end latency: ~100-200ms for retrieval.


## Worked Example: "Boundary Completion" Query Expansion

This example demonstrates the complete traversal from a user query through concept extraction, graph traversal, and result fusion.

### Scenario
**User query:** "How does boundary completion work in Grossberg's model?"

### Step-by-Step Trace

**1. Concept Extraction**
```python
query = "How does boundary completion work in Grossberg's model?"
extracted = concept_extractor.extract(query)
# Result: concept_id = "BCS_boundary_completion"
```

**2. Multi-Hop Graph Traversal (2-hop)**
```python
builder = OntologyBuilder()
traversal = builder.traverse_graph(
    start_concept="BCS_boundary_completion",
    max_hops=2
)
# Traversal path:
# BCS_boundary_completion --[part_of]--> BCS --[relates_to]--> FCS --[part_of]--> LAMINART
# Secondary path:
# FCS --[comprises]--> FCS_filling_in
# LAMINART --[contains]--> LAMINART_layer23
```

**3. Expanded Concept Set**
```python
expanded_concepts = {
    "BCS_boundary_completion",      # original
    "BCS",                          # parent
    "FCS",                          # related layer
    "FCS_filling_in",              # FCS sublayer
    "LAMINART",                     # higher architecture
    "LAMINART_layer23"             # LAMINART detail
}
```

**4. Chunk Retrieval via LanceDB**
```python
expander = QueryExpander()
results_per_concept = {}
for concept_id in expanded_concepts:
    chunks = lancedb_client.search(
        table=f"chunks_{concept_id}",
        query_embedding=embed(query),
        top_k=5
    )
    results_per_concept[concept_id] = chunks
```

**5. Reciprocal Rank Fusion (RRF)**
```python
fused_scores = {}
for concept_id, ranked_chunks in results_per_concept.items():
    for rank, chunk in enumerate(ranked_chunks, 1):
        chunk_id = chunk['id']
        rrf_score = 1.0 / (60 + rank)  # k=60
        if chunk_id not in fused_scores:
            fused_scores[chunk_id] = 0
        fused_scores[chunk_id] += rrf_score

ranked_results = sorted(
    fused_scores.items(),
    key=lambda x: x[1],
    reverse=True
)
```

**6. Diversity-Enforced Final Ranking**
```python
final_results = []
concepts_represented = set()
for chunk_id, rrf_score in ranked_results:
    concept_source = chunk_metadata[chunk_id]['concept_id']
    if concept_source not in concepts_represented:
        final_results.append({
            'chunk_id': chunk_id,
            'rrf_score': rrf_score,
            'concept': concept_source,
            'text': chunk_metadata[chunk_id]['text']
        })
        concepts_represented.add(concept_source)
```

**Expected Output:**
- **Top result (BCS_boundary_completion):** Mechanism of boundary completion in BCS layer
- **2nd result (BCS):** Overall BCS architecture and function
- **3rd result (FCS):** Feature contrast system interaction with BCS
- **4th result (FCS_filling_in):** Filling-in process details
- **5th result (LAMINART):** LAMINART's role in the feedback hierarchy
- **6th result (LAMINART_layer23):** Layer 2/3 specifics

This multi-concept, RRF-fused approach ensures both relevance (via graph structure) and diversity (at least one chunk per concept traversed).
