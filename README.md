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

Artykuły zostały wyodrębnione z dumpa Wikipedii przy użyciu **[WikiExtractora](https://github.com/attardi/wikiextractor)**. Łącznie przetworzono **180 000 artykułów**, a bag of words zawiera **220 000 słów** po filtracji.

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
 - Bag of words (dictionary)
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
|   Pozycja | cosine                         | svd_100                       | svd_200               | svd_300               | svd_400               | svd_500               | svd_600               | svd_700               | svd_800               | svd_900               | svd_1000              |
|----------:|:-------------------------------|:------------------------------|:----------------------|:----------------------|:----------------------|:----------------------|:----------------------|:----------------------|:----------------------|:----------------------|:----------------------|
|         1 | Apache HTTP Server             | NCSA HTTPd                    | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            | NCSA HTTPd            |
|         2 | Web server                     | Server-side scripting         | Server-side scripting | Server-side scripting | Server-side scripting | Server-side scripting | Server-side scripting | Server-side scripting | Server-side scripting | Server-side scripting | Server-side scripting |
|         3 | Server (computing)             | Internet Information Services | Server (computing)    | Squid (software)      | Web cache             | Web cache             | Web cache             | Web cache             | Web cache             | Web cache             | Web cache             |
|         4 | The Apache Software Foundation | Internet Explorer             | Squid (software)      | Name server           | Squid (software)      | Squid (software)      | Squid (software)      | Squid (software)      | Squid (software)      | Squid (software)      | Squid (software)      |
|         5 | Apache                         | Mac OS X Server               | Name server           | Server hog            | Server hog            | AOLserver             | Server hog            | Server hog            | HTTP                  | Httpd                 | Server hog            |
|         6 | Boeing AH-64 Apache            | IPX/SPX                       | Server hog            | Server (computing)    | Name server           | Server hog            | AOLserver             | AOLserver             | Httpd                 | Server hog            | Httpd                 |
|         7 | Mac OS X Server                | Microsoft FrontPage           | Web developer         | Web cache             | AOLserver             | Web server            | Web server            | Httpd                 | Server hog            | HTTP                  | Web server            |
|         8 | Apache Junction, Arizona       | Name server                   | WebDAV                | Virtual hosting       | Web server            | Web developer         | Web developer         | HTTP                  | AOLserver             | Web server            | HTTP                  |
|         9 | Web developer                  | Netscape Navigator            | TOC protocol          | Web developer         | Virtual hosting       | HTTP                  | HTTP                  | Web server            | Web server            | AOLserver             | Active Server Pages   |
|        10 | Server hog                     | TOC protocol                  | SPNEGO                | AOLserver             | Httpd                 | Httpd                 | Httpd                 | Virtual hosting       | Virtual hosting       | Virtual hosting       | Server (computing)    |

### Zapytanie `"ancient Egyptian civilization achievements"`

|   Pozycja | cosine                         | svd_100                         | svd_200                         | svd_300                         | svd_400          | svd_500          | svd_600          | svd_700          | svd_800           | svd_900           | svd_1000          |
|----------:|:-------------------------------|:--------------------------------|:--------------------------------|:--------------------------------|:-----------------|:-----------------|:-----------------|:-----------------|:------------------|:------------------|:------------------|
|         1 | Civilization                   | Upper Egypt                     | Upper Egypt                     | Ancient Egypt                   | Ancient Egypt    | Ancient Egypt    | Ancient Egypt    | Ancient Egypt    | Ancient Egypt     | Ancient Egypt     | Ancient Egypt     |
|         2 | Ancient Egypt                  | Ancient Egypt                   | Ahmes                           | Ahmes                           | Ahmes            | Ahmes            | Ahmes            | Ahmes            | Ahmes             | Ahmes             | Ahmes             |
|         3 | Music of Egypt                 | Index of Egypt-related articles | Ancient Egypt                   | Culture of Egypt                | Culture of Egypt | Culture of Egypt | Culture of Egypt | Culture of Egypt | Culture of Egypt  | Culture of Egypt  | Culture of Egypt  |
|         4 | Pharaonism                     | Egyptology                      | Culture of Egypt                | Upper Egypt                     | Upper Egypt      | Pharaonism       | Zahi Hawass      | Zahi Hawass      | Pharaonism        | Pharaonism        | Pharaonism        |
|         5 | Culture of Egypt               | Ahmes                           | Zahi Hawass                     | Zahi Hawass                     | Zahi Hawass      | Zahi Hawass      | Pharaonism       | Pharaonism       | Zahi Hawass       | Maat              | Egyptian language |
|         6 | Kardashev scale                | Hemsut                          | Index of Egypt-related articles | Egyptology                      | Pharaonism       | Upper Egypt      | Egyptology       | Egyptology       | Maat              | Zahi Hawass       | Hetepet           |
|         7 | Civilization II                | Khensit                         | Pharaonism                      | Pharaonism                      | Egyptology       | Egyptology       | Hetepet          | Hetepet          | Hetepet           | Hetepet           | Maat              |
|         8 | Civilization (1980 board game) | Lower Egypt                     | Lower Egypt                     | Lower Egypt                     | Arensnuphis      | Hetepet          | Arensnuphis      | Upper Egypt      | Egyptology        | Egyptian language | Zahi Hawass       |
|         9 | Egyptian language              | Zahi Hawass                     | Egyptology                      | Index of Egypt-related articles | Copts            | Arensnuphis      | Upper Egypt      | Arensnuphis      | Egyptian language | Egyptology        | Upper Egypt       |
|        10 | Civilization III               | Culture of Egypt                | Narmer                          | History of Egypt                | History of Egypt | Maat             | Maat             | Maat             | Upper Egypt       | Upper Egypt       | Arensnuphis       |

### Zapytanie `"climate change effects"`

|   Pozycja | cosine                                 | svd_100                          | svd_200                        | svd_300                                | svd_400                                | svd_500                                | svd_600                                | svd_700                                | svd_800                                | svd_900                                | svd_1000                               |
|----------:|:---------------------------------------|:---------------------------------|:-------------------------------|:---------------------------------------|:---------------------------------------|:---------------------------------------|:---------------------------------------|:---------------------------------------|:---------------------------------------|:---------------------------------------|:---------------------------------------|
|         1 | Climate                                | Extreme weather                  | Climatology                    | Climatology                            | Climate                                | Climate                                | Climate                                | Climate                                | Climate                                | Climate                                | Climate                                |
|         2 | Köppen climate classification          | Natural disaster                 | Climate                        | Climate                                | Climatology                            | Climatology                            | Climatology                            | Climatology                            | Climatology                            | Climatology                            | Köppen climate classification          |
|         3 | Continental climate                    | Climatology                      | Extreme weather                | Global cooling                         | Scientific consensus on climate change | Köppen climate classification          | Köppen climate classification          | Köppen climate classification          | Köppen climate classification          | Köppen climate classification          | Climatology                            |
|         4 | Climate variability and change         | Climate                          | Cloud feedback                 | Scientific consensus on climate change | Köppen climate classification          | Scientific consensus on climate change | Temperate climate                      | Scientific consensus on climate change | Scientific consensus on climate change | Scientific consensus on climate change | Scientific consensus on climate change |
|         5 | Climatology                            | Land use                         | Climate variability and change | List of climate change controversies   | Global cooling                         | Temperate climate                      | Scientific consensus on climate change | Temperate climate                      | Temperate climate                      | Temperate climate                      | Temperate climate                      |
|         6 | Temperate climate                      | El Niño–Southern Oscillation     | Global dimming                 | Cloud feedback                         | List of climate change controversies   | Continental climate                    | Continental climate                    | Continental climate                    | Continental climate                    | List of climate change controversies   | List of climate change controversies   |
|         7 | Climate of the Alps                    | Köppen climate classification    | Global cooling                 | Global dimming                         | Climate variability and change         | List of climate change controversies   | Climate variability and change         | List of climate change controversies   | List of climate change controversies   | Continental climate                    | Continental climate                    |
|         8 | Scientific consensus on climate change | Climate variability and change   | Köppen climate classification  | Psilocybin                             | Temperate climate                      | Climate variability and change         | List of climate change controversies   | Global cooling                         | Climate variability and change         | Climate variability and change         | Climate variability and change         |
|         9 | Mediterranean climate                  | List of severe weather phenomena | El Niño–Southern Oscillation   | Effects of cannabis                    | Continental climate                    | Global cooling                         | Global cooling                         | Climate variability and change         | Global cooling                         | Climate of the Alps                    | Subtropics                             |
|        10 | Met Office Hadley Centre               | Quasi-biennial oscillation       | Climate of the Alps            | Köppen climate classification          | Climate of the Alps                    | Subtropics                             | Subtropics                             | Subtropics                             | Subtropics                             | Subtropics                             | Climate of the Alps                    |
