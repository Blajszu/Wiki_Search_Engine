import sqlite3

def delete_short_articles(db_path='database.db', min_words=20):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Pobierz wszystkie artykuły do sprawdzenia
        cursor.execute("SELECT id, parsed_content FROM articles")
        articles = cursor.fetchall()
        
        # Znajdź artykuły do usunięcia
        to_delete = [
            id for id, content in articles 
            if content and len(content.split()) < min_words
        ]

        print(to_delete)
        
        # Usuń artykuły
        if to_delete:
            placeholders = ','.join(['?'] * len(to_delete))
            # cursor.execute(
            #     f"DELETE FROM articles WHERE id IN ({placeholders})",
            #     to_delete
            # )
            # conn.commit()
            print(f"Usunięto {len(to_delete)} artykułów z mniej niż {min_words} słowami.")
        else:
            print("Nie znaleziono artykułów do usunięcia.")
            
    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    delete_short_articles()