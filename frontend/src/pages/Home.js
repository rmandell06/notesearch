import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import NoteCard from "../components/NoteCard";
import UploadArea from "../components/UploadArea";

const RECENT_NOTES = [
  {
    id: "1",
    title: "Meeting notes — Q2 planning",
    preview: "Discussed roadmap priorities for Q2. Key themes: search UX, onboarding flow, and performance benchmarks...",
    date: "Mar 30, 2026",
  },
  {
    id: "2",
    title: "Research: vector embeddings",
    preview: "Explored cosine similarity vs dot product for nearest-neighbor search. Sentence transformers outperform...",
    date: "Mar 27, 2026",
  },
  {
    id: "3",
    title: "Book notes — Thinking Fast and Slow",
    preview: "System 1 vs System 2 thinking. Anchoring bias affects estimates even when people know the anchor is random...",
    date: "Mar 22, 2026",
  },
];

export default function Home() {
  const [showUpload, setShowUpload] = useState(false);
  const navigate = useNavigate();

  function handleSearch(query) {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <span className="text-lg font-semibold tracking-tight text-gray-900">NoteSearch</span>
        <nav className="flex gap-5 text-sm text-gray-500">
          <a href="/" className="hover:text-gray-900">Home</a>
          <button
            onClick={() => setShowUpload((v) => !v)}
            className="hover:text-gray-900 cursor-pointer"
          >
            Upload
          </button>
        </nav>
      </header>

      <main className="max-w-2xl mx-auto px-6 pt-24 pb-16">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">Search your notes</h1>
          <p className="text-gray-400 text-sm">Find anything across all your uploads using semantic search</p>
        </div>

        <SearchBar onSearch={handleSearch} />

        {showUpload && (
          <div className="mt-8">
            <UploadArea />
          </div>
        )}

        <section className="mt-14">
          <h2 className="text-xs font-medium text-gray-400 uppercase tracking-widest mb-4">Recent notes</h2>
          <div className="flex flex-col gap-3">
            {RECENT_NOTES.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
