import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import NoteCard from "../components/NoteCard";

const MOCK_RESULTS = [
  {
    id: "2",
    title: "Research: vector embeddings",
    preview: "Explored cosine similarity vs dot product for nearest-neighbor search. Sentence transformers outperform bag-of-words significantly on semantic tasks...",
    date: "Mar 27, 2026",
    relevance: 0.94,
  },
  {
    id: "1",
    title: "Meeting notes — Q2 planning",
    preview: "Discussed roadmap priorities for Q2. Key themes: search UX, onboarding flow, and performance benchmarks for the embedding pipeline...",
    date: "Mar 30, 2026",
    relevance: 0.81,
  },
  {
    id: "4",
    title: "Notes on information retrieval",
    preview: "TF-IDF vs dense retrieval. BM25 is a strong baseline but struggles with paraphrase and synonym matching where embedding models excel...",
    date: "Mar 18, 2026",
    relevance: 0.76,
  },
];

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get("q") || "";
  const [results] = useState(MOCK_RESULTS);

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
      </main>
    </div>
  );
}
