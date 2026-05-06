import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
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

  function handleSearch(q) {
    if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <AppShell>
      <section className="text-center mb-10 rise">
        <p className="eyebrow mb-3">Results for</p>
        <h1 className="display mb-6" style={{ fontSize: "clamp(40px, 6vw, 72px)" }}>
          <span className="serif italic" style={{ color: "var(--accent)", fontWeight: 500 }}>
            "{query}"
          </span>
        </h1>
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          <SearchBar onSearch={handleSearch} initialValue={query} large />
        </div>
      </section>

      {loading && (
        <p className="serif italic text-center fade" style={{
          fontSize: 24, color: "var(--ink-muted)", padding: "60px 0",
        }}>
          searching…
        </p>
      )}

      {error && !loading && (
        <div className="glass r-lg fade" role="alert" style={{
          padding: "16px 20px", color: "var(--error)", fontSize: 13,
        }}>
          {error}
        </div>
      )}

      {!loading && !error && results.length === 0 && query && (
        <div className="text-center fade" style={{ padding: "80px 0" }}>
          <p className="serif italic mb-2" style={{ fontSize: 28, color: "var(--ink)" }}>
            Nothing found.
          </p>
          <p className="muted" style={{ fontSize: 13 }}>
            No notes match this query — upload more, or rephrase.
          </p>
        </div>
      )}

      {!loading && !error && results.length > 0 && (
        <div className="fade">
          <p className="eyebrow mb-5">
            {results.length} {results.length === 1 ? "match" : "matches"}
          </p>
          <div className="col gap-3">
            {results.map((note, i) => (
              <div key={note.id} className="rise" style={{ animationDelay: `${i * 50}ms` }}>
                <NoteCard note={note} showRelevance />
              </div>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
