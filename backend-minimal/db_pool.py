"""
PostgreSQL Connection Pooling for STRYDA-v2 Supabase
Reuses database connections to reduce overhead and improve performance
"""

import psycopg2
from psycopg2 import pool
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Global connection pool
_connection_pool: Optional[pool.SimpleConnectionPool] = None

def init_connection_pool(minconn: int = 2, maxconn: int = 10):
    """Initialize the connection pool"""
    global _connection_pool
    
    if _connection_pool is not None:
        print("⚠️ Connection pool already initialized")
        return _connection_pool
    
    try:
        _connection_pool = pool.SimpleConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            dsn=DATABASE_URL,
            sslmode="require",
            connect_timeout=10
        )
        print(f"✅ PostgreSQL connection pool initialized (min={minconn}, max={maxconn})")
        return _connection_pool
    except Exception as e:
        print(f"❌ Connection pool initialization failed: {e}")
        return None

def get_db_connection():
    """Get a connection from the pool"""
    global _connection_pool
    
    # Initialize pool if not yet created
    if _connection_pool is None:
        init_connection_pool()
    
    try:
        conn = _connection_pool.getconn()
        return conn
    except Exception as e:
        print(f"❌ Failed to get connection from pool: {e}")
        # Fallback to direct connection
        return psycopg2.connect(DATABASE_URL, sslmode="require")

def return_db_connection(conn):
    """Return a connection to the pool"""
    global _connection_pool
    
    if _connection_pool is not None and conn is not None:
        try:
            _connection_pool.putconn(conn)
        except Exception as e:
            print(f"⚠️ Failed to return connection to pool: {e}")
            # Close connection if can't return to pool
            try:
                conn.close()
            except:
                pass

def get_pool_stats() -> dict:
    """Get connection pool statistics"""
    global _connection_pool
    
    if _connection_pool is None:
        return {
            "status": "not_initialized",
            "minconn": 0,
            "maxconn": 0,
            "active": 0
        }
    
    try:
        # SimpleConnectionPool doesn't expose stats directly
        # Return configuration info
        return {
            "status": "active",
            "minconn": _connection_pool.minconn,
            "maxconn": _connection_pool.maxconn,
            "pool_type": "SimpleConnectionPool"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def close_pool():
    """Close all connections in the pool"""
    global _connection_pool
    
    if _connection_pool is not None:
        try:
            _connection_pool.closeall()
            print("✅ Connection pool closed")
        except Exception as e:
            print(f"⚠️ Error closing connection pool: {e}")
        finally:
            _connection_pool = None

# Initialize pool on module import
init_connection_pool()

# Export for use in other modules
__all__ = ['get_db_connection', 'return_db_connection', 'get_pool_stats', 'close_pool']
