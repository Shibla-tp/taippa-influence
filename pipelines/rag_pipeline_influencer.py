import openai, pinecone, pandas as pd, sqlite3
from docx import Document
import pdfplumber

# Initialize clients (keys omitted)
openai.api_key = "OPENAI_API_KEY"
pinecone.init(api_key="PINECONE_API_KEY", environment="us-west1-gcp")
index = pinecone.Index("brand-index")

# 1. Ingest and parse files (mock example text)
excel_text = "Brand Values: Innovation, Health; Target audience: Gen-Z fitness enthusiasts"
word_text  = "Our brand is eco-friendly and sporty. Audience: millennials, Gen-Z."
pdf_text   = "Fitness domain focus. India market. Gen-Z priority."

# (In reality, use extract_text_from_excel/… on actual files)
all_text = "\n".join([excel_text, word_text, pdf_text])

# 2. Optionally, refine context (skipped here; assume all_text already contains needed info)

# 3. Embed and index (we treat each file as a single doc chunk for demo)
for i, text in enumerate([excel_text, word_text, pdf_text], start=1):
    res = openai.Embedding.create(input=[text], model="text-embedding-ada-002")
    vec = res['data'][0]['embedding']
    meta = {"text": text}
    index.upsert(vectors=[(str(i), vec, meta)])

# 4. Mock influencer database in SQLite (instead of Postgres for demo)
conn = sqlite3.connect(':memory:')
cur = conn.cursor()
cur.execute("""
CREATE TABLE influencers (
    influencer_id INTEGER PRIMARY KEY,
    name TEXT, instagram_followers_count INTEGER,
    influencer_nationality TEXT, targeted_domain TEXT,
    influencer_age INTEGER
)
""")
# Insert some sample data
influencers_data = [
    (1, "Alice", 150000, "India",    "fitness", 22),  # Gen-Z fitness India
    (2, "Bob",   120000, "India",    "fashion", 30),
    (3, "Charlie",200000,"USA",      "fitness", 24),  # US Gen-Z
    (4, "Diana", 110000, "India",    "fitness", 19),  # Young fitness India
    (5, "Eve",   90000,  "India",    "fitness", 21),
]
cur.executemany("INSERT INTO influencers VALUES (?,?,?,?,?,?)", influencers_data)
conn.commit()

# 5. User query example
user_query = "Find Gen-Z fitness influencers in India with 100K+ followers"

# Embed query and retrieve context
q_res = openai.Embedding.create(input=[user_query], model="text-embedding-ada-002")
q_vec = q_res['data'][0]['embedding']
query_resp = index.query([q_vec], top_k=3, include_metadata=True)
retrieved_texts = [match['metadata']['text'] for match in query_resp['matches']]
context = " ".join(retrieved_texts)

# 6. Generate SQL via GPT (schema must be included)
schema = "Table influencers(id, name, instagram_followers_count, influencer_nationality, targeted_domain, influencer_age)."
prompt = f"{schema}\nContext: {context}\nUser question: {user_query}\nSQL:"
sql_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)
generated_sql = sql_response.choices[0].message.content.strip()

print("Generated SQL query:")
print(generated_sql)
# e.g. SELECT * FROM influencers WHERE instagram_followers_count >= 100000 
#       AND influencer_nationality = 'India' 
#       AND targeted_domain = 'fitness' 
#       AND influencer_age BETWEEN 18 AND 25;

# 7. Execute SQL and fetch results
try:
    cur.execute(generated_sql)
    rows = cur.fetchall()
    print("Query Results:")
    for row in rows:
        print(row)
finally:
    cur.close()
    conn.close()
