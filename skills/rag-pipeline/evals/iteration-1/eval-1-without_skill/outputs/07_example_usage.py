#!/usr/bin/env python3
"""
Example usage patterns for the RAG Query Engine.
Demonstrates different ways to interact with the system.
"""

from rag_query_engine import RAGQueryEngine
import json

def example_1_basic_search():
    """Basic semantic search without LLM augmentation."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Semantic Search")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=3)
    
    question = "What papers discuss the relationship between VWM capacity and attention control?"
    
    results = engine.query(question, use_llm=False, return_search_results=True)
    
    print("\nRaw results (JSON):")
    print(json.dumps(results, indent=2, default=str)[:1000] + "...")

def example_2_llm_augmented():
    """Search with LLM-augmented response synthesis."""
    print("\n" + "="*60)
    print("EXAMPLE 2: LLM-Augmented Search")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=5, temperature=0.7)
    
    question = "How does working memory load affect attentional filtering?"
    
    results = engine.query(question, use_llm=True, return_search_results=True)
    
    if "llm_response" in results:
        print("\nLLM Response:")
        print("-" * 60)
        print(results["llm_response"])

def example_3_batch_queries():
    """Process multiple queries efficiently."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Query Processing")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=3)
    
    questions = [
        "What neural mechanisms underlie VWM capacity limitations?",
        "How does attention modulate consolidation of working memory?",
        "What are neurophysiological correlates of working memory maintenance?",
    ]
    
    print(f"\nProcessing {len(questions)} questions...")
    
    results = engine.batch_query(questions, use_llm=False)
    
    print(f"\nProcessed {len(results)} queries")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['question'][:50]}... ({result['num_results']} results)")

def example_4_custom_top_k():
    """Use different retrieval parameters."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Retrieval Parameters")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=10)
    
    question = "Visual working memory"
    
    print(f"\nSearching with top_k=10...")
    results = engine.semantic_search(question, top_k=10)
    
    print(f"Retrieved {len(results)} passages")
    
    # Analyze relevance distribution
    scores = [r['similarity_score'] for r in results]
    print(f"\nRelevance scores:")
    print(f"  Min: {min(scores):.3f}")
    print(f"  Max: {max(scores):.3f}")
    print(f"  Avg: {sum(scores)/len(scores):.3f}")

def example_5_search_statistics():
    """Analyze search patterns and performance."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Search Statistics")
    print("="*60)
    
    engine = RAGQueryEngine()
    
    stats = engine.get_search_stats()
    
    print("\nSearch Statistics:")
    print(f"  Total searches: {stats.get('total_searches', 0)}")
    print(f"  Average time: {stats.get('avg_time_ms', 0):.2f}ms")
    print(f"  Min time: {stats.get('min_time_ms', 0):.2f}ms")
    print(f"  Max time: {stats.get('max_time_ms', 0):.2f}ms")
    print(f"  Average results: {stats.get('avg_results', 0):.1f}")
    
    if "top_queries" in stats:
        print("\nTop 5 Most Common Queries:")
        for i, q in enumerate(stats["top_queries"][:5], 1):
            print(f"  {i}. {q['query'][:50]}... ({q['count']} searches)")

def example_6_relevance_filtering():
    """Filter results by relevance threshold."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Relevance-Based Filtering")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=10)
    
    question = "How does attention affect working memory encoding?"
    
    results = engine.semantic_search(question)
    
    # Filter by relevance threshold
    threshold = 0.7
    high_relevance = [r for r in results if r['similarity_score'] >= threshold]
    
    print(f"\nTotal results: {len(results)}")
    print(f"High relevance (>{threshold}): {len(high_relevance)}")
    
    if high_relevance:
        print(f"\nHigh-relevance papers:")
        for r in high_relevance:
            print(f"  - {r['title']} ({r['year']})")
            print(f"    Score: {r['similarity_score']:.3f}")

def example_7_paper_focused_search():
    """Search and retrieve papers by specific authors/years."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Paper-Focused Retrieval")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=20)
    
    question = "attention and working memory"
    
    results = engine.semantic_search(question)
    
    # Organize by paper
    by_paper = {}
    for result in results:
        paper_key = (result['paper_id'], result['title'])
        if paper_key not in by_paper:
            by_paper[paper_key] = {
                'title': result['title'],
                'year': result['year'],
                'authors': result['authors'],
                'doi': result['doi'],
                'chunks': []
            }
        by_paper[paper_key]['chunks'].append({
            'index': result['chunk_index'],
            'score': result['similarity_score'],
            'preview': result['chunk_text'][:100]
        })
    
    print(f"\nFound {len(by_paper)} papers containing relevant passages:")
    for (pid, title), paper_data in list(by_paper.items())[:5]:
        print(f"\n  {paper_data['title']} ({paper_data['year']})")
        print(f"  Chunks retrieved: {len(paper_data['chunks'])}")
        print(f"  Top score: {max(c['score'] for c in paper_data['chunks']):.3f}")

def example_8_semantic_similarity_exploration():
    """Find semantically similar passages across papers."""
    print("\n" + "="*60)
    print("EXAMPLE 8: Semantic Similarity Exploration")
    print("="*60)
    
    engine = RAGQueryEngine(top_k=5)
    
    queries = [
        "working memory capacity",
        "attention capacity",
        "memory limitations"
    ]
    
    print(f"\nSearching for semantically related passages:\n")
    
    for query in queries:
        results = engine.semantic_search(query)
        avg_score = sum(r['similarity_score'] for r in results) / len(results)
        print(f"  '{query}'")
        print(f"    Average relevance: {avg_score:.3f}")
        print(f"    Papers found: {len(set(r['paper_id'] for r in results))}")

# Run all examples
if __name__ == "__main__":
    print("\n" + "="*60)
    print("RAG Query Engine - Usage Examples")
    print("="*60)
    
    try:
        example_1_basic_search()
        example_2_llm_augmented()
        example_3_batch_queries()
        example_4_custom_top_k()
        example_5_search_statistics()
        example_6_relevance_filtering()
        example_7_paper_focused_search()
        example_8_semantic_similarity_exploration()
        
        print("\n" + "="*60)
        print("Examples completed!")
        print("="*60)
    
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nMake sure the pipeline is fully initialized:")
        print("  1. Run: python3 01_setup_database.py")
        print("  2. Run: python3 02_ingest_papers.py")
        print("  3. Run: python3 03_chunking_and_embeddings.py")
