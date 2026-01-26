import os
import psycopg2
import psycopg2.extras
from typing import Optional, Dict, List, Any

def get_conn():
    """Get database connection or None if not configured"""
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("⚠️ DATABASE_URL not configured")
        return None
    try:
        conn = psycopg2.connect(dsn)
        print("✅ Database connected")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def search_embeddings(
    conn, 
    query_vec: List[float], 
    top_k: int = 6, 
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar documents using vector similarity
    
    Args:
        conn: Database connection
        query_vec: Query embedding vector
        top_k: Number of results to return
        filters: Optional filters (e.g., {"source": "NZMRM"})
    
    Returns:
        List of documents with scores
    """
    where = []
    params = [query_vec, top_k]
    
    if filters and "source" in filters:
        where.append("source = %s")
        params.insert(1, filters["source"])
    
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    
    sql = f"""
      WITH q AS (SELECT %s::vector AS embedding)
      SELECT id, source, page, content,
             1 - (documents.embedding <=> (SELECT embedding FROM q)) AS score
      FROM documents
      {where_sql}
      ORDER BY documents.embedding <=> (SELECT embedding FROM q)
      LIMIT %s;
    """
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [dict(r) for r in rows]
            print(f"✅ Found {len(results)} relevant documents")
            return results
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return []
