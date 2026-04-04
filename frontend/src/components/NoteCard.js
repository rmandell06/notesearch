import { useNavigate } from "react-router-dom";

export default function NoteCard({ note, showRelevance = false }) {
  const navigate = useNavigate();

  return (
    <article
      onClick={() => navigate(`/note/${note.id}`)}
      className="group p-4 border border-gray-100 rounded-lg bg-white hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors truncate">
            {note.title}
          </h3>
          <p className="mt-1 text-sm text-gray-400 line-clamp-2 leading-snug">
            {note.preview}
          </p>
        </div>
        {showRelevance && note.relevance != null && (
          <span className="shrink-0 text-xs text-gray-400 bg-gray-50 border border-gray-100 px-2 py-0.5 rounded-full mt-0.5">
            {Math.round(note.relevance * 100)}% match
          </span>
        )}
      </div>
      <p className="mt-2 text-xs text-gray-300">{note.date}</p>
    </article>
  );
}
