import { useState, useRef } from "react";

export default function UploadArea() {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const inputRef = useRef(null);

  function handleFiles(incoming) {
    const list = Array.from(incoming);
    setFiles((prev) => [...prev, ...list]);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleChange(e) {
    handleFiles(e.target.files);
    e.target.value = "";
  }

  function removeFile(index) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <div>
      <div
        role="region"
        aria-label="File upload area"
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg px-6 py-10 text-center cursor-pointer transition-colors
          ${dragging ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:border-gray-400 bg-gray-50"}`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleChange}
          className="hidden"
          data-testid="file-input"
        />
        <div className="flex flex-col items-center gap-2 pointer-events-none">
          <svg
            width="24" height="24" fill="none" stroke="currentColor"
            strokeWidth="1.5" viewBox="0 0 24 24"
            className={dragging ? "text-blue-400" : "text-gray-300"}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0-3.5 3.5M12 4l3.5 3.5" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
          </svg>
          <p className="text-sm text-gray-400">
            Drag & drop files here, or <span className="text-gray-600 underline">browse</span>
          </p>
          <p className="text-xs text-gray-300">Supports .txt, .md, .pdf</p>
        </div>
      </div>

      {files.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1.5" aria-label="Uploaded files">
          {files.map((file, i) => (
            <li
              key={i}
              className="flex items-center justify-between px-3 py-2 bg-white border border-gray-100 rounded-md text-sm"
            >
              <span className="text-gray-700 truncate" data-testid="file-name">{file.name}</span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                className="ml-3 text-gray-300 hover:text-gray-500 shrink-0"
                aria-label={`Remove ${file.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
