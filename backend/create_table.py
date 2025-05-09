import requests
import pandas as pd
from tabulate import tabulate

BASE_URL = "http://localhost:5000"  # Zmień na adres Twojego backendu
QUERY = "climate change effects"  # Tu wpisz swoje zapytanie

def perform_search(search_type, params=None):
    url = f"{BASE_URL}/{search_type}"
    payload = {"query": QUERY}
    if params:
        payload.update(params)
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in {search_type}: {e}")
        return []

# Wykonaj wszystkie typy wyszukiwań
results = {
    "cosine": perform_search("linear_search"),
    "svd_100": perform_search("svd_search", {"k": 100}),
    "svd_200": perform_search("svd_search", {"k": 200}),
    "svd_300": perform_search("svd_search", {"k": 300}),
    "svd_400": perform_search("svd_search", {"k": 400}),
    "svd_500": perform_search("svd_search", {"k": 500}),
    "svd_600": perform_search("svd_search", {"k": 600}),
    "svd_700": perform_search("svd_search", {"k": 700}),
    "svd_800": perform_search("svd_search", {"k": 800}),
    "svd_900": perform_search("svd_search", {"k": 900}),
    "svd_1000": perform_search("svd_search", {"k": 1000}),
}

# Przygotuj dane do tabeli
max_results = max(len(r) for r in results.values())
table_data = []

for i in range(max_results):
    row = {"Pozycja": i+1}
    for method, method_results in results.items():
        if i < len(method_results):
            row[method] = method_results[i].get("title", "BRAK TYTUŁU")
        else:
            row[method] = ""
    table_data.append(row)

# Konwersja do DataFrame pandas
df = pd.DataFrame(table_data)

# Wyświetlenie tabeli w konsoli
print(tabulate(df, headers="keys", tablefmt="pipe", showindex=False))

# Zapis do pliku Markdown
with open("wyniki_wyszukiwania.md", "w", encoding="utf-8") as f:
    f.write(tabulate(df, headers="keys", tablefmt="pipe", showindex=False))

print("\nTabela została zapisana do pliku 'wyniki_wyszukiwania.md'")