import { useNavigate } from "react-router-dom";

export default function NoteCard({ note, showRelevance = false }) {
  const navigate = useNavigate();

  return (
    <article
      onClick={() => navigate(`/note/${note.id}`)}
      className="p-4 rounded-xl cursor-pointer transition-all"
      style={{
        background: "#0e0e1c",
        border: "1.5px solid #1a1a2e",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.border = "1.5px solid #00e5ff";
        e.currentTarget.style.boxShadow = "0 0 20px rgba(0,229,255,0.07)";
        e.currentTarget.querySelector(".note-title").style.color = "#00e5ff";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.border = "1.5px solid #1a1a2e";
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.querySelector(".note-title").style.color = "#c8c8e0";
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3
            className="note-title text-sm font-semibold truncate transition-colors"
            style={{ color: "#c8c8e0" }}
          >
            {note.title}
          </h3>
          <p className="mt-1 text-xs line-clamp-2 leading-relaxed" style={{ color: "#3a3a5a" }}>
            {note.preview}
          </p>
        </div>
        {showRelevance && note.relevance != null && (
          <span
            className="shrink-0 mono text-xs px-2 py-0.5 rounded mt-0.5"
            style={{
              background: "rgba(191,90,242,0.08)",
              color: "#bf5af2",
              border: "1px solid rgba(191,90,242,0.25)",
              textShadow: "0 0 8px rgba(191,90,242,0.4)",
              letterSpacing: "0.02em",
            }}
          >
            {Math.round(note.relevance * 100)}%
          </span>
        )}
      </div>
      <p className="mt-2 mono text-xs" style={{ color: "#252540" }}>{note.date}</p>
    </article>
  );
}
