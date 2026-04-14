#!/usr/bin/env python3
"""
RAG Pipeline Setup Script
Complete setup for PostgreSQL with pgvector, BGE-M3 embeddings, and section-aware chunking.

SKILL.md Patterns Used:
- EMBEDDING_DIM configuration variable (1024 for BGE-M3)
- pgvector schema with parameterized dimensions
- Section-aware chunking from paper-processor
- Device management for M4 Pro Mac (MPS)
"""

import os
import json
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SKILL.md Pattern: EMBEDDING_DIM configuration variable
# BGE-M3 produces 1024-dimensional embeddings
EMBEDDING_DIM = 1024

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'rag_neuroscience')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')


class PipelineSetup:
    """Setup PostgreSQL database with pgvector extension for RAG pipeline."""

    def __init__(self):
        self.conn = None
        self.embedding_dim = EMBEDDING_DIM

    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database='postgres'
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info(f"Connected to PostgreSQL at {DB_HOST}:{DB_PORT}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def create_database(self):
        """Create the RAG database if it doesn't exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE {DB_NAME}")
                logger.info(f"Created database: {DB_NAME}")
            else:
                logger.info(f"Database {DB_NAME} already exists")
            
            cursor.close()
        except Exception as e:
            logger.error(f"Database creation failed: {e}")
            raise

    def enable_pgvector(self):
        """Enable pgvector extension in the target database."""
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("pgvector extension enabled")
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"pgvector setup failed: {e}")
            raise

    def create_schema(self):
        """
        SKILL.md Pattern: pgvector schema with parameterized dimensions
        Creates tables for papers, chunks, and embeddings with flexible dimension support.
        """
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            cursor = conn.cursor()
            
            # Papers table - stores metadata about papers
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS papers (
                    id SERIAL PRIMARY KEY,
                    zotero_key VARCHAR(255) UNIQUE NOT NULL,
                    title VARCHAR(500),
                    authors TEXT,
                    year INTEGER,
                    doi VARCHAR(255),
                    abstract TEXT,
                    source_file VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Created papers table")
            
            # SKILL.md Pattern: Section-aware chunking schema
            # Chunks table - stores text chunks with section information
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
                    section_type VARCHAR(50),  -- abstract, methods, results, discussion, etc.
                    section_title VARCHAR(255),
                    chunk_index INTEGER,
                    content TEXT NOT NULL,
                    start_char INTEGER,
                    end_char INTEGER,
                    token_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Created chunks table")
            
            # Embeddings table - stores vector embeddings for chunks
            # Using parameterized dimension (EMBEDDING_DIM=1024)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id SERIAL PRIMARY KEY,
                    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
                    embedding vector({self.embedding_dim}) NOT NULL,
                    model_name VARCHAR(255),
                    embedding_dim INTEGER DEFAULT {self.embedding_dim},
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info(f"Created embeddings table with {self.embedding_dim}-dimensional vectors")
            
            # BM25 statistics table - for hybrid search support
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS bm25_stats (
                    id SERIAL PRIMARY KEY,
                    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
                    term_frequency JSONB,  -- term → count mapping
                    doc_length INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Created BM25 statistics table for hybrid search")
            
            # Search results table - for query logging and optimization
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS search_results (
                    id SERIAL PRIMARY KEY,
                    query_text TEXT,
                    query_embedding vector({self.embedding_dim}),
                    top_k INTEGER,
                    search_type VARCHAR(50),  -- hybrid, dense, sparse
                    results JSONB,
                    execution_time_ms FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Created search results logging table")
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_zotero ON papers(zotero_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_paper_id ON chunks(paper_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
            logger.info("Created database indexes")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise

    def create_config(self):
        """Create the RAG pipeline configuration file."""
        config = {
            "embedding": {
                "model": "BAAI/bge-m3",
                "embedding_dim": EMBEDDING_DIM,
                "device": "mps",  # Metal Performance Shaders for M4 Pro
                "batch_size": 32,
                "normalize": True,
                "use_fp16": False
            },
            "chunking": {
                "strategy": "section-aware",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "section_types": ["abstract", "introduction", "methods", "results", "discussion", "conclusion"],
                "preserve_section_boundaries": True
            },
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.5,
                "hybrid_search": True,
                "bm25_enabled": True,
                "dense_weight": 0.6,
                "sparse_weight": 0.4,
                "rrf_k": 60  # Reciprocal Rank Fusion parameter
            },
            "database": {
                "host": DB_HOST,
                "port": DB_PORT,
                "name": DB_NAME,
                "user": DB_USER,
                "embedding_table": "embeddings",
                "chunks_table": "chunks",
                "papers_table": "papers"
            }
        }
        
        with open('rag_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Created rag_config.json with SKILL.md patterns:")
        logger.info(f"  - EMBEDDING_DIM: {EMBEDDING_DIM}")
        logger.info(f"  - Device: mps (M4 Pro Mac)")
        logger.info(f"  - Section-aware chunking: enabled")
        logger.info(f"  - Hybrid search: enabled (RRF)")

    def run_setup(self):
        """Run complete setup sequence."""
        try:
            logger.info("Starting RAG pipeline setup...")
            self.connect()
            self.create_database()
            self.enable_pgvector()
            self.create_schema()
            self.create_config()
            logger.info("RAG pipeline setup complete!")
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()


if __name__ == '__main__':
    setup = PipelineSetup()
    setup.run_setup()
