#!/usr/bin/env python3
"""
Ingest papers from Zotero library and extract text from PDFs.
Stores metadata in PostgreSQL and prepares documents for chunking.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from pyzotero import zotero
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import psycopg2
from tqdm import tqdm

load_dotenv()

class ZoteroIngester:
    def __init__(self):
        """Initialize Zotero API and database connection."""
        self.api_key = os.getenv("ZOTERO_API_KEY")
        self.user_id = os.getenv("ZOTERO_USER_ID")
        self.library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "user")
        
        if not self.api_key or not self.user_id:
            print("ERROR: ZOTERO_API_KEY and ZOTERO_USER_ID required in .env")
            sys.exit(1)
        
        # Initialize Zotero API
        self.zot = zotero.Zotero(self.user_id, self.library_type, self.api_key)
        
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
    
    def fetch_papers(self, collection_name: Optional[str] = None) -> List[Dict]:
        """Fetch papers from Zotero library."""
        print(f"Fetching papers from Zotero...")
        
        try:
            if collection_name:
                # Get collection key by name
                collections = self.zot.collections()
                collection_key = None
                for coll in collections:
                    if coll['data']['name'] == collection_name:
                        collection_key = coll['key']
                        break
                
                if not collection_key:
                    print(f"Collection '{collection_name}' not found")
                    items = self.zot.everything(self.zot.items())
                else:
                    items = self.zot.collection_items(collection_key)
            else:
                # Fetch all items
                items = self.zot.everything(self.zot.items())
            
            papers = []
            for item in items:
                if item['data']['itemType'] in ['journalArticle', 'conferencePaper', 'book']:
                    papers.append(item)
            
            print(f"Found {len(papers)} relevant papers")
            return papers
        
        except Exception as e:
            print(f"ERROR fetching papers: {e}")
            sys.exit(1)
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page_num, page in enumerate(reader.pages):
                try:
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
            
            return text if text.strip() else None
        
        except Exception as e:
            print(f"ERROR reading PDF {pdf_path}: {e}")
            return None
    
    def get_attachment_path(self, item_key: str) -> Optional[str]:
        """Get PDF attachment path from Zotero item."""
        try:
            children = self.zot.children(item_key)
            for child in children:
                if child['data']['itemType'] == 'attachment':
                    if child['data'].get('contentType') == 'application/pdf':
                        # Try to get file path from linkMode
                        if child['data'].get('linkMode') == 'linked_file':
                            path = child['data'].get('path', '')
                            if path:
                                return path
        except Exception as e:
            print(f"Warning: Could not fetch attachments for {item_key}: {e}")
        
        return None
    
    def ingest_papers(self, collection_name: Optional[str] = None):
        """Ingest papers into database."""
        papers = self.fetch_papers(collection_name)
        
        conn = self.connect_db()
        cur = conn.cursor()
        
        ingested = 0
        skipped = 0
        
        print(f"\nIngesting {len(papers)} papers...")
        
        for paper in tqdm(papers, desc="Ingesting papers"):
            try:
                data = paper['data']
                zotero_id = paper['key']
                title = data.get('title', 'Untitled')
                
                # Extract authors
                creators = data.get('creators', [])
                authors = ', '.join([
                    f"{c.get('lastName', '')}, {c.get('firstName', '')}"
                    for c in creators
                    if c.get('creatorType') == 'author'
                ])
                
                year = data.get('date', '')
                abstract = data.get('abstractNote', '')
                doi = data.get('DOI', '')
                url = data.get('url', '')
                
                # Try to get PDF text
                pdf_text = None
                pdf_path = self.get_attachment_path(zotero_id)
                
                if pdf_path and os.path.exists(pdf_path):
                    pdf_text = self.extract_pdf_text(pdf_path)
                
                # Store in database
                cur.execute("""
                    INSERT INTO papers 
                    (zotero_id, title, authors, year, abstract, doi, url, pdf_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (zotero_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (zotero_id, title, authors, year, abstract, doi, url, pdf_path))
                
                paper_id = cur.fetchone()[0]
                
                # Store document content for later chunking
                doc_content = f"""
Title: {title}
Authors: {authors}
Year: {year}
DOI: {doi}
Abstract: {abstract}

Content:
{pdf_text if pdf_text else 'No PDF available'}
"""
                
                # Save to local file for chunking
                doc_dir = Path("documents")
                doc_dir.mkdir(exist_ok=True)
                doc_file = doc_dir / f"{paper_id}_{zotero_id}.txt"
                
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(doc_content)
                
                conn.commit()
                ingested += 1
            
            except psycopg2.IntegrityError:
                conn.rollback()
                skipped += 1
            except Exception as e:
                print(f"ERROR ingesting {paper.get('data', {}).get('title', 'Unknown')}: {e}")
                conn.rollback()
                skipped += 1
        
        cur.close()
        conn.close()
        
        print(f"\nIngestion complete:")
        print(f"  Ingested: {ingested}")
        print(f"  Skipped: {skipped}")
        print(f"  Documents saved to: ./documents/")

if __name__ == "__main__":
    ingester = ZoteroIngester()
    collection = None  # Set to specific collection name if desired
    ingester.ingest_papers(collection)
