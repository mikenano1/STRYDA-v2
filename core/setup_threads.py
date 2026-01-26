
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

def setup_threads():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()
        
        # Check if threads table exists
        cur.execute("""
            SELECT exists(
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'threads'
            );
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            print("Creating threads table...")
            cur.execute("""
                CREATE TABLE threads (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    project_id UUID REFERENCES projects(id),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    preview_text TEXT
                );
            """)
            conn.commit()
            print("Threads table created.")
            
            # Seed some sample threads
            print("Seeding threads...")
            # Get a project ID
            cur.execute("SELECT id FROM projects LIMIT 1;")
            pid = cur.fetchone()[0]
            
            cur.execute("""
                INSERT INTO threads (session_id, title, project_id, preview_text) VALUES 
                ('sess_demo_1', 'Joist Spacing Query', %s, 'What is the max span for 140x45...'),
                ('sess_demo_2', 'Waterproofing Check', NULL, 'Can I use Ardex on plywood...'),
                ('sess_demo_3', 'Foundation Depth', %s, 'How deep for standard piles...');
            """, (pid, pid))
            conn.commit()
            print("Seeding complete.")
            
        else:
            print("Threads table already exists.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_threads()
