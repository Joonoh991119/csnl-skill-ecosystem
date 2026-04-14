#!/usr/bin/env python3
"""
Hybrid Search Implementation - Dense + BM25 + Reciprocal Rank Fusion

SKILL.md Patterns Used:
- Hybrid search combining dense vectors with BM25 sparse retrieval
- Reciprocal Rank Fusion (RRF) for result fusion
- Configurable density weights
"""

import json
import math
import psycopg2
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    SKILL.md Pattern: Hybrid search combining dense vectors with BM25 sparse retrieval
    Uses Reciprocal Rank Fusion to combine dense and sparse results.
    """

    def __init__(self, config_path: str):
        """Initialize hybrid search engine with config."""
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.embedding_dim = self.config['embedding']['embedding_dim']
        self.device = self.config['embedding']['device']
        self.model = None
        self.db_conn = None
        self.rrf_k = self.config['retrieval'].get('rrf_k', 60)
        
    def connect_model(self):
        """Initialize sentence-transformers model with MPS device."""
        model_name = self.config['embedding']['model']
        
        # SKILL.md Pattern: sentence-transformers with MPS device
        # MPS (Metal Performance Shaders) for M4 Pro Mac
        try:
            import torch
            if self.device == 'mps' and torch.backends.mps.is_available():
                logger.info("Using MPS (Metal Performance Shaders) for M4 Pro Mac")
                self.model = SentenceTransformer(model_name, device='mps')
            else:
                logger.info(f"Using device: {self.device}")
                self.model = SentenceTransformer(model_name, device=self.device)
        except Exception as e:
            logger.warning(f"MPS not available, falling back to CPU: {e}")
            self.model = SentenceTransformer(model_name, device='cpu')
        
        logger.info(f"Loaded model: {model_name}")

    def connect_database(self):
        """Connect to PostgreSQL database."""
        db_config = self.config['database']
        try:
            self.db_conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['name'],
                user=db_config['user']
            )
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _embed_query(self, query: str) -> np.ndarray:
        """Embed query using sentence-transformers."""
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding

    def _dense_search(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        """
        SKILL.md Pattern: Dense vector similarity search
        Uses PostgreSQL vector cosine distance with pgvector.
        """
        cursor = self.db_conn.cursor()
        
        # Convert numpy array to list for PostgreSQL
        embedding_list = query_embedding.tolist()
        
        cursor.execute(f"""
            SELECT 
                e.id as embedding_id,
                c.id as chunk_id,
                c.content,
                c.section_type,
                c.section_title,
                p.title,
                p.authors,
                p.year,
                1 - (e.embedding <=> %s::vector) as similarity_score
            FROM {self.config['database']['embeddings_table']} e
            JOIN {self.config['database']['chunks_table']} c ON e.chunk_id = c.id
            JOIN {self.config['database']['papers_table']} p ON c.paper_id = p.id
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """, (embedding_list, embedding_list, top_k))
        
        results = []
        for i, row in enumerate(cursor.fetchall(), 1):
            results.append({
                'rank': i,
                'embedding_id': row[0],
                'chunk_id': row[1],
                'content': row[2],
                'section_type': row[3],
                'section_title': row[4],
                'title': row[5],
                'authors': row[6],
                'year': row[7],
                'similarity': float(row[8]),
                'search_type': 'dense'
            })
        
        cursor.close()
        return results

    def _bm25_search(self, query: str, top_k: int) -> List[Dict]:
        """
        SKILL.md Pattern: BM25 sparse retrieval for hybrid search
        Implements probabilistic ranking function for text matching.
        """
        cursor = self.db_conn.cursor()
        
        # Split query into terms
        query_terms = query.lower().split()
        
        # Simple BM25-like search using PostgreSQL full-text search
        cursor.execute(f"""
            SELECT 
                c.id as chunk_id,
                c.content,
                c.section_type,
                c.section_title,
                p.title,
                p.authors,
                p.year,
                ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as bm25_score
            FROM {self.config['database']['chunks_table']} c
            JOIN {self.config['database']['papers_table']} p ON c.paper_id = p.id
            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
            ORDER BY bm25_score DESC
            LIMIT %s
        """, (query, query, top_k))
        
        results = []
        for i, row in enumerate(cursor.fetchall(), 1):
            results.append({
                'rank': i,
                'chunk_id': row[0],
                'content': row[1],
                'section_type': row[2],
                'section_title': row[3],
                'title': row[4],
                'authors': row[5],
                'year': row[6],
                'bm25_score': float(row[7]),
                'search_type': 'sparse'
            })
        
        cursor.close()
        return results

    def _reciprocal_rank_fusion(
        self, 
        dense_results: List[Dict], 
        sparse_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """
        SKILL.md Pattern: Reciprocal Rank Fusion (RRF) for combining results
        Combines dense and sparse search results using RRF formula.
        
        RRF score = sum(1 / (k + rank)) across all ranking systems
        """
        rrf_scores = {}
        
        # Calculate RRF scores from dense results
        for result in dense_results:
            chunk_id = result['chunk_id']
            rank = result['rank']
            rrf_score = 1.0 / (k + rank)
            
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {
                    'dense_score': 0,
                    'sparse_score': 0,
                    'data': result
                }
            rrf_scores[chunk_id]['dense_score'] = rrf_score
        
        # Calculate RRF scores from sparse results
        for result in sparse_results:
            chunk_id = result['chunk_id']
            rank = result['rank']
            rrf_score = 1.0 / (k + rank)
            
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {
                    'dense_score': 0,
                    'sparse_score': 0,
                    'data': result
                }
            rrf_scores[chunk_id]['sparse_score'] = rrf_score
        
        # Combine scores using weighted average
        dense_weight = self.config['retrieval'].get('dense_weight', 0.6)
        sparse_weight = self.config['retrieval'].get('sparse_weight', 0.4)
        
        combined_results = []
        for chunk_id, scores in rrf_scores.items():
            combined_score = (
                dense_weight * scores['dense_score'] +
                sparse_weight * scores['sparse_score']
            )
            
            result = scores['data'].copy()
            result['rrf_score'] = combined_score
            result['search_type'] = 'hybrid'
            combined_results.append(result)
        
        # Sort by combined RRF score
        combined_results.sort(key=lambda x: x['rrf_score'], reverse=True)
        
        return combined_results

    def search(self, query: str, top_k: int = 5, hybrid: bool = True) -> List[Dict]:
        """
        Execute hybrid or dense-only search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            hybrid: If True, use hybrid search; if False, use dense only
        
        Returns:
            List of ranked search results with metadata
        """
        # Embed query
        query_embedding = self._embed_query(query)
        
        if not hybrid or not self.config['retrieval'].get('bm25_enabled', False):
            # Dense search only
            results = self._dense_search(query_embedding, top_k)
        else:
            # Hybrid search with RRF
            logger.info(f"Executing hybrid search for: {query[:50]}...")
            
            # Run both searches with more results to combine
            search_k = max(top_k * 2, 10)
            dense_results = self._dense_search(query_embedding, search_k)
            sparse_results = self._bm25_search(query, search_k)
            
            # Combine using RRF
            combined = self._reciprocal_rank_fusion(
                dense_results,
                sparse_results,
                k=self.rrf_k
            )
            
            # Return top-k
            results = combined[:top_k]
        
        return results

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()
            logger.info("Database connection closed")


class InteractiveSearchInterface:
    """Interactive interface for the hybrid search engine."""

    def __init__(self, config_path: str):
        self.engine = HybridSearchEngine(config_path)
        self.engine.connect_model()
        self.engine.connect_database()

    def run(self):
        """Run interactive search loop."""
        print("\n" + "="*60)
        print("RAG Hybrid Search Engine - Interactive Mode")
        print("="*60)
        print("Type 'quit' to exit")
        print("="*60 + "\n")
        
        while True:
            try:
                query = input("Query: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                if not query:
                    continue
                
                results = self.engine.search(query, top_k=5, hybrid=True)
                
                print(f"\n{len(results)} results found:\n")
                for i, result in enumerate(results, 1):
                    print(f"[{i}] {result['title']} ({result['year']})")
                    print(f"    Authors: {result['authors']}")
                    print(f"    Section: {result['section_type']}")
                    print(f"    RRF Score: {result.get('rrf_score', 0):.4f}")
                    print(f"    Content: {result['content'][:150]}...")
                    print()
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.engine.close()


if __name__ == '__main__':
    interface = InteractiveSearchInterface('rag_config.json')
    interface.run()
