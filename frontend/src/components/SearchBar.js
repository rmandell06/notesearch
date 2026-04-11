import { useState } from "react";

export default function SearchBar({ onSearch, initialValue = "" }) {
  const [value, setValue] = useState(initialValue);
  const [focused, setFocused] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    onSearch(value);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full" role="search">
      <div
        className="flex items-center rounded-xl transition-all"
        style={{
          background: "#0e0e1c",
          border: focused ? "1.5px solid #00e5ff" : "1.5px solid #1e1e32",
          boxShadow: focused
            ? "0 0 0 3px rgba(0,229,255,0.1), 0 0 20px rgba(0,229,255,0.08)"
            : "none",
        }}
      >
        <span className="pl-4" style={{ color: focused ? "#00e5ff" : "#2a2a4a" }}>
          <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </span>
        <input
          type="search"
          aria-label="Search notes"
          placeholder="try: 'notes on transformer attention'..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="flex-1 px-3 py-3 text-sm bg-transparent outline-none"
          style={{
            color: "#e2e2f0",
            caretColor: "#00e5ff",
          }}
        />
        {value && (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => setValue("")}
            className="pr-3 transition-colors text-xs"
            style={{ color: "#2a2a4a" }}
            onMouseEnter={(e) => (e.target.style.color = "#e2e2f0")}
            onMouseLeave={(e) => (e.target.style.color = "#2a2a4a")}
          >
            ✕
          </button>
        )}
        <button
          type="submit"
          className="m-1.5 px-4 py-1.5 mono text-xs font-bold rounded-lg transition-all"
          style={{
            background: "transparent",
            border: "1.5px solid #00e5ff",
            color: "#00e5ff",
            letterSpacing: "0.05em",
            textShadow: "0 0 8px rgba(0,229,255,0.5)",
            boxShadow: "0 0 10px rgba(0,229,255,0.1)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(0,229,255,0.08)";
            e.currentTarget.style.boxShadow = "0 0 16px rgba(0,229,255,0.2)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.boxShadow = "0 0 10px rgba(0,229,255,0.1)";
          }}
        >
          search_
        </button>
      </div>
    </form>
  );
}
