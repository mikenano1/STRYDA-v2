
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_db():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()
        
        # Check for projects table
        cur.execute("""
            SELECT exists(
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'projects'
            );
        """)
        exists = cur.fetchone()[0]
        
        print(f"Projects table exists: {exists}")
        
        if not exists:
            print("Creating projects table...")
            cur.execute("""
                CREATE TABLE projects (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL,
                    address TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Seed some data
            print("Seeding data...")
            cur.execute("""
                INSERT INTO projects (name, address) VALUES 
                ('Queen Street Reno', '123 Queen St, Auckland'),
                ('Ponsonby Villa', '45 Ponsonby Rd, Auckland'),
                ('New Lynn Build', '12 Great North Rd, Auckland');
            """)
            conn.commit()
            print("Table created and seeded.")
        else:
            # Show existing data
            cur.execute("SELECT * FROM projects;")
            rows = cur.fetchall()
            print(f"Existing projects: {len(rows)}")
            for row in rows:
                print(row)

        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
