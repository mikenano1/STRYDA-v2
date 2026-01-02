
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

def check_docs():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT source FROM documents LIMIT 20;")
        rows = cur.fetchall()
        print("Sources:")
        for r in rows:
            print(r)
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_docs()
