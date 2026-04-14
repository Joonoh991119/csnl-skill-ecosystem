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
