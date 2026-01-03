import psycopg2
import psycopg2.extras
import sys
import time

DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'

KEYWORDS = {
    'screws': ['screw', 'self drill', 'bugle', 'countersunk', 'timber screw'],
    'anchoring': ['anchor', 'dynabolt', 'chemical', 'wedge', 'sleeve', 'masonry anchor'],
    'bolts': ['bolt', 'coach', 'hex bolt', 'carriage'],
    'nails': ['nail', 'brad', 'collated', 'framing nail', 'gun nail'],
    'hardware': ['hinge', 'latch', 'handle', 'hook', 'bracket'],
    'rivets': ['rivet', 'blind rivet'],
    'roofing': ['roof', 'roofing', 'cladding screw'],
    'decking': ['deck', 'decking'],
}

def detect(content):
    text = content.lower()
    for trade, kws in KEYWORDS.items():
        if any(k in text for k in kws):
            return trade
    return 'fasteners'

brand = sys.argv[1] if len(sys.argv) > 1 else 'Zenith'
print(f'Updating {brand}...')

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cur.execute('SELECT id, content, trade FROM documents WHERE brand_name ILIKE %s', (f'%{brand}%',))
docs = cur.fetchall()
print(f'Found {len(docs)} docs')

stats = {}
updated = 0
for i, doc in enumerate(docs):
    new_trade = detect(doc['content'])
    stats[new_trade] = stats.get(new_trade, 0) + 1
    if doc['trade'] != new_trade:
        cur.execute('UPDATE documents SET trade = %s WHERE id = %s', (new_trade, doc['id']))
        updated += 1
    if (i+1) % 500 == 0:
        conn.commit()
        print(f'  {i+1}/{len(docs)}...')

conn.commit()
conn.close()

print(f'\\nUpdated {updated}/{len(docs)}')
for t, c in sorted(stats.items(), key=lambda x: -x[1]):
    print(f'  {t}: {c}')
