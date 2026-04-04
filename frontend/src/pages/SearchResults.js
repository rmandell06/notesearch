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
    <div className="min-h-screen bg-white">
      <header className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <a href="/" className="text-lg font-semibold tracking-tight text-gray-900">NoteSearch</a>
      </header>

      <main className="max-w-2xl mx-auto px-6 pt-8 pb-16">
        <div className="mb-6">
          <SearchBar onSearch={handleSearch} initialValue={query} />
        </div>

        <p className="text-sm text-gray-400 mb-5">
          {results.length} results for <span className="text-gray-700 font-medium">"{query}"</span>
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
