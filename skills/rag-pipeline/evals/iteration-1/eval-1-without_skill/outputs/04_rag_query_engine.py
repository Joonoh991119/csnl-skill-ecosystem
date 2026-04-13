#!/usr/bin/env python3
"""
RAG Query Engine - Main interface for querying papers and retrieving relevant passages.
Supports semantic search with LLM-augmented responses.
"""

import os
import sys
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()

class RAGQueryEngine:
    def __init__(self, top_k: int = 5, temperature: float = 0.7):
        """Initialize RAG query engine."""
        self.top_k = top_k
        self.temperature = temperature
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        # Initialize LLM for generation
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=temperature
        )
        
        # Database connection
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "neuroscience_rag")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD")
        
        if not self.db_password:
            print("ERROR: DB_PASSWORD not set")
            sys.exit(1)
    
    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
    
    def semantic_search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Retrieve relevant chunks using semantic search."""
        if top_k is None:
            top_k = self.top_k
        
        start_time = time.time()
        
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search PostgreSQL using cosine similarity
            conn = self.connect_db()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Use pgvector cosine distance operator (<->)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            cur.execute(f"""
                SELECT 
                    c.id,
                    c.chunk_text,
                    c.chunk_index,
                    p.id as paper_id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    (1 - (c.embedding <-> '{embedding_str}'::vector)) as similarity_score
                FROM chunks c
                JOIN papers p ON c.paper_id = p.id
                ORDER BY c.embedding <-> '{embedding_str}'::vector
                LIMIT %s
            """, (top_k,))
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log search
            self._log_search(query, len(results), execution_time)
            
            return [dict(r) for r in results]
        
        except Exception as e:
            print(f"ERROR during search: {e}")
            return []
    
    def _log_search(self, query: str, num_results: int, execution_time_ms: float):
        """Log search to database."""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO search_history (query, num_results, execution_time_ms)
                VALUES (%s, %s, %s)
            """, (query, num_results, execution_time_ms))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not log search: {e}")
    
    def augment_with_llm(self, query: str, search_results: List[Dict]) -> str:
        """Use LLM to generate answer based on retrieved passages."""
        if not search_results:
            return "No relevant papers found for your query."
        
        # Build context from search results
        context = self._build_context(search_results)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert neuroscience researcher specializing 
in visual working memory and attention. Answer questions based on the provided research 
passages. Always cite the papers and specific passages you reference. Be precise and 
technical in your language."""),
            HumanMessage(content=f"""Based on the following research passages, answer this question:

Question: {query}

Research Passages:
{context}

Please provide a comprehensive answer that synthesizes information from multiple papers 
where relevant. Cite specific papers and page/section information.""")
        ])
        
        # Generate response
        response = self.llm.invoke(prompt)
        
        return response.content
    
    def _build_context(self, search_results: List[Dict]) -> str:
        """Build context string from search results."""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            part = f"""
[Paper {i}] {result['title']}
Authors: {result['authors']}
Year: {result['year']}
DOI: {result['doi']}
Relevance Score: {result['similarity_score']:.3f}

Passage (from section {result['chunk_index']}):
{result['chunk_text'][:500]}...
---
"""
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    def query(self, question: str, use_llm: bool = True, 
              return_search_results: bool = True) -> Dict:
        """Main query interface."""
        print(f"\nQuery: {question}")
        print("-" * 60)
        
        # Perform semantic search
        search_results = self.semantic_search(question)
        
        response = {
            "question": question,
            "search_results": search_results,
            "timestamp": datetime.now().isoformat(),
            "num_results": len(search_results)
        }
        
        if return_search_results:
            print(f"\nRetrieved {len(search_results)} relevant passages:")
            for i, result in enumerate(search_results, 1):
                print(f"\n{i}. {result['title']} ({result['year']})")
                print(f"   Relevance: {result['similarity_score']:.3f}")
                print(f"   DOI: {result['doi']}")
                print(f"   Passage preview: {result['chunk_text'][:200]}...")
        
        if use_llm:
            print("\nGenerating synthesis with LLM...")
            llm_response = self.augment_with_llm(question, search_results)
            response["llm_response"] = llm_response
            print(f"\nLLM Response:\n{llm_response}")
        
        return response
    
    def batch_query(self, questions: List[str], use_llm: bool = True) -> List[Dict]:
        """Process multiple queries."""
        results = []
        for question in questions:
            result = self.query(question, use_llm=use_llm)
            results.append(result)
        return results
    
    def get_search_stats(self) -> Dict:
        """Get statistics about search activity."""
        try:
            conn = self.connect_db()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_searches,
                    AVG(execution_time_ms) as avg_time_ms,
                    MIN(execution_time_ms) as min_time_ms,
                    MAX(execution_time_ms) as max_time_ms,
                    AVG(num_results) as avg_results
                FROM search_history
            """)
            
            stats = dict(cur.fetchone())
            
            # Get top queries
            cur.execute("""
                SELECT query, COUNT(*) as count
                FROM search_history
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            """)
            
            top_queries = [dict(row) for row in cur.fetchall()]
            stats["top_queries"] = top_queries
            
            cur.close()
            conn.close()
            
            return stats
        
        except Exception as e:
            print(f"ERROR getting stats: {e}")
            return {}

def interactive_query():
    """Run interactive query interface."""
    engine = RAGQueryEngine(top_k=5)
    
    print("RAG Query Engine - Neuroscience Papers")
    print("=" * 60)
    print("Type your question to search papers on visual working memory and attention")
    print("Type 'stats' to see search statistics")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if not question:
                continue
            
            if question.lower() == 'quit':
                print("Exiting...")
                break
            
            if question.lower() == 'stats':
                stats = engine.get_search_stats()
                print("\nSearch Statistics:")
                print(f"  Total searches: {stats.get('total_searches', 0)}")
                print(f"  Avg time: {stats.get('avg_time_ms', 0):.2f}ms")
                print(f"  Min time: {stats.get('min_time_ms', 0):.2f}ms")
                print(f"  Max time: {stats.get('max_time_ms', 0):.2f}ms")
                continue
            
            engine.query(question, use_llm=True)
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Process command line argument as query
        query = " ".join(sys.argv[1:])
        engine = RAGQueryEngine()
        engine.query(query, use_llm=True)
    else:
        # Run interactive mode
        interactive_query()
