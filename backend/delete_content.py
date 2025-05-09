import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("SELECT id, content FROM articles_180k")
rows = cursor.fetchall()

def truncate_to_n_words(text, n=50):
    return ' '.join(text.split()[:n])

for article_id, content in rows:
    truncated = truncate_to_n_words(content, 50)
    cursor.execute("UPDATE articles_180k SET content = ? WHERE id = ?", (truncated, article_id))

conn.commit()
conn.close()