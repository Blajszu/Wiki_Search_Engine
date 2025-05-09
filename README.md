# 🧠 Wyszukiwarka WikiSearch

Projekt zrealizowany w ramach **laboratorium z przedmiotu "Metody obliczeniowe w nauce i technice"**. Aplikacja pozwala na wyszukiwanie informacji w zbiorze **180 000 artykułów z Wikipedii**, korzystając z **modelu bag-of-words** zawierającego **220 000 unikalnych słów** oraz oferuje dwie metody wyszukiwania.

## 🔍 Opis działania

Aplikacja składa się z dwóch części:
- **Backend** (`/backend`) – napisany w Pythonie z użyciem Flask
- **Frontend** (`/frontend`) – aplikacja TypeScript do interakcji z użytkownikiem

Obsługuje dwa tryby wyszukiwania:

- **Cosine Similarity** (TF-IDF)
- **SVD/LSI** (dla różnych wartości `k`: 100, 200, ..., 1000)

### 📥 Dane wejściowe

Artykuły zostały wyodrębnione z dumpa Wikipedii przy użyciu **[WikiExtractora](https://github.com/attardi/wikiextractor)**. Łącznie przetworzono **180 000 artykułów**, a bag fo words zawiera **220 000 słów** po filtracji.

### 🧹 Przetwarzanie tekstu

Zarówno artykuły, jak i zapytania użytkownika są przetwarzane w ten sam sposób:
- lematyzacja (sprowadzenie słów do bezokoliczników),
- usuwanie znaków specjalnych,
- filtrowanie bardzo rzadkich słów,
- konwersja do reprezentacji TF-IDF.

### 💾 Baza danych

Dane są przechowywane w **SQLite** (`database.db`) i zawierają:
- Artykuły (tytuł, treść),
- Słownik bag-of-words z identyfikatorami i częstotliwościami.

> ⚠️ **Uwaga**: Ze względu na rozmiar, pliki bazy danych (`database.db`) oraz dane SVD (`.joblib`) nie są zawarte w repozytorium.

## 📦 Opis wykorzystanych skryptów

| Plik                            | Opis                                    |
| ------------------------------- | --------------------------------------- |
| app.py                          | Serwer Flask, obsługuje zapytania       |
| article\_checker.py             | Sprawdzenie wektora dla danego artykułu |
| calculate\_articles\_vectors.py | Oblicza TF-IDF dla wszystkich artykułów |
| create\_bag\_of\_words.py       | Tworzy bag-of-words jako unię słów z artykułów|
| database.db                     | Baza danych SQLite (nie dołączona)      |
| delete\_content.py              |Czyści kolumnę `content` w bazie danych  |
| delete\_wrong\_articles.py      | Usuwa niepotrzebne treści (np puste lub bardzo krótkie artykuły)|
| filter\_bag\_of\_words.py       | Filtrowanie słownika BOW jako wzięcie jego części wspólnej ze słowami z pliku `unigram_freq.csv`|
| generate\_svd\_files.py         | Generuje komponenty SVD do `.joblib`    |
| get\_50k\_articles.py           | Pobiera próbkę 50 000 artykułów         |
| import.py                       | Import danych do SQLite                 |
| parse\_content.py               | Lematizacja i czyszczenie tekstu        |
| unigram\_freq.csv               | Plik z 300 000 najczęściej używanych unigramów|

## Wygląd strony głównej

<div align="center">

  ![strona_glowna](https://github.com/user-attachments/assets/4a39867b-2e32-42cf-a84d-aa1c08894176)

</div>

## Wygląd wyników wyszukiwania

<div align="center">

  ![wyniki_wyszukiwania](https://github.com/user-attachments/assets/b0b938d5-a0a1-4f31-96e4-4f21bd137371)

</div>

## Opis implementacji

### Architektura rozwiązania

System został zaimplementowany jako usługa HTTP oparta na frameworku Flask, udostępniająca dwa endpointy do wyszukiwania artykułów:

 - /linear_search - wyszukiwanie liniowe z wykorzystaniem podobieństwa cosinusowego
 - /svd_search - wyszukiwanie z wykorzystaniem dekompozycji SVD (Singular Value Decomposition)

### Przetwarzanie danych

**Źródło danych:**

Dane pochodzą z bazy SQLite zawierającej artykuły z Wikipedii (180k rekordów)
Baza przechowuje:
 - Słownik terminów (dictionary)
 - Artykuły z wektorami TF (articles_180k)
 - Metadane artykułów (tytuły, linki)

**Przetwarzanie tekstu:**

Czyszczenie tekstu:
 - Usuwanie znaczników HTML/XML i szablonów Wikipedii
 - Normalizacja tekstu (usuwanie znaków specjalnych, sprowadzenie do małych liter)
 - Tokenizacja i lematyzacja przy użyciu WordNetLemmatizer
 - Filtracja stop words i nieistotnych słów

**Reprezentacja wektorowa:**
 - Budowa macierzy TF (Term Frequency) w formacie rzadkim (csc_matrix)
 - Obliczenie wag IDF (Inverse Document Frequency)
 - Normalizacja wektorów w normie L2

### Mechanizmy wyszukiwania

**1. Wyszukiwanie liniowe (`/linear_search`):**

 - Przetworzenie zapytania do postaci wektora TF-IDF
 - Obliczenie podobieństwa cosinusowego między wektorem zapytania a artykułami
 - Sortowanie wyników według malejącego podobieństwa
 - Pobranie fragmentów artykułów dla najlepszych wyników

**2. Wyszukiwanie z SVD (`/svd_search`):**

 - Dekompozycja macierzy przy użyciu SVD
 - Redukcja wymiarowości do zadanego ranku k (od 100 do 1000)
 - Przekształcanie zapytania i dokumentów do postaci zredukowanych wektorów liczbowych
 - Obliczanie podobieństwa między tymi uproszczonymi reprezentacjami

W praktyce svd nie liczy się za każdym razem przy uruchamianu aplikacji. Wszystkie macierze są obliczone wcześniej i zapisane w plikach `.joblib`, a następnie odpowiednio ładowane podczas wyszukiwania.

## ▶️ Uruchamianie
### Backend (/backend)

Wymagania: Python 3.10+

```
cd backend
python -m venv venv
source venv/bin/activate # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
### Frontend (/frontend)

Wymagania: Node.js + npm

```
cd frontend
npm install
npm run dev
```

Aplikacja frontendowa będzie domyślnie dostępna pod adresem http://localhost:5173.

## Porównanie różnych zapytań i wyników w zależności od metody wyszukiwania

### Zapytanie `"apache web server"`

| Pozycja | cosine | svd\_100 | svd\_200 | svd\_300 | svd\_400 | svd\_500 | svd\_600 | svd\_700 | svd\_800 | svd\_900 | svd\_1000 |
| ------- | ------ | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | --------- | --------- |
| 1       | ✔️     | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️        |           |
| 2       |        | ✔️       | ✔️       | ✔️       |          |          |          |          |          |           |           |
| 3       | ✔️     |          |          | ✔️       | ✔️       |          |          |          |          |           |           |
| 4       | ✔️     | ✔️       |          |          | ✔️       | ✔️       |          |          |          |           |           |
| 5       |        | ✔️       | ✔️       | ✔️       |          |          |          |          |          |           |           |
| 6       | ✔️     |          |          | ✔️       | ✔️       | ✔️       |          |          |          |           |           |
| 7       |        |          | ✔️       | ✔️       | ✔️       |          |          |          |          |           |           |
| 8       | ✔️     | ✔️       |          |          |          |          | ✔️       |          |          |           |           |
| 9       |        |          | ✔️       |          |          |          |          | ✔️       | ✔️       | ✔️        |           |
| 10      | ✔️     |          |          |          |          |          |          |          |          |           |           |

### Zapytanie `"apache web server"`

| Pozycja | cosine | svd\_100 | svd\_200 | svd\_300 | svd\_400 | svd\_500 | svd\_600 | svd\_700 | svd\_800 | svd\_900 | svd\_1000 |
| ------- | ------ | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | --------- | --------- |
| 1       | ✔️     | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️        |           |
| 2       |        | ✔️       | ✔️       | ✔️       |          |          |          |          |          |           |           |
| 3       | ✔️     |          |          | ✔️       | ✔️       |          |          |          |          |           |           |
| 4       | ✔️     | ✔️       |          |          | ✔️       | ✔️       |          |          |          |           |           |
| 5       |        | ✔️       | ✔️       | ✔️       |          |          |          |          |          |           |           |
| 6       | ✔️     |          |          | ✔️       | ✔️       | ✔️       |          |          |          |           |           |
| 7       |        |          | ✔️       | ✔️       | ✔️       |          |          |          |          |           |           |
| 8       | ✔️     | ✔️       |          |          |          |          | ✔️       |          |          |           |           |
| 9       |        |          | ✔️       |          |          |          |          | ✔️       | ✔️       | ✔️        |           |
| 10      | ✔️     |          |          |          |          |          |          |          |          |           |           |

### Zapytanie `"apache web server"`

| Pozycja | cosine | svd\_100 | svd\_200 | svd\_300 | svd\_400 | svd\_500 | svd\_600 | svd\_700 | svd\_800 | svd\_900 | svd\_1000 |
| ------- | ------ | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | --------- | --------- |
| 1       | ✔️     | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️       | ✔️        |           |
| 2       |        | ✔️       | ✔️       | ✔️       |          |          |          |          |          |           |           |
| 3       | ✔️     |          |          | ✔️       | ✔️       |          |          |          |          |           |           |
| 4       | ✔️     | ✔️       |          |          | ✔️       | ✔️       |          |          |          |           |           |
| 5       |        | ✔️       | ✔️       | ✔️       |          |          |          |          |          |           |           |
| 6       | ✔️     |          |          | ✔️       | ✔️       | ✔️       |          |          |          |           |           |
| 7       |        |          | ✔️       | ✔️       | ✔️       |          |          |          |          |           |           |
| 8       | ✔️     | ✔️       |          |          |          |          | ✔️       |          |          |           |           |
| 9       |        |          | ✔️       |          |          |          |          | ✔️       | ✔️       | ✔️        |           |
| 10      | ✔️     |          |          |          |          |          |          |          |          |           |           |
