import sqlite3
import sys

def decode_article(article_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Pobranie słownika
    cursor.execute("SELECT content FROM dictionary LIMIT 1")
    dictionary_row = cursor.fetchone()
    
    if not dictionary_row:
        print("Brak słownika w bazie danych!")
        return
    
    dictionary_words = dictionary_row[0].split()
    
    # Pobranie wektora dla artykułu
    cursor.execute("SELECT vector FROM articles WHERE id = ?", (article_id,))
    vector_row = cursor.fetchone()
    
    if not vector_row or not vector_row[0]:
        print(f"Artykuł o ID {article_id} nie ma wektora lub nie istnieje!")
        return
    
    vector_str = vector_row[0]
    counts = vector_str.split()
    
    print(f"\nAnaliza artykułu ID: {article_id}")
    print("=" * 30)
    
    # Wyświetlanie statystyk
    found_words = False
    for word, count in zip(dictionary_words, counts):
        count = int(count)
        if count > 0:
            print(f"{word}: {count}")
            found_words = True
    
    if not found_words:
        print("Brak wystąpień słów ze słownika w tym artykule")
    
    conn.close()

if __name__ == "__main__": 
    try:
        article_id = int(sys.argv[1])
        decode_article(article_id)
    except ValueError:
        print("Error!")
        sys.exit(1)