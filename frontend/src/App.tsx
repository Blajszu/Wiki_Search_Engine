import React, { useState } from "react";
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import logo from "@/img/logo.png";
import "./App.css";
import "./index.css";

interface Article {
  title: string;
  link: string;
  summary: string;
}

// Lista pre-komputowanych rang SVD (k) - dostosuj, jeśli generujesz inne pliki
const SVD_RANKS = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000];

const App: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  // Metoda będzie teraz stringiem, np. "linear", "ann", lub "svd-300"
  const [method, setMethod] = useState<string>("linear"); // Zmieniamy typ na string
  const [results, setResults] = useState<Article[]>([]);
  const [searched, setSearched] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [backendError, setBackendError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setBackendError(null);
    setResults([]);

    try {
      let endpoint = "";
      let requestBody: { query: string; k?: number; } = {
          query: query.trim()
      };

      if (method === "linear") {
        endpoint = "/linear_search";
      } else if (method.startsWith("svd-")) {
        // Jeśli metoda zaczyna się od "svd-", parsjemy k
        const kValue = parseInt(method.substring(4), 10); // Usuwamy "svd-" i parsjemy liczbę
        if (isNaN(kValue)) {
             throw new Error("Invalid SVD rank selected.");
        }
        endpoint = "/svd_search";
        requestBody.k = kValue; // Dodaj parametr k dla SVD
      } else {
           console.error("Unknown search method selected:", method);
           setIsLoading(false);
           setSearched(true);
           return;
      }

      const res = await fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });

      if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || `Backend returned status ${res.status}`);
      }

      const data: Article[] = await res.json();
      setResults(data);
      setSearched(true);

    } catch (error: any) {
        console.error("Search error:", error);
        setBackendError(error.message || "An unexpected error occurred during search.");
        setResults([]);
        setSearched(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className={'app'}>
      <div className={`container ${searched ? "searched" : ""}`}>
        {(!searched || isLoading) && (
          <img className={`logo ${searched || isLoading ? "fade-out" : "fade-in"}`} src={logo} alt="Logo" />
        )}

        <div className={`search-container ${searched ? "sticky" : ""}`}>
          <div className="search-box">
            <Input
              className="min-w-[140px] w-[400px] md:w-[500px]"
              type="text"
              placeholder="Wpisz zapytanie..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
            />

            {/* Main Select for Search Method including SVD ranks */}
            <Select
              value={method}
              onValueChange={(value: string) => setMethod(value)}
              disabled={isLoading}
              className="select"
            >
              <SelectTrigger className="w-[250px] min-w-[180px]"> {/* Adjusted width */}
                <SelectValue placeholder="Select search method" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="linear">Linear Search (TF-IDF Cosine)</SelectItem>
                  {/* Dynamically generated SelectItems for each SVD rank */}
                  {SVD_RANKS.map(k => (
                    <SelectItem key={`svd-${k}`} value={`svd-${k}`}>
                        Linear SVD Search (k={k})
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>

            {/* Removed the separate Select for SVD rank */}

            <Button onClick={handleSearch} disabled={isLoading}>
              {isLoading ? (
                <span className="spinner"></span>
              ) : (
                "Search"
              )}
            </Button>
          </div>
        </div>

        {/* Display Loading Spinner */}
        {isLoading && (
            <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Searching...</p>
            </div>
        )}

        {/* Display Backend Error */}
        {!isLoading && backendError && (
             <div className="error-message text-red-500 mt-4 max-w-[800px] w-full text-center">
                 <p>{backendError}</p>
             </div>
        )}

        {/* Display Results */}
        {!isLoading && !backendError && searched && results.length > 0 && (
          <div className="results mt-4 w-full flex flex-col items-center">
            {results.map((item, index) => (
              <Card
              className={`result-card w-full max-w-[800px] mb-4 animate-fade-in-up`}
              key={index}
              style={{ animationDelay: `${index * 0.05}s` }}
              >
                <CardHeader>
                  <CardTitle className="text-lg md:text-2xl text-balance">{item.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm md:text-base text-muted-foreground">{item.summary}</p>
                </CardContent>
                <CardFooter>
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-sm font-medium underline-offset-4 hover:underline text-blue-600 dark:text-blue-400"
                  >
                    Czytaj dalej →
                  </a>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

         {/* Display No Results Message */}
        {!isLoading && !backendError && searched && results.length === 0 && (
             <div className="no-results-message mt-4 max-w-[800px] w-full text-center text-muted-foreground">
                 <p>Brak wyników dla zapytania "{query}".</p>
             </div>
        )}

      </div>
    </div>
  );
};

export default App;