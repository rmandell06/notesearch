import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import NoteCard from "../components/NoteCard";
import { searchNotes } from "../api";

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get("q") || "";

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults([]);

    searchNotes(query)
      .then((data) => setResults(data.results ?? data))
      .catch((err) => setError(err.message || "Search failed"))
      .finally(() => setLoading(false));
  }, [query]);

  function handleSearch(newQuery) {
    if (newQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(newQuery.trim())}`);
    }
  }

  return (
    <div className="min-h-screen">
      <header
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid #1a1a2e" }}
      >
        <a href="/" className="mono text-base font-bold tracking-tight neon-cyan" style={{ textDecoration: "none" }}>
          note<span style={{ color: "#bf5af2", textShadow: "0 0 8px rgba(191,90,242,0.55)" }}>search</span>
          <span style={{ color: "#3a3a5a" }}>.app</span>
        </a>
      </header>

      <main className="max-w-2xl mx-auto px-6 pt-8 pb-16">
        <div className="mb-6">
          <SearchBar onSearch={handleSearch} initialValue={query} />
        </div>

        {loading && (
          <p className="mono text-xs text-center py-10" style={{ color: "#3a3a5a" }} role="status" aria-label="loading">
            searching...
          </p>
        )}

        {error && !loading && (
          <div
            className="rounded-xl px-4 py-3 mono text-xs"
            role="alert"
            style={{ background: "rgba(255,45,85,0.07)", border: "1.5px solid rgba(255,45,85,0.2)", color: "#ff2d55" }}
          >
            something went wrong — {error}
          </div>
        )}

        {!loading && !error && results.length === 0 && query && (
          <div className="text-center py-14">
            <p className="mono text-xs mb-1" style={{ color: "#3a3a5a" }}>// no results</p>
            <p className="text-sm" style={{ color: "#252540" }}>
              nothing matched <span style={{ color: "#00e5ff" }}>"{query}"</span>
            </p>
          </div>
        )}

        {!loading && !error && results.length > 0 && (
          <>
            <p className="mono text-xs mb-5" style={{ color: "#3a3a5a", letterSpacing: "0.05em" }}>
              {results.length} results for{" "}
              <span style={{ color: "#00e5ff", textShadow: "0 0 8px rgba(0,229,255,0.4)" }}>
                "{query}"
              </span>
            </p>
            <div className="flex flex-col gap-3">
              {results.map((note) => (
                <NoteCard key={note.id} note={note} showRelevance />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
