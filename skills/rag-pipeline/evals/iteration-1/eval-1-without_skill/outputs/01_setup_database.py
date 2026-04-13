#!/usr/bin/env python3
"""
Setup PostgreSQL database with pgvector extension for RAG pipeline.
Run this once to initialize the database schema.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import sys

load_dotenv()

def setup_database():
    """Create database and pgvector extension."""
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "neuroscience_rag")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    
    if not db_password:
        print("ERROR: DB_PASSWORD not set in .env file")
        sys.exit(1)
    
    # Connect to PostgreSQL default database
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database="postgres",
            user=db_user,
            password=db_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        db_exists = cur.fetchone()
        
        if not db_exists:
            print(f"Creating database {db_name}...")
            cur.execute(f"CREATE DATABASE {db_name}")
            print(f"Database {db_name} created successfully")
        else:
            print(f"Database {db_name} already exists")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"ERROR connecting to PostgreSQL: {e}")
        sys.exit(1)
    
    # Connect to the new database and create tables
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        # Enable pgvector extension
        print("Installing pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Create papers table
        print("Creating papers table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id SERIAL PRIMARY KEY,
                zotero_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                abstract TEXT,
                doi TEXT,
                url TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create chunks table for document sections
        print("Creating chunks table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(paper_id, chunk_index)
            )
        """)
        
        # Create vector index for fast retrieval
        print("Creating vector index...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
            ON chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        
        # Create search history table
        print("Creating search history table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                num_results INTEGER,
                execution_time_ms FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("\nDatabase setup completed successfully!")
        print(f"Connected to: {db_name} on {db_host}:{db_port}")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"ERROR setting up database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
