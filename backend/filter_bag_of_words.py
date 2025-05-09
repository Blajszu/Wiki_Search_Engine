import sqlite3
import csv

def create_filtered_dictionary(common_words_file, output_dictionary_file='filtered_dictionary.txt', top_words=300000):
    # Połączenie z bazą danych
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Pobranie istniejącego słownika
    cursor.execute("SELECT content FROM dictionary LIMIT 1")
    dictionary_row = cursor.fetchone()
    
    if not dictionary_row:
        print("Brak słownika w bazie danych!")
        return
    
    current_dictionary = set(dictionary_row[0].split())
    print(f"Obecny słownik zawiera {len(current_dictionary)} słów")
    
    # Wczytanie listy popularnych słów (pierwszych top_words)
    common_words = set()
    with open(common_words_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # Pomijamy nagłówek
        for i, row in enumerate(csv_reader):
            if i >= top_words:
                break
            word = row[0].strip().lower()
            if word:
                common_words.add(word)
    
    print(f"Wczytano {len(common_words)} najpopularniejszych słów z pliku CSV")
    
    # Część wspólna
    filtered_dictionary = current_dictionary & common_words
    print(f"Nowy słownik będzie zawierał {len(filtered_dictionary)} słów")
    
    # Sortowanie alfabetyczne
    sorted_dictionary = sorted(filtered_dictionary)
    
    # Aktualizacja bazy danych (opcjonalnie)
    update = input("Czy chcesz zaktualizować słownik w bazie danych? (t/n): ").lower()
    if update == 't':
        # Utwórz kopię zapasową starego słownika
        cursor.execute("CREATE TABLE IF NOT EXISTS dictionary_backup AS SELECT * FROM dictionary")
        # Zaktualizuj słownik
        cursor.execute("UPDATE dictionary SET content = ?", (" ".join(sorted_dictionary),))
        conn.commit()
        print("Zaktualizowano słownik w bazie danych (stara wersja w dictionary_backup)")
    
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Użycie: python skrypt.py <ścieżka_do_pliku_csv>")
        print("Przykład: python skrypt.py word_frequency.csv")
        sys.exit(1)
    
    common_words_file = sys.argv[1]
    create_filtered_dictionary(common_words_file)