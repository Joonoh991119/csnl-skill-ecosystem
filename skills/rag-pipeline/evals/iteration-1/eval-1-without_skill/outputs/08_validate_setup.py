#!/usr/bin/env python3
"""
Validate RAG pipeline setup and dependencies.
Run this to diagnose configuration and connectivity issues.
"""

import os
import sys
from dotenv import load_dotenv
import subprocess

def check_python():
    """Check Python version."""
    print("\n[1] Python Environment")
    print("-" * 40)
    
    py_version = sys.version
    print(f"Python {py_version}")
    
    if sys.version_info < (3, 9):
        print("WARNING: Python 3.9+ recommended")
        return False
    
    print("✓ Python version OK")
    return True

def check_dependencies():
    """Check required Python packages."""
    print("\n[2] Python Dependencies")
    print("-" * 40)
    
    required = [
        'pyzotero', 'langchain', 'langchain_openai', 'PyPDF2',
        'psycopg2', 'pgvector', 'numpy', 'dotenv'
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check .env file configuration."""
    print("\n[3] Environment Configuration")
    print("-" * 40)
    
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("Create with: cp .env.example .env")
        return False
    
    print("✓ .env file exists")
    
    load_dotenv()
    
    required_vars = {
        'ZOTERO_API_KEY': 'Zotero API key',
        'ZOTERO_USER_ID': 'Zotero user ID',
        'OPENAI_API_KEY': 'OpenAI API key',
        'DB_PASSWORD': 'PostgreSQL password'
    }
    
    missing = []
    invalid = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        if not value:
            print(f"✗ {var}: not set")
            missing.append(var)
        elif '_here' in value or value == 'your_key' or value == 'your_password_here':
            print(f"✗ {var}: not configured (placeholder value)")
            invalid.append(var)
        else:
            masked = value[:10] + "***" if len(value) > 10 else "***"
            print(f"✓ {var}: {masked}")
    
    if missing or invalid:
        if missing:
            print(f"\nMissing variables: {', '.join(missing)}")
        if invalid:
            print(f"Unconfigured variables: {', '.join(invalid)}")
        print("Edit .env and set all required values")
        return False
    
    return True

def check_postgresql():
    """Check PostgreSQL connectivity."""
    print("\n[4] PostgreSQL Database")
    print("-" * 40)
    
    # Check if PostgreSQL is installed
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        print(f"✓ PostgreSQL installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print("✗ PostgreSQL not found (install with: brew install postgresql)")
        return False
    
    # Check connectivity
    db_user = os.getenv('DB_USER', 'postgres')
    
    try:
        result = subprocess.run(
            ['psql', '-U', db_user, '-c', 'SELECT version();'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.split('PostgreSQL')[1].split('on')[0].strip()
            print(f"✓ PostgreSQL connection OK (v{version})")
        else:
            print(f"✗ PostgreSQL connection failed")
            print(f"Error: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print("✗ PostgreSQL connection timeout (is it running?)")
        print("Start with: brew services start postgresql")
        return False
    except Exception as e:
        print(f"✗ PostgreSQL error: {e}")
        return False
    
    return True

def check_zotero_api():
    """Check Zotero API connectivity."""
    print("\n[5] Zotero API")
    print("-" * 40)
    
    try:
        from pyzotero import zotero
        
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        
        if not api_key or not user_id:
            print("✗ Zotero credentials not set")
            return False
        
        zot = zotero.Zotero(user_id, 'user', api_key)
        
        # Try to fetch a single item to verify API access
        items = zot.items(limit=1)
        
        print(f"✓ Zotero API connection OK")
        print(f"✓ User ID: {user_id}")
        
        # Count total items
        try:
            all_items = zot.everything(zot.items())
            print(f"✓ Total items in library: {len(all_items)}")
        except Exception as e:
            print(f"Warning: Could not count items: {e}")
        
        return True
    
    except Exception as e:
        print(f"✗ Zotero API error: {e}")
        print("Check your API key and user ID in .env")
        return False

def check_openai_api():
    """Check OpenAI API connectivity."""
    print("\n[6] OpenAI API")
    print("-" * 40)
    
    try:
        from langchain_openai import OpenAIEmbeddings
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("✗ OpenAI API key not set")
            return False
        
        embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
        
        # Try a test embedding
        test_text = "test embedding"
        embedding = embeddings.embed_query(test_text)
        
        print(f"✓ OpenAI API connection OK")
        print(f"✓ Embedding model: text-embedding-3-small")
        print(f"✓ Embedding dimension: {len(embedding)}")
        
        return True
    
    except Exception as e:
        print(f"✗ OpenAI API error: {e}")
        print("Check your API key in .env")
        return False

def check_database_schema():
    """Check if database schema is initialized."""
    print("\n[7] Database Schema")
    print("-" * 40)
    
    try:
        import psycopg2
        
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'neuroscience_rag')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')
        
        conn = psycopg2.connect(
            host=db_host, port=db_port, database=db_name,
            user=db_user, password=db_password
        )
        
        cur = conn.cursor()
        
        # Check tables
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        
        expected = ['papers', 'chunks', 'search_history']
        missing = [t for t in expected if t not in tables]
        
        if missing:
            print(f"✗ Missing tables: {', '.join(missing)}")
            print("Run: python3 01_setup_database.py")
            return False
        
        print(f"✓ Database schema OK")
        print(f"✓ Tables: {', '.join(expected)}")
        
        # Check data
        cur.execute("SELECT COUNT(*) FROM papers")
        paper_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cur.fetchone()[0]
        
        print(f"✓ Papers ingested: {paper_count}")
        print(f"✓ Chunks created: {chunk_count}")
        
        cur.close()
        conn.close()
        
        return paper_count > 0 and chunk_count > 0
    
    except Exception as e:
        print(f"✗ Database schema error: {e}")
        return False

def main():
    """Run all validation checks."""
    print("\n" + "="*50)
    print("RAG Pipeline Setup Validation")
    print("="*50)
    
    checks = [
        ("Python Environment", check_python),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("PostgreSQL", check_postgresql),
        ("Zotero API", check_zotero_api),
        ("OpenAI API", check_openai_api),
        ("Database Schema", check_database_schema),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} validation error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*50)
    print("Validation Summary")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All checks passed! Your pipeline is ready to use.")
        print("\nNext steps:")
        print("1. Ingest papers: python3 02_ingest_papers.py")
        print("2. Generate embeddings: python3 03_chunking_and_embeddings.py")
        print("3. Query papers: python3 04_rag_query_engine.py")
        return 0
    else:
        print("\n✗ Some checks failed. Review the errors above.")
        print("Run this script again after fixing the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
