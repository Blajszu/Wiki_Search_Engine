import sqlite3
import random

def create_articles_sample(sample_size=50000):
    # Połączenie z bazą danych
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. Sprawdzenie czy tabela articles istnieje
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
    if not cursor.fetchone():
        print("Tabela 'articles' nie istnieje w bazie danych!")
        return
    
    # 2. Zmiana nazwy obecnej tabeli na backup
    print("Tworzenie kopii zapasowej...")
    cursor.execute("ALTER TABLE articles RENAME TO articles_backup")
    
    # 3. Pobranie wszystkich ID artykułów z kopii zapasowej
    print("Pobieranie ID artykułów...")
    cursor.execute("SELECT id FROM articles_backup")
    all_ids = [row[0] for row in cursor.fetchall()]
    
    # 4. Losowanie próbki
    print("Losowanie próbki...")
    sampled_ids = random.sample(all_ids, min(sample_size, len(all_ids)))
    
    # 5. Tworzenie nowej tabeli articles z próbką
    print("Tworzenie nowej tabeli articles...")
    
    # a) Tworzymy nową tabelę z tą samą strukturą
    cursor.execute("CREATE TABLE articles AS SELECT * FROM articles_backup WHERE 1=0")
    
    # b) Wstawiamy wybrane artykuły partiami (dla wydajności)
    batch_size = 1000
    for i in range(0, len(sampled_ids), batch_size):
        batch_ids = sampled_ids[i:i + batch_size]
        placeholders = ','.join(['?'] * len(batch_ids))
        cursor.execute(f"""
            INSERT INTO articles 
            SELECT * FROM articles_backup 
            WHERE id IN ({placeholders})
        """, batch_ids)
        print(f"Załadowano {min(i + batch_size, len(sampled_ids))}/{len(sampled_ids)} artykułów")
    
    # 6. Tworzenie indeksów (jeśli były w oryginale)
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_id ON articles (id)")
    except:
        pass
    
    # Zatwierdzenie zmian
    conn.commit()
    conn.close()
    
    print("\nZakończono pomyślnie!")
    print(f"- Utworzono kopię zapasową: articles_backup ({len(all_ids)} artykułów)")
    print(f"- Utworzono nową tabelę articles z {len(sampled_ids)} artykułami")

if __name__ == "__main__":
    create_articles_sample(50000)