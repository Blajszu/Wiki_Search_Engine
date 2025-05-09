import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("SELECT parsed_content FROM articles")
rows = cursor.fetchall()

cnt = 0

unique_words = set()
for row in rows:
    cnt += 1
    if cnt % 1000 == 0:
        print(f"Przetworzono {cnt} wierszy")
    if row[0]:
        words = row[0].split()
        unique_words.update(words)

all_words_string = " ".join(sorted(unique_words))  # sortowanie opcjonalne


try:
    cursor.execute("INSERT INTO dictionary (content) VALUES (?)", (all_words_string,))
except sqlite3.IntegrityError:
    pass

conn.commit()
conn.close()

print(f"Dodano {len(unique_words)} unikalnych słów do tabeli dictionary.")