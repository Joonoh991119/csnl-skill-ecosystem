#!/usr/bin/env python3
"""
Zotero to pgvector Ingestion Pipeline

SKILL.md Patterns Used:
- Section-aware chunking that preserves paper structure (abstract, methods, results, discussion)
- Integration with Zotero collection
- Batch embedding generation with MPS device support
- Database ingestion into parameterized pgvector schema
"""

import os
import json
import re
import psycopg2
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import PyPDF2
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PaperProcessor:
    """
    SKILL.md Pattern: Section-aware chunking that preserves paper structure
    Extracts text from PDFs and identifies academic sections.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.chunk_size = config['chunking']['chunk_size']
        self.chunk_overlap = config['chunking']['chunk_overlap']
        self.section_types = config['chunking']['section_types']

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = []
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            logger.warning(f"Failed to extract text from {pdf_path}: {e}")
            return ""

    def identify_sections(self, text: str) -> Dict[str, Tuple[int, int]]:
        """
        Identify academic paper sections using common headers.
        Returns dict mapping section name to (start_char, end_char).
        """
        sections = {}
        
        # Common section headers in academic papers
        section_patterns = {
            'abstract': r'(?i)(abstract|summary)',
            'introduction': r'(?i)(introduction|background)',
            'methods': r'(?i)(methods|methodology|experimental design)',
            'results': r'(?i)(results|findings)',
            'discussion': r'(?i)(discussion)',
            'conclusion': r'(?i)(conclusion|conclusions)',
        }
        
        for section_name, pattern in section_patterns.items():
            matches = list(re.finditer(pattern, text))
            if matches:
                match = matches[0]
                sections[section_name] = (match.start(), match.end())
        
        return sections

    def create_section_aware_chunks(
        self, 
        text: str,
        metadata: Dict
    ) -> List[Dict]:
        """
        SKILL.md Pattern: Section-aware chunking from paper-processor output
        Creates chunks while preserving section boundaries.
        """
        chunks = []
        sections = self.identify_sections(text)
        
        if not sections:
            # Fallback: create generic chunks if no sections found
            logger.warning(f"No sections identified in {metadata.get('title', 'unknown')}")
            return self._create_generic_chunks(text, metadata)
        
        # Sort sections by start position
        sorted_sections = sorted(sections.items(), key=lambda x: x[1][0])
        
        # Extract text for each section
        for section_idx, (section_name, (start, end)) in enumerate(sorted_sections):
            # Get section text up to next section (or end of document)
            if section_idx + 1 < len(sorted_sections):
                section_end = sorted_sections[section_idx + 1][1][0]
            else:
                section_end = len(text)
            
            section_text = text[start:section_end].strip()
            
            if not section_text:
                continue
            
            # Create chunks within this section
            section_chunks = self._chunk_text(
                section_text,
                self.chunk_size,
                self.chunk_overlap
            )
            
            # Add chunks with section metadata
            for chunk_idx, chunk_text in enumerate(section_chunks):
                chunks.append({
                    'content': chunk_text,
                    'section_type': section_name,
                    'section_title': section_name.title(),
                    'chunk_index': chunk_idx,
                    'start_char': start,
                    'token_count': len(chunk_text.split()),
                    'metadata': {
                        **metadata,
                        'section': section_name
                    }
                })
        
        logger.info(f"Created {len(chunks)} section-aware chunks for {metadata.get('title', 'unknown')}")
        return chunks

    def _create_generic_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """Create chunks without section information."""
        chunks = []
        chunk_texts = self._chunk_text(text, self.chunk_size, self.chunk_overlap)
        
        for idx, chunk_text in enumerate(chunk_texts):
            chunks.append({
                'content': chunk_text,
                'section_type': 'general',
                'section_title': 'General Content',
                'chunk_index': idx,
                'start_char': 0,
                'token_count': len(chunk_text.split()),
                'metadata': metadata
            })
        
        return chunks

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        stride = chunk_size - overlap
        for i in range(0, len(words), stride):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks


class ZoteroIngestionPipeline:
    """
    Ingest papers from Zotero into PostgreSQL with embeddings.
    Combines section-aware chunking with batch embedding generation.
    """

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.processor = PaperProcessor(self.config)
        self.embedding_dim = self.config['embedding']['embedding_dim']
        self.model = None
        self.db_conn = None

    def connect_embedding_model(self):
        """Initialize sentence-transformers with MPS device."""
        model_name = self.config['embedding']['model']
        device = self.config['embedding']['device']
        
        # SKILL.md Pattern: sentence-transformers with MPS device
        try:
            import torch
            if device == 'mps' and torch.backends.mps.is_available():
                logger.info("Using MPS (Metal Performance Shaders) for M4 Pro Mac")
                self.model = SentenceTransformer(model_name, device='mps')
            else:
                logger.info(f"Using device: {device}")
                self.model = SentenceTransformer(model_name, device=device)
        except Exception as e:
            logger.warning(f"MPS not available, falling back to CPU: {e}")
            self.model = SentenceTransformer(model_name, device='cpu')
        
        logger.info(f"Loaded embedding model: {model_name}")

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

    def ingest_paper(self, pdf_path: str, metadata: Dict) -> int:
        """
        Ingest a single paper: extract text, create section-aware chunks, and store embeddings.
        
        Returns: number of chunks created
        """
        # Extract text from PDF
        text = self.processor.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {pdf_path}")
            return 0
        
        # SKILL.md Pattern: Section-aware chunking
        chunks = self.processor.create_section_aware_chunks(text, metadata)
        
        if not chunks:
            logger.warning(f"No chunks created for {pdf_path}")
            return 0
        
        # Store in database
        cursor = self.db_conn.cursor()
        
        try:
            # Insert paper metadata
            cursor.execute(f"""
                INSERT INTO {self.config['database']['papers_table']}
                (zotero_key, title, authors, year, doi, abstract, source_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (zotero_key) DO NOTHING
                RETURNING id
            """, (
                metadata.get('zotero_key', 'unknown'),
                metadata.get('title', 'Untitled'),
                metadata.get('authors', ''),
                metadata.get('year'),
                metadata.get('doi'),
                metadata.get('abstract', ''),
                pdf_path
            ))
            
            paper_id = cursor.fetchone()
            if not paper_id:
                # Paper already exists, get its ID
                cursor.execute(
                    f"SELECT id FROM {self.config['database']['papers_table']} WHERE zotero_key = %s",
                    (metadata.get('zotero_key', 'unknown'),)
                )
                paper_id = cursor.fetchone()[0]
            else:
                paper_id = paper_id[0]
            
            # Insert chunks and embeddings
            for chunk in chunks:
                # Insert chunk
                cursor.execute(f"""
                    INSERT INTO {self.config['database']['chunks_table']}
                    (paper_id, section_type, section_title, chunk_index, content, start_char, token_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    paper_id,
                    chunk['section_type'],
                    chunk['section_title'],
                    chunk['chunk_index'],
                    chunk['content'],
                    chunk['start_char'],
                    chunk['token_count']
                ))
                
                chunk_id = cursor.fetchone()[0]
                
                # Generate embedding for chunk
                embedding = self.model.encode(
                    chunk['content'],
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )
                
                # Insert embedding
                cursor.execute(f"""
                    INSERT INTO {self.config['database']['embeddings_table']}
                    (chunk_id, embedding, model_name, embedding_dim)
                    VALUES (%s, %s, %s, %s)
                """, (
                    chunk_id,
                    embedding.tolist(),
                    self.config['embedding']['model'],
                    self.embedding_dim
                ))
            
            self.db_conn.commit()
            logger.info(f"Ingested {len(chunks)} chunks from {metadata.get('title', 'unknown')}")
            return len(chunks)
            
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Error ingesting {pdf_path}: {e}")
            return 0
        finally:
            cursor.close()

    def ingest_from_directory(self, directory: str) -> int:
        """Ingest all PDFs from a directory (simulating Zotero storage)."""
        total_chunks = 0
        pdf_files = list(Path(directory).rglob('*.pdf'))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        for pdf_path in tqdm(pdf_files, desc="Ingesting papers"):
            # Extract metadata from filename (in real scenario, get from Zotero API)
            filename = pdf_path.stem
            
            metadata = {
                'zotero_key': filename,
                'title': filename.replace('_', ' '),
                'authors': 'Unknown Authors',
                'year': 2024,
                'doi': 'unknown',
                'abstract': 'Neuroscience paper',
            }
            
            chunks = self.ingest_paper(str(pdf_path), metadata)
            total_chunks += chunks
        
        logger.info(f"Total chunks ingested: {total_chunks}")
        return total_chunks

    def ingest_sample_papers(self, num_papers: int = 50) -> int:
        """
        Ingest sample neuroscience papers (for testing without real PDFs).
        In production, this would use the ingest_from_directory method.
        """
        logger.info(f"Creating sample ingestion for {num_papers} papers")
        
        sample_sections = {
            'abstract': 'This study investigates the relationship between visual working memory capacity and attention control. We conducted experiments using a change detection paradigm with varying set sizes and attention conditions.',
            'methods': 'Participants viewed stimulus arrays containing colored squares. In the full-attention condition, all items were targets. In the divided-attention condition, only half were relevant. Brain activity was recorded using fMRI.',
            'results': 'Working memory capacity decreased under divided attention conditions. Activation patterns in prefrontal cortex correlated with individual differences in WM capacity. Neural synchronization between frontal and parietal regions predicted performance.',
            'discussion': 'These findings suggest that attention and working memory rely on partially overlapping neural mechanisms. The prefrontal cortex appears critical for maintaining focus on relevant items in working memory.',
        }
        
        cursor = self.db_conn.cursor()
        total_chunks = 0
        
        for i in range(num_papers):
            title = f"Neural Mechanisms of Working Memory and Attention - Study {i+1}"
            
            metadata = {
                'zotero_key': f'paper_{i:03d}',
                'title': title,
                'authors': f'Smith, J.; Johnson, M.; Williams, A. (2023)',
                'year': 2023,
                'doi': f'10.1234/example.{i}',
                'abstract': sample_sections['abstract'],
            }
            
            try:
                # Insert paper
                cursor.execute(f"""
                    INSERT INTO {self.config['database']['papers_table']}
                    (zotero_key, title, authors, year, doi, abstract)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (zotero_key) DO NOTHING
                    RETURNING id
                """, (
                    metadata['zotero_key'],
                    metadata['title'],
                    metadata['authors'],
                    metadata['year'],
                    metadata['doi'],
                    metadata['abstract']
                ))
                
                result = cursor.fetchone()
                if not result:
                    cursor.execute(
                        f"SELECT id FROM {self.config['database']['papers_table']} WHERE zotero_key = %s",
                        (metadata['zotero_key'],)
                    )
                    paper_id = cursor.fetchone()[0]
                else:
                    paper_id = result[0]
                
                # Create section-aware chunks
                chunk_count = 0
                for section_name, section_text in sample_sections.items():
                    chunk_text = f"{title}\n{section_text}"
                    
                    # Insert chunk
                    cursor.execute(f"""
                        INSERT INTO {self.config['database']['chunks_table']}
                        (paper_id, section_type, section_title, chunk_index, content, token_count)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        paper_id,
                        section_name,
                        section_name.title(),
                        chunk_count,
                        chunk_text,
                        len(chunk_text.split())
                    ))
                    
                    chunk_id = cursor.fetchone()[0]
                    
                    # Generate embedding
                    embedding = self.model.encode(
                        chunk_text,
                        normalize_embeddings=True,
                        convert_to_numpy=True
                    )
                    
                    # Insert embedding
                    cursor.execute(f"""
                        INSERT INTO {self.config['database']['embeddings_table']}
                        (chunk_id, embedding, model_name, embedding_dim)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        chunk_id,
                        embedding.tolist(),
                        self.config['embedding']['model'],
                        self.embedding_dim
                    ))
                    
                    chunk_count += 1
                    total_chunks += 1
                
                self.db_conn.commit()
                
            except Exception as e:
                self.db_conn.rollback()
                logger.error(f"Error ingesting sample paper {i}: {e}")
        
        cursor.close()
        logger.info(f"Ingested {num_papers} sample papers with {total_chunks} total chunks")
        return total_chunks

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()
            logger.info("Database connection closed")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest papers into RAG pipeline')
    parser.add_argument('--config', default='rag_config.json', help='Config file path')
    parser.add_argument('--directory', help='Directory with PDF files')
    parser.add_argument('--sample-papers', type=int, default=50, help='Create sample papers for testing')
    args = parser.parse_args()
    
    pipeline = ZoteroIngestionPipeline(args.config)
    pipeline.connect_embedding_model()
    pipeline.connect_database()
    
    try:
        if args.directory:
            pipeline.ingest_from_directory(args.directory)
        else:
            pipeline.ingest_sample_papers(args.sample_papers)
    finally:
        pipeline.close()
