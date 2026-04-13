#!/usr/bin/env python3
"""
Split documents into chunks and generate embeddings using OpenAI API.
Stores embeddings in PostgreSQL with pgvector.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv
import psycopg2
from tqdm import tqdm

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector

load_dotenv()

class ChunkingAndEmbedding:
    def __init__(self):
        """Initialize chunking and embedding components."""
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        # Initialize text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
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
        
        self.connection_string = (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
    
    def chunk_document(self, text: str) -> List[str]:
        """Split document into chunks."""
        chunks = self.splitter.split_text(text)
        return [chunk for chunk in chunks if len(chunk.strip()) > 0]
    
    def process_documents(self):
        """Process all documents in the documents directory."""
        doc_dir = Path("documents")
        
        if not doc_dir.exists():
            print("No documents directory found. Run 02_ingest_papers.py first.")
            sys.exit(1)
        
        doc_files = list(doc_dir.glob("*.txt"))
        
        if not doc_files:
            print("No documents found in ./documents/")
            sys.exit(1)
        
        print(f"Found {len(doc_files)} documents to process")
        
        conn = self.connect_db()
        cur = conn.cursor()
        
        total_chunks = 0
        
        for doc_file in tqdm(doc_files, desc="Processing documents"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Extract paper_id from filename
                paper_id = int(doc_file.stem.split('_')[0])
                
                # Check if already processed
                cur.execute(
                    "SELECT COUNT(*) FROM chunks WHERE paper_id = %s",
                    (paper_id,)
                )
                
                if cur.fetchone()[0] > 0:
                    print(f"Skipping {doc_file.name} (already processed)")
                    continue
                
                # Chunk document
                chunks = self.chunk_document(text)
                
                if not chunks:
                    continue
                
                # Generate embeddings and store
                print(f"Generating embeddings for {len(chunks)} chunks...")
                
                embeddings = self.embeddings.embed_documents(chunks)
                
                # Store chunks with embeddings
                for chunk_idx, (chunk_text, embedding) in enumerate(
                    zip(chunks, embeddings)
                ):
                    # Convert embedding list to string format for pgvector
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                    
                    cur.execute("""
                        INSERT INTO chunks 
                        (paper_id, chunk_text, chunk_index, embedding)
                        VALUES (%s, %s, %s, %s)
                    """, (paper_id, chunk_text, chunk_idx, embedding_str))
                
                conn.commit()
                total_chunks += len(chunks)
                
            except Exception as e:
                print(f"ERROR processing {doc_file.name}: {e}")
                conn.rollback()
        
        cur.close()
        conn.close()
        
        print(f"\nEmbedding generation complete:")
        print(f"  Total chunks created: {total_chunks}")
        print(f"  Embedding model: {os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')}")

if __name__ == "__main__":
    processor = ChunkingAndEmbedding()
    processor.process_documents()
