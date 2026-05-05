import { useNavigate } from "react-router-dom";
import { gradientClass } from "../lib/colors";
import { safePreview } from "../lib/text";

export default function NoteCard({ note, showRelevance = false, variant = "row" }) {
  const navigate = useNavigate();
  const seed = note.id ?? note.title ?? "";
  const previewText = safePreview(note.preview ?? note.content ?? "");

  if (variant === "tile") {
    return (
      <article
        onClick={() => navigate(`/note/${note.id}`)}
        className="glass r-lg fade"
        style={{ overflow: "hidden", cursor: "pointer", transition: "all 220ms ease" }}
        role="link" tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter") navigate(`/note/${note.id}`); }}
        onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}
      >
        <div
          className={gradientClass(seed)}
          style={{ position: "relative", aspectRatio: "16/9", width: "100%" }}
          aria-hidden="true"
        >
          <div style={{
            position: "absolute", inset: 0, display: "flex", alignItems: "flex-end",
            padding: "16px 20px",
            background: "linear-gradient(180deg, transparent 30%, rgba(20,17,13,0.32) 100%)",
          }}>
            <span className="serif italic" style={{
              fontSize: 40, fontWeight: 600, lineHeight: 1, color: "rgba(255,251,244,0.92)",
              fontVariationSettings: '"opsz" 144',
            }}>
              {(note.title || "?").trim().charAt(0).toUpperCase()}
            </span>
          </div>
          {showRelevance && note.relevance != null && (
            <span
              className="glass-2 r-pill tabular"
              style={{
                position: "absolute", top: 12, right: 12,
                padding: "4px 10px", fontSize: 11, fontWeight: 500, color: "var(--ink)",
              }}
            >
              {Math.round(note.relevance * 100)}%
            </span>
          )}
        </div>
        <div style={{ padding: 18 }}>
          <h3 className="serif clamp-2" style={{
            fontSize: 18, fontWeight: 600, lineHeight: 1.3, color: "var(--ink)",
            margin: 0,
          }}>
            {note.title}
          </h3>
          {previewText && (
            <p className="muted clamp-2" style={{ marginTop: 8, fontSize: 13, lineHeight: 1.55 }}>
              {previewText}
            </p>
          )}
          {note.date && (
            <p className="subtle" style={{ marginTop: 12, fontSize: 11 }}>{note.date}</p>
          )}
        </div>
      </article>
    );
  }

  // row variant — default
  return (
    <article
      onClick={() => navigate(`/note/${note.id}`)}
      className="glass r-lg row gap-4 fade"
      style={{ padding: 14, cursor: "pointer", transition: "background 200ms" }}
      role="link" tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") navigate(`/note/${note.id}`); }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--glass-2)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "var(--glass)")}
    >
      <div
        className={gradientClass(seed)}
        style={{ width: 48, height: 48, borderRadius: 10, flexShrink: 0 }}
        aria-hidden="true"
      />
      <div className="flex-1">
        <h3 className="serif clamp-1" style={{
          fontSize: 17, fontWeight: 600, lineHeight: 1.25, color: "var(--ink)",
          margin: 0,
        }}>
          {note.title}
        </h3>
        {previewText && (
          <p className="muted clamp-1" style={{ marginTop: 4, fontSize: 12 }}>
            {previewText}
          </p>
        )}
      </div>
      <div className="row gap-3 shrink-0">
        {note.date && <span className="subtle" style={{ fontSize: 12 }}>{note.date}</span>}
        {showRelevance && note.relevance != null && <RelevanceBar value={note.relevance} />}
      </div>
    </article>
  );
}

function RelevanceBar({ value }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="row gap-2">
      <div style={{ width: 64, height: 4, background: "var(--hairline-2)", borderRadius: 999, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: "var(--accent)" }} />
      </div>
      <span className="muted tabular" style={{ fontSize: 11, fontWeight: 500 }}>
        {pct}%
      </span>
    </div>
  );
}
