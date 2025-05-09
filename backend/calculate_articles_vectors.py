import sqlite3
from collections import defaultdict

def process_all_articles_optimized(batch_size=1000):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Pobranie słownika
    cursor.execute("SELECT content FROM dictionary LIMIT 1")
    dictionary_row = cursor.fetchone()

    if not dictionary_row:
        print("Dictionary is empty. Run dictionary creation script first.")
        return

    dictionary_words = dictionary_row[0].split()
    word_to_index = {word: idx for idx, word in enumerate(dictionary_words)}

    total_processed = 0
    batch_number = 1

    while True:
        print(f"\nStarting batch #{batch_number} (size: {batch_size})")
        
        # Znajdź nieprzetworzone artykuły (gdzie vector jest pusty lub NULL)
        cursor.execute("""
            SELECT id, parsed_content 
            FROM articles_180k
            WHERE vector IS NULL OR vector = ''
            LIMIT ?
        """, (batch_size,))
        
        articles = cursor.fetchall()
        if not articles:
            print("\nAll articles processed successfully!")
            break

        processed_in_batch = 0
        for article_id, parsed_content in articles:
            try:
                if not parsed_content:
                    # Dla pustego contentu - zapisz pusty string
                    vector_str = ""
                else:
                    word_counts = defaultdict(int)
                    for word in parsed_content.split():
                        if word in word_to_index:
                            word_counts[word] += 1
                    
                    # Format optymalny: "indeks=liczba indeks=liczba"
                    vector_str = " ".join(
                        f"{word_to_index[word]}={count}"
                        for word, count in word_counts.items()
                        if count > 0
                    )

                cursor.execute("""
                    UPDATE articles_180k
                    SET vector = ? 
                    WHERE id = ?
                """, (vector_str, article_id))
                
                processed_in_batch += 1
                if processed_in_batch % 100 == 0:
                    print(f"  Processed {processed_in_batch} in current batch")

            except Exception as e:
                print(f"Error processing article {article_id}: {str(e)}")
                conn.rollback()
                continue

        conn.commit()
        total_processed += processed_in_batch
        remaining = get_remaining_count(cursor)
        
        print(f"Completed batch #{batch_number}")
        print(f"  Processed in this batch: {processed_in_batch}")
        print(f"  Total processed: {total_processed}")
        print(f"  Remaining articles: {remaining}")
        
        batch_number += 1

    conn.close()
    print(f"\nFinal summary: Processed {total_processed} articles in total")

def get_remaining_count(cursor):
    cursor.execute("SELECT COUNT(*) FROM articles_180k WHERE vector IS NULL OR vector = ''")
    return cursor.fetchone()[0]

if __name__ == "__main__":
    process_all_articles_optimized(batch_size=1000)