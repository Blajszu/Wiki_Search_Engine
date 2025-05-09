import sqlite3
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk

# Pobranie wymaganych zasobów NLTK (wykonaj raz)
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('omw-1.4')

def clean_text(text):
    """Funkcja czyszcząca tekst z wszystkich niepożądanych elementów"""
    if not text:
        return ""
    
    # Usunięcie wszystkich tagów HTML i szablonów (w każdej formie)
    text = re.sub(r'&lt;.*?&gt;', '', text)  # Usuwa tagi HTML zapisane jako encje
    text = re.sub(r'<.*?>', '', text)       # Usuwa zwykłe tagi HTML
    text = re.sub(r'\{\{.*?\}\}', '', text) # Usuwa szablony wiki
    text = re.sub(r'\[\[.*?\]\]', '', text) # Usuwa linki wiki
    
    # Usunięcie wzorów matematycznych (formula_XX, formulaXX, (formula XX) itp.)
    text = re.sub(r'formula[_ ]?\d+', '', text)
    text = re.sub(r'\(formula[^)]*\)', '', text)
    
    # Usunięcie pozostałych artefaktów po wzorach
    text = re.sub(r'oc\+sc', '', text)
    text = re.sub(r'oc sc', '', text)
    
    # Usunięcie znaków specjalnych, cyfr i nadmiarowych spacji
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Zmiana na małe litery
    text = text.lower()
    
    # Tokenizacja
    tokens = text.split()
    
    # Usunięcie stop words i bardzo krótkich słów
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens 
              if token not in stop_words 
              and len(token) > 2
              and not token.isdigit()]
    
    # Lematyzacja
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Filtrowanie pozostałych niechcianych słów
    unwanted_words = {'see', 'also', 'references', 'history', 'value', 'term'}
    tokens = [token for token in tokens if token not in unwanted_words]

    print(f"Przetworzono tekst: {text[:30]}...")  # Debugging output
    
    return ' '.join(tokens)

def process_database(db_path='database.db'):
    """Funkcja przetwarzająca całą bazę danych"""
    try:
        # Połączenie z bazą danych
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Pobranie wszystkich artykułów
        cursor.execute("SELECT id, content FROM articles")
        articles = cursor.fetchall()
        
        # Przetworzenie każdego artykułu
        for article in articles:
            id, content = article
            parsed_content = clean_text(content)
            
            # Aktualizacja rekordu
            cursor.execute("""
                UPDATE articles 
                SET parsed_content = ? 
                WHERE id = ?
            """, (parsed_content, id))
            
        # Zatwierdzenie zmian i zamknięcie połączenia
        conn.commit()
        print(f"Przetworzono {len(articles)} artykułów.")
        
    except sqlite3.Error as e:
        print(f"Błąd SQLite: {e}")
    except Exception as e:
        print(f"Inny błąd: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    process_database()