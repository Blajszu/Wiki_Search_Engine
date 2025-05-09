import os
import json
import sqlite3

# Ścieżka do folderu z plikami WikiExtractora
INPUT_DIR = "output"
DB_FILE = "database.db"

# Połączenie z bazą danych
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Funkcja do przetwarzania pojedynczego pliku
def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                link = data.get("url", "")
                title = data.get("title", "")
                content = data.get("text", "")

                cursor.execute("""
                    INSERT INTO articles (vector, link, title, content, parsed_content)
                    VALUES (?, ?, ?, ?, ?)
                """, ("", link, title, content, ""))
            except json.JSONDecodeError:
                print(f"Błąd dekodowania JSON w pliku {filepath}")
            except Exception as e:
                print(f"Nieoczekiwany błąd przy pliku {filepath}: {e}")
    
    print(f"Przetworzono plik: {filepath}")

# Przejście przez wszystkie foldery i pliki
for root, dirs, files in os.walk(INPUT_DIR):
    for filename in files:
        if filename.startswith("wiki_"):
            filepath = os.path.join(root, filename)
            process_file(filepath)

# Zapis i zamknięcie
conn.commit()
conn.close()

print("Import zakończony!")
